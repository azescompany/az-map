# -*- coding: utf-8 -*-
"""
Reassign Sumqayıt places to most-specific verified child by point-in-polygon.

Children-first: if a place falls in a child boundary → that child's area_id;
else if in city polygon → Sumqayıt city; else → review / leave flagged.

Does not scrape sources; does not touch areas/boundaries.
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from shapely.geometry import Point, shape
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

OUT = Path("data")
CITY_ID = "a02b58f1-3009-5ce3-a728-69d77b411dec"
KEY = "sumqayit"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


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
    return unary_union(geoms)


def main() -> int:
    areas = load_json(OUT / "areas" / "areas.json")["areas"]
    city = next((a for a in areas if a["id"] == CITY_ID), None)
    if not city:
        print("ERROR: Sumqayıt city not found")
        return 1

    city_geom = load_boundary_geom(city.get("boundary_file"))
    if city_geom is None:
        print("ERROR: city boundary missing")
        return 1

    children = [
        a
        for a in areas
        if a.get("parent_id") == CITY_ID
        and a.get("parent_status") == "verified"
        and a.get("geom_status") == "verified"
        and a.get("type") in ("neighborhood", "settlement")
    ]

    child_geoms: list[tuple[dict, object, float]] = []
    missing_bf = []
    for a in children:
        g = load_boundary_geom(a.get("boundary_file"))
        if g is None or g.is_empty:
            missing_bf.append(a["name"])
            continue
        child_geoms.append((a, g, float(g.area)))

    # Smallest area first so most-specific wins on overlap (first match).
    child_geoms.sort(key=lambda t: t[2])

    print(f"City: {city['name']} · children with geom: {len(child_geoms)}")
    for a, _g, ar in child_geoms:
        print(f"  {a['name']:40} area={ar:.8f}  {a.get('boundary_file')}")
    if missing_bf:
        print("  missing boundary:", missing_bf)

    places_path = OUT / "places" / f"{KEY}_all.json"
    payload = load_json(places_path)
    places = payload.get("places") or []
    before_ids = Counter(p.get("area_id") for p in places)

    by_child = Counter()
    city_only = 0
    outside = []
    changed = 0

    for p in places:
        coords = p.get("coordinates") or {}
        lat = coords.get("lat")
        lon = coords.get("lon")
        if lat is None or lon is None:
            outside.append({"id": p.get("id"), "name": p.get("name"), "reason": "no_coords"})
            continue
        pt = Point(float(lon), float(lat))

        assigned = None
        for a, g, _ar in child_geoms:
            if g.covers(pt) or g.contains(pt) or g.intersects(pt):
                # intersects for boundary points; still prefer smallest already sorted
                assigned = a
                break

        if assigned is not None:
            new_id = assigned["id"]
            by_child[assigned["name"]] += 1
        elif city_geom.covers(pt) or city_geom.contains(pt) or city_geom.intersects(pt):
            new_id = CITY_ID
            city_only += 1
        else:
            outside.append(
                {
                    "id": p.get("id"),
                    "name": p.get("name"),
                    "lat": lat,
                    "lon": lon,
                    "reason": "outside_city_and_children",
                }
            )
            # keep previous area_id but flag
            p["area_assign_method"] = "conflict_outside"
            p["area_assign_status"] = "conflict"
            continue

        old = p.get("area_id")
        if old != new_id:
            changed += 1
        p["area_id"] = new_id
        p["area_assign_method"] = "containment_verified"
        p["area_assign_status"] = "verified"

    after_ids = Counter(p.get("area_id") for p in places)
    id_to_name = {CITY_ID: city["name"]}
    for a, *_ in child_geoms:
        id_to_name[a["id"]] = a["name"]

    write_json(
        places_path,
        {
            "area_id": CITY_ID,
            "city_key": KEY,
            "places": places,
        },
    )

    # index count unchanged in total; refresh entry
    idx_path = OUT / "places" / "index.json"
    idx = load_json(idx_path)
    by_rayon = idx.setdefault("by_rayon", {})
    by_rayon[KEY] = {
        "name": city["name"],
        "area_id": CITY_ID,
        "count": len(places),
        "file": f"places/{KEY}_all.json",
    }
    idx["total"] = sum(int(v.get("count") or 0) for v in by_rayon.values())
    write_json(idx_path, idx)

    manifest_path = OUT / "manifest.json"
    if manifest_path.exists():
        manifest = load_json(manifest_path)
        manifest["generated_at"] = datetime.now(timezone.utc).isoformat()
        cov = manifest.setdefault("coverage", {})
        cov["places"] = idx["total"]
        write_json(manifest_path, manifest)

    if outside:
        write_json(
            OUT / "reviews" / "landmark_sumqayit_reassign_conflict.json",
            {
                "key": KEY,
                "city_id": CITY_ID,
                "count": len(outside),
                "items": outside[:200],
            },
        )

    dist = {id_to_name.get(i, i): n for i, n in after_ids.most_common()}
    report = {
        "key": KEY,
        "places": len(places),
        "changed_area_id": changed,
        "city_only": city_only,
        "by_child_name": dict(by_child.most_common()),
        "distribution": dist,
        "outside": len(outside),
        "before_unique_area_ids": len(before_ids),
        "after_unique_area_ids": len(after_ids),
        "children_used": len(child_geoms),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    write_json(OUT / "reviews" / "landmark_sumqayit_reassign.json", report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
