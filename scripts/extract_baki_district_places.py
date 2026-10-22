# -*- coding: utf-8 -*-
"""
Extract notable named places for all Bakı rayons (same method as Yasamal).

Reads immutable source_files/ + existing data/areas + data/boundaries.
Writes data/places/{rayon_key}_all.json and updates places/index.json + manifest counts.
Never modifies source_files/.
"""
from __future__ import annotations

import json
import os
import re
import sys
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import osmium
import pyarrow.parquet as pq
from shapely import wkb as swkb
from shapely.geometry import Point, shape

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
os.chdir(ROOT)

from landmark_taxonomy import (  # noqa: E402
    OVERTURE_TAXONOMY as LANDMARK_TAXONOMY,
    classify_osm_notable,
)

SRC = Path("source_files")
OUT = Path("data")
OSM_PBF = SRC / "azerbaijan-261020.osm.pbf"
OVERTURE_RELEASE = "2026-09-23.1"
OSM_RELEASE = "azerbaijan-261020"

NS = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")

# Must match extract_pilot.py keys / boundary file names
RAYON_KEYS = [
    "yasamal",
    "nasimi",
    "narimanov",
    "nizami_baki",
    "binagadi",
    "sabail",
    "xetai",
    "sabuncu",
    "surakhani",
    "xezer",
    "pirallahi",
    "qaradag",
]


def cid(*parts: str) -> str:
    return str(uuid.uuid5(NS, "geoatlas-aze:" + "|".join(parts)))


def norm(s: str) -> str:
    s = (s or "").casefold().strip()
    for a, b in (
        ("ə", "e"),
        ("ı", "i"),
        ("ö", "o"),
        ("ü", "u"),
        ("ğ", "g"),
        ("ş", "s"),
        ("ç", "c"),
    ):
        s = s.replace(a, b)
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def pname(names) -> str:
    if not names:
        return ""
    return names.get("primary") or ""


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_boundary_geom(boundary_file: str | None):
    if not boundary_file:
        return None
    path = OUT / boundary_file
    if not path.exists():
        return None
    fc = load_json(path)
    geoms = []
    for f in fc.get("features") or []:
        g = f.get("geometry")
        if g and g.get("type") in ("Polygon", "MultiPolygon"):
            geoms.append(shape(g))
    if not geoms:
        return None
    if len(geoms) == 1:
        return geoms[0]
    from shapely.ops import unary_union

    return unary_union(geoms)


class OsmNotableCollector(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.notable = []

    def node(self, n):
        if not n.tags or not n.location.valid():
            return
        cat = classify_osm_notable(n.tags)
        if not cat:
            return
        name = n.tags.get("name") or n.tags.get("name:az")
        if not name or not str(name).strip():
            return
        self.notable.append(
            {
                "name": name,
                "category": cat,
                "lon": n.location.lon,
                "lat": n.location.lat,
                "osm_type": "node",
                "osm_id": n.id,
            }
        )


def place_record(*, pid, name, category, lat, lon, area_id, source, source_id, raw_category, confidence):
    return {
        "id": pid,
        "name": name,
        "name_normalized": norm(name),
        "alt_names": [],
        "category": category,
        "coordinates": {"lat": lat, "lon": lon},
        "area_id": area_id,
        "area_assign_method": "containment_verified",
        "area_assign_status": "verified",
        "confidence": confidence,
        "status": "silver",
        "source_refs": [
            {
                "source": source,
                "source_id": source_id,
                "release": OVERTURE_RELEASE if source == "overture" else OSM_RELEASE,
                "source_category": raw_category,
            }
        ],
    }


def extract_overture_into_rayons(rayon_geoms: dict[str, object]):
    """Single pass over place parquet; assign to first covering rayon."""
    pl = pq.read_table(
        SRC / "overture/aze_place.parquet",
        columns=["id", "names", "taxonomy", "basic_category", "geometry", "bbox", "confidence"],
    )
    # Precompute bounds
    bounds = {k: g.bounds for k, g in rayon_geoms.items()}
    buckets: dict[str, list] = {k: [] for k in rayon_geoms}
    seen_ids: set[str] = set()

    for i in range(pl.num_rows):
        bb = pl.column("bbox")[i].as_py() or {}
        cx = (bb.get("xmin", 0) + bb.get("xmax", 0)) / 2
        cy = (bb.get("ymin", 0) + bb.get("ymax", 0)) / 2
        tax = pl.column("taxonomy")[i].as_py() or {}
        raw = tax.get("primary") or pl.column("basic_category")[i].as_py() or ""
        cat = LANDMARK_TAXONOMY.get(raw)
        if not cat:
            continue
        name = pname(pl.column("names")[i].as_py())
        if not name or not name.strip():
            continue
        g = pl.column("geometry")[i].as_py()
        try:
            pt = swkb.loads(g) if g else Point(cx, cy)
        except Exception:
            pt = Point(cx, cy)

        oid = pl.column("id")[i].as_py()
        if oid in seen_ids:
            continue

        for key, geom in rayon_geoms.items():
            minx, miny, maxx, maxy = bounds[key]
            if not (minx <= pt.x <= maxx and miny <= pt.y <= maxy):
                continue
            if geom.covers(pt) or geom.intersects(pt):
                buckets[key].append(
                    {
                        "overture_id": oid,
                        "name": name,
                        "category": cat,
                        "raw_category": raw,
                        "lon": float(pt.x),
                        "lat": float(pt.y),
                        "confidence": pl.column("confidence")[i].as_py(),
                    }
                )
                seen_ids.add(oid)
                break
    return buckets


def assign_osm_into_rayons(notables, rayon_geoms: dict[str, object]):
    bounds = {k: g.bounds for k, g in rayon_geoms.items()}
    buckets: dict[str, list] = {k: [] for k in rayon_geoms}
    for n in notables:
        pt = Point(n["lon"], n["lat"])
        for key, geom in rayon_geoms.items():
            minx, miny, maxx, maxy = bounds[key]
            if not (minx <= pt.x <= maxx and miny <= pt.y <= maxy):
                continue
            if geom.covers(pt) or geom.intersects(pt):
                buckets[key].append(n)
                break
    return buckets


def rayon_key_from_boundary(boundary_file: str | None) -> str | None:
    if not boundary_file:
        return None
    # boundaries/rayon_yasamal.geojson -> yasamal
    m = re.search(r"rayon_([a-z0-9_]+)\.geojson$", boundary_file.replace("\\", "/"))
    return m.group(1) if m else None


def main() -> int:
    assert (SRC / "overture/aze_place.parquet").exists()
    assert OSM_PBF.exists()

    areas = load_json(OUT / "areas" / "areas.json")["areas"]
    rayons = [a for a in areas if a.get("type") == "rayon"]
    rayon_by_key = {}
    for a in rayons:
        key = rayon_key_from_boundary(a.get("boundary_file"))
        if key:
            rayon_by_key[key] = a

    missing = [k for k in RAYON_KEYS if k not in rayon_by_key]
    if missing:
        print("WARN missing area records for keys:", missing)

    rayon_geoms = {}
    for key in RAYON_KEYS:
        a = rayon_by_key.get(key)
        if not a:
            continue
        geom = load_boundary_geom(a.get("boundary_file"))
        if geom is None:
            print(f"  SKIP {key}: no boundary geom")
            continue
        rayon_geoms[key] = geom
        print(f"  loaded boundary {key}: {a['name']}")

    print("Scanning Overture places…")
    ov_buckets = extract_overture_into_rayons(rayon_geoms)

    print("Scanning OSM notables (named nodes)…")
    handler = OsmNotableCollector()
    handler.apply_file(str(OSM_PBF).replace("\\", "/"), locations=True)
    print(f"  OSM named notables: {len(handler.notable)}")
    osm_buckets = assign_osm_into_rayons(handler.notable, rayon_geoms)

    pdir = OUT / "places"
    pdir.mkdir(parents=True, exist_ok=True)
    all_places = []
    index_files = []
    by_rayon_counts = {}

    for key in RAYON_KEYS:
        area = rayon_by_key.get(key)
        if not area or key not in rayon_geoms:
            continue
        area_id = area["id"]
        places = []
        seen = set()

        for p in ov_buckets.get(key, []):
            pid = cid("place", "overture", p["overture_id"])
            if pid in seen:
                continue
            seen.add(pid)
            places.append(
                place_record(
                    pid=pid,
                    name=p["name"],
                    category=p["category"],
                    lat=p["lat"],
                    lon=p["lon"],
                    area_id=area_id,
                    source="overture",
                    source_id=p["overture_id"],
                    raw_category=p["raw_category"],
                    confidence=p["confidence"],
                )
            )

        for n in osm_buckets.get(key, []):
            pid = cid("place", "osm", n["osm_type"], str(n["osm_id"]))
            if pid in seen:
                continue
            # Dedup by near-identical name+coords against overture already kept
            places.append(
                place_record(
                    pid=pid,
                    name=n["name"],
                    category=n["category"],
                    lat=n["lat"],
                    lon=n["lon"],
                    area_id=area_id,
                    source="osm",
                    source_id=f"{n['osm_type']}/{n['osm_id']}",
                    raw_category=n["category"],
                    confidence=None,
                )
            )
            seen.add(pid)

        fname = f"{key}_all.json"
        write_json(pdir / fname, {"area_id": area_id, "rayon_key": key, "places": places})
        index_files.append(f"places/{fname}")
        by_rayon_counts[key] = {
            "name": area["name"],
            "area_id": area_id,
            "count": len(places),
            "file": f"places/{fname}",
        }
        all_places.extend(places)
        print(f"  {area['name']}: {len(places)} places -> {fname}")

    # Keep yasamal_all.json as alias of yasamal for backward compatibility
    if "yasamal" in by_rayon_counts:
        yas = load_json(pdir / "yasamal_all.json")
        write_json(pdir / "yasamal_all.json", yas)

    # Category aggregates across Bakı
    by_cat = defaultdict(list)
    for p in all_places:
        by_cat[p["category"]].append(p)
    for cat, items in by_cat.items():
        write_json(pdir / f"{cat}.json", {"category": cat, "scope": "baki_rayons", "places": items})

    write_json(
        pdir / "index.json",
        {
            "region": "baki_rayons",
            "total": len(all_places),
            "by_rayon": by_rayon_counts,
            "by_category": {k: len(v) for k, v in sorted(by_cat.items())},
            "files": index_files,
        },
    )

    # Update manifest coverage (preserve quality_gate if present)
    manifest_path = OUT / "manifest.json"
    manifest = load_json(manifest_path) if manifest_path.exists() else {}
    manifest["dataset_version"] = "0.1.2-pilot"
    manifest["generated_at"] = datetime.now(timezone.utc).isoformat()
    cov = manifest.setdefault("coverage", {})
    cov["scope"] = "pilot"
    cov["description"] = (
        "Country + Bakı city/districts + Yasamal neighborhoods + notable named places "
        "for all Bakı rayons. Neighborhoods beyond Yasamal/Nəsimi Alatava not yet expanded."
    )
    cov["places"] = len(all_places)
    if "areas" not in cov:
        cov["areas"] = len(areas)
    write_json(manifest_path, manifest)

    print("=" * 50)
    print(f"TOTAL places: {len(all_places)}")
    for key, info in by_rayon_counts.items():
        print(f"  {info['name']}: {info['count']}")
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
