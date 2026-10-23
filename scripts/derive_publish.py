#!/usr/bin/env python3
"""
Build data-derived/ consumer tree from canonical data/.

Canonical SoT is never modified. See docs/claude/03-cdn-file-plan.md.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "data-derived"
DERIVE_SCHEMA = "1.0.0"


def load_json(path: Path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, obj, *, compact: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        if compact:
            json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
        else:
            json.dump(obj, f, ensure_ascii=False, indent=2)
            f.write("\n")


def center_lat_lon(center) -> tuple[float | None, float | None]:
    if not isinstance(center, dict):
        return None, None
    lat = center.get("lat", center.get("latitude"))
    lon = center.get("lon", center.get("longitude"))
    try:
        if lat is None or lon is None:
            return None, None
        return float(lat), float(lon)
    except (TypeError, ValueError):
        return None, None


def slim_center(center) -> dict | None:
    lat, lon = center_lat_lon(center)
    if lat is None or lon is None:
        return None
    return {"lat": lat, "lon": lon, "latitude": lat, "longitude": lon}


def is_named_place(p: dict) -> bool:
    name = p.get("name")
    if not isinstance(name, str) or not name.strip():
        return False
    if p.get("nameStatus") == "unnamed":
        return False
    refs = p.get("source_refs") or []
    if not refs:
        return False
    return True


def catalog_row(a: dict, places_shard_area_id: str | None) -> dict:
    aid = a["id"]
    bf = a.get("boundary_file")
    row = {
        "id": aid,
        "name": a.get("name"),
        "name_normalized": a.get("name_normalized"),
        "type": a.get("type"),
        "subtype": a.get("subtype"),
        "parent_id": a.get("parent_id"),
        "parent_status": a.get("parent_status"),
        "geom_status": a.get("geom_status"),
        "center": slim_center(a.get("center")),
        "center_status": a.get("center_status"),
        "center_method": a.get("center_method"),
        "bbox": a.get("bbox"),
        "boundary_ref": f"boundaries/{aid}.geojson" if bf else None,
        "places_shard_area_id": places_shard_area_id,
    }
    return row


def area_detail(a: dict, places_shard_area_id: str | None) -> dict:
    row = catalog_row(a, places_shard_area_id)
    row.update(
        {
            "alt_names": a.get("alt_names") or [],
            "source_refs": a.get("source_refs") or [],
            "wikidata": a.get("wikidata"),
            "notes": a.get("notes"),
            "crs": a.get("crs"),
            "geometry_type": a.get("geometry_type"),
            "center_within_boundary": a.get("center_within_boundary"),
            "canonical_boundary_file": a.get("boundary_file"),
        }
    )
    return row


def slim_place(p: dict) -> dict | None:
    if not is_named_place(p):
        return None
    coords = p.get("coordinates") or {}
    try:
        lat = float(coords.get("lat"))
        lon = float(coords.get("lon"))
    except (TypeError, ValueError):
        return None
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return None
    # Keep source_refs so filterNamedPlaces / isDisplayableNamedPlace still pass
    refs = p.get("source_refs") or []
    compact_refs = [
        {
            "source": r.get("source"),
            "source_id": r.get("source_id"),
            "release": r.get("release"),
        }
        for r in refs
        if r.get("source") and r.get("source_id")
    ]
    if not compact_refs:
        return None
    return {
        "id": p["id"],
        "name": p.get("name"),
        "name_normalized": p.get("name_normalized"),
        "category": p.get("category"),
        "coordinates": {"lat": lat, "lon": lon},
        "area_id": p.get("area_id"),
        "source_refs": compact_refs,
        "area_assign_status": p.get("area_assign_status"),
    }


def detail_place(p: dict) -> dict | None:
    base = slim_place(p)
    if not base:
        return None
    base.update(
        {
            "alt_names": p.get("alt_names") or [],
            "source_refs": p.get("source_refs") or [],
            "area_assign_status": p.get("area_assign_status"),
            "area_assign_method": p.get("area_assign_method"),
            "status": p.get("status"),
            "confidence": p.get("confidence"),
        }
    )
    return base


def search_row(p: dict) -> dict | None:
    s = slim_place(p)
    if not s:
        return None
    return {
        "id": s["id"],
        "name_normalized": s.get("name_normalized") or "",
        "category": s.get("category"),
        "lat": s["coordinates"]["lat"],
        "lon": s["coordinates"]["lon"],
        "area_id": s.get("area_id"),
    }


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    if not DATA.is_dir():
        print("ERROR: data/ missing", file=sys.stderr)
        return 1

    areas_doc = load_json(DATA / "areas" / "areas.json")
    areas = areas_doc.get("areas") or []
    by_id = {a["id"]: a for a in areas if a.get("id")}

    places_index = load_json(DATA / "places" / "index.json")
    by_rayon = places_index.get("by_rayon") or {}

    # area_id → places shard owner
    shard_owner: dict[str, str] = {}
    shards_meta: dict[str, dict] = {}
    for key, meta in by_rayon.items():
        aid = meta.get("area_id")
        file = meta.get("file")
        if not aid or not file:
            continue
        shard_owner[aid] = aid
        shards_meta[key] = {
            "key": key,
            "area_id": aid,
            "canonical_file": file.replace("\\", "/").lstrip("/"),
            "count": meta.get("count"),
            "name": meta.get("name"),
            "derived_index": f"places/index/{aid}.json",
            "derived_detail": f"places/detail/{aid}.json",
            "derived_search": f"search/{aid}.json",
        }

    if OUT.exists():
        for child in OUT.iterdir():
            # Keep README.md (tracked); wipe generated artifacts only
            if child.name.lower() == "readme.md":
                continue
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
    OUT.mkdir(parents=True, exist_ok=True)

    # --- catalog top: country + cities + country-child rayons ---
    top_ids: list[str] = []
    for a in areas:
        t = a.get("type")
        pid = a.get("parent_id")
        if t == "country":
            top_ids.append(a["id"])
        elif t == "city":
            top_ids.append(a["id"])
        elif t == "rayon" and pid and by_id.get(pid, {}).get("type") == "country":
            top_ids.append(a["id"])

    top_rows = [
        catalog_row(by_id[i], shard_owner.get(i))
        for i in top_ids
        if i in by_id
    ]
    write_json(
        OUT / "catalog" / "top.json",
        {"type": "CatalogTop", "count": len(top_rows), "areas": top_rows},
    )

    # Full slim catalog (cold start without fat areas.json) — dual-read loadAreas
    all_slim = [catalog_row(a, shard_owner.get(a["id"])) for a in areas]
    write_json(
        OUT / "catalog" / "all-slim.json",
        {
            "type": "CatalogAllSlim",
            "count": len(all_slim),
            "areas": all_slim,
        },
    )

    # --- children shards (verified only) ---
    children_map: dict[str, list[dict]] = defaultdict(list)
    for a in areas:
        if a.get("parent_status") != "verified":
            continue
        pid = a.get("parent_id")
        if not pid:
            continue
        children_map[pid].append(catalog_row(a, shard_owner.get(a["id"])))

    for pid, rows in children_map.items():
        rows.sort(key=lambda r: (r.get("name") or "").lower())
        write_json(
            OUT / "catalog" / "children" / f"{pid}.json",
            {"parent_id": pid, "count": len(rows), "areas": rows},
        )

    # --- area details + verbatim boundaries ---
    boundary_hashes: list[dict] = []
    copied_boundaries = 0
    for a in areas:
        aid = a["id"]
        write_json(OUT / "areas" / f"{aid}.json", area_detail(a, shard_owner.get(aid)))
        bf = a.get("boundary_file")
        if not bf:
            continue
        src = DATA / bf.replace("\\", "/").lstrip("/")
        if not src.is_file():
            print(f"WARN: missing boundary {bf} for {aid}", file=sys.stderr)
            continue
        dst = OUT / "boundaries" / f"{aid}.geojson"
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        copied_boundaries += 1
        boundary_hashes.append(
            {
                "area_id": aid,
                "canonical": bf.replace("\\", "/"),
                "derived": f"boundaries/{aid}.geojson",
                "sha256": file_sha256(src),
            }
        )

    write_json(
        OUT / "boundaries" / "_hashes.json",
        {"count": len(boundary_hashes), "items": boundary_hashes},
        compact=False,
    )

    # --- places index / detail / search per shard ---
    place_files_written = 0
    national_by_id: dict[str, dict] = {}
    for key, meta in shards_meta.items():
        src_rel = meta["canonical_file"]
        src = DATA / src_rel
        if not src.is_file():
            print(f"WARN: missing places file {src_rel}", file=sys.stderr)
            continue
        doc = load_json(src)
        places = doc.get("places") or []
        slim = []
        detail = []
        search = []
        for p in places:
            s = slim_place(p)
            if not s:
                continue
            slim.append(s)
            d = detail_place(p)
            if d:
                detail.append(d)
            sr = search_row(p)
            if sr:
                search.append(sr)
                national_by_id[sr["id"]] = sr
        aid = meta["area_id"]
        write_json(
            OUT / "places" / "index" / f"{aid}.json",
            {
                "area_id": aid,
                "key": key,
                "count": len(slim),
                "places": slim,
            },
        )
        write_json(
            OUT / "places" / "detail" / f"{aid}.json",
            {
                "area_id": aid,
                "key": key,
                "count": len(detail),
                "places": detail,
            },
        )
        write_json(
            OUT / "search" / f"{aid}.json",
            {"area_id": aid, "count": len(search), "items": search},
        )
        place_files_written += 1

    write_json(
        OUT / "places" / "shards.json",
        {
            "type": "PlacesShards",
            "count": len(shards_meta),
            "by_key": shards_meta,
            "by_area_id": {
                m["area_id"]: {**m} for m in shards_meta.values()
            },
        },
        compact=False,
    )

    national_items = sorted(
        national_by_id.values(),
        key=lambda r: (r.get("name_normalized") or "", r.get("id") or ""),
    )
    write_json(
        OUT / "search" / "national.json",
        {
            "type": "SearchNational",
            "count": len(national_items),
            "items": national_items,
        },
    )

    manifest = load_json(DATA / "manifest.json")
    version = manifest.get("dataset_version") or "0.0.0"
    tag = f"v{version}" if not str(version).startswith("v") else str(version)
    pin = {
        "tag": tag,
        "dataset_version": version,
        "consumer_root": "data-derived/",
        "DEFAULT_DATA_BASE": (
            f"https://cdn.jsdelivr.net/gh/azescompany/az-map@{tag}/data-derived/"
        ),
        "DEFAULT_DATA_BASE_CANONICAL": (
            f"https://cdn.jsdelivr.net/gh/azescompany/az-map@{tag}/data/"
        ),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    write_json(OUT / "pin.json", pin, compact=False)

    derived_manifest = {
        **manifest,
        "derive_schema": DERIVE_SCHEMA,
        "derived_at": datetime.now(timezone.utc).isoformat(),
        "canonical_dataset_version": manifest.get("dataset_version"),
        "derived_coverage": {
            "catalog_top": len(top_rows),
            "catalog_children_files": len(children_map),
            "area_details": len(areas),
            "boundaries_copied": copied_boundaries,
            "place_shards": place_files_written,
            "search_national": len(national_items),
        },
        "consumer_root": "data-derived/",
        "pin_file": "pin.json",
        "notes": {
            **(manifest.get("notes") or {}),
            "reviews_excluded": True,
            "boundary_verbatim": True,
        },
    }
    write_json(OUT / "manifest.json", derived_manifest, compact=False)

    # size report
    top_path = OUT / "catalog" / "top.json"
    top_raw = top_path.stat().st_size
    nat_path = OUT / "search" / "national.json"
    print("derive_publish OK")
    print(f"  out: {OUT}")
    print(f"  catalog/top.json bytes: {top_raw}")
    print(f"  children files: {len(children_map)}")
    print(f"  boundaries: {copied_boundaries}")
    print(f"  place shards: {place_files_written}")
    print(f"  search/national.json bytes: {nat_path.stat().st_size}")
    print(f"  pin.json tag: {tag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
