# -*- coding: utf-8 -*-
"""
Extract Xırdalan under Abşeron rayonu + microhood children + named places.

Requires Abşeron parent from extract_masazir.py.
Hierarchy.md verified rules. source_files/ read-only.
"""
from __future__ import annotations

import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pyarrow.parquet as pq
from shapely import wkb as swkb
from shapely.geometry import Point, mapping
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
SRC = Path("source_files")
OUT = Path("data")
OVERTURE_RELEASE = "2026-09-23.1"
OSM_RELEASE = "azerbaijan-261020"
OSM_XIRDALAN_NODE = 1886282981

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


def load_boundary_file(rel: str | None):
    if not rel:
        return None
    path = OUT / rel
    if not path.exists():
        return None
    from shapely.geometry import shape

    fc = load_json(path)
    geoms = []
    for f in fc.get("features") or []:
        g = f.get("geometry")
        if g and g.get("type") in ("Polygon", "MultiPolygon"):
            geoms.append(shape(g))
    if not geoms:
        return None
    return geoms[0] if len(geoms) == 1 else unary_union(geoms)


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


def make_area(*, key, name, type_, subtype, parent_id, parent_status, geom, geom_status, center, wikidata, source_refs, notes=None, alt_names=None, boundary_name=None):
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


def main() -> int:
    areas_path = OUT / "areas" / "areas.json"
    areas = load_json(areas_path)["areas"]
    reviews_path = OUT / "reviews" / "pilot_reviews.json"
    reviews = list((load_json(reviews_path) if reviews_path.exists() else {}).get("reviews") or [])

    absheron = next((a for a in areas if a.get("name") == "Abşeron rayonu"), None)
    if not absheron:
        raise SystemExit("Abşeron rayonu missing — run pnpm extract:masazir first")

    # Remove previous Xırdalan tree
    drop = {a["id"] for a in areas if a.get("name") == "Xırdalan" or "xirdalan" in (a.get("boundary_file") or "")}
    changed = True
    while changed:
        changed = False
        for a in areas:
            if a.get("parent_id") in drop and a["id"] not in drop:
                drop.add(a["id"])
                changed = True
    areas = [a for a in areas if a["id"] not in drop]
    print(f"Removed previous Xırdalan areas: {len(drop)}")

    ov_div, ov_areas = load_overture()
    ov_abs = next(
        (v for v in ov_div.values() if v["name"] == "Abşeron rayonu" and v["subtype"] == "region"),
        None,
    )
    ov_x = next(
        (v for v in ov_div.values() if v["name"] == "Xırdalan" and v["subtype"] == "locality"),
        None,
    )
    if not ov_x:
        raise SystemExit("Overture Xırdalan locality not found")

    abs_geom = load_boundary_file(absheron.get("boundary_file"))
    x_geom = ov_areas.get(ov_x["id"])
    parent_status = "verified" if ov_abs and ov_x.get("parent") == ov_abs["id"] else "conflict"
    notes = None
    if parent_status != "verified":
        notes = f"Overture parent mismatch vs Abşeron"
        reviews.append(
            {
                "id": cid("review", "xirdalan-parent"),
                "kind": "hierarchy_conflict",
                "entity": "Xırdalan",
                "detail": notes,
                "status": "open",
            }
        )
    if x_geom is not None and abs_geom is not None and parent_status == "verified":
        if not contained(x_geom, abs_geom):
            parent_status = "conflict"
            notes = "Geometry not contained in Abşeron rayonu polygon"
            reviews.append(
                {
                    "id": cid("review", "xirdalan-containment"),
                    "kind": "hierarchy_conflict",
                    "entity": "Xırdalan",
                    "detail": notes,
                    "status": "open",
                }
            )

    label = (40.4531707, 49.7454579, "osm_place_node")
    x_rec, x_id = make_area(
        key="neighborhood:xirdalan",
        name="Xırdalan",
        type_="neighborhood",
        subtype="locality",
        parent_id=absheron["id"],
        parent_status=parent_status,
        geom=x_geom,
        geom_status="verified" if x_geom is not None else "missing",
        center=label,
        wikidata="Q642109",
        source_refs=[
            {
                "source": "overture",
                "source_id": ov_x["id"],
                "release": OVERTURE_RELEASE,
                "role": "boundary",
                "match_method": "id",
                "overture_parent_id": ov_x.get("parent"),
            },
            {
                "source": "osm",
                "source_id": f"node/{OSM_XIRDALAN_NODE}",
                "release": OSM_RELEASE,
                "role": "label",
                "match_method": "id",
            },
        ],
        notes=notes
        or "City/settlement under Abşeron rayonu. Microhoods are verified children (UI drill-down).",
        alt_names=["Khirdalan", "Xirdalan"],
        boundary_name="neighborhood_xirdalan",
    )
    areas.append(x_rec)
    if x_geom is not None:
        write_boundary(
            x_id,
            "Xırdalan",
            x_geom,
            "boundaries/neighborhood_xirdalan.geojson",
            {"type": "neighborhood", "parent_id": absheron["id"], "parent_status": parent_status},
        )
    print(f"Xırdalan parent_status={parent_status} geom={'OK' if x_geom else 'MISSING'}")

    verified_kids = []
    conflicts = []
    used = set()
    for child in sorted(
        (v for v in ov_div.values() if v.get("parent") == ov_x["id"]),
        key=lambda z: z["name"] or "",
    ):
        if (child.get("subtype") or "") not in ALLOWED:
            continue
        if not child.get("name") or not child["name"].strip():
            continue
        key = "xirdalan_" + slug(child["name"])
        base = key
        n = 2
        while key in used:
            key = f"{base}_{n}"
            n += 1
        used.add(key)
        geom = ov_areas.get(child["id"])
        st = "verified"
        gstatus = "verified" if geom is not None else "missing"
        cnotes = "Overture child of Xırdalan"
        if geom is None:
            st = "missing"
            continue
        if x_geom is not None and not contained(geom, x_geom):
            st = "conflict"
            cnotes = "Parent=Xırdalan but not contained in Xırdalan polygon"
            conflicts.append(child["name"])
            reviews.append(
                {
                    "id": cid("review", "containment", key),
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
            parent_id=x_id,
            parent_status=st,
            geom=geom,
            geom_status=gstatus,
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
                "parent_id": x_id,
                "parent_status": st,
                "subtype": child["subtype"],
            },
        )
        if st == "verified":
            verified_kids.append(child["name"])

    print(f"Verified microhoods: {len(verified_kids)} → {verified_kids}")
    print(f"Conflicts: {conflicts}")

    places = []
    if x_geom is not None:
        for p in extract_places_in(x_geom, max_places=400):
            places.append(
                {
                    "id": cid("place", "overture", p["overture_id"]),
                    "name": p["name"],
                    "name_normalized": norm(p["name"]),
                    "alt_names": [],
                    "category": p["category"],
                    "coordinates": {"lat": p["lat"], "lon": p["lon"]},
                    "area_id": x_id,
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
    print(f"Places: {len(places)}")

    pdir = OUT / "places"
    write_json(
        pdir / "xirdalan_all.json",
        {"area_id": x_id, "parent_area_id": absheron["id"], "places": places},
    )
    index_path = pdir / "index.json"
    index = load_json(index_path) if index_path.exists() else {}
    files = list(index.get("files") or [])
    if "places/xirdalan_all.json" not in files:
        files.append("places/xirdalan_all.json")
    by_rayon = dict(index.get("by_rayon") or {})
    by_rayon["xirdalan"] = {
        "name": "Xırdalan",
        "area_id": x_id,
        "count": len(places),
        "file": "places/xirdalan_all.json",
    }
    total = 0
    for f in files:
        fp = OUT / f
        if fp.exists():
            total += len(load_json(fp).get("places") or [])
    write_json(
        index_path,
        {
            "region": index.get("region") or "absheron_agglomeration",
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
    write_json(reviews_path, {"reviews": list({r["id"]: r for r in reviews}.values())})

    report = {
        "xirdalan_id": x_id,
        "parent": absheron["name"],
        "parent_status": parent_status,
        "verified_microhoods": verified_kids,
        "conflicts": conflicts,
        "places": len(places),
        "areas_total": len(areas),
    }
    write_json(OUT / "reviews" / "xirdalan_extract.json", report)

    manifest = load_json(OUT / "manifest.json")
    manifest["dataset_version"] = "0.1.6-pilot"
    manifest["generated_at"] = datetime.now(timezone.utc).isoformat()
    cov = manifest.setdefault("coverage", {})
    cov["areas"] = len(areas)
    cov["boundaries"] = len(b_index)
    cov["places"] = total
    cov["description"] = (
        "Country + Bakı + Sumqayıt + Abşeron (Masazır, Xırdalan+microhoods). "
        "Hierarchy.md / WORKER.md."
    )
    write_json(OUT / "manifest.json", manifest)

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
