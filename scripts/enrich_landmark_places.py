# -*- coding: utf-8 -*-
"""
Enrich one rayon's places/{key}_all.json with expanded landmark taxonomy.

- Reads source_files/ (OSM PBF + Overture) — never writes sources
- Does not touch areas/boundaries
- Dedupe: source_id / place.id / wikidata / near(≤30m)+same name
- Same-name disambiguation via addr:street / Overture address / #N fallback
- Updates places/index.json entry + manifest places count (optional version bump)

Usage:
  python scripts/enrich_landmark_places.py --key yasamal [--bump-version 0.2.1-national]
"""
from __future__ import annotations

import argparse
import json
import math
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
    classify_osm_tags,
    classify_overture,
)

SRC = Path("source_files")
OUT = Path("data")
OSM_PBF = SRC / "azerbaijan-261020.osm.pbf"
OVERTURE = SRC / "overture" / "aze_place.parquet"
OVERTURE_RELEASE = "2026-09-23.1"
OSM_RELEASE = "azerbaijan-261020"
NS = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")
NEAR_M = 30.0


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


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def haversine_m(lat1, lon1, lat2, lon2) -> float:
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(a)))


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


def rayon_key_from_boundary(boundary_file: str | None) -> str | None:
    if not boundary_file:
        return None
    bf = boundary_file.replace("\\", "/")
    for pat in (
        r"rayon_([a-z0-9_]+)\.geojson$",
        r"city_([a-z0-9_]+)\.geojson$",
        r"neighborhood_([a-z0-9_]+)\.geojson$",
    ):
        m = re.search(pat, bf)
        if m:
            return m.group(1)
    return None


def street_suffix(street: str | None) -> str | None:
    if not street or not str(street).strip():
        return None
    s = str(street).strip()
    # shorten long freeform addresses — take first segment before comma
    s = s.split(",")[0].strip()
    if len(s) > 48:
        s = s[:45] + "…"
    if not s.casefold().endswith("küç") and "küç" not in s.casefold() and "st" not in s.casefold():
        if not any(x in s.casefold() for x in ("prospekt", "pr.", "məhəllə", "döngə")):
            s = f"{s} küç."
    return s


class OsmCollector(osmium.SimpleHandler):
    def __init__(self, geom, minx, miny, maxx, maxy):
        super().__init__()
        self.geom = geom
        self.minx, self.miny, self.maxx, self.maxy = minx, miny, maxx, maxy
        self.rows = []

    def node(self, n):
        if not n.tags or not n.location.valid():
            return
        lon, lat = n.location.lon, n.location.lat
        if not (self.minx <= lon <= self.maxx and self.miny <= lat <= self.maxy):
            return
        cat = classify_osm_tags(n.tags)
        if not cat:
            return
        name = n.tags.get("name") or n.tags.get("name:az")
        if not name or not str(name).strip():
            return
        pt = Point(lon, lat)
        if not (self.geom.covers(pt) or self.geom.intersects(pt)):
            return
        street = n.tags.get("addr:street") or n.tags.get("addr:housename")
        self.rows.append(
            {
                "name": str(name).strip(),
                "category": cat,
                "lat": lat,
                "lon": lon,
                "source": "osm",
                "source_id": f"node/{n.id}",
                "raw_category": cat,
                "street": street,
                "wikidata": n.tags.get("wikidata"),
                "confidence": None,
            }
        )


def collect_overture(geom, minx, miny, maxx, maxy):
    pl = pq.read_table(
        OVERTURE,
        columns=[
            "id",
            "names",
            "taxonomy",
            "basic_category",
            "geometry",
            "bbox",
            "confidence",
            "addresses",
            "brand",
        ],
    )
    out = []
    for i in range(pl.num_rows):
        bb = pl.column("bbox")[i].as_py() or {}
        cx = (bb.get("xmin", 0) + bb.get("xmax", 0)) / 2
        cy = (bb.get("ymin", 0) + bb.get("ymax", 0)) / 2
        if not (minx <= cx <= maxx and miny <= cy <= maxy):
            continue
        tax = pl.column("taxonomy")[i].as_py() or {}
        raw = tax.get("primary") or pl.column("basic_category")[i].as_py() or ""
        cat = classify_overture(raw)
        if not cat:
            continue
        names = pl.column("names")[i].as_py() or {}
        name = (names.get("primary") or "").strip()
        if not name:
            continue
        g = pl.column("geometry")[i].as_py()
        try:
            pt = swkb.loads(g) if g else Point(cx, cy)
        except Exception:
            pt = Point(cx, cy)
        if not (geom.covers(pt) or geom.intersects(pt)):
            continue
        street = None
        addrs = pl.column("addresses")[i].as_py() or []
        if addrs:
            free = (addrs[0] or {}).get("freeform")
            if free and str(free).strip():
                street = str(free).strip()
        brand = pl.column("brand")[i].as_py() or {}
        wikidata = brand.get("wikidata")
        out.append(
            {
                "name": name,
                "category": cat,
                "lat": float(pt.y),
                "lon": float(pt.x),
                "source": "overture",
                "source_id": pl.column("id")[i].as_py(),
                "raw_category": raw,
                "street": street,
                "wikidata": wikidata,
                "confidence": pl.column("confidence")[i].as_py(),
            }
        )
    return out


def candidate_to_place(c, area_id: str) -> dict:
    if c["source"] == "overture":
        pid = cid("place", "overture", c["source_id"])
    else:
        # osm source_id like node/123
        parts = c["source_id"].split("/")
        pid = cid("place", "osm", *parts)
    base = c["name"]
    return {
        "id": pid,
        "name": base,
        "name_normalized": norm(base),
        "alt_names": [],
        "category": c["category"],
        "coordinates": {"lat": c["lat"], "lon": c["lon"]},
        "area_id": area_id,
        "area_assign_method": "containment_verified",
        "area_assign_status": "verified",
        "confidence": c.get("confidence"),
        "status": "silver",
        "source_refs": [
            {
                "source": c["source"],
                "source_id": c["source_id"],
                "release": OVERTURE_RELEASE if c["source"] == "overture" else OSM_RELEASE,
                "source_category": c.get("raw_category"),
            }
        ],
        "_street": c.get("street"),
        "_wikidata": c.get("wikidata"),
        "_base_name": base,
    }


def merge_source_refs(a: list, b: list) -> list:
    seen = {(r.get("source"), r.get("source_id")) for r in a}
    out = list(a)
    for r in b:
        key = (r.get("source"), r.get("source_id"))
        if key not in seen:
            out.append(r)
            seen.add(key)
    return out


def dedupe_places(places: list[dict]) -> tuple[list[dict], int]:
    """Merge duplicates; return (places, merge_count)."""
    by_id: dict[str, dict] = {}
    by_source: dict[tuple, str] = {}
    by_wd: dict[str, str] = {}
    order: list[str] = []
    merges = 0

    def absorb(into: dict, other: dict):
        nonlocal merges
        merges += 1
        into["source_refs"] = merge_source_refs(
            into.get("source_refs") or [], other.get("source_refs") or []
        )
        if not into.get("_street") and other.get("_street"):
            into["_street"] = other["_street"]
        if not into.get("_wikidata") and other.get("_wikidata"):
            into["_wikidata"] = other["_wikidata"]
        alts = set(into.get("alt_names") or [])
        for n in other.get("alt_names") or []:
            alts.add(n)
        if other.get("_base_name") and other["_base_name"] != into.get("name"):
            alts.add(other["_base_name"])
        into["alt_names"] = sorted(alts)

    for p in places:
        pid = p["id"]
        # source_id
        src_keys = []
        for r in p.get("source_refs") or []:
            src_keys.append((r.get("source"), r.get("source_id")))
        wd = p.get("_wikidata")

        match_id = None
        if pid in by_id:
            match_id = pid
        if match_id is None:
            for sk in src_keys:
                if sk in by_source:
                    match_id = by_source[sk]
                    break
        if match_id is None and wd and wd in by_wd:
            match_id = by_wd[wd]
        if match_id is None:
            lat = p["coordinates"]["lat"]
            lon = p["coordinates"]["lon"]
            nn = p.get("name_normalized") or norm(p.get("name") or "")
            for oid in order:
                o = by_id[oid]
                if (o.get("name_normalized") or norm(o.get("name") or "")) != nn:
                    continue
                d = haversine_m(
                    lat,
                    lon,
                    o["coordinates"]["lat"],
                    o["coordinates"]["lon"],
                )
                if d <= NEAR_M:
                    match_id = oid
                    break

        if match_id is not None:
            absorb(by_id[match_id], p)
            for sk in src_keys:
                by_source[sk] = match_id
            if wd:
                by_wd[wd] = match_id
            continue

        by_id[pid] = p
        order.append(pid)
        for sk in src_keys:
            by_source[sk] = pid
        if wd:
            by_wd[wd] = pid

    return [by_id[i] for i in order], merges


def disambiguate(places: list[dict]) -> tuple[list[dict], int, list[str]]:
    """Same base name in rayon → street suffix; returns (places, count, review notes)."""
    groups: dict[str, list[dict]] = defaultdict(list)
    for p in places:
        base = p.get("_base_name") or p.get("name") or ""
        groups[norm(base)].append(p)

    disambig = 0
    reviews: list[str] = []
    for _key, group in groups.items():
        if len(group) < 2:
            # single: keep plain name
            for p in group:
                p["name"] = p.get("_base_name") or p["name"]
                p["name_normalized"] = norm(p["name"])
            continue
        used_suffix: dict[str, int] = {}
        for idx, p in enumerate(group, start=1):
            base = p.get("_base_name") or p["name"]
            street = street_suffix(p.get("_street"))
            if street:
                display = f"{base} ({street})"
            else:
                lat = p["coordinates"]["lat"]
                lon = p["coordinates"]["lon"]
                display = f"{base} ({lat:.4f},{lon:.4f})"
                reviews.append(
                    f"no street for duplicate name '{base}' @ {lat:.5f},{lon:.5f} → coord suffix"
                )
            # collision of same street suffix
            if display in used_suffix:
                display = f"{base} (#{idx})"
                reviews.append(f"street collision for '{base}' → #{idx}")
            used_suffix[display] = idx
            alts = set(p.get("alt_names") or [])
            alts.add(base)
            p["alt_names"] = sorted(alts)
            p["name"] = display
            p["name_normalized"] = norm(base) + " " + norm(street or display)
            disambig += 1
    return places, disambig, reviews


def strip_private(p: dict) -> dict:
    return {k: v for k, v in p.items() if not k.startswith("_")}


def existing_to_working(p: dict) -> dict:
    w = dict(p)
    w["_base_name"] = p.get("name")
    # strip previous disambiguation parentheses for regrouping if re-run
    m = re.match(r"^(.*)\s+\([^)]+\)\s*$", p.get("name") or "")
    if m and (p.get("alt_names") or []):
        # prefer short alt as base
        short = next((a for a in p["alt_names"] if a and "(" not in a), None)
        if short:
            w["_base_name"] = short
    w["_street"] = None
    w["_wikidata"] = None
    for r in p.get("source_refs") or []:
        # no street in old records
        pass
    w["name_normalized"] = norm(w["_base_name"])
    return w


def resolve_area_by_key(areas: list, key: str):
    for a in areas:
        if rayon_key_from_boundary(a.get("boundary_file")) == key:
            return a
    idx = load_json(OUT / "places" / "index.json")
    meta = (idx.get("by_rayon") or {}).get(key)
    if meta:
        return next((x for x in areas if x["id"] == meta["area_id"]), None)
    return None


def point_in_any(pt: Point, geoms: list) -> bool:
    for g in geoms:
        if g is None:
            continue
        if g.covers(pt) or g.intersects(pt):
            return True
    return False


def assign_city_children(places: list[dict], city: dict, areas: list) -> dict:
    """Children-first containment for city-direct place files (e.g. Sumqayıt).

    Smallest overlapping child wins; else city polygon; else conflict.
    """
    city_id = city["id"]
    city_geom = load_boundary_geom(city.get("boundary_file"))
    child_geoms: list[tuple[dict, object, float]] = []
    for a in areas:
        if a.get("parent_id") != city_id:
            continue
        if a.get("parent_status") != "verified" or a.get("geom_status") != "verified":
            continue
        if a.get("type") not in ("neighborhood", "settlement"):
            continue
        g = load_boundary_geom(a.get("boundary_file"))
        if g is None or g.is_empty:
            continue
        child_geoms.append((a, g, float(g.area)))
    child_geoms.sort(key=lambda t: t[2])

    by_child: dict[str, int] = defaultdict(int)
    city_only = 0
    conflict_n = 0
    for p in places:
        coords = p.get("coordinates") or {}
        lat, lon = coords.get("lat"), coords.get("lon")
        if lat is None or lon is None:
            p["area_assign_method"] = "conflict_outside"
            p["area_assign_status"] = "conflict"
            conflict_n += 1
            continue
        pt = Point(float(lon), float(lat))
        assigned = None
        for a, g, _ar in child_geoms:
            if g.covers(pt) or g.contains(pt) or g.intersects(pt):
                assigned = a
                break
        if assigned is not None:
            p["area_id"] = assigned["id"]
            p["area_assign_method"] = "containment_verified"
            p["area_assign_status"] = "verified"
            by_child[assigned["name"]] += 1
        elif city_geom is not None and (
            city_geom.covers(pt) or city_geom.contains(pt) or city_geom.intersects(pt)
        ):
            p["area_id"] = city_id
            p["area_assign_method"] = "containment_verified"
            p["area_assign_status"] = "verified"
            city_only += 1
        else:
            p["area_assign_method"] = "conflict_outside"
            p["area_assign_status"] = "conflict"
            conflict_n += 1
    return {
        "children": len(child_geoms),
        "city_only": city_only,
        "by_child": dict(by_child),
        "conflict": conflict_n,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--key", required=True, help="places key, e.g. yasamal")
    ap.add_argument(
        "--exclude-keys",
        default="",
        help="comma-separated place keys whose polygons are subtracted (e.g. masazir,xirdalan)",
    )
    ap.add_argument("--bump-version", default=None, help="manifest.dataset_version")
    args = ap.parse_args()
    key = args.key

    assert OVERTURE.exists(), OVERTURE
    assert OSM_PBF.exists(), OSM_PBF

    areas = load_json(OUT / "areas" / "areas.json")["areas"]
    area = resolve_area_by_key(areas, key)
    if not area:
        print(f"ERROR: no area for key={key}")
        return 1

    geom = load_boundary_geom(area.get("boundary_file"))
    if geom is None:
        print("ERROR: no boundary")
        return 1

    exclude_keys = [k.strip() for k in (args.exclude_keys or "").split(",") if k.strip()]
    # Abşeron remaining: Masazır / Xırdalan go to their own place files
    if key == "absheron" and not exclude_keys:
        exclude_keys = ["masazir", "xirdalan"]
    exclude_geoms = []
    for ek in exclude_keys:
        ea = resolve_area_by_key(areas, ek)
        if not ea:
            print(f"  WARN: exclude key={ek} area not found")
            continue
        eg = load_boundary_geom(ea.get("boundary_file"))
        if eg is None:
            print(f"  WARN: exclude key={ek} no boundary")
            continue
        exclude_geoms.append(eg)
        print(f"  exclude polygon: {ek} · {ea['name']}")

    minx, miny, maxx, maxy = geom.bounds
    area_id = area["id"]
    print(f"Enrich {key} · {area['name']} · {area_id}")

    places_path = OUT / "places" / f"{key}_all.json"
    before_payload = load_json(places_path) if places_path.exists() else {}
    before = before_payload.get("places") or []
    print(f"  baseline: {len(before)}")

    print("  OSM scan…")
    handler = OsmCollector(geom, minx, miny, maxx, maxy)
    handler.apply_file(str(OSM_PBF).replace("\\", "/"), locations=True)
    if exclude_geoms:
        handler.rows = [
            r
            for r in handler.rows
            if not point_in_any(Point(r["lon"], r["lat"]), exclude_geoms)
        ]
    print(f"  OSM candidates: {len(handler.rows)}")

    print("  Overture scan…")
    ov = collect_overture(geom, minx, miny, maxx, maxy)
    if exclude_geoms:
        ov = [
            r
            for r in ov
            if not point_in_any(Point(r["lon"], r["lat"]), exclude_geoms)
        ]
    print(f"  Overture candidates: {len(ov)}")

    # Drop baseline rows that now belong to excluded child polygons
    if exclude_geoms:
        kept_before = []
        dropped = 0
        for p in before:
            c = p.get("coordinates") or {}
            pt = Point(float(c.get("lon") or 0), float(c.get("lat") or 0))
            if point_in_any(pt, exclude_geoms):
                dropped += 1
                continue
            kept_before.append(p)
        if dropped:
            print(f"  baseline dropped (in exclude polygons): {dropped}")
        before = kept_before

    working = [existing_to_working(p) for p in before]
    for c in ov + handler.rows:
        working.append(candidate_to_place(c, area_id))

    deduped, merge_n = dedupe_places(working)
    print(f"  after dedupe: {len(deduped)} (merges={merge_n})")

    disambiged, dis_n, rev_notes = disambiguate(deduped)
    print(f"  disambiguated names: {dis_n}")

    final = [strip_private(p) for p in disambiged]
    child_assign_stats = None
    # City-direct + Abşeron settlements (Xırdalan/Masazır): children-first PIP
    if area.get("type") == "city" or key in ("masazir", "xirdalan"):
        child_assign_stats = assign_city_children(final, area, areas)
        print(
            f"  children-first assign: parent_only={child_assign_stats['city_only']} "
            f"children={child_assign_stats['children']} "
            f"conflict={child_assign_stats['conflict']} "
            f"by_child={child_assign_stats['by_child']}"
        )
    final.sort(key=lambda p: (p.get("category") or "", p.get("name_normalized") or ""))

    by_cat = defaultdict(int)
    for p in final:
        by_cat[p.get("category") or "other_poi"] += 1

    payload = {"area_id": area_id, "places": final}
    parent_area_id = before_payload.get("parent_area_id") or area.get("parent_id")
    if parent_area_id:
        payload["parent_area_id"] = parent_area_id
    if area.get("type") == "city":
        payload["city_key"] = key
    elif key in ("masazir", "xirdalan"):
        payload["settlement_key"] = key
    else:
        payload["rayon_key"] = key
    write_json(places_path, payload)

    # index.json — patch entry only
    idx_path = OUT / "places" / "index.json"
    idx = load_json(idx_path)
    by_rayon = idx.setdefault("by_rayon", {})
    by_rayon[key] = {
        "name": area["name"],
        "area_id": area_id,
        "count": len(final),
        "file": f"places/{key}_all.json",
    }
    files = idx.get("files") or []
    rel = f"places/{key}_all.json"
    if rel not in files:
        files.append(rel)
    idx["files"] = files
    idx["total"] = sum(int(v.get("count") or 0) for v in by_rayon.values())
    write_json(idx_path, idx)

    manifest_path = OUT / "manifest.json"
    manifest = load_json(manifest_path)
    if args.bump_version:
        manifest["dataset_version"] = args.bump_version
    manifest["generated_at"] = datetime.now(timezone.utc).isoformat()
    cov = manifest.setdefault("coverage", {})
    cov["places"] = idx["total"]
    write_json(manifest_path, manifest)

    if rev_notes:
        rev_path = OUT / "reviews" / f"landmark_{key}_disambiguate.json"
        write_json(
            rev_path,
            {
                "key": key,
                "area_id": area_id,
                "notes": rev_notes[:200],
                "count": len(rev_notes),
            },
        )

    print(
        json.dumps(
            {
                "key": key,
                "before": len(before),
                "after": len(final),
                "merges": merge_n,
                "disambiguated": dis_n,
                "by_category": dict(sorted(by_cat.items())),
                "index_total": idx["total"],
                "dataset_version": manifest.get("dataset_version"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
