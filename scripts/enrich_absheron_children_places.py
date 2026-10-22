# -*- coding: utf-8 -*-
"""
Enrich Abşeron rayonu verified children — one places file per child.

- Single OSM + Overture scan inside rayon polygon
- Exclude Masazır / Xırdalan polygons (already have dedicated files)
- Children-first PIP → write data/places/{key}_all.json per child
- Leftovers (in rayon, not in any child) → absheron_all.json
- Does not touch areas/boundaries; no git

Usage:
  python scripts/enrich_absheron_children_places.py
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from shapely.geometry import Point

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
os.chdir(ROOT)

from enrich_landmark_places import (  # noqa: E402
    OSM_PBF,
    OsmCollector,
    assign_city_children,
    candidate_to_place,
    collect_overture,
    dedupe_places,
    disambiguate,
    existing_to_working,
    load_boundary_geom,
    load_json,
    point_in_any,
    rayon_key_from_boundary,
    strip_private,
    write_json,
)

OUT = Path("data")
SKIP_KEYS = {"masazir", "xirdalan"}  # already enriched separately


def main() -> int:
    areas = load_json(OUT / "areas" / "areas.json")["areas"]
    parent = next(
        a
        for a in areas
        if (a.get("boundary_file") or "")
        .replace("\\", "/")
        .endswith("rayon_absheron.geojson")
    )
    geom = load_boundary_geom(parent.get("boundary_file"))
    if geom is None:
        print("ERROR: Abşeron boundary missing")
        return 1

    children = [
        a
        for a in areas
        if a.get("parent_id") == parent["id"]
        and a.get("parent_status") == "verified"
        and a.get("geom_status") == "verified"
        and a.get("type") in ("neighborhood", "settlement")
    ]
    child_rows: list[tuple[dict, str, object]] = []
    skip_geoms = []
    for a in children:
        key = rayon_key_from_boundary(a.get("boundary_file"))
        g = load_boundary_geom(a.get("boundary_file"))
        if g is None or g.is_empty:
            print(f"  SKIP no geom: {a['name']}")
            continue
        if key in SKIP_KEYS:
            skip_geoms.append(g)
            print(f"  exclude (done): {a['name']} · {key}")
            continue
        if not key:
            print(f"  SKIP no key: {a['name']}")
            continue
        child_rows.append((a, key, g))

    child_rows.sort(key=lambda t: float(t[2].area))
    print(f"Parent {parent['name']} · children to enrich: {len(child_rows)}")

    minx, miny, maxx, maxy = geom.bounds
    print("OSM scan…")
    handler = OsmCollector(geom, minx, miny, maxx, maxy)
    handler.apply_file(str(OSM_PBF).replace("\\", "/"), locations=True)
    osm_rows = handler.rows
    if skip_geoms:
        osm_rows = [
            r
            for r in osm_rows
            if not point_in_any(Point(r["lon"], r["lat"]), skip_geoms)
        ]
    print(f"  OSM candidates: {len(osm_rows)}")

    print("Overture scan…")
    ov = collect_overture(geom, minx, miny, maxx, maxy)
    if skip_geoms:
        ov = [
            r
            for r in ov
            if not point_in_any(Point(r["lon"], r["lat"]), skip_geoms)
        ]
    print(f"  Overture candidates: {len(ov)}")

    # Working set (no baseline merge across children — fresh from sources)
    working = [candidate_to_place(c, parent["id"]) for c in ov + osm_rows]
    deduped, merge_n = dedupe_places(working)
    print(f"after dedupe: {len(deduped)} (merges={merge_n})")

    # Assign to smallest covering child; else parent residual
    buckets: dict[str, list[dict]] = defaultdict(list)
    residual: list[dict] = []
    conflict: list[dict] = []
    by_child_name: Counter[str] = Counter()

    for p in deduped:
        coords = p.get("coordinates") or {}
        lat, lon = coords.get("lat"), coords.get("lon")
        if lat is None or lon is None:
            conflict.append(p)
            continue
        pt = Point(float(lon), float(lat))
        assigned_key = None
        assigned_area = None
        for a, key, g in child_rows:
            if g.covers(pt) or g.contains(pt) or g.intersects(pt):
                assigned_key = key
                assigned_area = a
                break
        if assigned_area is not None:
            p["area_id"] = assigned_area["id"]
            p["area_assign_method"] = "containment_verified"
            p["area_assign_status"] = "verified"
            buckets[assigned_key].append(p)
            by_child_name[assigned_area["name"]] += 1
        elif geom.covers(pt) or geom.contains(pt) or geom.intersects(pt):
            p["area_id"] = parent["id"]
            p["area_assign_method"] = "containment_verified"
            p["area_assign_status"] = "verified"
            residual.append(p)
        else:
            p["area_assign_method"] = "conflict_outside"
            p["area_assign_status"] = "conflict"
            conflict.append(p)

    print(f"assigned to children: {sum(len(v) for v in buckets.values())}")
    print(f"residual (rayon only): {len(residual)}")
    print(f"conflict: {len(conflict)}")
    for name, n in by_child_name.most_common():
        print(f"  {name}: {n}")

    # Write each child file (disambiguate within child)
    summary = []
    idx_path = OUT / "places" / "index.json"
    idx = load_json(idx_path)
    by_rayon = idx.setdefault("by_rayon", {})

    for a, key, _g in sorted(child_rows, key=lambda t: t[0]["name"]):
        group = buckets.get(key) or []
        # also try children-first under this settlement (microhoods)
        if group:
            assign_city_children(group, a, areas)
        dis, dis_n, rev = disambiguate(group)
        final = [strip_private(p) for p in dis]
        final.sort(key=lambda p: (p.get("category") or "", p.get("name_normalized") or ""))
        by_cat = defaultdict(int)
        for p in final:
            by_cat[p.get("category") or "other_poi"] += 1

        places_path = OUT / "places" / f"{key}_all.json"
        write_json(
            places_path,
            {
                "area_id": a["id"],
                "parent_area_id": parent["id"],
                "settlement_key": key,
                "places": final,
            },
        )
        by_rayon[key] = {
            "name": a["name"],
            "area_id": a["id"],
            "count": len(final),
            "file": f"places/{key}_all.json",
        }
        rel = f"places/{key}_all.json"
        files = idx.setdefault("files", [])
        if rel not in files:
            files.append(rel)

        if rev:
            write_json(
                OUT / "reviews" / f"landmark_{key}_disambiguate.json",
                {"key": key, "area_id": a["id"], "notes": rev[:200], "count": len(rev)},
            )

        summary.append(
            {
                "key": key,
                "name": a["name"],
                "count": len(final),
                "disambiguated": dis_n,
                "by_category": dict(sorted(by_cat.items())),
            }
        )
        print(f"wrote {key}: {len(final)}")

    # Residual → absheron_all.json
    # Keep prior absheron places that fall in residual zone / not in skip kids
    before_path = OUT / "places" / "absheron_all.json"
    before = []
    if before_path.exists():
        before = load_json(before_path).get("places") or []
    before_w = [existing_to_working(p) for p in before]
    # drop if inside any child we just wrote or skip geoms
    all_child_geoms = [g for _a, _k, g in child_rows] + skip_geoms
    kept_before = []
    for p in before_w:
        c = p.get("coordinates") or {}
        pt = Point(float(c.get("lon") or 0), float(c.get("lat") or 0))
        if point_in_any(pt, all_child_geoms):
            continue
        kept_before.append(p)

    residual_working = kept_before + residual
    res_deduped, res_merges = dedupe_places(residual_working)
    res_dis, res_dis_n, res_rev = disambiguate(res_deduped)
    res_final = [strip_private(p) for p in res_dis]
    for p in res_final:
        p["area_id"] = parent["id"]
        p["area_assign_method"] = "containment_verified"
        p["area_assign_status"] = "verified"
    res_final.sort(key=lambda p: (p.get("category") or "", p.get("name_normalized") or ""))

    write_json(
        before_path,
        {
            "area_id": parent["id"],
            "rayon_key": "absheron",
            "places": res_final,
        },
    )
    by_rayon["absheron"] = {
        "name": parent["name"],
        "area_id": parent["id"],
        "count": len(res_final),
        "file": "places/absheron_all.json",
    }
    print(f"wrote absheron residual: {len(res_final)} (merges={res_merges}, dis={res_dis_n})")
    if res_rev:
        write_json(
            OUT / "reviews" / "landmark_absheron_disambiguate.json",
            {
                "key": "absheron",
                "area_id": parent["id"],
                "notes": res_rev[:200],
                "count": len(res_rev),
            },
        )

    idx["files"] = sorted(set(idx.get("files") or []))
    idx["total"] = sum(int(v.get("count") or 0) for v in by_rayon.values())
    write_json(idx_path, idx)

    manifest_path = OUT / "manifest.json"
    manifest = load_json(manifest_path)
    manifest["generated_at"] = datetime.now(timezone.utc).isoformat()
    manifest.setdefault("coverage", {})["places"] = idx["total"]
    write_json(manifest_path, manifest)

    report = {
        "parent": parent["name"],
        "parent_id": parent["id"],
        "osm": len(osm_rows),
        "overture": len(ov),
        "dedupe_merges": merge_n,
        "children_enriched": len(summary),
        "skipped": sorted(SKIP_KEYS),
        "residual_absheron": len(res_final),
        "conflict": len(conflict),
        "by_child": dict(by_child_name),
        "summary": summary,
        "index_total": idx["total"],
    }
    write_json(OUT / "reviews" / "landmark_absheron_children_enrich.json", report)
    print(json.dumps({k: report[k] for k in ("children_enriched", "residual_absheron", "conflict", "index_total")}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
