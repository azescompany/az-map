#!/usr/bin/env python3
"""CI gates for data-derived/ — see docs/claude/12-ci-gates.md."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DER = ROOT / "data-derived"


def load_json(path: Path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def center_pair(c) -> tuple[float | None, float | None]:
    if not isinstance(c, dict):
        return None, None
    try:
        lat = c.get("lat", c.get("latitude"))
        lon = c.get("lon", c.get("longitude"))
        if lat is None or lon is None:
            return None, None
        return float(lat), float(lon)
    except (TypeError, ValueError):
        return None, None


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    if not DER.is_dir():
        print("ERROR: data-derived/ missing — run pnpm derive:publish", file=sys.stderr)
        return 1

    # Gate 7: no audit/reviews under consumer path
    for bad in ("reviews",):
        if (DER / bad).exists():
            errors.append(f"audit/reviews path present under derived: {bad}")
    for p in DER.rglob("*audit*"):
        errors.append(f"audit-like path under derived: {p.relative_to(DER)}")

    # Gate 6: no cross-district aggregates
    for p in DER.rglob("*"):
        name = p.name.lower()
        if "baki_all" in name or "all_districts" in name:
            errors.append(f"forbidden aggregate: {p.relative_to(DER)}")

    manifest = load_json(DER / "manifest.json")
    if not manifest.get("derive_schema"):
        errors.append("manifest missing derive_schema")

    top = load_json(DER / "catalog" / "top.json")
    top_areas = top.get("areas") or []
    if not top_areas:
        errors.append("catalog/top.json empty")

    all_slim_path = DER / "catalog" / "all-slim.json"
    if not all_slim_path.is_file():
        errors.append("catalog/all-slim.json missing")
    else:
        all_slim = load_json(all_slim_path)
        if not (all_slim.get("areas") or []):
            errors.append("catalog/all-slim.json empty")

    hashes_path = DER / "boundaries" / "_hashes.json"
    if not hashes_path.is_file():
        errors.append("boundaries/_hashes.json missing")
    else:
        hashes = load_json(hashes_path)
        for item in hashes.get("items") or []:
            aid = item["area_id"]
            canonical = DATA / item["canonical"]
            derived = DER / item["derived"]
            if not canonical.is_file():
                errors.append(f"canonical boundary missing: {item['canonical']}")
                continue
            if not derived.is_file():
                errors.append(f"derived boundary missing: {item['derived']}")
                continue
            # Gate 1: byte identity
            if sha256_file(canonical) != sha256_file(derived):
                errors.append(f"boundary hash mismatch: {aid}")
            if item.get("sha256") and item["sha256"] != sha256_file(canonical):
                errors.append(f"stale hash entry: {aid}")

    # Gate 8: catalog center == detail center (sample all top + spot-check children)
    def check_center(row: dict, label: str) -> None:
        detail_path = DER / "areas" / f"{row['id']}.json"
        if not detail_path.is_file():
            errors.append(f"missing area detail: {row['id']}")
            return
        detail = load_json(detail_path)
        clat, clon = center_pair(row.get("center"))
        dlat, dlon = center_pair(detail.get("center"))
        if clat is None or clon is None:
            # Gate 4-ish for catalog rows used in UI
            if row.get("type") != "country":
                errors.append(f"catalog center missing: {label}")
            return
        if dlat is None or abs(clat - dlat) > 1e-9 or abs(clon - dlon) > 1e-9:
            errors.append(f"catalog/detail center mismatch: {label}")

    for row in top_areas:
        check_center(row, row.get("name") or row["id"])

    # Gate 2 + 5: places index
    shards = load_json(DER / "places" / "shards.json")
    by_area = shards.get("by_area_id") or {}
    seen_place_owners: dict[str, str] = {}
    for aid, meta in by_area.items():
        idx_path = DER / "places" / "index" / f"{aid}.json"
        if not idx_path.is_file():
            errors.append(f"missing places index for {aid}")
            continue
        idx = load_json(idx_path)
        for p in idx.get("places") or []:
            pid = p.get("id")
            coords = p.get("coordinates") or {}
            try:
                lat = float(coords["lat"])
                lon = float(coords["lon"])
            except (KeyError, TypeError, ValueError):
                errors.append(f"place missing coords: {pid}")
                continue
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                errors.append(f"place bad coords: {pid}")
            if not (p.get("name") or "").strip():
                errors.append(f"place empty name: {pid}")
            if pid in seen_place_owners and seen_place_owners[pid] != aid:
                warnings.append(
                    f"place {pid} in multiple shards: {seen_place_owners[pid]} and {aid}"
                )
            else:
                seen_place_owners[pid] = aid

    # Gate 3: verified children — spot-check country children file exists for AZ
    country = next((a for a in top_areas if a.get("type") == "country"), None)
    if country:
        ch = DER / "catalog" / "children" / f"{country['id']}.json"
        if not ch.is_file():
            errors.append("missing children shard for country")
        else:
            kids = load_json(ch).get("areas") or []
            for k in kids:
                if k.get("parent_status") != "verified":
                    errors.append(f"non-verified child in children shard: {k.get('id')}")
                bref = k.get("boundary_ref")
                if bref and not (DER / bref).is_file():
                    errors.append(f"child boundary_ref missing on disk: {bref}")

    # Gate 9: manifest totals vs disk (derived_coverage)
    cov = manifest.get("derived_coverage") or {}
    boundary_count = len(list((DER / "boundaries").glob("*.geojson")))
    # exclude nothing — only *.geojson
    if cov.get("boundaries_copied") is not None and cov["boundaries_copied"] != boundary_count:
        errors.append(
            f"manifest boundaries_copied {cov['boundaries_copied']} != disk {boundary_count}"
        )

    print("validate_derived")
    print(f"  errors: {len(errors)}  warnings: {len(warnings)}")
    for w in warnings[:20]:
        print(f"  WARN: {w}")
    for e in errors[:50]:
        print(f"  ERROR: {e}")
    if len(errors) > 50:
        print(f"  ... {len(errors) - 50} more errors")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
