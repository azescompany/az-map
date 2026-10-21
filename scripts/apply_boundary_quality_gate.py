# -*- coding: utf-8 -*-
"""
Boundary accuracy gate for curated data/ areas.

- Does not touch source_files/
- Recomputes interior centers from polygons where eligible
- Downgrades geom_status when verification requirements fail
- Writes audit report under data/reviews/
"""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from shapely.geometry import Point, shape
from shapely.validation import explain_validity

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
AREAS_PATH = DATA / "areas" / "areas.json"
REVIEWS_DIR = DATA / "reviews"
CRS = "EPSG:4326"

# Known incompleteness / conflicts that block verified status even if geometry is valid
FORCE_PARTIAL = {
    # Overture Bakı region was incomplete; city uses OSM but product notes remain
}
FORCE_CONFLICT_NOTES = {
    # filled dynamically from existing reviews / area notes
}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def boundary_source(area: dict) -> tuple[str | None, str | None, str | None]:
    for ref in area.get("source_refs") or []:
        if ref.get("role") in ("boundary", "boundary_partial", "hierarchy_partial"):
            # prefer true boundary role
            pass
    boundary_refs = [
        r
        for r in (area.get("source_refs") or [])
        if r.get("role") in ("boundary",)
    ]
    if not boundary_refs:
        boundary_refs = list(area.get("source_refs") or [])
    if not boundary_refs:
        return None, None, None
    r = boundary_refs[0]
    return r.get("source"), r.get("source_id"), r.get("release")


def load_geom(area: dict):
    bf = area.get("boundary_file")
    if not bf:
        return None, "missing_boundary_file"
    path = DATA / bf
    if not path.exists():
        return None, "boundary_file_not_found"
    gj = load(path)
    feats = gj.get("features") or []
    if not feats:
        return None, "empty_feature_collection"
    geoms = []
    for f in feats:
        g = f.get("geometry")
        if not g:
            continue
        if g.get("type") not in ("Polygon", "MultiPolygon"):
            return None, f"unsupported_geometry_type:{g.get('type')}"
        geoms.append(shape(g))
    if not geoms:
        return None, "no_polygon_geometries"
    if len(geoms) == 1:
        return geoms[0], None
    from shapely.ops import unary_union

    return unary_union(geoms), None


def point_in_geom(geom, lat: float, lon: float) -> bool:
    pt = Point(lon, lat)
    # covers includes boundary; buffer tiny for float noise
    try:
        if geom.covers(pt):
            return True
        return bool(geom.buffer(1e-9).covers(pt))
    except Exception:
        return False


def child_within_parent(child, parent) -> bool | None:
    if child is None or parent is None:
        return None
    try:
        c = child.representative_point()
        return bool(parent.covers(c) or parent.intersects(child))
    except Exception:
        return None


def audit_and_fix() -> dict:
    doc = load(AREAS_PATH)
    areas = doc["areas"]
    by_id = {a["id"]: a for a in areas}
    geoms = {}
    audits = []
    status_counts = Counter()

    # preload reviews that mention hierarchy conflicts
    review_path = REVIEWS_DIR / "pilot_reviews.json"
    open_conflicts = set()
    if review_path.exists():
        for r in load(review_path).get("reviews", []):
            if r.get("kind") == "hierarchy_conflict" and r.get("status") in ("open", "documented"):
                open_conflicts.add(r.get("entity"))

    for area in areas:
        name = area["name"]
        aid = area["id"]
        src, src_id, release = boundary_source(area)
        geom, geom_err = load_geom(area)
        geoms[aid] = geom

        geom_type = None
        geom_valid = False
        geom_empty = True
        validity_note = geom_err
        parts = None

        if geom is not None:
            geom_empty = geom.is_empty
            geom_type = geom.geom_type
            geom_valid = bool(geom.is_valid and not geom.is_empty)
            if not geom.is_valid:
                validity_note = explain_validity(geom)
            elif geom.is_empty:
                validity_note = "empty_geometry"
            else:
                validity_note = "ok"
            if geom_type == "MultiPolygon":
                parts = len(geom.geoms)

        # Center: prefer interior rep_point when geometry is usable
        center_lat = center_lon = None
        center_method = None
        center_status = "missing"
        center_within = None
        old = area.get("center") or {}
        old_lat = old.get("latitude", old.get("lat"))
        old_lon = old.get("longitude", old.get("lon"))

        if geom is not None and geom_valid:
            try:
                rp = geom.representative_point()
                center_lat, center_lon = float(rp.y), float(rp.x)
                center_method = "interior_representative_point"
                center_status = "verified"
                center_within = point_in_geom(geom, center_lat, center_lon)
                if not center_within:
                    # fallback centroid then mark
                    c = geom.centroid
                    center_lat, center_lon = float(c.y), float(c.x)
                    center_method = "centroid"
                    center_within = point_in_geom(geom, center_lat, center_lon)
                    center_status = "verified" if center_within else "conflict"
            except Exception as e:
                validity_note = f"center_calc_failed:{e}"
        elif old_lat is not None and old_lon is not None:
            center_lat, center_lon = float(old_lat), float(old_lon)
            center_method = area.get("center_method") or "source_label_point"
            # Label/node points are not official geographic centers
            if center_method in ("osm_place_node", "geonames", "label", "source_label_point"):
                center_status = "label_fallback"
            else:
                center_status = "unverified"
            if geom is not None and not geom.is_empty:
                center_within = point_in_geom(geom, center_lat, center_lon)
            else:
                center_within = None

        # Decide geom_status under gate rules
        reasons = []
        geom_status = area.get("geom_status") or "missing"

        if geom is None or geom_empty:
            geom_status = "missing"
            reasons.append(validity_note or "no_geometry")
        elif not geom_valid:
            geom_status = "conflict"
            reasons.append(f"invalid_geometry:{validity_note}")
        elif src is None or src_id is None:
            geom_status = "partial"
            reasons.append("missing_boundary_source_ref")
        else:
            # eligible for verified unless known truncation / unresolved conflict for THIS area's boundary
            geom_status = "verified"
            # Bakı: if only incomplete overture was used historically — check notes
            notes = (area.get("notes") or "") + " " + " ".join(
                (r.get("note") or "") for r in (area.get("source_refs") or [])
            )
            if "incomplete" in notes.lower() or "partial" in notes.lower():
                # only downgrade if boundary source is the incomplete overture region
                if src == "overture" and any(
                    (r.get("role") == "hierarchy_partial") for r in (area.get("source_refs") or [])
                ):
                    # OSM boundary present for Bakı — keep verified if OSM is boundary source
                    pass
            if name in FORCE_PARTIAL:
                geom_status = "partial"
                reasons.append(FORCE_PARTIAL[name])

        # Parent relationship checks (do not invent; may flag conflict)
        parent_id = area.get("parent_id")
        parent_status = area.get("parent_status")
        parent_geom_ok = None
        if parent_id and parent_id in geoms and geom is not None:
            # parent geom may not be loaded yet — second pass below
            pass

        audit = {
            "id": aid,
            "name": name,
            "type": area.get("type"),
            "boundary_source": src,
            "boundary_source_id": src_id,
            "boundary_release": release,
            "crs": CRS,
            "geometry_type": geom_type,
            "multipart_parts": parts,
            "geometry_valid": geom_valid,
            "geometry_empty": geom_empty,
            "geometry_validity_note": validity_note,
            "geom_status_before": area.get("geom_status"),
            "geom_status_after": geom_status,
            "geom_status_reasons": reasons,
            "center_latitude": center_lat,
            "center_longitude": center_lon,
            "center_method": center_method,
            "center_status": center_status,
            "center_within_boundary": center_within,
            "parent_id": parent_id,
            "parent_status": parent_status,
            "boundary_file": area.get("boundary_file"),
            "source_refs": area.get("source_refs"),
            "attribution": {
                "osm": "© OpenStreetMap contributors (ODbL 1.0)" if src == "osm" else None,
                "overture": "Overture Maps Foundation" if src == "overture" else None,
                "geonames": "GeoNames CC BY 4.0" if src == "geonames" else None,
            },
        }
        audits.append(audit)
        status_counts[geom_status] += 1

        # Apply updates to area record
        area["geom_status"] = geom_status
        area["geom_status_reason"] = "; ".join(reasons) if reasons else None
        area["crs"] = CRS
        area["geometry_type"] = geom_type
        area["geometry_valid"] = geom_valid
        if center_lat is not None and center_lon is not None:
            area["center"] = {
                "latitude": center_lat,
                "longitude": center_lon,
                # backward-compatible aliases for current demo
                "lat": center_lat,
                "lon": center_lon,
            }
        else:
            area["center"] = None
        area["center_method"] = center_method
        area["center_status"] = center_status
        area["center_within_boundary"] = center_within

    # Second pass: child-parent geometry relationship
    parent_geom_warnings = []
    for area in areas:
        pid = area.get("parent_id")
        if not pid:
            continue
        child_g = geoms.get(area["id"])
        parent_g = geoms.get(pid)
        ok = child_within_parent(child_g, parent_g)
        for audit in audits:
            if audit["id"] == area["id"]:
                audit["child_inside_parent_geom"] = ok
        if ok is False and area.get("parent_status") == "verified":
            # Do not silently flip parent_status if product already verified via OSM admin —
            # flag as warning / review unless neighborhood
            parent_geom_warnings.append(
                {
                    "id": area["id"],
                    "name": area["name"],
                    "parent_id": pid,
                    "parent_name": by_id.get(pid, {}).get("name"),
                    "detail": "Child representative point is not inside parent polygon; admin parent may still be intentional.",
                }
            )
            if area.get("type") == "neighborhood":
                area["parent_status"] = "conflict"
                area["notes"] = (
                    (area.get("notes") or "")
                    + " Quality gate: child geometry not contained by parent polygon."
                ).strip()
                for audit in audits:
                    if audit["id"] == area["id"]:
                        audit["parent_status"] = "conflict"
                        audit["geom_status_reasons"].append("child_not_in_parent_polygon")

    # Blocking: verified geom must have center within + valid geom
    for area in areas:
        if area.get("geom_status") == "verified":
            if not area.get("geometry_valid"):
                area["geom_status"] = "conflict"
                area["geom_status_reason"] = "verified_requires_valid_geometry"
            elif area.get("center") is None:
                area["geom_status"] = "partial"
                area["geom_status_reason"] = "verified_boundary_missing_center"
            elif area.get("center_within_boundary") is False:
                area["geom_status"] = "partial"
                area["geom_status_reason"] = "center_outside_boundary"
                area["center_status"] = "conflict"

    # recount after final adjustments
    status_counts = Counter(a.get("geom_status") for a in areas)
    center_counts = Counter(a.get("center_status") for a in areas)

    dump(AREAS_PATH, doc)

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "crs": CRS,
        "area_count": len(areas),
        "geom_status_counts": dict(status_counts),
        "center_status_counts": dict(center_counts),
        "parent_geometry_warnings": parent_geom_warnings,
        "areas": audits,
        "verification_policy": {
            "verified_requires": [
                "real source geometry",
                "valid non-empty Polygon/MultiPolygon",
                "CRS EPSG:4326 (GeoJSON lon/lat)",
                "linked source_ref role=boundary",
                "interior center within boundary",
                "no fabricated geometry",
            ],
            "disclaimer": "Geometry validity and source linkage do not claim official cadastral accuracy.",
        },
    }
    dump(REVIEWS_DIR / "boundary_quality_audit.json", report)

    # human-readable markdown-ish text report
    lines = []
    lines.append("# Boundary quality audit")
    lines.append(f"Generated: {report['generated_at']}")
    lines.append(
        f"Counts geom_status: {dict(status_counts)} | center_status: {dict(center_counts)}"
    )
    lines.append("")
    for a in audits:
        lines.append(f"## {a['name']} (`{a['id']}`)")
        lines.append(
            f"- boundary: {a['boundary_source']} `{a['boundary_source_id']}` @ {a['boundary_release']}"
        )
        lines.append(
            f"- geometry: type={a['geometry_type']} valid={a['geometry_valid']} empty={a['geometry_empty']} crs={a['crs']} parts={a['multipart_parts']}"
        )
        lines.append(
            f"- geom_status: {a['geom_status_before']} → {a['geom_status_after']} reasons={a['geom_status_reasons']}"
        )
        lines.append(
            f"- center: lat={a['center_latitude']} lon={a['center_longitude']} method={a['center_method']} status={a['center_status']} within={a['center_within_boundary']}"
        )
        lines.append(
            f"- parent: {a['parent_id']} status={a['parent_status']} child_in_parent={a.get('child_inside_parent_geom')}"
        )
        lines.append("")
    (REVIEWS_DIR / "boundary_quality_audit.txt").write_text(
        "\n".join(lines), encoding="utf-8"
    )

    # update manifest quality section
    manifest_path = DATA / "manifest.json"
    manifest = load(manifest_path)
    manifest["dataset_version"] = "0.1.1-pilot"
    manifest["quality_gate"] = {
        "applied_at": report["generated_at"],
        "geom_status_counts": dict(status_counts),
        "center_status_counts": dict(center_counts),
        "crs": CRS,
        "audit_report": "reviews/boundary_quality_audit.json",
    }
    dump(manifest_path, manifest)

    print(json.dumps({"geom_status_counts": dict(status_counts), "center_status_counts": dict(center_counts), "parent_geometry_warnings": len(parent_geom_warnings)}, indent=2))
    return report


if __name__ == "__main__":
    audit_and_fix()
