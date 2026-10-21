# -*- coding: utf-8 -*-
"""Validate GeoAtlas curated dataset under data/. Readable report to stdout."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


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
    areas_doc = load(areas_path)
    areas = areas_doc.get("areas", [])
    ids = [a["id"] for a in areas]
    id_set = set(ids)

    # duplicate IDs
    seen = set()
    for i in ids:
        if i in seen:
            errors.append(f"duplicate area id: {i}")
        seen.add(i)

    for a in areas:
        aid = a["id"]
        name = a.get("name", "?")
        # dangling parent
        pid = a.get("parent_id")
        if pid is not None and pid not in id_set:
            errors.append(f"dangling parent_id on {name}: {pid}")
        # coordinates
        c = a.get("center")
        if c:
            lat, lon = c.get("lat"), c.get("lon")
            if lat is None or lon is None or not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                errors.append(f"invalid center on {name}: {c}")
        # source refs
        refs = a.get("source_refs") or []
        if not refs:
            errors.append(f"missing source_refs on {name}")
        for r in refs:
            if not r.get("source") or not r.get("source_id") or not r.get("release"):
                errors.append(f"incomplete source_ref on {name}: {r}")
        # boundary file
        bf = a.get("boundary_file")
        gs = a.get("geom_status")
        if bf:
            bp = DATA / bf
            if not bp.exists():
                errors.append(f"missing boundary file for {name}: {bf}")
            else:
                try:
                    gj = load(bp)
                    if gj.get("type") != "FeatureCollection":
                        errors.append(f"invalid GeoJSON type in {bf}")
                    feats = gj.get("features") or []
                    if not feats:
                        errors.append(f"empty FeatureCollection in {bf}")
                    for f in feats:
                        g = f.get("geometry")
                        if not g or g.get("type") not in (
                            "Polygon",
                            "MultiPolygon",
                        ):
                            errors.append(f"non-polygon geometry in {bf}")
                        if g and g.get("coordinates") is None:
                            errors.append(f"null coordinates in {bf}")
                except Exception as e:
                    errors.append(f"cannot parse {bf}: {e}")
        elif gs == "verified":
            warnings.append(f"geom_status=verified but no boundary_file: {name}")

        # parent status honesty
        if a.get("parent_status") == "verified" and pid is None and a.get("type") != "country":
            errors.append(f"verified parent_status but parent_id null: {name}")

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

    # manifest counts vs actual
    cov = manifest.get("coverage", {})
    if cov.get("areas") != len(areas):
        warnings.append(f"manifest areas {cov.get('areas')} != actual {len(areas)}")
    if places_file.exists() and cov.get("places") != len(place_ids):
        warnings.append(f"manifest places {cov.get('places')} != actual {len(place_ids)}")

    print("=" * 60)
    print("GeoAtlas dataset validation")
    print("=" * 60)
    print(f"dataset_version: {manifest.get('dataset_version')}")
    print(f"areas: {len(areas)}")
    print(f"places: {len(place_ids)}")
    print(f"errors: {len(errors)}")
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
