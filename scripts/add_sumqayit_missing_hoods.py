# -*- coding: utf-8 -*-
"""
Add missing Sumqayıt neighborhood/mikrorayon children from OSM (+ nested Corat Overture).

Incremental — does not wipe Sumqayıt city/children/places.
Reads source_files/; writes data/areas, data/boundaries, data/reviews only.
"""
from __future__ import annotations

import json
import os
import re
import sys
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import osmium
import pyarrow.parquet as pq
from shapely import wkb as swkb
from shapely import wkt as load_wkt
from shapely.geometry import Point, mapping, shape
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT / "scripts"))

SRC = Path("source_files")
OUT = Path("data")
OSM_PBF = SRC / "azerbaijan-261020.osm.pbf"
OSM_RELEASE = "azerbaijan-261020"
OVERTURE_RELEASE = "2026-09-23.1"
CITY_ID = "a02b58f1-3009-5ce3-a728-69d77b411dec"
NS = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")

HOOD_NAME_RE = re.compile(
    r"(mikrorayon|mikro\s*rayon|mkr\.?|məhəllə|mehelle|məhelle|qəsəbə|qesebe|mtk|bağları|baglari)",
    re.I,
)
SKIP_NAME_RE = re.compile(
    r"(çimər|cimer|beach|məktəb|mekteb|idman|dairəsi|dairesi|school|\\\\)",
    re.I,
)
MIN_AREA = 1e-8


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


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_boundary_geom(boundary_file: str | None):
    if not boundary_file:
        return None
    path = OUT / boundary_file
    if not path.exists():
        return None
    fc = load_json(path)
    geoms = [
        shape(f["geometry"])
        for f in fc.get("features") or []
        if f.get("geometry") and f["geometry"].get("type") in ("Polygon", "MultiPolygon")
    ]
    if not geoms:
        return None
    return unary_union(geoms) if len(geoms) > 1 else geoms[0]


def center_from_geom(geom):
    p = geom.representative_point()
    return float(p.y), float(p.x), "interior_representative_point"


def contained_point(pt: Point, parent_geom) -> bool:
    return bool(parent_geom.covers(pt) or parent_geom.intersects(pt))


def write_boundary(aid, name, geom, path_rel, props):
    feat = {
        "type": "Feature",
        "id": aid,
        "properties": {"id": aid, "name": name, **props},
        "geometry": mapping(geom),
    }
    write_json(OUT / path_rel, {"type": "FeatureCollection", "features": [feat]})


def subtype_for_name(name: str, place_tag: str | None) -> str:
    n = name.casefold()
    if "mikrorayon" in n or "mikro rayon" in n or re.search(r"\bmkr\b", n):
        return "macrohood"
    if "qəsəbə" in n or "qesebe" in n:
        return "neighborhood"
    if "mtk" in n:
        return "microhood"
    if place_tag in ("suburb", "neighbourhood", "neighborhood"):
        return "neighborhood"
    if place_tag == "quarter":
        return "microhood"
    return "microhood"


class OsmHoodExtractor(osmium.SimpleHandler):
    def __init__(self, city_geom, broad_geom, minx, miny, maxx, maxy):
        super().__init__()
        self.city = city_geom
        self.broad = broad_geom
        self.minx, self.miny, self.maxx, self.maxy = minx, miny, maxx, maxy
        self.wk = osmium.geom.WKTFactory()
        self.rows = []

    def area(self, a):
        tags = a.tags
        if not tags:
            return
        name = tags.get("name") or tags.get("name:az")
        if not name or not str(name).strip():
            return
        name = str(name).strip()
        if SKIP_NAME_RE.search(name):
            return
        place = tags.get("place")
        landuse = tags.get("landuse")
        # Accept named residential/city_block/quarter/neighbourhood or hood-pattern names
        ok = place in (
            "suburb",
            "neighbourhood",
            "neighborhood",
            "quarter",
            "city_block",
            "village",
            "hamlet",
        ) or (HOOD_NAME_RE.search(name) and landuse in ("residential", "industrial", None))
        if not ok:
            return
        if not HOOD_NAME_RE.search(name) and place not in (
            "suburb",
            "neighbourhood",
            "neighborhood",
            "quarter",
            "city_block",
        ):
            return
        try:
            wkt = self.wk.create_multipolygon(a)
            if not wkt:
                return
            geom = load_wkt.loads(wkt)
        except Exception:
            return
        if geom is None or geom.is_empty or float(geom.area) < MIN_AREA:
            return
        c = geom.representative_point()
        if not (self.minx <= c.x <= self.maxx and self.miny <= c.y <= self.maxy):
            return
        if contained_point(c, self.city):
            where = "city"
            parent_poly = self.city
        elif self.broad is not None and contained_point(c, self.broad):
            where = "broad"
            parent_poly = self.broad
        else:
            return
        # majority overlap with chosen parent poly
        inter = geom.intersection(parent_poly)
        if inter.is_empty or float(inter.area) < float(geom.area) * 0.5:
            return
        osm_id = a.orig_id()
        osm_type = "way" if a.from_way() else "relation"
        self.rows.append(
            {
                "name": name,
                "osm": f"{osm_type}/{osm_id}",
                "place": place or landuse or "named",
                "where": where,
                "geom": geom,
                "area": float(geom.area),
                "wikidata": tags.get("wikidata"),
            }
        )


def make_child_area(
    *,
    key: str,
    name: str,
    subtype: str,
    parent_id: str,
    geom,
    source_refs: list,
    notes: str,
):
    lat, lon, method = center_from_geom(geom)
    aid = cid("area", key)
    bfile = f"boundaries/neighborhood_{key}.geojson"
    return {
        "id": aid,
        "name": name,
        "name_normalized": norm(name),
        "alt_names": [],
        "type": "neighborhood",
        "subtype": subtype,
        "parent_id": parent_id,
        "parent_status": "verified",
        "geom_status": "verified",
        "center": {
            "latitude": lat,
            "longitude": lon,
            "lat": lat,
            "lon": lon,
        },
        "center_method": method,
        "wikidata": next(
            (r.get("wikidata") for r in source_refs if r.get("wikidata")), None
        ),
        "population": None,
        "population_source": None,
        "bbox": list(geom.bounds),
        "source_refs": source_refs,
        "notes": notes,
        "boundary_file": bfile,
        "geom_status_reason": None,
        "crs": "EPSG:4326",
        "geometry_type": geom.geom_type,
        "geometry_valid": True,
        "center_status": "verified",
        "center_within_boundary": True,
    }, aid, bfile, geom


def load_overture_nested_corat(corat_ov_id: str, corat_geom, city_geom, broad_geom):
    """Təzə Corat / Köhnə Corat under Corat; 75-ci under Təzə Corat."""
    div = pq.read_table(
        SRC / "overture/aze_division.parquet",
        columns=["id", "names", "subtype", "parent_division_id"],
    )
    da = pq.read_table(
        SRC / "overture/aze_division_area.parquet",
        columns=["division_id", "geometry"],
    )
    area_by = {}
    for i in range(da.num_rows):
        did = da.column("division_id")[i].as_py()
        g = da.column("geometry")[i].as_py()
        try:
            geom = swkb.loads(g) if g else None
        except Exception:
            geom = None
        if geom and not geom.is_empty:
            area_by[did] = geom

    children = []
    for i in range(div.num_rows):
        parent = div.column("parent_division_id")[i].as_py()
        if parent != corat_ov_id:
            continue
        name = (div.column("names")[i].as_py() or {}).get("primary") or ""
        if not name or name == "Corat":
            continue
        did = div.column("id")[i].as_py()
        subtype = div.column("subtype")[i].as_py()
        geom = area_by.get(did)
        children.append(
            {
                "id": did,
                "name": name,
                "subtype": subtype,
                "parent": parent,
                "geom": geom,
            }
        )
    # also 75-ci under Təzə Corat
    teze = next((c for c in children if c["name"] == "Təzə Corat"), None)
    extra = []
    if teze:
        for i in range(div.num_rows):
            if div.column("parent_division_id")[i].as_py() != teze["id"]:
                continue
            name = (div.column("names")[i].as_py() or {}).get("primary") or ""
            did = div.column("id")[i].as_py()
            extra.append(
                {
                    "id": did,
                    "name": name,
                    "subtype": div.column("subtype")[i].as_py(),
                    "parent": teze["id"],
                    "geom": area_by.get(did),
                    "nest_under": "Təzə Corat",
                }
            )
    return children, extra


def main() -> int:
    areas_path = OUT / "areas" / "areas.json"
    doc = load_json(areas_path)
    areas = doc["areas"]
    city = next(a for a in areas if a["id"] == CITY_ID)
    city_geom = load_boundary_geom(city["boundary_file"])
    broad_geom = load_boundary_geom("boundaries/extent_sumqayit_al6.geojson")
    assert city_geom is not None

    existing_children = [a for a in areas if a.get("parent_id") == CITY_ID]
    existing_norm = {norm(a["name"]) for a in existing_children}
    # also any area already keyed under sumqayit boundary
    for a in areas:
        bf = a.get("boundary_file") or ""
        if "sumqayit" in bf:
            existing_norm.add(norm(a["name"]))

    scan = unary_union([g for g in (city_geom, broad_geom) if g is not None])
    minx, miny, maxx, maxy = scan.bounds

    print("Scanning OSM hood polygons…")
    h = OsmHoodExtractor(city_geom, broad_geom, minx, miny, maxx, maxy)
    h.apply_file(str(OSM_PBF).replace("\\", "/"), locations=True, idx="flex_mem")
    print(f"  OSM candidates raw: {len(h.rows)}")

    # Dedupe by normalized name — keep largest polygon
    by_name: dict[str, list] = defaultdict(list)
    for r in h.rows:
        by_name[norm(r["name"])].append(r)

    skipped = []
    to_add_osm = []
    for nn, group in sorted(by_name.items(), key=lambda x: x[0]):
        group.sort(key=lambda x: -x["area"])
        best = group[0]
        if nn in existing_norm:
            skipped.append(
                {
                    "name": best["name"],
                    "reason": "already_verified_child",
                    "osm": best["osm"],
                }
            )
            continue
        if len(group) > 1:
            skipped.append(
                {
                    "name": best["name"],
                    "reason": f"duplicate_osm_kept_largest_n={len(group)}",
                    "kept": best["osm"],
                    "dropped": [g["osm"] for g in group[1:]],
                }
            )
        to_add_osm.append(best)

    print(f"  OSM to add: {len(to_add_osm)} (skip existing/dup notes: {len(skipped)})")

    used_keys = set()
    for a in areas:
        bf = a.get("boundary_file") or ""
        m = re.search(r"neighborhood_(sumqayit_[a-z0-9_]+)\.geojson$", bf.replace("\\", "/"))
        if m:
            used_keys.add(m.group(1))

    added = []
    for r in sorted(to_add_osm, key=lambda x: x["name"]):
        key = "sumqayit_" + slug(r["name"])
        base = key
        n = 2
        while key in used_keys:
            key = f"{base}_{n}"
            n += 1
        used_keys.add(key)
        subtype = subtype_for_name(r["name"], r["place"])
        rec, aid, bfile, geom = make_child_area(
            key=key,
            name=r["name"],
            subtype=subtype,
            parent_id=CITY_ID,
            geom=r["geom"],
            source_refs=[
                {
                    "source": "osm",
                    "source_id": r["osm"],
                    "release": OSM_RELEASE,
                    "role": "boundary",
                    "match_method": "id",
                    "note": f"place/landuse={r['place']}; containment={r['where']}",
                }
            ],
            notes=(
                "OSM named hood polygon contained in Sumqayıt "
                f"{'city core' if r['where']=='city' else 'al=6 extent'}; "
                "Overture parent absent — verified via OSM id + containment."
            ),
        )
        if r.get("wikidata"):
            rec["wikidata"] = r["wikidata"]
        write_boundary(
            aid,
            r["name"],
            geom,
            bfile,
            {
                "type": "neighborhood",
                "parent_id": CITY_ID,
                "parent_status": "verified",
                "subtype": subtype,
            },
        )
        areas.append(rec)
        added.append(
            {
                "name": r["name"],
                "id": aid,
                "source": r["osm"],
                "where": r["where"],
                "subtype": subtype,
                "parent": "Sumqayıt",
            }
        )
        print(f"  + {r['name']} ← {r['osm']} ({r['where']})")

    # --- Nested Corat (Overture parent chain) ---
    corat = next(
        (a for a in areas if a.get("parent_id") == CITY_ID and a.get("name") == "Corat"),
        None,
    )
    corat_added = []
    if corat:
        corat_geom = load_boundary_geom(corat.get("boundary_file"))
        corat_ov = None
        for ref in corat.get("source_refs") or []:
            if ref.get("source") == "overture":
                corat_ov = ref.get("source_id")
                break
        # known Corat overture id from inventory
        corat_ov = corat_ov or "3d5725d7-3102-4785-937b-51839abb6bd2"
        direct, nested75 = load_overture_nested_corat(
            corat_ov, corat_geom, city_geom, broad_geom
        )
        # existing children of Corat
        corat_child_norm = {
            norm(a["name"]) for a in areas if a.get("parent_id") == corat["id"]
        }

        id_by_name = {}
        for c in direct:
            nn = norm(c["name"])
            if nn in corat_child_norm or nn in existing_norm:
                skipped.append(
                    {"name": c["name"], "reason": "corat_child_exists_or_city_dup", "id": c["id"]}
                )
                continue
            if c["geom"] is None:
                skipped.append({"name": c["name"], "reason": "no_division_area", "id": c["id"]})
                continue
            # containment in Corat preferred; else broad
            parent_poly = corat_geom or broad_geom
            cpt = c["geom"].representative_point()
            if parent_poly is None or not contained_point(cpt, parent_poly):
                skipped.append(
                    {"name": c["name"], "reason": "not_contained_in_corat", "id": c["id"]}
                )
                continue
            key = "sumqayit_" + slug(c["name"])
            base = key
            n = 2
            while key in used_keys:
                key = f"{base}_{n}"
                n += 1
            used_keys.add(key)
            rec, aid, bfile, geom = make_child_area(
                key=key,
                name=c["name"],
                subtype=c["subtype"] or "neighborhood",
                parent_id=corat["id"],
                geom=c["geom"],
                source_refs=[
                    {
                        "source": "overture",
                        "source_id": c["id"],
                        "release": OVERTURE_RELEASE,
                        "role": "boundary",
                        "match_method": "id",
                        "overture_parent_id": c["parent"],
                    }
                ],
                notes="Overture child of Corat locality; Corat is Sumqayıt verified child.",
            )
            write_boundary(
                aid,
                c["name"],
                geom,
                bfile,
                {
                    "type": "neighborhood",
                    "parent_id": corat["id"],
                    "parent_status": "verified",
                    "subtype": c["subtype"],
                },
            )
            areas.append(rec)
            id_by_name[c["name"]] = aid
            corat_added.append(
                {
                    "name": c["name"],
                    "id": aid,
                    "source": c["id"],
                    "parent": "Corat",
                }
            )
            print(f"  + {c['name']} ← overture (parent Corat)")

        teze_id = id_by_name.get("Təzə Corat") or next(
            (
                a["id"]
                for a in areas
                if a.get("name") == "Təzə Corat" and a.get("parent_id") == corat["id"]
            ),
            None,
        )
        for c in nested75:
            if not teze_id:
                skipped.append({"name": c["name"], "reason": "teze_corat_missing"})
                continue
            if norm(c["name"]) in {
                norm(a["name"]) for a in areas if a.get("parent_id") == teze_id
            }:
                skipped.append({"name": c["name"], "reason": "exists_under_teze"})
                continue
            if c["geom"] is None:
                skipped.append({"name": c["name"], "reason": "no_division_area"})
                continue
            key = "sumqayit_" + slug(c["name"])
            base = key
            n = 2
            while key in used_keys:
                key = f"{base}_{n}"
                n += 1
            used_keys.add(key)
            rec, aid, bfile, geom = make_child_area(
                key=key,
                name=c["name"],
                subtype=c["subtype"] or "microhood",
                parent_id=teze_id,
                geom=c["geom"],
                source_refs=[
                    {
                        "source": "overture",
                        "source_id": c["id"],
                        "release": OVERTURE_RELEASE,
                        "role": "boundary",
                        "match_method": "id",
                        "overture_parent_id": c["parent"],
                    }
                ],
                notes="Overture child of Təzə Corat (under Corat → Sumqayıt).",
            )
            write_boundary(
                aid,
                c["name"],
                geom,
                bfile,
                {
                    "type": "neighborhood",
                    "parent_id": teze_id,
                    "parent_status": "verified",
                    "subtype": c["subtype"],
                },
            )
            areas.append(rec)
            corat_added.append(
                {"name": c["name"], "id": aid, "source": c["id"], "parent": "Təzə Corat"}
            )
            print(f"  + {c['name']} ← overture (parent Təzə Corat)")

    write_json(areas_path, {"type": "AreaCollection", "areas": areas})

    # refresh boundary index
    b_index = [
        {"file": a["boundary_file"], "area_id": a["id"], "name": a["name"]}
        for a in areas
        if a.get("boundary_file")
    ]
    write_json(OUT / "boundaries" / "index.json", {"boundaries": b_index})

    # manifest areas count only (do not bump dataset_version / wipe places)
    manifest_path = OUT / "manifest.json"
    manifest = load_json(manifest_path)
    manifest["generated_at"] = datetime.now(timezone.utc).isoformat()
    cov = manifest.setdefault("coverage", {})
    cov["areas"] = len(areas)
    cov["boundaries"] = len(b_index)
    write_json(manifest_path, manifest)

    verified_now = sorted(
        a["name"]
        for a in areas
        if a.get("parent_id") == CITY_ID and a.get("parent_status") == "verified"
    )
    report = {
        "city_id": CITY_ID,
        "added_osm_under_sumqayit": added,
        "added_overture_nested_corat": corat_added,
        "skipped": skipped,
        "verified_children_count": len(verified_now),
        "verified_children": verified_now,
        "areas_total": len(areas),
        "note": (
            "No synthetic hoods. OSM mikrorayon/məhəllə via named polygons + containment. "
            "Places not modified — LandmarkAgent may reassign children-first."
        ),
    }
    write_json(OUT / "reviews" / "sumqayit_missing_hoods.json", report)
    # update extract summary pointer
    extract_rep = {
        "city_id": CITY_ID,
        "verified_children": verified_now,
        "added_this_run": [x["name"] for x in added] + [x["name"] for x in corat_added],
        "areas_total": len(areas),
        "source": "add_sumqayit_missing_hoods.py",
    }
    write_json(OUT / "reviews" / "sumqayit_extract.json", extract_rep)

    print("=" * 50)
    print(f"Added under Sumqayıt: {len(added)}")
    print(f"Added nested Corat: {len(corat_added)}")
    print(f"Verified Sumqayıt children now: {len(verified_now)}")
    print(f"Areas total: {len(areas)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
