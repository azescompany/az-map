# -*- coding: utf-8 -*-
"""
Extract Abşeron rayonu (parent) + Masazır settlement + named places.

Hierarchy.md rules. Sources read-only → data/.

Parent (mənbə):
  - OSM relation/3764533 Abşeron rayonu admin_level=6 wikidata=Q179538
  - Overture region Abşeron rayonu

Child:
  - Overture Masazır macrohood (has division_area); locality has no polygon
  - OSM node/1886282982 place=village (label)

UI: Abşeron is country→rayon (top-level); Masazır is neighborhood under it.
"""
from __future__ import annotations

import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

import osmium
import pyarrow.parquet as pq
from shapely import wkb as swkb
from shapely.geometry import Point, mapping
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
SRC = Path("source_files")
OUT = Path("data")
OSM_PBF = SRC / "azerbaijan-261020.osm.pbf"
OVERTURE_RELEASE = "2026-09-23.1"
OSM_RELEASE = "azerbaijan-261020"

NS = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")
OSM_ABSHERON_REL = 3764533
OSM_MASAZIR_NODE = 1886282982

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


class OsmAreaExtractor(osmium.SimpleHandler):
    def __init__(self, want: set[int]):
        super().__init__()
        self.want = want
        self.geoms: dict[int, object] = {}
        self.wk = osmium.geom.WKTFactory()

    def area(self, a):
        try:
            rid = a.orig_id()
        except Exception:
            return
        if rid not in self.want or a.from_way():
            return
        try:
            from shapely import wkt as load_wkt

            g = load_wkt.loads(self.wk.create_multipolygon(a))
            self.geoms[rid] = unary_union([self.geoms[rid], g]) if rid in self.geoms else g
        except Exception:
            return


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


def make_area(**kw):
    geom = kw.get("geom")
    lat = lon = None
    center_method = None
    center = kw.get("center")
    if center:
        lat, lon, center_method = center
    elif geom is not None and not geom.is_empty:
        lat, lon, center_method = center_from_geom(geom)
    key = kw["key"]
    aid = cid("area", key)
    bname = kw.get("boundary_name") or key.replace(":", "_")
    geom_status = kw["geom_status"]
    return {
        "id": aid,
        "name": kw["name"],
        "name_normalized": norm(kw["name"]),
        "alt_names": kw.get("alt_names") or [],
        "type": kw["type_"],
        "subtype": kw.get("subtype"),
        "parent_id": kw["parent_id"],
        "parent_status": kw["parent_status"],
        "geom_status": geom_status,
        "center": {"lat": lat, "lon": lon} if lat is not None else None,
        "center_method": center_method,
        "wikidata": kw.get("wikidata"),
        "population": kw.get("population"),
        "population_source": kw.get("population_source"),
        "bbox": list(geom.bounds) if geom is not None and not geom.is_empty else None,
        "source_refs": kw["source_refs"],
        "notes": kw.get("notes"),
        "boundary_file": f"boundaries/{bname}.geojson"
        if geom is not None and geom_status != "missing"
        else None,
    }, aid


def main() -> int:
    assert OSM_PBF.exists()
    areas_path = OUT / "areas" / "areas.json"
    areas = load_json(areas_path)["areas"]
    reviews_path = OUT / "reviews" / "pilot_reviews.json"
    reviews = list((load_json(reviews_path) if reviews_path.exists() else {}).get("reviews") or [])

    # Drop previous Absheron/Masazır extract on re-run
    drop = set()
    for a in areas:
        bf = a.get("boundary_file") or ""
        if (
            a.get("name") in ("Abşeron rayonu", "Masazır")
            or "absheron" in bf
            or "masazir" in bf
        ):
            drop.add(a["id"])
    changed = True
    while changed:
        changed = False
        for a in areas:
            if a.get("parent_id") in drop and a["id"] not in drop:
                drop.add(a["id"])
                changed = True
    areas = [a for a in areas if a["id"] not in drop]
    print(f"Removed previous Absheron/Masazır areas: {len(drop)}")

    country = next(a for a in areas if a.get("type") == "country")

    print("OSM Absheron geometry…")
    osm_path = str(OSM_PBF).replace("\\", "/")
    area_h = OsmAreaExtractor({OSM_ABSHERON_REL})
    area_h.apply_file(osm_path, locations=True, idx="flex_mem")
    absheron_osm = area_h.geoms.get(OSM_ABSHERON_REL)
    print(f"  rel/{OSM_ABSHERON_REL}: {'OK' if absheron_osm else 'MISSING'}")

    print("Overture…")
    ov_div, ov_areas = load_overture()
    ov_abs = next(
        (v for v in ov_div.values() if v["name"] == "Abşeron rayonu" and v["subtype"] == "region"),
        None,
    )
    ov_mas_macro = next(
        (v for v in ov_div.values() if v["name"] == "Masazır" and v["subtype"] == "macrohood"),
        None,
    )
    ov_mas_loc = next(
        (v for v in ov_div.values() if v["name"] == "Masazır" and v["subtype"] == "locality"),
        None,
    )

    absheron_geom = absheron_osm or (ov_areas.get(ov_abs["id"]) if ov_abs else None)
    absheron_geom_status = "verified" if absheron_geom is not None else "missing"
    if absheron_osm is None and absheron_geom is not None:
        absheron_geom_status = "partial"
        reviews.append(
            {
                "id": cid("review", "absheron-osm-missing"),
                "kind": "partial_geometry",
                "entity": "Abşeron rayonu",
                "detail": "OSM relation geometry missing in extract; using Overture region polygon.",
                "status": "open",
            }
        )

    # Label for Masazır from inventory
    masazir_label = (40.471873, 49.7552234, "osm_place_node")

    abs_rec, abs_id = make_area(
        key="rayon:absheron",
        name="Abşeron rayonu",
        type_="rayon",
        subtype="district",
        parent_id=country["id"],
        parent_status="verified",
        geom=absheron_geom,
        geom_status=absheron_geom_status,
        center=center_from_geom(absheron_geom) if absheron_geom else None,
        wikidata="Q179538",
        population=None,
        population_source=None,
        source_refs=[
            {
                "source": "osm",
                "source_id": f"relation/{OSM_ABSHERON_REL}",
                "release": OSM_RELEASE,
                "role": "boundary",
                "match_method": "id",
                "note": "admin_level=6",
            }
        ]
        + (
            [
                {
                    "source": "overture",
                    "source_id": ov_abs["id"],
                    "release": OVERTURE_RELEASE,
                    "role": "hierarchy",
                    "match_method": "name+subtype",
                }
            ]
            if ov_abs
            else []
        ),
        notes=(
            "Top-level rayon under country (not under Bakı). "
            "Settlements (Masazır, Xırdalan, …) are verified children. "
            "UI shows this in Şəhər/rayon selector."
        ),
        alt_names=["Absheron", "Absheron District"],
        boundary_name="rayon_absheron",
    )
    areas.append(abs_rec)
    if absheron_geom is not None:
        write_boundary(
            abs_id,
            "Abşeron rayonu",
            absheron_geom,
            "boundaries/rayon_absheron.geojson",
            {"type": "rayon", "parent_id": country["id"]},
        )

    # Masazır — prefer macrohood geom; link locality id in source_refs
    mas_ov = ov_mas_macro or ov_mas_loc
    mas_geom = ov_areas.get(ov_mas_macro["id"]) if ov_mas_macro else None
    if mas_geom is None and ov_mas_loc:
        mas_geom = ov_areas.get(ov_mas_loc["id"])

    parent_status = "missing"
    notes = None
    if mas_ov and ov_abs and mas_ov.get("parent") == ov_abs["id"]:
        parent_status = "verified"
    elif mas_ov:
        parent_status = "conflict"
        notes = f"Overture parent {mas_ov.get('parent')} != Abşeron {ov_abs['id'] if ov_abs else None}"

    if mas_geom is not None and absheron_geom is not None:
        if parent_status == "verified" and not contained(mas_geom, absheron_geom):
            parent_status = "conflict"
            notes = "Overture parent=Abşeron but geometry not contained in Absheron polygon"
            reviews.append(
                {
                    "id": cid("review", "masazir-containment"),
                    "kind": "hierarchy_conflict",
                    "entity": "Masazır",
                    "detail": notes,
                    "status": "open",
                }
            )

    geom_status = "verified" if mas_geom is not None else "missing"
    refs = []
    if ov_mas_macro:
        refs.append(
            {
                "source": "overture",
                "source_id": ov_mas_macro["id"],
                "release": OVERTURE_RELEASE,
                "role": "boundary",
                "match_method": "id",
                "overture_parent_id": ov_mas_macro.get("parent"),
                "note": "macrohood polygon (locality has no division_area)",
            }
        )
    if ov_mas_loc:
        refs.append(
            {
                "source": "overture",
                "source_id": ov_mas_loc["id"],
                "release": OVERTURE_RELEASE,
                "role": "hierarchy",
                "match_method": "id",
                "overture_parent_id": ov_mas_loc.get("parent"),
                "note": "locality record without polygon",
            }
        )
    refs.append(
        {
            "source": "osm",
            "source_id": f"node/{OSM_MASAZIR_NODE}",
            "release": OSM_RELEASE,
            "role": "label",
            "match_method": "id",
        }
    )

    mas_rec, mas_id = make_area(
        key="neighborhood:masazir",
        name="Masazır",
        type_="neighborhood",
        subtype=(mas_ov or {}).get("subtype") or "settlement",
        parent_id=abs_id,
        parent_status=parent_status,
        geom=mas_geom,
        geom_status=geom_status,
        center=masazir_label if mas_geom is None else None,
        wikidata=None,
        population=None,
        population_source=None,
        source_refs=refs,
        notes=notes
        or "Settlement under Abşeron rayonu (WORKER 1.3). Boundary from Overture macrohood.",
        alt_names=["Masazir"],
        boundary_name="neighborhood_masazir",
    )
    # Prefer OSM village node as label when geom exists — quality gate will set interior center;
    # store label as note only; use geom center for now.
    if mas_geom is not None:
        mas_rec["center"] = {
            "lat": masazir_label[0],
            "lon": masazir_label[1],
        }
        mas_rec["center_method"] = "osm_place_node"

    areas.append(mas_rec)
    if mas_geom is not None:
        write_boundary(
            mas_id,
            "Masazır",
            mas_geom,
            "boundaries/neighborhood_masazir.geojson",
            {
                "type": "neighborhood",
                "parent_id": abs_id,
                "parent_status": parent_status,
            },
        )

    print(f"Masazır parent_status={parent_status} geom={geom_status}")

    # Places in Masazır polygon (fallback Absheron∩bbox if no mas geom — shouldn't happen)
    place_poly = mas_geom or absheron_geom
    places = []
    if place_poly is not None:
        # If using Absheron poly by mistake, still filter — we have mas geom
        for p in extract_places_in(mas_geom or place_poly, max_places=300):
            places.append(
                {
                    "id": cid("place", "overture", p["overture_id"]),
                    "name": p["name"],
                    "name_normalized": norm(p["name"]),
                    "alt_names": [],
                    "category": p["category"],
                    "coordinates": {"lat": p["lat"], "lon": p["lon"]},
                    "area_id": mas_id,
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
        pdir / "masazir_all.json",
        {"area_id": mas_id, "parent_area_id": abs_id, "places": places},
    )
    index_path = pdir / "index.json"
    index = load_json(index_path) if index_path.exists() else {}
    files = list(index.get("files") or [])
    if "places/masazir_all.json" not in files:
        files.append("places/masazir_all.json")
    by_rayon = dict(index.get("by_rayon") or {})
    by_rayon["masazir"] = {
        "name": "Masazır",
        "area_id": mas_id,
        "count": len(places),
        "file": "places/masazir_all.json",
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
    by_rid = {r["id"]: r for r in reviews}
    write_json(reviews_path, {"reviews": list(by_rid.values())})

    report = {
        "absheron_id": abs_id,
        "masazir_id": mas_id,
        "masazir_parent_status": parent_status,
        "places": len(places),
        "areas_total": len(areas),
    }
    write_json(OUT / "reviews" / "masazir_extract.json", report)

    manifest = load_json(OUT / "manifest.json")
    manifest["dataset_version"] = "0.1.5-pilot"
    manifest["generated_at"] = datetime.now(timezone.utc).isoformat()
    cov = manifest.setdefault("coverage", {})
    cov["areas"] = len(areas)
    cov["boundaries"] = len(b_index)
    cov["places"] = total
    cov["reviews"] = len(by_rid)
    cov["description"] = (
        "Country + Bakı + Sumqayıt + Abşeron rayonu + Masazır. See Hierarchy.md / WORKER.md."
    )
    write_json(OUT / "manifest.json", manifest)

    print(json.dumps(report, ensure_ascii=False, indent=2))
    print("Next: pnpm quality:gate && pnpm validate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
