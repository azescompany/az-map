# -*- coding: utf-8 -*-
"""
Extract remaining Abşeron rayonu settlements + nested microhoods + rayon places.

Requires Abşeron parent (extract_masazir) + keeps Masazır / Xırdalan trees intact.
Hierarchy.md verified rules. source_files/ read-only → data/.
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
from shapely.geometry import Point, mapping, shape
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
SRC = Path("source_files")
OUT = Path("data")
OVERTURE_RELEASE = "2026-09-23.1"
OSM_RELEASE = "azerbaijan-261020"

NS = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")
ALLOWED = {"microhood", "macrohood", "neighborhood", "locality"}
# Already extracted as dedicated WORKER blocks — do not recreate
SKIP_TOP_NAMES = {"Masazır", "Xırdalan"}

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
    fc = load_json(path)
    geoms = []
    for f in fc.get("features") or []:
        g = f.get("geometry")
        if g and g.get("type") in ("Polygon", "MultiPolygon"):
            geoms.append(shape(g))
    if not geoms:
        return None
    return geoms[0] if len(geoms) == 1 else unary_union(geoms)


def extract_places_in(poly, max_places=800):
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


def is_absheron_extract(a, absheron_id: str, keep_ids: set[str]) -> bool:
    """True if area was produced by this script (direct/indirect Absheron child, not Masazır/Xırdalan)."""
    if a["id"] in keep_ids:
        return False
    notes = a.get("notes") or ""
    bf = a.get("boundary_file") or ""
    if "WORKER 1.5" in notes or bf.startswith("boundaries/neighborhood_absheron_"):
        return True
    # also drop orphaned prior runs by parent chain under Absheron excluding keep trees
    return False


def collect_keep_tree(areas, root_names: set[str]) -> set[str]:
    keep = {a["id"] for a in areas if a.get("name") in root_names}
    changed = True
    while changed:
        changed = False
        for a in areas:
            if a.get("parent_id") in keep and a["id"] not in keep:
                keep.add(a["id"])
                changed = True
    return keep


def pick_best_children(candidates: list[dict], ov_areas: dict) -> list[dict]:
    """Dedupe by name: prefer record that has geometry; prefer locality over others."""
    rank = {"locality": 0, "macrohood": 1, "neighborhood": 2, "microhood": 3}
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


def add_child_area(
    *,
    areas,
    reviews,
    ov_areas,
    abs_geom,
    parent_area_id,
    parent_geom,
    child,
    key_prefix: str,
    used_keys: set,
    verified_names: list,
    conflict_names: list,
):
    if (child.get("subtype") or "") not in ALLOWED:
        return None
    if not child.get("name") or not child["name"].strip():
        return None
    if child["name"] in SKIP_TOP_NAMES and key_prefix == "absheron":
        return None

    key = f"{key_prefix}_{slug(child['name'])}"
    base = key
    n = 2
    while key in used_keys:
        key = f"{base}_{n}"
        n += 1
    used_keys.add(key)

    geom = ov_areas.get(child["id"])
    if geom is None:
        return None

    st = "verified"
    cnotes = f"WORKER 1.5 · Overture child under Absheron extract ({key_prefix})"
    if parent_geom is not None and not contained(geom, parent_geom):
        st = "conflict"
        cnotes = f"Overture parent ok but not contained in parent polygon ({key_prefix})"
        conflict_names.append(child["name"])
        reviews.append(
            {
                "id": cid("review", "absheron-containment", key),
                "kind": "hierarchy_conflict",
                "entity": child["name"],
                "detail": cnotes,
                "overture_id": child["id"],
                "status": "open",
            }
        )
    elif abs_geom is not None and not contained(geom, abs_geom):
        st = "conflict"
        cnotes = "Not contained in Abşeron rayonu polygon"
        conflict_names.append(child["name"])
        reviews.append(
            {
                "id": cid("review", "absheron-rayon-containment", key),
                "kind": "hierarchy_conflict",
                "entity": child["name"],
                "detail": cnotes,
                "overture_id": child["id"],
                "status": "open",
            }
        )

    bname = f"neighborhood_absheron_{key}"
    rec, aid = make_area(
        key=f"neighborhood:{key}",
        name=child["name"],
        type_="neighborhood",
        subtype=child["subtype"],
        parent_id=parent_area_id,
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
        boundary_name=bname,
    )
    areas.append(rec)
    write_boundary(
        aid,
        child["name"],
        geom,
        rec["boundary_file"],
        {
            "type": "neighborhood",
            "parent_id": parent_area_id,
            "parent_status": st,
            "subtype": child["subtype"],
        },
    )
    if st == "verified":
        verified_names.append(child["name"])
    return {"id": aid, "ov_id": child["id"], "name": child["name"], "geom": geom, "status": st}


def main() -> int:
    areas_path = OUT / "areas" / "areas.json"
    areas = load_json(areas_path)["areas"]
    reviews_path = OUT / "reviews" / "pilot_reviews.json"
    reviews = list((load_json(reviews_path) if reviews_path.exists() else {}).get("reviews") or [])

    absheron = next((a for a in areas if a.get("name") == "Abşeron rayonu"), None)
    if not absheron:
        raise SystemExit("Abşeron rayonu missing — run pnpm extract:masazir first")

    keep = collect_keep_tree(areas, SKIP_TOP_NAMES)
    keep.add(absheron["id"])

    # Drop prior WORKER 1.5 Absheron settlement areas (not Masazır/Xırdalan)
    drop = {
        a["id"]
        for a in areas
        if is_absheron_extract(a, absheron["id"], keep)
        or (
            a.get("parent_id") == absheron["id"]
            and a.get("name") not in SKIP_TOP_NAMES
            and a["id"] not in keep
            and ("WORKER 1.5" in (a.get("notes") or "") or "absheron_" in (a.get("boundary_file") or ""))
        )
    }
    # Also drop children of dropped
    changed = True
    while changed:
        changed = False
        for a in areas:
            if a.get("parent_id") in drop and a["id"] not in drop and a["id"] not in keep:
                drop.add(a["id"])
                changed = True
    # Clean boundary files for dropped
    for a in areas:
        if a["id"] in drop and a.get("boundary_file"):
            p = OUT / a["boundary_file"]
            if p.exists() and "absheron_" in a["boundary_file"]:
                p.unlink()
    areas = [a for a in areas if a["id"] not in drop]
    print(f"Removed previous Absheron settlement areas: {len(drop)}")

    ov_div, ov_areas = load_overture()
    ov_abs = next(
        (v for v in ov_div.values() if v["name"] == "Abşeron rayonu" and v["subtype"] == "region"),
        None,
    )
    if not ov_abs:
        raise SystemExit("Overture Abşeron rayonu region not found")

    abs_geom = load_boundary_file(absheron.get("boundary_file"))
    if abs_geom is None:
        raise SystemExit("Abşeron boundary missing")

    direct_raw = [
        v
        for v in ov_div.values()
        if v.get("parent") == ov_abs["id"]
        and (v.get("subtype") or "") in ALLOWED
        and v.get("name")
        and v["name"].strip()
        and v["name"] not in SKIP_TOP_NAMES
    ]
    direct = pick_best_children(direct_raw, ov_areas)
    print(f"Overture Absheron children (excl Masazır/Xırdalan): {len(direct)}")

    used_keys: set[str] = set()
    verified_top: list[str] = []
    conflicts: list[str] = []
    nested_verified: dict[str, list[str]] = {}
    added_top = []

    for child in direct:
        res = add_child_area(
            areas=areas,
            reviews=reviews,
            ov_areas=ov_areas,
            abs_geom=abs_geom,
            parent_area_id=absheron["id"],
            parent_geom=abs_geom,
            child=child,
            key_prefix="absheron",
            used_keys=used_keys,
            verified_names=verified_top,
            conflict_names=conflicts,
        )
        if not res or res["status"] != "verified":
            continue
        added_top.append(res)

        # Nested Overture children (e.g. Digah → Digah qəsəbəsi)
        nest_raw = [
            v
            for v in ov_div.values()
            if v.get("parent") == child["id"]
            and (v.get("subtype") or "") in ALLOWED
            and v.get("name")
            and v["name"].strip()
        ]
        nest = pick_best_children(nest_raw, ov_areas)
        nest_ok: list[str] = []
        nest_conf: list[str] = []
        for nc in nest:
            add_child_area(
                areas=areas,
                reviews=reviews,
                ov_areas=ov_areas,
                abs_geom=abs_geom,
                parent_area_id=res["id"],
                parent_geom=res["geom"],
                child=nc,
                key_prefix=f"absheron_{slug(child['name'])}",
                used_keys=used_keys,
                verified_names=nest_ok,
                conflict_names=nest_conf,
            )
        if nest_ok:
            nested_verified[child["name"]] = nest_ok
        if nest_conf:
            conflicts.extend(nest_conf)

    print(f"Verified top settlements: {len(verified_top)}")
    for n in verified_top:
        print(f"  · {n}")
    if nested_verified:
        print("Nested verified:")
        for k, v in nested_verified.items():
            print(f"  {k} → {v}")
    print(f"Conflicts: {conflicts}")

    # Avoid duplicate place ids across rayon files (validator hard-fail)
    existing_place_ids: set[str] = set()
    pdir = OUT / "places"
    index_path = pdir / "index.json"
    if index_path.exists():
        for f in (load_json(index_path).get("files") or []):
            if f == "places/absheron_all.json":
                continue
            fp = OUT / f
            if not fp.exists():
                continue
            for pl in load_json(fp).get("places") or []:
                if pl.get("id"):
                    existing_place_ids.add(pl["id"])

    places = []
    skipped_dup = 0
    for p in extract_places_in(abs_geom, max_places=800):
        pid = cid("place", "overture", p["overture_id"])
        if pid in existing_place_ids:
            skipped_dup += 1
            continue
        places.append(
            {
                "id": pid,
                "name": p["name"],
                "name_normalized": norm(p["name"]),
                "alt_names": [],
                "category": p["category"],
                "coordinates": {"lat": p["lat"], "lon": p["lon"]},
                "area_id": absheron["id"],
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
    print(f"Absheron-scope places: {len(places)} (skipped dup {skipped_dup})")

    write_json(
        pdir / "absheron_all.json",
        {"area_id": absheron["id"], "parent_area_id": absheron.get("parent_id"), "places": places},
    )
    index = load_json(index_path) if index_path.exists() else {}
    files = list(index.get("files") or [])
    if "places/absheron_all.json" not in files:
        files.append("places/absheron_all.json")
    by_rayon = dict(index.get("by_rayon") or {})
    by_rayon["absheron"] = {
        "name": "Abşeron rayonu",
        "area_id": absheron["id"],
        "count": len(places),
        "file": "places/absheron_all.json",
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
    write_json(reviews_path, {"reviews": reviews})
    write_json(
        OUT / "reviews" / "absheron_extract.json",
        {
            "parent": "Abşeron rayonu",
            "skipped_dedicated": sorted(SKIP_TOP_NAMES),
            "verified_settlements": verified_top,
            "nested_verified": nested_verified,
            "conflicts": conflicts,
            "places": len(places),
            "areas_total": len(areas),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "osm_release": OSM_RELEASE,
            "overture_release": OVERTURE_RELEASE,
        },
    )

    # Manifest bump hint
    man_path = OUT / "manifest.json"
    if man_path.exists():
        m = load_json(man_path)
        m["dataset_version"] = "0.1.7-pilot"
        m.setdefault("coverage", {})
        m["coverage"]["areas"] = len(areas)
        m["coverage"]["places"] = total
        m["coverage"]["boundaries"] = len(b_index)
        m.setdefault("notes", {})
        if isinstance(m.get("description"), str):
            m["description"] = (
                "Country + Bakı + Sumqayıt + Abşeron (Masazır, Xırdalan, remaining settlements). "
                "Hierarchy.md / WORKER.md."
            )
        write_json(man_path, m)

    print(json.dumps(
        {
            "verified_settlements": len(verified_top),
            "nested": {k: len(v) for k, v in nested_verified.items()},
            "conflicts": conflicts,
            "places": len(places),
            "areas_total": len(areas),
        },
        ensure_ascii=False,
        indent=2,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
