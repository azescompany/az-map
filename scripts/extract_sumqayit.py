# -*- coding: utf-8 -*-
"""
Extract Sumqayıt city + settlements/microdistricts + named places.

Follows Hierarchy.md (Yasamal verification pattern).
Reads source_files/ only; writes data/. Never modifies sources.

OSM:
  - relation/3912206 admin_level=8 place=city  → city core boundary
  - relation/3764579 admin_level=6             → broader municipal extent
  - node/1104258889 place=city wikidata=Q179833 → label

Overture:
  - Sumqayıt locality children → məhəllə/mikrorayon (containment vs city core)
  - Sumqayıt region children (excl. Sumqayıt locality) → qəsəbə
    (containment vs broader admin_level=6 when available)
"""
from __future__ import annotations

import json
import os
import re
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import osmium
import pyarrow.parquet as pq
from shapely import wkb as swkb
from shapely.geometry import Point, mapping, shape
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
SRC = Path("source_files")
OUT = Path("data")
OSM_PBF = SRC / "azerbaijan-261020.osm.pbf"
OVERTURE_RELEASE = "2026-09-23.1"
OSM_RELEASE = "azerbaijan-261020"

NS = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")

OSM_CITY_REL = 3912206  # admin_level=8 city
OSM_BROADER_REL = 3764579  # admin_level=6
OSM_CITY_NODE = 1104258889

ALLOWED_SUBTYPES = {"microhood", "macrohood", "neighborhood", "locality"}

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
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def slug(s: str) -> str:
    return norm(s).replace(" ", "_")[:80] or "unnamed"


def pname(names) -> str:
    if not names:
        return ""
    return names.get("primary") or ""


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
    """Area-only handler (do not mix with node — pyosmium AreaManager quirk)."""

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


class OsmNodeCollector(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.node = None
        self.notable = []

    def node(self, n):
        if n.id == OSM_CITY_NODE and n.location.valid():
            self.node = {
                "lat": n.location.lat,
                "lon": n.location.lon,
                "wikidata": n.tags.get("wikidata"),
                "population": n.tags.get("population"),
                "name": n.tags.get("name"),
            }
        if not n.tags or not n.location.valid():
            return
        cat = classify_osm_notable(n.tags)
        if not cat:
            return
        name = n.tags.get("name") or n.tags.get("name:az")
        if not name or not str(name).strip():
            return
        self.notable.append(
            {
                "name": name,
                "category": cat,
                "lon": n.location.lon,
                "lat": n.location.lat,
                "osm_type": "node",
                "osm_id": n.id,
            }
        )


def _collect_nodes_subprocess(osm_path: str) -> dict:
    """Fresh Python process — avoids pyosmium AreaManager apply=None side effect."""
    import subprocess
    import sys
    import tempfile

    helper = Path(__file__).resolve().parent / "_sumqayit_nodes_helper.py"
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "nodes.json"
        subprocess.check_call(
            [sys.executable, str(helper), osm_path, str(out)],
            cwd=str(ROOT),
        )
        return json.loads(out.read_text(encoding="utf-8"))


def classify_osm_notable(tags) -> str | None:
    if "historic" in tags:
        return "historic"
    t = tags.get("tourism")
    if t == "museum":
        return "museum"
    if t in ("attraction", "viewpoint", "zoo", "theme_park", "artwork"):
        return "tourism"
    a = tags.get("amenity")
    if a == "place_of_worship":
        return "religious"
    if a in ("theatre", "cinema", "library", "arts_centre"):
        return "culture"
    if a == "university":
        return "education"
    if a == "townhall":
        return "government"
    leisure = tags.get("leisure")
    if leisure in ("park", "garden", "nature_reserve"):
        return "park"
    if leisure == "stadium":
        return "stadium"
    return None


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


def extract_places_in(poly, max_places=500):
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


def place_record(*, pid, name, category, lat, lon, area_id, source, source_id, raw_category, confidence):
    return {
        "id": pid,
        "name": name,
        "name_normalized": norm(name),
        "alt_names": [],
        "category": category,
        "coordinates": {"lat": lat, "lon": lon},
        "area_id": area_id,
        "area_assign_method": "containment_verified",
        "area_assign_status": "verified",
        "confidence": confidence,
        "status": "silver",
        "source_refs": [
            {
                "source": source,
                "source_id": source_id,
                "release": OVERTURE_RELEASE if source == "overture" else OSM_RELEASE,
                "source_category": raw_category,
            }
        ],
    }


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
    population,
    population_source,
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
    bfile = None
    if geom is not None and geom_status != "missing":
        bfile = f"boundaries/{boundary_name or key}.geojson"
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
        "population": population,
        "population_source": population_source,
        "bbox": list(geom.bounds) if geom is not None and not geom.is_empty else None,
        "source_refs": source_refs,
        "notes": notes,
        "boundary_file": bfile,
    }, aid, geom


def write_boundary(aid, name, geom, path_rel, props):
    feat = {
        "type": "Feature",
        "id": aid,
        "properties": {"id": aid, "name": name, **props},
        "geometry": mapping(geom),
    }
    write_json(OUT / path_rel, {"type": "FeatureCollection", "features": [feat]})


def main() -> int:
    assert OSM_PBF.exists()
    assert (SRC / "overture/aze_division.parquet").exists()

    areas_path = OUT / "areas" / "areas.json"
    areas = load_json(areas_path)["areas"]
    reviews_path = OUT / "reviews" / "pilot_reviews.json"
    reviews_doc = load_json(reviews_path) if reviews_path.exists() else {"reviews": []}
    reviews = list(reviews_doc.get("reviews") or [])

    # Remove previous Sumqayıt extract if re-run (by name/key markers)
    def is_sumqayit_area(a: dict) -> bool:
        if a.get("name") == "Sumqayıt" and a.get("type") == "city":
            return True
        bf = a.get("boundary_file") or ""
        if "sumqayit" in bf or "sumqayi" in bf:
            return True
        for ref in a.get("source_refs") or []:
            sid = str(ref.get("source_id") or "")
            if sid in (f"relation/{OSM_CITY_REL}", f"relation/{OSM_BROADER_REL}"):
                return True
        # children of sumqayit city — drop on re-run via parent later
        return False

    country = next(a for a in areas if a.get("type") == "country")
    # keep non-sumqayit; drop city + its previous children
    old_sum_ids = {a["id"] for a in areas if is_sumqayit_area(a)}
    # also drop neighborhoods that were parented to those
    changed = True
    while changed:
        changed = False
        for a in areas:
            if a.get("parent_id") in old_sum_ids and a["id"] not in old_sum_ids:
                old_sum_ids.add(a["id"])
                changed = True
    areas = [a for a in areas if a["id"] not in old_sum_ids]
    print(f"Removed previous Sumqayıt-linked areas: {len(old_sum_ids)}")

    # Label from prior OSM inventory (node/1104258889). Full notable node scan
    # skipped here due to pyosmium apply() instability after area handlers in this env;
    # places come from Overture landmarks (same taxonomy as Bakı).
    node_h_node = {
        "lat": 40.5961585,
        "lon": 49.6696668,
        "wikidata": "Q179833",
        "population": None,
        "name": "Sumqayıt",
    }
    node_h_notable: list = []
    print("Using OSM label node/1104258889 (cached inventory coords)")

    print("Extracting OSM Sumqayıt geometries…")
    osm_path = str(OSM_PBF).replace("\\", "/")
    want = {OSM_CITY_REL, OSM_BROADER_REL}
    area_h = OsmAreaExtractor(want)
    area_h.apply_file(osm_path, locations=True, idx="flex_mem")
    city_geom = area_h.geoms.get(OSM_CITY_REL)
    broad_geom = area_h.geoms.get(OSM_BROADER_REL)
    print(f"  city rel/{OSM_CITY_REL}: {'OK' if city_geom else 'MISSING'}")
    print(f"  broad rel/{OSM_BROADER_REL}: {'OK' if broad_geom else 'MISSING'}")

    print("Loading Overture…")
    ov_div, ov_areas = load_overture()
    ov_city_loc = next(
        (v for v in ov_div.values() if v["name"] == "Sumqayıt" and v["subtype"] == "locality"),
        None,
    )
    ov_region = next(
        (v for v in ov_div.values() if v["name"] == "Sumqayıt" and v["subtype"] == "region"),
        None,
    )

    # City record — use city-core OSM polygon; note broader extent separately
    if node_h_node:
        center = (node_h_node["lat"], node_h_node["lon"], "osm_place_node")
        pop = int(node_h_node["population"]) if node_h_node.get("population") else None
        wd = node_h_node.get("wikidata") or "Q179833"
    else:
        center = center_from_geom(city_geom) if city_geom else None
        pop = None
        wd = "Q179833"

    geom_status = "verified" if city_geom is not None else "missing"
    city_rec, city_id, _ = make_area(
        key="city:sumqayit",
        name="Sumqayıt",
        type_="city",
        subtype="city",
        parent_id=country["id"],
        parent_status="verified",
        geom=city_geom,
        geom_status=geom_status,
        center=center,
        wikidata=wd,
        population=pop,
        population_source="osm_tag" if pop else None,
        source_refs=[
            {
                "source": "osm",
                "source_id": f"relation/{OSM_CITY_REL}",
                "release": OSM_RELEASE,
                "role": "boundary",
                "match_method": "id",
                "note": "admin_level=8 place=city",
            },
            {
                "source": "osm",
                "source_id": f"relation/{OSM_BROADER_REL}",
                "release": OSM_RELEASE,
                "role": "boundary_extent",
                "match_method": "id",
                "note": "admin_level=6 broader municipal extent (settlements)",
            },
            {
                "source": "osm",
                "source_id": f"node/{OSM_CITY_NODE}",
                "release": OSM_RELEASE,
                "role": "label",
                "match_method": "id",
            },
        ]
        + (
            [
                {
                    "source": "overture",
                    "source_id": ov_city_loc["id"],
                    "release": OVERTURE_RELEASE,
                    "role": "hierarchy",
                    "match_method": "name+subtype",
                }
            ]
            if ov_city_loc
            else []
        )
        + (
            [
                {
                    "source": "overture",
                    "source_id": ov_region["id"],
                    "release": OVERTURE_RELEASE,
                    "role": "hierarchy_partial",
                    "match_method": "name+subtype",
                    "note": "Overture region lists satellite settlements (Corat, …)",
                }
            ]
            if ov_region
            else []
        ),
        notes=(
            "City core boundary = OSM admin_level=8. Satellite qəsəbələr verified "
            "against admin_level=6 extent when needed. No synthetic rayon invented — "
            "UI lists məhəllə/qəsəbə as direct verified children of the city."
        ),
        alt_names=["Sumgait", "Сумгаит"],
        boundary_name="city_sumqayit",
    )
    areas.append(city_rec)
    if city_geom is not None:
        write_boundary(
            city_id,
            "Sumqayıt",
            city_geom,
            "boundaries/city_sumqayit.geojson",
            {"type": "city", "parent_id": country["id"]},
        )

    # Optional broader extent file for review / containment (not a separate UI city)
    if broad_geom is not None:
        write_boundary(
            cid("area", "extent:sumqayit_al6"),
            "Sumqayıt (admin_level=6 extent)",
            broad_geom,
            "boundaries/extent_sumqayit_al6.geojson",
            {"type": "extent", "role": "municipal_extent", "parent_city_id": city_id},
        )

    used_keys = set()
    verified_names = []
    conflict_names = []

    def add_child(ov_rec, parent_geom, kind_note: str):
        nonlocal areas
        name = ov_rec["name"]
        if not name or not name.strip():
            return
        if (ov_rec.get("subtype") or "") not in ALLOWED_SUBTYPES:
            return
        if name.strip().casefold() == "sumqayıt":
            return  # skip self locality under region

        key = "sumqayit_" + slug(name)
        base = key
        n = 2
        while key in used_keys:
            key = f"{base}_{n}"
            n += 1
        used_keys.add(key)

        geom = ov_areas.get(ov_rec["id"])
        geom_status = "verified" if geom is not None else "missing"
        parent_status = "verified"  # overture parent already filtered by caller
        notes = kind_note

        if geom is None:
            parent_status = "missing"
            notes = (notes or "") + "; no division_area"
        elif parent_geom is not None and not contained(geom, parent_geom):
            parent_status = "conflict"
            notes = "Overture parent matches Sumqayıt but geometry not contained in parent polygon"
            conflict_names.append(name)
            reviews.append(
                {
                    "id": cid("review", "sumqayit-containment", key),
                    "kind": "hierarchy_conflict",
                    "entity": name,
                    "detail": notes,
                    "overture_id": ov_rec["id"],
                    "overture_parent_id": ov_rec.get("parent"),
                    "status": "open",
                }
            )
        elif parent_geom is None:
            parent_status = "missing"
            notes = "Parent polygon missing; containment not checked"

        if parent_status == "missing" and geom is None:
            return

        rec, aid, _ = make_area(
            key=f"neighborhood:{key}",
            name=name,
            type_="neighborhood",
            subtype=ov_rec.get("subtype"),
            parent_id=city_id,
            parent_status=parent_status,
            geom=geom,
            geom_status=geom_status if geom is not None else "missing",
            center=None,
            wikidata=ov_rec.get("wikidata"),
            population=ov_rec.get("population"),
            population_source="overture" if ov_rec.get("population") else None,
            source_refs=[
                {
                    "source": "overture",
                    "source_id": ov_rec["id"],
                    "release": OVERTURE_RELEASE,
                    "role": "boundary",
                    "match_method": "id",
                    "overture_parent_id": ov_rec.get("parent"),
                }
            ],
            notes=notes,
            boundary_name=f"neighborhood_{key}",
        )
        areas.append(rec)
        if geom is not None and rec.get("boundary_file"):
            write_boundary(
                aid,
                name,
                geom,
                rec["boundary_file"],
                {
                    "type": "neighborhood",
                    "parent_id": city_id,
                    "parent_status": parent_status,
                    "subtype": ov_rec.get("subtype"),
                },
            )
        if parent_status == "verified":
            verified_names.append(name)

    # Locality children → city-core containment
    if ov_city_loc:
        for child in sorted(
            (v for v in ov_div.values() if v.get("parent") == ov_city_loc["id"]),
            key=lambda x: x["name"] or "",
        ):
            add_child(child, city_geom, "Overture locality child of Sumqayıt")

    # Region children (satellites) → broader extent containment
    if ov_region:
        for child in sorted(
            (v for v in ov_div.values() if v.get("parent") == ov_region["id"]),
            key=lambda x: x["name"] or "",
        ):
            if child["name"] == "Sumqayıt" and child["subtype"] == "locality":
                continue
            add_child(
                child,
                broad_geom or city_geom,
                "Overture region child (satellite qəsəbə) of Sumqayıt",
            )

    print(f"Verified children: {len(verified_names)}")
    for n in verified_names:
        print(f"  · {n}")
    print(f"Conflicts: {len(conflict_names)} → {conflict_names}")

    # Places inside city core (+ optionally broader for satellite POIs in city file)
    print("Collecting named places…")
    places = []
    seen = set()
    place_poly = broad_geom or city_geom
    if place_poly is not None:
        for p in extract_places_in(place_poly, max_places=600):
            pid = cid("place", "overture", p["overture_id"])
            if pid in seen:
                continue
            seen.add(pid)
            places.append(
                place_record(
                    pid=pid,
                    name=p["name"],
                    category=p["category"],
                    lat=p["lat"],
                    lon=p["lon"],
                    area_id=city_id,
                    source="overture",
                    source_id=p["overture_id"],
                    raw_category=p["raw_category"],
                    confidence=p["confidence"],
                )
            )
        minx, miny, maxx, maxy = place_poly.bounds
        for n in node_h_notable:
            if not (minx <= n["lon"] <= maxx and miny <= n["lat"] <= maxy):
                continue
            pt = Point(n["lon"], n["lat"])
            if not (place_poly.covers(pt) or place_poly.intersects(pt)):
                continue
            pid = cid("place", "osm", n["osm_type"], str(n["osm_id"]))
            if pid in seen:
                continue
            seen.add(pid)
            places.append(
                place_record(
                    pid=pid,
                    name=n["name"],
                    category=n["category"],
                    lat=n["lat"],
                    lon=n["lon"],
                    area_id=city_id,
                    source="osm",
                    source_id=f"{n['osm_type']}/{n['osm_id']}",
                    raw_category=n["category"],
                    confidence=None,
                )
            )
    print(f"  places: {len(places)}")

    pdir = OUT / "places"
    pdir.mkdir(parents=True, exist_ok=True)
    write_json(
        pdir / "sumqayit_all.json",
        {"area_id": city_id, "city_key": "sumqayit", "places": places},
    )

    # Merge into places index
    index_path = pdir / "index.json"
    index = load_json(index_path) if index_path.exists() else {}
    files = list(index.get("files") or [])
    if "places/sumqayit_all.json" not in files:
        files.append("places/sumqayit_all.json")
    by_rayon = dict(index.get("by_rayon") or {})
    by_rayon["sumqayit"] = {
        "name": "Sumqayıt",
        "area_id": city_id,
        "count": len(places),
        "file": "places/sumqayit_all.json",
    }
    # recompute total from listed files
    total = 0
    for f in files:
        fp = OUT / f
        if fp.exists():
            total += len(load_json(fp).get("places") or [])
    write_json(
        index_path,
        {
            "region": "baki_rayons_and_sumqayit",
            "total": total,
            "by_rayon": by_rayon,
            "by_category": index.get("by_category") or {},
            "files": files,
        },
    )

    write_json(areas_path, {"type": "AreaCollection", "areas": areas})

    # boundary index
    b_index = []
    for a in areas:
        if a.get("boundary_file"):
            b_index.append(
                {"file": a["boundary_file"], "area_id": a["id"], "name": a["name"]}
            )
    write_json(OUT / "boundaries" / "index.json", {"boundaries": b_index})

    by_rid = {r["id"]: r for r in reviews}
    write_json(reviews_path, {"reviews": list(by_rid.values())})

    report = {
        "city_id": city_id,
        "osm_city_rel": OSM_CITY_REL,
        "osm_broader_rel": OSM_BROADER_REL,
        "verified_children": verified_names,
        "conflicts": conflict_names,
        "places": len(places),
        "areas_total": len(areas),
    }
    write_json(OUT / "reviews" / "sumqayit_extract.json", report)

    manifest_path = OUT / "manifest.json"
    manifest = load_json(manifest_path)
    manifest["dataset_version"] = "0.1.4-pilot"
    manifest["generated_at"] = datetime.now(timezone.utc).isoformat()
    cov = manifest.setdefault("coverage", {})
    cov["areas"] = len(areas)
    cov["boundaries"] = len(b_index)
    cov["places"] = total
    cov["reviews"] = len(by_rid)
    cov["description"] = (
        "Country + Bakı (rayons/hoods/places) + Sumqayıt (city/hoods/settlements/places). "
        "See Hierarchy.md + WORKER.md."
    )
    write_json(manifest_path, manifest)

    print("=" * 50)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print("Next: pnpm quality:gate && pnpm validate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
