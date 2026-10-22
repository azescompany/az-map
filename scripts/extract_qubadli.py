# -*- coding: utf-8 -*-
"""
Extract Qubadlı rayonu (top-level under country) + settlements + places.

Absheron-style: Ölkə → Rayon → Qəsəbə/kənd.
Hierarchy.md. source_files/ read-only → data/.

OSM: relation/11871223 admin_level=6 Qubadlı rayonu Q644048
Overture: region Qubadlı rayonu children (localities with geometry)
"""
from __future__ import annotations

import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

import osmium
import pyarrow.parquet as pq
from shapely import wkb as swkb
from shapely.geometry import Point, mapping
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
SRC = Path("source_files")
OUT = Path("data")
OSM_PBF = SRC / "azerbaijan-261020.osm.pbf"
OVERTURE_RELEASE = "2026-09-23.1"
OSM_RELEASE = "azerbaijan-261020"
OSM_RAYON_REL = 11871223
NS = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")
ALLOWED = {"microhood", "macrohood", "neighborhood", "locality"}

LANDMARK_TAXONOMY = {
    "historic_site": "historic",
    "park": "park",
    "museum": "museum",
    "monument": "monument",
    "tourist_attraction": "tourism",
    "arts_and_entertainment": "culture",
    "gallery": "culture",
    "library": "culture",
    "stadium_arena": "stadium",
    "muslim_place_of_worship": "religious",
    "christian_church": "religious",
    "theater": "culture",
    "cinema": "culture",
    "viewpoint": "tourism",
    "beach": "park",
    "garden": "park",
    "castle": "historic",
    "landmark": "monument",
    "plaza": "park",
}


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
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", s)).strip()


def slug(s: str) -> str:
    return norm(s).replace(" ", "_")[:80] or "unnamed"


def pname(names) -> str:
    return (names or {}).get("primary") or ""


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def center_from_geom(geom):
    try:
        p = geom.representative_point()
        return float(p.y), float(p.x), "rep_point"
    except Exception:
        c = geom.centroid
        return float(c.y), float(c.x), "centroid"


def contained(child_geom, parent_geom) -> bool:
    if child_geom is None or parent_geom is None:
        return False
    c = child_geom.representative_point()
    return bool(parent_geom.covers(c) or parent_geom.intersects(child_geom))


class OsmAreaExtractor(osmium.SimpleHandler):
    def __init__(self, want: set[int]):
        super().__init__()
        self.want = want
        self.geoms: dict[int, object] = {}
        self.wk = osmium.geom.WKTFactory()

    def area(self, a):
        try:
            rid = a.orig_id()
        except Exception:
            return
        if rid not in self.want or a.from_way():
            return
        try:
            from shapely import wkt as load_wkt

            g = load_wkt.loads(self.wk.create_multipolygon(a))
            self.geoms[rid] = unary_union([self.geoms[rid], g]) if rid in self.geoms else g
        except Exception:
            return


def load_overture():
    div = pq.read_table(
        SRC / "overture/aze_division.parquet",
        columns=[
            "id",
            "subtype",
            "country",
            "names",
            "parent_division_id",
            "wikidata",
            "population",
        ],
    )
    area = pq.read_table(
        SRC / "overture/aze_division_area.parquet",
        columns=["division_id", "geometry"],
    )
    by_id = {}
    for i in range(div.num_rows):
        if div.column("country")[i].as_py() != "AZ":
            continue
        did = div.column("id")[i].as_py()
        by_id[did] = {
            "id": did,
            "name": pname(div.column("names")[i].as_py()),
            "subtype": div.column("subtype")[i].as_py(),
            "parent": div.column("parent_division_id")[i].as_py(),
            "wikidata": div.column("wikidata")[i].as_py(),
            "population": div.column("population")[i].as_py(),
        }
    areas = {}
    for i in range(area.num_rows):
        did = area.column("division_id")[i].as_py()
        g = area.column("geometry")[i].as_py()
        if not did or not g:
            continue
        try:
            geom = swkb.loads(g)
        except Exception:
            continue
        areas[did] = unary_union([areas[did], geom]) if did in areas else geom
    return by_id, areas


def extract_places_in(poly, max_places=400):
    pl = pq.read_table(
        SRC / "overture/aze_place.parquet",
        columns=["id", "names", "taxonomy", "basic_category", "geometry", "bbox", "confidence"],
    )
    out = []
    minx, miny, maxx, maxy = poly.bounds
    for i in range(pl.num_rows):
        bb = pl.column("bbox")[i].as_py() or {}
        cx = (bb.get("xmin", 0) + bb.get("xmax", 0)) / 2
        cy = (bb.get("ymin", 0) + bb.get("ymax", 0)) / 2
        if not (minx <= cx <= maxx and miny <= cy <= maxy):
            continue
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
        if not (poly.covers(pt) or poly.intersects(pt)):
            continue
        out.append(
            {
                "overture_id": pl.column("id")[i].as_py(),
                "name": name,
                "category": cat,
                "raw_category": raw,
                "lon": float(pt.x),
                "lat": float(pt.y),
                "confidence": pl.column("confidence")[i].as_py(),
            }
        )
        if len(out) >= max_places:
            break
    return out


def write_boundary(aid, name, geom, path_rel, props):
    write_json(
        OUT / path_rel,
        {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "id": aid,
                    "properties": {"id": aid, "name": name, **props},
                    "geometry": mapping(geom),
                }
            ],
        },
    )


def make_area(
    *,
    key,
    name,
    type_,
    subtype,
    parent_id,
    parent_status,
    geom,
    geom_status,
    center,
    wikidata,
    source_refs,
    notes=None,
    alt_names=None,
    boundary_name=None,
):
    lat = lon = None
    center_method = None
    if center:
        lat, lon, center_method = center
    elif geom is not None and not geom.is_empty:
        lat, lon, center_method = center_from_geom(geom)
    aid = cid("area", key)
    bname = boundary_name or key.replace(":", "_")
    return {
        "id": aid,
        "name": name,
        "name_normalized": norm(name),
        "alt_names": alt_names or [],
        "type": type_,
        "subtype": subtype,
        "parent_id": parent_id,
        "parent_status": parent_status,
        "geom_status": geom_status,
        "center": {"lat": lat, "lon": lon} if lat is not None else None,
        "center_method": center_method,
        "wikidata": wikidata,
        "population": None,
        "population_source": None,
        "bbox": list(geom.bounds) if geom is not None and not geom.is_empty else None,
        "source_refs": source_refs,
        "notes": notes,
        "boundary_file": f"boundaries/{bname}.geojson"
        if geom is not None and geom_status != "missing"
        else None,
    }, aid


def pick_best(candidates, ov_areas):
    rank = {"neighborhood": 0, "macrohood": 1, "microhood": 2, "locality": 3}
    by_name: dict[str, list] = {}
    for c in candidates:
        by_name.setdefault(c["name"], []).append(c)
    out = []
    for name, group in by_name.items():
        group.sort(
            key=lambda z: (
                0 if z["id"] in ov_areas else 1,
                rank.get(z.get("subtype") or "", 9),
            )
        )
        out.append(group[0])
    return sorted(out, key=lambda z: z["name"] or "")


def main() -> int:
    areas_path = OUT / "areas" / "areas.json"
    areas = load_json(areas_path)["areas"]
    reviews_path = OUT / "reviews" / "pilot_reviews.json"
    reviews = list((load_json(reviews_path) if reviews_path.exists() else {}).get("reviews") or [])
    country = next((a for a in areas if a.get("type") == "country"), None)
    if not country:
        raise SystemExit("Country missing")

    drop = {
        a["id"]
        for a in areas
        if a.get("name") == "Qubadlı rayonu"
        or "qubadli" in (a.get("boundary_file") or "")
        or "WORKER 3.10-qubadli" in (a.get("notes") or "")
    }
    changed = True
    while changed:
        changed = False
        for a in areas:
            if a.get("parent_id") in drop and a["id"] not in drop:
                drop.add(a["id"])
                changed = True
    for a in areas:
        if a["id"] in drop and a.get("boundary_file") and "qubadli" in a["boundary_file"]:
            p = OUT / a["boundary_file"]
            if p.exists():
                p.unlink()
    areas = [a for a in areas if a["id"] not in drop]
    print(f"Removed previous Qubadlı areas: {len(drop)}")

    ov_div, ov_areas = load_overture()
    ov_region = next(
        (
            v
            for v in ov_div.values()
            if v["name"] == "Qubadlı Rayonu" and v["subtype"] == "region"
        ),
        None,
    )
    if not ov_region:
        raise SystemExit("Overture Qubadlı rayonu missing")

    print("Reading OSM boundary…")
    osm_h = OsmAreaExtractor({OSM_RAYON_REL})
    osm_h.apply_file(str(OSM_PBF), locations=True, idx="flex_mem")
    rayon_geom = osm_h.geoms.get(OSM_RAYON_REL) or ov_areas.get(ov_region["id"])
    if rayon_geom is None:
        raise SystemExit("Qubadlı geometry missing")
    print(f"OSM rayon geom: {OSM_RAYON_REL in osm_h.geoms}")

    rayon_rec, rayon_id = make_area(
        key="rayon:qubadli",
        name="Qubadlı rayonu",
        type_="rayon",
        subtype="rayon",
        parent_id=country["id"],
        parent_status="verified",
        geom=rayon_geom,
        geom_status="verified",
        center=None,
        wikidata="Q644048",
        source_refs=[
            {
                "source": "osm",
                "source_id": f"relation/{OSM_RAYON_REL}",
                "release": OSM_RELEASE,
                "role": "boundary",
                "match_method": "id",
            },
            {
                "source": "overture",
                "source_id": ov_region["id"],
                "release": OVERTURE_RELEASE,
                "role": "boundary",
                "match_method": "id",
            },
        ],
        notes="WORKER 3.10-qubadli · top-level rayon (Absheron-style mid-level in UI).",
        alt_names=["Qubadlı", "Qubadlı"],
        boundary_name="rayon_qubadli",
    )
    areas.append(rayon_rec)
    write_boundary(
        rayon_id,
        "Qubadlı rayonu",
        rayon_geom,
        "boundaries/rayon_qubadli.geojson",
        {"type": "rayon", "parent_id": country["id"]},
    )

    raw = [
        v
        for v in ov_div.values()
        if v.get("parent") == ov_region["id"]
        and (v.get("subtype") or "") in ALLOWED
        and v.get("name")
        and v["name"].strip()
        and not v["name"].endswith(" rayonu")
    ]
    kids = pick_best(raw, ov_areas)
    verified = []
    conflicts = []
    used = set()
    for child in kids:
        geom = ov_areas.get(child["id"])
        if geom is None:
            continue
        key = "qubadli_" + slug(child["name"])
        base = key
        n = 2
        while key in used:
            key = f"{base}_{n}"
            n += 1
        used.add(key)
        st = "verified"
        cnotes = "WORKER 3.10-qubadli · Overture child of Qubadlı rayonu"
        if not contained(geom, rayon_geom):
            st = "conflict"
            cnotes = "Not contained in Qubadlı rayonu polygon"
            conflicts.append(child["name"])
            reviews.append(
                {
                    "id": cid("review", "qubadli", key),
                    "kind": "hierarchy_conflict",
                    "entity": child["name"],
                    "detail": cnotes,
                    "overture_id": child["id"],
                    "status": "open",
                }
            )
        rec, aid = make_area(
            key=f"neighborhood:{key}",
            name=child["name"],
            type_="neighborhood",
            subtype=child["subtype"],
            parent_id=rayon_id,
            parent_status=st,
            geom=geom,
            geom_status="verified",
            center=None,
            wikidata=child.get("wikidata"),
            source_refs=[
                {
                    "source": "overture",
                    "source_id": child["id"],
                    "release": OVERTURE_RELEASE,
                    "role": "boundary",
                    "match_method": "id",
                    "overture_parent_id": child.get("parent"),
                }
            ],
            notes=cnotes,
            boundary_name=f"neighborhood_{key}",
        )
        areas.append(rec)
        write_boundary(
            aid,
            child["name"],
            geom,
            rec["boundary_file"],
            {
                "type": "neighborhood",
                "parent_id": rayon_id,
                "parent_status": st,
                "subtype": child["subtype"],
            },
        )
        if st == "verified":
            verified.append(child["name"])

    print(f"Verified: {len(verified)}")
    print(f"Conflicts: {conflicts}")

    existing_place_ids: set[str] = set()
    pdir = OUT / "places"
    index_path = pdir / "index.json"
    if index_path.exists():
        for f in load_json(index_path).get("files") or []:
            if f == "places/qubadli_all.json":
                continue
            fp = OUT / f
            if fp.exists():
                for pl in load_json(fp).get("places") or []:
                    if pl.get("id"):
                        existing_place_ids.add(pl["id"])

    places = []
    skipped = 0
    for p in extract_places_in(rayon_geom, max_places=400):
        pid = cid("place", "overture", p["overture_id"])
        if pid in existing_place_ids:
            skipped += 1
            continue
        places.append(
            {
                "id": pid,
                "name": p["name"],
                "name_normalized": norm(p["name"]),
                "alt_names": [],
                "category": p["category"],
                "coordinates": {"lat": p["lat"], "lon": p["lon"]},
                "area_id": rayon_id,
                "area_assign_method": "containment_verified",
                "area_assign_status": "verified",
                "confidence": p["confidence"],
                "status": "silver",
                "source_refs": [
                    {
                        "source": "overture",
                        "source_id": p["overture_id"],
                        "release": OVERTURE_RELEASE,
                        "source_category": p["raw_category"],
                    }
                ],
            }
        )
    print(f"Places: {len(places)} (skipped dup {skipped})")
    write_json(
        pdir / "qubadli_all.json",
        {"area_id": rayon_id, "parent_area_id": country["id"], "places": places},
    )

    index = load_json(index_path) if index_path.exists() else {}
    files = [f for f in (index.get("files") or []) if f != "places/qubadli_all.json"]
    files.append("places/qubadli_all.json")
    by_rayon = dict(index.get("by_rayon") or {})
    by_rayon["qubadli"] = {
        "name": "Qubadlı rayonu",
        "area_id": rayon_id,
        "count": len(places),
        "file": "places/qubadli_all.json",
    }
    total = 0
    for f in files:
        fp = OUT / f
        if fp.exists():
            total += len(load_json(fp).get("places") or [])
    write_json(
        index_path,
        {
            "region": index.get("region") or "azerbaijan",
            "total": total,
            "by_rayon": by_rayon,
            "by_category": index.get("by_category") or {},
            "files": files,
        },
    )

    write_json(areas_path, {"type": "AreaCollection", "areas": areas})
    b_index = [
        {"file": a["boundary_file"], "area_id": a["id"], "name": a["name"]}
        for a in areas
        if a.get("boundary_file")
    ]
    write_json(OUT / "boundaries" / "index.json", {"boundaries": b_index})
    write_json(reviews_path, {"reviews": reviews})
    write_json(
        OUT / "reviews" / "qubadli_extract.json",
        {
            "rayon": "Qubadlı rayonu",
            "verified_settlements": verified,
            "conflicts": conflicts,
            "places": len(places),
            "areas_total": len(areas),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "osm_release": OSM_RELEASE,
            "overture_release": OVERTURE_RELEASE,
        },
    )

    man_path = OUT / "manifest.json"
    if man_path.exists():
        m = load_json(man_path)
        m["dataset_version"] = "0.1.69-pilot"
        m.setdefault("coverage", {})
        m["coverage"]["areas"] = len(areas)
        m["coverage"]["places"] = total
        m["coverage"]["boundaries"] = len(b_index)
        m["description"] = (
            "Country + agglomeration cities + Faza2 cities + Qubadlı. Hierarchy.md / WORKER.md."
        )
        write_json(man_path, m)

    print(
        json.dumps(
            {
                "rayon_id": rayon_id,
                "verified": len(verified),
                "conflicts": conflicts,
                "places": len(places),
                "areas_total": len(areas),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
