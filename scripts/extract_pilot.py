# -*- coding: utf-8 -*-
"""
Extract GeoAtlas pilot canonical dataset from immutable source_files/.

Sources (read-only):
  - source_files/overture/*.parquet  (Overture 2026-09-23.1)
  - source_files/azerbaijan-261020.osm.pbf
  - source_files/AZ/AZ.txt

Writes only under data/ and data/reviews/. Never modifies source_files/.
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

# Use paths relative to repo root so native libs (libosmium) can open
# files under directories whose absolute path contains non-ASCII characters.
ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
SRC = Path("source_files")
OUT = Path("data")
OSM_PBF = SRC / "azerbaijan-261020.osm.pbf"
OVERTURE_RELEASE = "2026-09-23.1"
OSM_RELEASE = "azerbaijan-261020"
GEONAMES_RELEASE = "AZ.txt"

# Deterministic UUIDs from namespace + key
NS = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")


def cid(*parts: str) -> str:
    return str(uuid.uuid5(NS, "geoatlas-aze:" + "|".join(parts)))


def norm(s: str) -> str:
    s = (s or "").casefold().strip()
    for a, b in (("ə", "e"), ("ı", "i"), ("ö", "o"), ("ü", "u"), ("ğ", "g"), ("ş", "s"), ("ç", "c")):
        s = s.replace(a, b)
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def pname(names) -> str:
    if not names:
        return ""
    return names.get("primary") or ""


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def feat_collection(features):
    return {"type": "FeatureCollection", "features": features}


# ---------------------------------------------------------------------------
# Overture divisions / areas
# ---------------------------------------------------------------------------
def load_overture_divisions():
    div = pq.read_table(
        SRC / "overture/aze_division.parquet",
        columns=[
            "id",
            "subtype",
            "admin_level",
            "country",
            "names",
            "parent_division_id",
            "wikidata",
            "population",
            "geometry",
            "bbox",
        ],
    )
    area = pq.read_table(
        SRC / "overture/aze_division_area.parquet",
        columns=["id", "division_id", "geometry", "bbox", "country", "names", "subtype"],
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
            "admin_level": div.column("admin_level")[i].as_py(),
            "parent": div.column("parent_division_id")[i].as_py(),
            "wikidata": div.column("wikidata")[i].as_py(),
            "population": div.column("population")[i].as_py(),
            "point": div.column("geometry")[i].as_py(),
            "bbox": div.column("bbox")[i].as_py(),
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
        # Prefer land polygons; keep first then union if multiple
        if did in areas:
            areas[did] = unary_union([areas[did], geom])
        else:
            areas[did] = geom
    return by_id, areas


def center_from_geom(geom):
    try:
        p = geom.representative_point()
        return float(p.y), float(p.x), "rep_point"
    except Exception:
        c = geom.centroid
        return float(c.y), float(c.x), "centroid"


# ---------------------------------------------------------------------------
# OSM admin areas (pilot set)
# ---------------------------------------------------------------------------
PILOT_OSM_RELS = {
    # name_key -> (relation_id, expected_admin_level, wikidata or None, role)
    "country": (364110, "2", "Q227", "country"),
    "baki_city": (2415335, "6", None, "city"),
    "yasamal": (11826939, "7", "Q4539151", "rayon"),
    "nasimi": (11826962, "8", "Q4313899", "rayon"),
    "narimanov": (11827003, "8", None, "rayon"),
    "nizami_baki": (11827201, "8", "Q3912215", "rayon"),
    "binagadi": (11825936, "8", "Q864153", "rayon"),
    "sabail": (11826940, "8", "Q2028793", "rayon"),
    "xetai": (11827202, "8", "Q2076557", "rayon"),
    "sabuncu": (11827203, "8", "Q2210210", "rayon"),
    "surakhani": (11827250, "8", "Q4446443", "rayon"),
    "xezer": (11827332, "8", "Q526313", "rayon"),
    "pirallahi": (11827333, "8", "Q12843909", "rayon"),
    "qaradag": (11825937, "6", "Q4818249", "rayon"),
}

OSM_NAMES = {
    "country": "Azərbaycan",
    "baki_city": "Bakı",
    "yasamal": "Yasamal rayonu",
    "nasimi": "Nəsimi rayonu",
    "narimanov": "Nərimanov rayonu",
    "nizami_baki": "Nizami rayonu",
    "binagadi": "Binəqədi rayonu",
    "sabail": "Səbail rayonu",
    "xetai": "Xətai rayonu",
    "sabuncu": "Sabunçu rayonu",
    "surakhani": "Suraxanı rayonu",
    "xezer": "Xəzər rayonu",
    "pirallahi": "Pirallahı rayonu",
    "qaradag": "Qaradağ rayonu",
}


class OsmPilotCollector(osmium.SimpleHandler):
    def __init__(self, want_ids: set[int]):
        super().__init__()
        self.want = want_ids
        self.tags = {}
        self.baki_node = None
        self.notable = []  # (name, cat, lon, lat, osm_type, osm_id, tags_subset)

    def node(self, n):
        if n.id == 2117350415 and n.location.valid():
            self.baki_node = {
                "id": n.id,
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
        if not name:
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

    def relation(self, r):
        if r.id in self.want:
            self.tags[r.id] = {t.k: t.v for t in r.tags}


def classify_osm_notable(tags) -> str | None:
    if "historic" in tags:
        return "historic"
    t = tags.get("tourism")
    if t in ("attraction", "museum", "viewpoint", "zoo", "theme_park", "artwork"):
        return "tourism" if t != "museum" else "museum"
    if t == "museum":
        return "museum"
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


class OsmAreaExtractor(osmium.SimpleHandler):
    def __init__(self, want_ids: set[int]):
        super().__init__()
        self.want = want_ids
        self.geoms: dict[int, object] = {}
        self.wk = osmium.geom.WKTFactory()

    def area(self, a):
        # areas from relations have orig_id() == relation id for multipolygon/boundary
        try:
            rid = a.orig_id()
        except Exception:
            return
        if rid not in self.want:
            return
        if a.from_way():
            # closed-way areas — skip (we want relation multipolygons)
            return
        try:
            wkt = self.wk.create_multipolygon(a)
            from shapely import wkt as load_wkt

            g = load_wkt.loads(wkt)
            if rid in self.geoms:
                self.geoms[rid] = unary_union([self.geoms[rid], g])
            else:
                self.geoms[rid] = g
        except Exception:
            return


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


def extract_overture_places_in(poly, max_places=400):
    pl = pq.read_table(
        SRC / "overture/aze_place.parquet",
        columns=["id", "names", "taxonomy", "basic_category", "geometry", "bbox", "confidence", "sources"],
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
        g = pl.column("geometry")[i].as_py()
        try:
            pt = swkb.loads(g) if g else Point(cx, cy)
        except Exception:
            pt = Point(cx, cy)
        if not (poly.covers(pt) or poly.intersects(pt)):
            continue
        name = pname(pl.column("names")[i].as_py())
        if not name:
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


def area_record(
    *,
    key: str,
    name: str,
    type_: str,
    subtype: str | None,
    parent_id: str | None,
    parent_status: str,
    geom,
    geom_status: str,
    center: tuple[float, float, str] | None,
    wikidata: str | None,
    population: int | None,
    population_source: str | None,
    source_refs: list,
    alt_names: list | None = None,
    notes: str | None = None,
):
    lat = lon = None
    center_method = None
    if center:
        lat, lon, center_method = center
    elif geom is not None and not geom.is_empty:
        lat, lon, center_method = center_from_geom(geom)
    return {
        "id": cid("area", key),
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
        "bbox": list(geom.bounds) if geom is not None and not geom.is_empty else None,  # minx,miny,maxx,maxy
        "source_refs": source_refs,
        "notes": notes,
        "boundary_file": f"boundaries/{key}.geojson" if geom is not None and geom_status != "missing" else None,
    }


def boundary_feature(area_id: str, name: str, geom, props: dict):
    return {
        "type": "Feature",
        "id": area_id,
        "properties": {"id": area_id, "name": name, **props},
        "geometry": mapping(geom),
    }


def main():
    assert OSM_PBF.exists(), "OSM PBF missing under source_files/"
    assert (SRC / "overture/aze_division.parquet").exists(), "Overture missing"
    OUT.mkdir(exist_ok=True)
    osm_path = str(OSM_PBF).replace("\\", "/")

    print("Loading Overture divisions…")
    ov_div, ov_areas = load_overture_divisions()

    # Country from Overture
    country_ov = next(v for v in ov_div.values() if v["name"] == "Azərbaycan" and v["subtype"] == "country")
    country_geom = ov_areas.get(country_ov["id"])
    if country_geom is None:
        raise SystemExit("Country polygon missing in Overture division_area")

    # Overture Bakı region / Yasamal / Alatava / Nasimi
    def find_ov(name, subtype):
        for v in ov_div.values():
            if v["name"] == name and v["subtype"] == subtype:
                return v
        return None

    ov_baki_region = find_ov("Bakı", "region")
    ov_yasamal = find_ov("Yasamal rayonu", "locality")
    ov_nasimi = find_ov("Nəsimi rayonu", "locality")
    ov_alatava2 = find_ov("2-ci Alatava", "macrohood")
    ov_alatava1 = find_ov("1-ci Alatava", "microhood")
    ov_yeni = find_ov("Yeni Yasamal", "microhood")
    ov_yasamal_macro = find_ov("Yasamal", "macrohood")

    print("Extracting OSM relation geometries…")
    want_ids = {v[0] for v in PILOT_OSM_RELS.values()}
    # also 1-ci Alatava multipolygon
    ALATAVA1_OSM = 21262837
    want_ids.add(ALATAVA1_OSM)

    areas_handler = OsmAreaExtractor(want_ids)
    # locations + areas index required
    areas_handler.apply_file(osm_path, locations=True, idx="flex_mem")

    props_handler = OsmPilotCollector(want_ids)
    props_handler.apply_file(osm_path, locations=True)

    osm_geoms = areas_handler.geoms
    print(f"  OSM areas extracted: {len(osm_geoms)} / {len(want_ids)}")
    for k, (rid, *_rest) in PILOT_OSM_RELS.items():
        print(f"    {k} rel/{rid}: {'OK' if rid in osm_geoms else 'MISSING'}")

    reviews = []
    areas = []
    boundaries = {}

    # --- Country ---
    az_id = cid("area", "country:AZ")
    country_center = center_from_geom(country_geom)
    areas.append(
        area_record(
            key="country:AZ",
            name="Azərbaycan",
            type_="country",
            subtype="country",
            parent_id=None,
            parent_status="verified",
            geom=country_geom,
            geom_status="verified",
            center=country_center,
            wikidata="Q227",
            population=None,
            population_source=None,
            source_refs=[
                {
                    "source": "overture",
                    "source_id": country_ov["id"],
                    "release": OVERTURE_RELEASE,
                    "role": "boundary",
                    "match_method": "id",
                },
                {
                    "source": "osm",
                    "source_id": f"relation/{PILOT_OSM_RELS['country'][0]}",
                    "release": OSM_RELEASE,
                    "role": "boundary",
                    "match_method": "wikidata",
                },
            ],
            alt_names=["Azerbaijan", "Азербайджан"],
        )
    )
    boundaries["country_AZ"] = boundary_feature(
        az_id, "Azərbaycan", country_geom, {"type": "country", "wikidata": "Q227"}
    )
    # write as country.geojson via key
    boundaries_files = {}
    boundaries_files["country_AZ"] = ("country_AZ", boundaries["country_AZ"])
    # fix area boundary_file name
    areas[0]["boundary_file"] = "boundaries/country_AZ.geojson"
    areas[0]["id"] = az_id

    # --- Bakı city ---
    baki_rid = PILOT_OSM_RELS["baki_city"][0]
    baki_geom = osm_geoms.get(baki_rid)
    baki_geom_status = "verified" if baki_geom is not None else "missing"
    if baki_geom is None and ov_baki_region and ov_baki_region["id"] in ov_areas:
        baki_geom = ov_areas[ov_baki_region["id"]]
        baki_geom_status = "partial"
        reviews.append(
            {
                "id": cid("review", "baki-geom-partial"),
                "kind": "partial_geometry",
                "entity": "Bakı",
                "detail": "OSM city relation geometry unavailable in extract; using incomplete Overture region polygon.",
                "status": "open",
            }
        )

    baki_node = props_handler.baki_node
    if baki_node:
        baki_center = (baki_node["lat"], baki_node["lon"], "osm_place_node")
        baki_wd = baki_node.get("wikidata") or "Q9248"
        baki_pop = int(baki_node["population"]) if baki_node.get("population") else None
    else:
        baki_center = center_from_geom(baki_geom) if baki_geom else None
        baki_wd = "Q9248"
        baki_pop = None

    baki_id = cid("area", "city:baki")
    baki_refs = [
        {
            "source": "osm",
            "source_id": f"relation/{baki_rid}",
            "release": OSM_RELEASE,
            "role": "boundary",
            "match_method": "id",
        },
        {
            "source": "osm",
            "source_id": "node/2117350415",
            "release": OSM_RELEASE,
            "role": "label",
            "match_method": "id",
        },
        {
            "source": "geonames",
            "source_id": "587084",
            "release": GEONAMES_RELEASE,
            "role": "population",
            "match_method": "wikidata_or_name_review",
        },
    ]
    if ov_baki_region:
        baki_refs.append(
            {
                "source": "overture",
                "source_id": ov_baki_region["id"],
                "release": OVERTURE_RELEASE,
                "role": "hierarchy_partial",
                "match_method": "name+subtype",
                "note": "Overture Bakı region parent links incomplete; not used as sole boundary.",
            }
        )

    areas.append(
        area_record(
            key="city:baki",
            name="Bakı",
            type_="city",
            subtype="city",
            parent_id=az_id,
            parent_status="verified",
            geom=baki_geom,
            geom_status=baki_geom_status,
            center=baki_center,
            wikidata=baki_wd,
            population=baki_pop,
            population_source="osm_tag" if baki_pop else None,
            source_refs=baki_refs,
            alt_names=["Baku", "Bakı şəhəri"],
            notes="District children come from OSM admin relations, not Overture parent_division_id.",
        )
    )
    if baki_geom is not None:
        boundaries_files["city_baki"] = (
            "city_baki",
            boundary_feature(baki_id, "Bakı", baki_geom, {"type": "city", "geom_status": baki_geom_status}),
        )
    areas[-1]["boundary_file"] = "boundaries/city_baki.geojson" if baki_geom is not None else None
    areas[-1]["id"] = baki_id

    # --- Bakı districts from OSM ---
    district_keys = [
        "yasamal",
        "nasimi",
        "narimanov",
        "nizami_baki",
        "binagadi",
        "sabail",
        "xetai",
        "sabuncu",
        "surakhani",
        "xezer",
        "pirallahi",
        "qaradag",
    ]
    district_ids = {}
    for key in district_keys:
        rid, al, wd, role = PILOT_OSM_RELS[key]
        name = OSM_NAMES[key]
        geom = osm_geoms.get(rid)
        gstatus = "verified" if geom is not None else "missing"
        if geom is None:
            reviews.append(
                {
                    "id": cid("review", f"missing-geom-{key}"),
                    "kind": "missing_geometry",
                    "entity": name,
                    "detail": f"OSM relation/{rid} polygon not assembled from PBF areas.",
                    "status": "open",
                }
            )
        # Prefer Overture area if Wikidata-linked and OSM geom missing
        ov_match = None
        if key == "yasamal":
            ov_match = ov_yasamal
        elif key == "nasimi":
            ov_match = ov_nasimi
        if geom is None and ov_match and ov_match["id"] in ov_areas:
            geom = ov_areas[ov_match["id"]]
            gstatus = "partial"

        # admin_level inconsistency note for yasamal/qaradag
        parent_status = "verified"
        notes = f"OSM admin_level={al}."
        if key == "yasamal" and al != "8":
            notes += " Level differs from other Baku districts (usually 8)."
        if key == "qaradag" and al == "6":
            notes += " Same admin_level as Bakı city relation; retained as Bakı child for UI; see reviews."
            reviews.append(
                {
                    "id": cid("review", "qaradag-level"),
                    "kind": "hierarchy_conflict",
                    "entity": name,
                    "detail": "OSM admin_level=6 equals Bakı city; parent=Bakı kept for cascading UI pending cartographic review.",
                    "status": "open",
                }
            )

        aid = cid("area", f"rayon:{key}")
        district_ids[key] = aid
        refs = [
            {
                "source": "osm",
                "source_id": f"relation/{rid}",
                "release": OSM_RELEASE,
                "role": "boundary",
                "match_method": "id",
            }
        ]
        if wd:
            refs[0]["wikidata"] = wd
        if ov_match:
            refs.append(
                {
                    "source": "overture",
                    "source_id": ov_match["id"],
                    "release": OVERTURE_RELEASE,
                    "role": "boundary" if gstatus != "missing" else "label",
                    "match_method": "wikidata" if (wd and ov_match.get("wikidata") == wd) else "name+subtype",
                }
            )

        rec = area_record(
            key=f"rayon:{key}",
            name=name,
            type_="rayon",
            subtype="district",
            parent_id=baki_id,
            parent_status=parent_status,
            geom=geom,
            geom_status=gstatus,
            center=center_from_geom(geom) if geom is not None else None,
            wikidata=wd or (ov_match.get("wikidata") if ov_match else None),
            population=None,
            population_source=None,
            source_refs=refs,
            notes=notes,
        )
        rec["id"] = aid
        rec["boundary_file"] = f"boundaries/rayon_{key}.geojson" if geom is not None else None
        areas.append(rec)
        if geom is not None:
            boundaries_files[f"rayon_{key}"] = (
                f"rayon_{key}",
                boundary_feature(aid, name, geom, {"type": "rayon", "parent_id": baki_id}),
            )

    yasamal_id = district_ids["yasamal"]
    nasimi_id = district_ids["nasimi"]
    yasamal_geom = osm_geoms.get(PILOT_OSM_RELS["yasamal"][0]) or (
        ov_areas.get(ov_yasamal["id"]) if ov_yasamal else None
    )

    # --- Neighborhoods ---
    def add_neighborhood(key, name, subtype, parent_area_id, parent_status, ov_rec, osm_rel_or_way=None, notes=None):
        geom = ov_areas.get(ov_rec["id"]) if ov_rec else None
        gstatus = "verified" if geom is not None else "missing"
        # containment check vs parent geom
        parent_geom = None
        if parent_area_id == yasamal_id:
            parent_geom = yasamal_geom
        elif parent_area_id == nasimi_id:
            parent_geom = osm_geoms.get(PILOT_OSM_RELS["nasimi"][0]) or (
                ov_areas.get(ov_nasimi["id"]) if ov_nasimi else None
            )
        if geom is not None and parent_geom is not None:
            c = geom.representative_point()
            contained = parent_geom.covers(c) or parent_geom.intersects(geom)
            if parent_status == "verified" and not contained:
                parent_status = "conflict"
                reviews.append(
                    {
                        "id": cid("review", f"containment-{key}"),
                        "kind": "hierarchy_conflict",
                        "entity": name,
                        "detail": "Claimed parent does not contain neighborhood geometry.",
                        "status": "open",
                    }
                )
            if parent_status == "verified" and ov_rec and ov_rec.get("parent"):
                # check overture parent points to expected
                pass

        refs = []
        if ov_rec:
            refs.append(
                {
                    "source": "overture",
                    "source_id": ov_rec["id"],
                    "release": OVERTURE_RELEASE,
                    "role": "boundary",
                    "match_method": "id",
                    "overture_parent_id": ov_rec.get("parent"),
                }
            )
        if osm_rel_or_way:
            refs.append(
                {
                    "source": "osm",
                    "source_id": osm_rel_or_way,
                    "release": OSM_RELEASE,
                    "role": "boundary",
                    "match_method": "id",
                }
            )
        aid = cid("area", f"neighborhood:{key}")
        rec = area_record(
            key=f"neighborhood:{key}",
            name=name,
            type_="neighborhood",
            subtype=subtype,
            parent_id=parent_area_id,
            parent_status=parent_status,
            geom=geom,
            geom_status=gstatus,
            center=center_from_geom(geom) if geom else None,
            wikidata=ov_rec.get("wikidata") if ov_rec else None,
            population=None,
            population_source=None,
            source_refs=refs,
            notes=notes,
        )
        rec["id"] = aid
        rec["boundary_file"] = f"boundaries/neighborhood_{key}.geojson" if geom is not None else None
        areas.append(rec)
        if geom is not None:
            boundaries_files[f"neighborhood_{key}"] = (
                f"neighborhood_{key}",
                boundary_feature(
                    aid,
                    name,
                    geom,
                    {"type": "neighborhood", "parent_id": parent_area_id, "parent_status": parent_status},
                ),
            )
        return aid, geom

    # 2-ci Alatava under Yasamal — verify Overture parent + containment
    a2_parent_status = "missing"
    a2_notes = None
    if ov_alatava2 and ov_yasamal and ov_alatava2["parent"] == ov_yasamal["id"]:
        a2_parent_status = "verified"
    elif ov_alatava2:
        a2_parent_status = "conflict"
        a2_notes = f"Overture parent_division_id={ov_alatava2['parent']} != Yasamal {ov_yasamal['id'] if ov_yasamal else None}"
        reviews.append(
            {
                "id": cid("review", "alatava2-parent"),
                "kind": "hierarchy_conflict",
                "entity": "2-ci Alatava",
                "detail": a2_notes,
                "status": "open",
            }
        )
    alatava2_id, alatava2_geom = add_neighborhood(
        "2ci_alatava",
        "2-ci Alatava",
        "macrohood",
        yasamal_id,
        a2_parent_status,
        ov_alatava2,
        osm_rel_or_way="way/186431887",
        notes=a2_notes,
    )

    # 1-ci Alatava under Nəsimi (NOT Yasamal)
    a1_status = "missing"
    a1_notes = "Must not be listed as verified Yasamal child."
    if ov_alatava1 and ov_nasimi and ov_alatava1["parent"] == ov_nasimi["id"]:
        a1_status = "verified"
    elif ov_alatava1:
        a1_status = "conflict"
    reviews.append(
        {
            "id": cid("review", "alatava1-not-yasamal"),
            "kind": "hierarchy_conflict",
            "entity": "1-ci Alatava",
            "detail": "Geometry and Overture parent place this under Nəsimi rayonu, not Yasamal. Excluded from Yasamal children in verified UI.",
            "overture_id": ov_alatava1["id"] if ov_alatava1 else None,
            "overture_parent_id": ov_alatava1["parent"] if ov_alatava1 else None,
            "status": "documented",
        }
    )
    add_neighborhood(
        "1ci_alatava",
        "1-ci Alatava",
        "microhood",
        nasimi_id,
        a1_status,
        ov_alatava1,
        osm_rel_or_way=f"relation/{ALATAVA1_OSM}",
        notes=a1_notes,
    )

    # Yeni Yasamal + Yasamal macrohood if parent matches Yasamal
    for key, name, st, ov in [
        ("yeni_yasamal", "Yeni Yasamal", "microhood", ov_yeni),
        ("yasamal_macrohood", "Yasamal", "macrohood", ov_yasamal_macro),
    ]:
        st_parent = "missing"
        if ov and ov_yasamal and ov["parent"] == ov_yasamal["id"]:
            st_parent = "verified"
        elif ov:
            st_parent = "conflict"
            reviews.append(
                {
                    "id": cid("review", f"parent-{key}"),
                    "kind": "hierarchy_conflict",
                    "entity": name,
                    "detail": f"Overture parent {ov.get('parent')} vs Yasamal {ov_yasamal['id'] if ov_yasamal else None}",
                    "status": "open",
                }
            )
        add_neighborhood(key, name, st, yasamal_id, st_parent, ov)

    # Overture Bakı region incomplete children → review
    if ov_baki_region:
        ov_children = [v for v in ov_div.values() if v["parent"] == ov_baki_region["id"]]
        reviews.append(
            {
                "id": cid("review", "overture-baki-incomplete"),
                "kind": "coverage_gap",
                "entity": "Bakı (Overture region)",
                "detail": "Overture parent_division_id lists only: "
                + ", ".join(sorted(c["name"] for c in ov_children))
                + ". OSM district set used instead for cascading children.",
                "status": "documented",
            }
        )

    # --- Places inside Yasamal (curated landmark) ---
    print("Collecting notable places in Yasamal…")
    places = []
    if yasamal_geom is not None:
        ov_places = extract_overture_places_in(yasamal_geom, max_places=250)
        for p in ov_places:
            pid = cid("place", "overture", p["overture_id"])
            places.append(
                {
                    "id": pid,
                    "name": p["name"],
                    "name_normalized": norm(p["name"]),
                    "alt_names": [],
                    "category": p["category"],
                    "coordinates": {"lat": p["lat"], "lon": p["lon"]},
                    "area_id": yasamal_id,
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

        # OSM notables in Yasamal bbox/poly
        minx, miny, maxx, maxy = yasamal_geom.bounds
        osm_added = 0
        for n in props_handler.notable:
            if not (minx <= n["lon"] <= maxx and miny <= n["lat"] <= maxy):
                continue
            pt = Point(n["lon"], n["lat"])
            if not (yasamal_geom.covers(pt) or yasamal_geom.intersects(pt)):
                continue
            pid = cid("place", "osm", n["osm_type"], str(n["osm_id"]))
            places.append(
                {
                    "id": pid,
                    "name": n["name"],
                    "name_normalized": norm(n["name"]),
                    "alt_names": [],
                    "category": n["category"],
                    "coordinates": {"lat": n["lat"], "lon": n["lon"]},
                    "area_id": yasamal_id,
                    "area_assign_method": "containment_verified",
                    "area_assign_status": "verified",
                    "confidence": None,
                    "status": "silver",
                    "source_refs": [
                        {
                            "source": "osm",
                            "source_id": f"{n['osm_type']}/{n['osm_id']}",
                            "release": OSM_RELEASE,
                            "source_category": n["category"],
                        }
                    ],
                }
            )
            osm_added += 1
        print(f"  Overture landmarks: {len(ov_places)}; OSM notables added: {osm_added}")

    # Write areas index (no heavy geom)
    areas_out = []
    for a in areas:
        areas_out.append(a)

    write_json(OUT / "areas" / "areas.json", {"type": "AreaCollection", "areas": areas_out})

    # Boundaries as individual files + index
    bdir = OUT / "boundaries"
    bdir.mkdir(parents=True, exist_ok=True)
    boundary_index = []
    for file_key, (fname, feat) in boundaries_files.items():
        # wrap FeatureCollection
        fc = feat_collection([feat])
        write_json(bdir / f"{fname}.geojson", fc)
        boundary_index.append({"file": f"boundaries/{fname}.geojson", "area_id": feat["properties"]["id"], "name": feat["properties"]["name"]})
    write_json(bdir / "index.json", {"boundaries": boundary_index})

    # Places by category
    pdir = OUT / "places"
    pdir.mkdir(parents=True, exist_ok=True)
    by_cat = defaultdict(list)
    for p in places:
        by_cat[p["category"]].append(p)
    for cat, items in by_cat.items():
        write_json(pdir / f"{cat}.json", {"category": cat, "places": items})
    write_json(
        pdir / "index.json",
        {
            "region": "yasamal_pilot",
            "area_id": yasamal_id,
            "total": len(places),
            "by_category": {k: len(v) for k, v in sorted(by_cat.items())},
            "files": [f"places/{k}.json" for k in sorted(by_cat)],
        },
    )
    write_json(pdir / "yasamal_all.json", {"area_id": yasamal_id, "places": places})

    write_json(OUT / "reviews" / "pilot_reviews.json", {"reviews": reviews})

    manifest = {
        "name": "GeoAtlas Azerbaijan",
        "dataset_version": "0.1.0-pilot",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "coverage": {
            "scope": "pilot",
            "description": "Country + Bakı city/districts + Yasamal neighborhoods + Yasamal notable places. Not full national coverage.",
            "areas": len(areas_out),
            "boundaries": len(boundary_index),
            "places": len(places),
            "reviews": len(reviews),
        },
        "sources": {
            "overture": {
                "release": OVERTURE_RELEASE,
                "path": "source_files/overture/",
                "license": "CDLA Permissive 2.0 (component sources vary; see feature sources)",
            },
            "osm": {
                "release": OSM_RELEASE,
                "path": "source_files/azerbaijan-261020.osm.pbf",
                "license": "ODbL 1.0",
                "attribution": "© OpenStreetMap contributors",
            },
            "geonames": {
                "release": GEONAMES_RELEASE,
                "path": "source_files/AZ/",
                "license": "CC BY 4.0",
            },
        },
        "basemap": {
            "provider": "OpenFreeMap / Liberty",
            "url": "https://tiles.openfreemap.org/styles/liberty",
            "note": "External basemap for context only. Administrative boundaries and place markers come from GeoAtlas data/.",
        },
        "hierarchy_policy": {
            "baki_districts": "OSM admin relations",
            "alatava": "2-ci under Yasamal only if verified; 1-ci under Nəsimi",
            "no_name_only_merge": True,
        },
    }
    write_json(OUT / "manifest.json", manifest)

    # Attribution doc snippet
    print("Done.")
    print(json.dumps(manifest["coverage"], indent=2))


if __name__ == "__main__":
    main()
