# -*- coding: utf-8 -*-
"""Validate GeoAtlas curated dataset under data/. Boundary accuracy gate aware."""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

from shapely.geometry import Point, shape

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def center_lat_lon(center: dict | None):
    if not center:
        return None, None
    lat = center.get("latitude", center.get("lat"))
    lon = center.get("longitude", center.get("lon"))
    return lat, lon


def load_area_geom(area: dict):
    bf = area.get("boundary_file")
    if not bf:
        return None
    path = DATA / bf
    if not path.exists():
        return None
    gj = load(path)
    geoms = []
    for f in gj.get("features") or []:
        g = f.get("geometry")
        if g and g.get("type") in ("Polygon", "MultiPolygon"):
            geoms.append(shape(g))
    if not geoms:
        return None
    if len(geoms) == 1:
        return geoms[0]
    from shapely.ops import unary_union

    return unary_union(geoms)


def point_in(geom, lat, lon) -> bool:
    pt = Point(lon, lat)
    try:
        return bool(geom.covers(pt) or geom.buffer(1e-9).covers(pt))
    except Exception:
        return False


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    manifest_path = DATA / "manifest.json"
    areas_path = DATA / "areas" / "areas.json"
    if not manifest_path.exists():
        errors.append("missing data/manifest.json")
    if not areas_path.exists():
        errors.append("missing data/areas/areas.json")
    if errors:
        print("FAIL")
        for e in errors:
            print("  ERROR:", e)
        return 1

    manifest = load(manifest_path)
    areas = load(areas_path).get("areas", [])
    ids = [a["id"] for a in areas]
    id_set = set(ids)
    geom_status_counts = Counter()
    center_status_counts = Counter()
    parent_status_counts = Counter()
    geoms = {}

    seen = set()
    for i in ids:
        if i in seen:
            errors.append(f"duplicate area id: {i}")
        seen.add(i)

    for a in areas:
        name = a.get("name", "?")
        gs = a.get("geom_status") or "missing"
        cs = a.get("center_status") or "missing"
        ps = a.get("parent_status") or "missing"
        geom_status_counts[gs] += 1
        center_status_counts[cs] += 1
        parent_status_counts[ps] += 1

        pid = a.get("parent_id")
        if pid is not None and pid not in id_set:
            errors.append(f"dangling parent_id on {name}: {pid}")

        if ps == "verified" and pid is None and a.get("type") != "country":
            errors.append(f"verified parent_status but parent_id null: {name}")

        refs = a.get("source_refs") or []
        if not refs:
            errors.append(f"missing source_refs on {name}")
        for r in refs:
            if not r.get("source") or not r.get("source_id") or not r.get("release"):
                errors.append(f"incomplete source_ref on {name}: {r}")

        lat, lon = center_lat_lon(a.get("center"))
        if lat is None or lon is None:
            if a.get("type") != "country" or gs != "missing":
                # selectable areas must have centers
                errors.append(f"missing center coordinates: {name}")
        else:
            if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                errors.append(f"invalid center range on {name}: {lat},{lon}")

        geom = load_area_geom(a)
        geoms[a["id"]] = geom
        bf = a.get("boundary_file")

        if gs == "verified":
            if not bf:
                errors.append(f"verified geom without boundary_file: {name}")
            if geom is None:
                errors.append(f"verified geom missing/unreadable GeoJSON: {name}")
            else:
                if geom.is_empty:
                    errors.append(f"verified geom is empty: {name}")
                if not geom.is_valid:
                    errors.append(f"verified geom is invalid: {name}")
                if geom.geom_type not in ("Polygon", "MultiPolygon"):
                    errors.append(f"verified geom wrong type {geom.geom_type}: {name}")
                if lat is not None and lon is not None and not point_in(geom, lat, lon):
                    errors.append(f"center outside verified boundary: {name}")
            # unresolved conflict incorrectly marked verified
            if ps == "conflict":
                errors.append(
                    f"unresolved parent conflict incorrectly paired — check {name} (parent_status=conflict while presenting as selectable)"
                )
            boundary_refs = [
                r for r in refs if r.get("role") == "boundary"
            ]
            if not boundary_refs:
                errors.append(f"verified geom missing source_ref role=boundary: {name}")
            if a.get("crs") not in (None, "EPSG:4326"):
                warnings.append(f"unexpected crs on {name}: {a.get('crs')}")
            elif a.get("crs") is None:
                warnings.append(f"missing crs field on verified area: {name}")

        elif bf:
            if geom is None:
                errors.append(f"boundary_file unreadable for {name}: {bf}")
            elif geom.is_empty:
                errors.append(f"empty geometry in {bf}")
            elif not geom.is_valid:
                warnings.append(f"invalid geometry (status={gs}) in {bf}")

        if gs == "verified" and cs == "conflict":
            errors.append(f"verified boundary with conflict center_status: {name}")

        # label fallback honesty
        if a.get("center_method") in ("osm_place_node", "geonames") and cs == "verified":
            errors.append(
                f"label/node center incorrectly marked verified: {name}"
            )

    # child-parent geometry for neighborhoods with verified parents
    for a in areas:
        if a.get("type") != "neighborhood":
            continue
        pid = a.get("parent_id")
        if not pid or a.get("parent_status") != "verified":
            continue
        cg, pg = geoms.get(a["id"]), geoms.get(pid)
        if cg is None or pg is None:
            continue
        c = cg.representative_point()
        if not (pg.covers(c) or pg.intersects(cg)):
            errors.append(
                f"verified neighborhood parent geometry mismatch: {a.get('name')} not in parent"
            )

    # places
    places_file = DATA / "places" / "yasamal_all.json"
    place_ids = []
    if places_file.exists():
        places = load(places_file).get("places", [])
        for p in places:
            place_ids.append(p["id"])
            c = p.get("coordinates") or {}
            lat, lon = c.get("lat"), c.get("lon")
            if lat is None or lon is None or not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                errors.append(f"invalid place coords: {p.get('name')}")
            if not p.get("source_refs"):
                errors.append(f"place missing source_refs: {p.get('name')}")
            aid = p.get("area_id")
            if aid and aid not in id_set:
                errors.append(f"place dangling area_id: {p.get('name')} -> {aid}")
        if len(place_ids) != len(set(place_ids)):
            errors.append("duplicate place ids")
    else:
        warnings.append("no places/yasamal_all.json (pilot places missing)")

    cov = manifest.get("coverage", {})
    if cov.get("areas") != len(areas):
        warnings.append(f"manifest areas {cov.get('areas')} != actual {len(areas)}")
    if places_file.exists() and cov.get("places") != len(place_ids):
        warnings.append(f"manifest places {cov.get('places')} != actual {len(place_ids)}")

    if not (DATA / "reviews" / "boundary_quality_audit.json").exists():
        warnings.append("boundary_quality_audit.json missing — run scripts/apply_boundary_quality_gate.py")

    print("=" * 60)
    print("GeoAtlas dataset validation (boundary accuracy gate)")
    print("=" * 60)
    print(f"dataset_version: {manifest.get('dataset_version')}")
    print(f"areas: {len(areas)} | places: {len(place_ids)}")
    print(f"geom_status: {dict(geom_status_counts)}")
    print(f"center_status: {dict(center_status_counts)}")
    print(f"parent_status: {dict(parent_status_counts)}")
    print(f"errors (blocking): {len(errors)}")
    print(f"warnings: {len(warnings)}")
    for e in errors:
        print("  ERROR:", e)
    for w in warnings:
        print("  WARN:", w)
    if errors:
        print("\nRESULT: FAIL")
        return 1
    print("\nRESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
