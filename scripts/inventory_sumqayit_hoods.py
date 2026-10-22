# -*- coding: utf-8 -*-
"""Inventory Sumqayıt neighborhood/mikrorayon candidates from OSM + Overture.

Read-only on source_files/. Does not write areas (report only).
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

import osmium
import pyarrow.parquet as pq
from shapely import wkb as swkb
from shapely.geometry import Point, shape
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
SRC = Path("source_files")
OUT = Path("data")
OSM_PBF = SRC / "azerbaijan-261020.osm.pbf"
CITY_ID = "a02b58f1-3009-5ce3-a728-69d77b411dec"

HOOD_RE = re.compile(
    r"(mikrorayon|mikro\s*rayon|mkr\.?|məhəllə|mehelle|məhelle|qəsəbə|qesebe|"
    r"микрорайон|махалля|mtk|bağları|baglari)",
    re.I,
)


def load_json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def load_geom(bf):
    fc = load_json(OUT / bf)
    geoms = [
        shape(f["geometry"])
        for f in fc["features"]
        if f.get("geometry", {}).get("type") in ("Polygon", "MultiPolygon")
    ]
    if not geoms:
        return None
    return unary_union(geoms) if len(geoms) > 1 else geoms[0]


def pname(names):
    if not names:
        return ""
    return names.get("primary") or ""


class OsmHoods(osmium.SimpleHandler):
    """Collect named place=suburb/neighbourhood/quarter nodes + area relations/ways."""

    def __init__(self, city, broad, minx, miny, maxx, maxy):
        super().__init__()
        self.city = city
        self.broad = broad
        self.minx, self.miny, self.maxx, self.maxy = minx, miny, maxx, maxy
        self.nodes = []
        self.areas = []  # from area callback

    def _in_bbox(self, lon, lat):
        return self.minx <= lon <= self.maxx and self.miny <= lat <= self.maxy

    def _inside(self, pt):
        if self.city.covers(pt) or self.city.intersects(pt):
            return "city"
        if self.broad is not None and (self.broad.covers(pt) or self.broad.intersects(pt)):
            return "broad"
        return None

    def node(self, n):
        if not n.tags or not n.location.valid():
            return
        place = n.tags.get("place")
        if place not in ("suburb", "neighbourhood", "neighborhood", "quarter", "city_block"):
            return
        name = n.tags.get("name") or n.tags.get("name:az")
        if not name:
            return
        lon, lat = n.location.lon, n.location.lat
        if not self._in_bbox(lon, lat):
            return
        where = self._inside(Point(lon, lat))
        if not where:
            return
        self.nodes.append(
            {
                "osm": f"node/{n.id}",
                "name": name,
                "place": place,
                "lat": lat,
                "lon": lon,
                "where": where,
                "wikidata": n.tags.get("wikidata"),
            }
        )

    def area(self, a):
        tags = a.tags
        if not tags:
            return
        place = tags.get("place")
        # also landuse=residential with name + mikrorayon pattern
        name = tags.get("name") or tags.get("name:az")
        if not name:
            return
        if place not in ("suburb", "neighbourhood", "neighborhood", "quarter", "city_block") and not (
            HOOD_RE.search(name) and tags.get("landuse") in ("residential", "residential")
        ):
            if place not in ("suburb", "neighbourhood", "neighborhood", "quarter", "city_block"):
                # allow admin_level 9/10 named
                al = tags.get("admin_level")
                if al not in ("9", "10") and not HOOD_RE.search(name):
                    return
                if place is None and al not in ("9", "10") and not HOOD_RE.search(name):
                    return
        try:
            from osmium.geom import WKTFactory

            wkt = WKTFactory().create_multipolygon(a)
            if not wkt:
                return
            from shapely import wkt as swkt

            geom = swkt.loads(wkt)
        except Exception:
            return
        if geom.is_empty:
            return
        c = geom.representative_point()
        if not self._in_bbox(c.x, c.y):
            return
        where = self._inside(c)
        if not where:
            # also try centroid
            return
        osm_id = a.orig_id()
        osm_type = "way" if a.from_way() else "relation"
        self.areas.append(
            {
                "osm": f"{osm_type}/{osm_id}",
                "name": name,
                "place": place or tags.get("landuse") or f"al{tags.get('admin_level')}",
                "where": where,
                "area": float(geom.area),
                "wikidata": tags.get("wikidata"),
                "geom": geom,
            }
        )


def main():
    areas = load_json(OUT / "areas/areas.json")["areas"]
    city = next(a for a in areas if a["id"] == CITY_ID)
    existing = [
        a
        for a in areas
        if a.get("parent_id") == CITY_ID and a.get("parent_status") == "verified"
    ]
    existing_names = {a["name"] for a in existing}
    existing_ov = set()
    for a in existing:
        for r in a.get("source_refs") or []:
            if r.get("source") == "overture":
                existing_ov.add(r.get("source_id"))

    city_geom = load_geom(city["boundary_file"])
    broad_geom = load_geom("boundaries/extent_sumqayit_al6.geojson")
    # use broad bbox for scan
    scan = unary_union([g for g in (city_geom, broad_geom) if g is not None])
    minx, miny, maxx, maxy = scan.bounds
    print(f"Existing verified children: {len(existing)}")
    for n in sorted(existing_names):
        print(f"  · {n}")

    # --- Overture ---
    print("\n=== Overture divisions ===")
    div = pq.read_table(
        SRC / "overture/aze_division.parquet",
        columns=["id", "names", "subtype", "class", "parent_division_id", "country", "region"],
    )
    # column may be parent_division_id or similar — check
    cols = div.column_names
    print("division columns:", cols)

    # load areas by id
    da = pq.read_table(
        SRC / "overture/aze_division_area.parquet",
        columns=["id", "division_id", "geometry", "subtype", "country"],
    )
    area_by_div = {}
    for i in range(da.num_rows):
        did = da.column("division_id")[i].as_py()
        g = da.column("geometry")[i].as_py()
        try:
            geom = swkb.loads(g) if g else None
        except Exception:
            geom = None
        if geom and not geom.is_empty:
            area_by_div[did] = geom

    # find Sumqayıt locality + region ids
    sum_loc = sum_reg = None
    all_div = []
    for i in range(div.num_rows):
        names = div.column("names")[i].as_py() or {}
        name = pname(names)
        subtype = div.column("subtype")[i].as_py()
        did = div.column("id")[i].as_py()
        parent = None
        for cand in ("parent_division_id", "parent", "hierarchy"):
            if cand in cols:
                parent = div.column(cand)[i].as_py()
                break
        all_div.append(
            {"id": did, "name": name, "subtype": subtype, "parent": parent}
        )
        if name == "Sumqayıt" and subtype == "locality":
            sum_loc = did
        if name == "Sumqayıt" and subtype == "region":
            sum_reg = did
    print(f"Sumqayıt locality={sum_loc} region={sum_reg}")

    # children by parent
    by_parent = [d for d in all_div if d["parent"] in (sum_loc, sum_reg)]
    print(f"Direct Overture children of Sumqayıt loc/region: {len(by_parent)}")
    for d in sorted(by_parent, key=lambda x: x["name"] or ""):
        has = d["id"] in area_by_div
        known = d["name"] in existing_names or d["id"] in existing_ov
        print(
            f"  [{'HAVE' if known else 'NEW '}] {d['name']!r:40} subtype={d['subtype']:12} "
            f"geom={'Y' if has else 'N'} parent={'loc' if d['parent']==sum_loc else 'reg'}"
        )

    # Containment scan: all microhood/macrohood/neighborhood with geom inside city/broad
    print("\n=== Overture containment (hood subtypes inside Sumqayıt) ===")
    ALLOWED = {"microhood", "macrohood", "neighborhood", "locality"}
    contained_new = []
    for d in all_div:
        if d["subtype"] not in ALLOWED:
            continue
        if not d["name"] or d["name"] == "Sumqayıt":
            continue
        geom = area_by_div.get(d["id"])
        if geom is None:
            continue
        c = geom.representative_point()
        in_city = city_geom.covers(c) or city_geom.intersects(c)
        in_broad = broad_geom is not None and (
            broad_geom.covers(c) or broad_geom.intersects(c)
        )
        if not (in_city or in_broad):
            continue
        # require majority of geom in city or broad
        parent_poly = city_geom if in_city else broad_geom
        inter = geom.intersection(parent_poly)
        if inter.is_empty or inter.area < geom.area * 0.5:
            continue
        known = d["name"] in existing_names or d["id"] in existing_ov
        tag = "HAVE" if known else "NEW"
        parent_note = (
            "loc-child"
            if d["parent"] == sum_loc
            else ("reg-child" if d["parent"] == sum_reg else f"parent={d['parent']}")
        )
        line = (
            f"  [{tag}] {d['name']!r:40} subtype={d['subtype']:12} "
            f"in={'city' if in_city else 'broad'} {parent_note}"
        )
        print(line)
        if not known:
            contained_new.append(d)

    print(f"\nNew Overture by containment: {len(contained_new)}")

    # --- OSM ---
    print("\n=== OSM named hoods (scan) ===")
    h = OsmHoods(city_geom, broad_geom, minx, miny, maxx, maxy)
    h.apply_file(str(OSM_PBF).replace("\\", "/"), locations=True, idx="flex_mem")
    print(f"OSM area polygons: {len(h.areas)}")
    for a in sorted(h.areas, key=lambda x: x["name"]):
        known = a["name"] in existing_names
        print(
            f"  [{'HAVE' if known else 'NEW '}] {a['name']!r:40} {a['osm']:20} "
            f"place={a['place']} where={a['where']} area={a['area']:.8f}"
        )
    print(f"OSM label nodes: {len(h.nodes)}")
    for n in sorted(h.nodes, key=lambda x: x["name"]):
        # nodes without polygon can't be verified boundary — list for review
        match_poly = any(
            x["name"].casefold() == n["name"].casefold() for x in h.areas
        )
        print(
            f"  node {n['name']!r:40} {n['osm']} where={n['where']} "
            f"poly={'Y' if match_poly else 'N-no-boundary'}"
        )

    # Summary table
    print("\n=== SUMMARY: actionable NEW with polygon ===")
    actionable = []
    for d in contained_new:
        actionable.append(
            {
                "source": "overture",
                "id": d["id"],
                "name": d["name"],
                "subtype": d["subtype"],
                "parent": d["parent"],
            }
        )
    for a in h.areas:
        if a["name"] not in existing_names:
            # skip if already in overture list same name
            if any(x["name"] == a["name"] for x in actionable):
                continue
            actionable.append(
                {
                    "source": "osm",
                    "id": a["osm"],
                    "name": a["name"],
                    "subtype": a["place"],
                    "where": a["where"],
                }
            )
    for x in actionable:
        print(f"  + {x}")
    print(f"Total actionable: {len(actionable)}")

    OUT.joinpath("reviews").mkdir(parents=True, exist_ok=True)
    # strip geoms for json
    report = {
        "existing_verified": sorted(existing_names),
        "overture_direct_children": [
            {"name": d["name"], "id": d["id"], "subtype": d["subtype"], "parent": d["parent"]}
            for d in sorted(by_parent, key=lambda x: x["name"] or "")
        ],
        "overture_new_containment": [
            {"name": d["name"], "id": d["id"], "subtype": d["subtype"], "parent": d["parent"]}
            for d in contained_new
        ],
        "osm_areas": [
            {k: v for k, v in a.items() if k != "geom"}
            for a in sorted(h.areas, key=lambda x: x["name"])
        ],
        "osm_nodes_no_poly": [
            n
            for n in h.nodes
            if not any(x["name"].casefold() == n["name"].casefold() for x in h.areas)
        ],
        "actionable_new": actionable,
    }
    Path("data/reviews/sumqayit_hoods_inventory.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("Wrote data/reviews/sumqayit_hoods_inventory.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
