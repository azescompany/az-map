# -*- coding: utf-8 -*-
"""
Extract Gəncə city + Kəpəz / Nizami rayons + məhəllə + named places.

Hierarchy.md (Bakı-style: city → rayon → hood).
source_files/ read-only → data/.

OSM:
  - relation/3764556 admin_level=6 Gəncə İnzibati Ərazisi (city extent)
  - relation/11901821 admin_level=8 Kəpəz rayonu Q16418369
  - relation/11901822 admin_level=8 Nizami rayonu Q15623482

Overture:
  - region Gəncə İnzibati Ərazisi → locality Gəncə + Kəpəz/Nizami rayons
  - rayon children → verified hoods (geom + containment)

Also removes Bakı-Nizami mis-parented conflict hoods that share Gəncə Overture ids.
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
OSM_CITY_REL = 3764556
OSM_KAPAZ_REL = 11901821
OSM_NIZAMI_REL = 11901822
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


def overture_ids_of(area) -> set[str]:
    return {
        r.get("source_id")
        for r in (area.get("source_refs") or [])
        if r.get("source") == "overture" and r.get("source_id")
    }


def main() -> int:
    areas_path = OUT / "areas" / "areas.json"
    areas = load_json(areas_path)["areas"]
    reviews_path = OUT / "reviews" / "pilot_reviews.json"
    reviews = list((load_json(reviews_path) if reviews_path.exists() else {}).get("reviews") or [])

    country = next((a for a in areas if a.get("type") == "country"), None)
    if not country:
        raise SystemExit("Country area missing")

    ov_div, ov_areas = load_overture()
    ov_region = next(
        (
            v
            for v in ov_div.values()
            if v["name"] == "Gəncə İnzibati Ərazisi" and v["subtype"] == "region"
        ),
        None,
    )
    if not ov_region:
        raise SystemExit("Overture Gəncə İnzibati Ərazisi region not found")

    ov_kapaz = next(
        (
            v
            for v in ov_div.values()
            if v["name"] == "Kəpəz rayonu" and v.get("parent") == ov_region["id"]
        ),
        None,
    )
    ov_nizami = next(
        (
            v
            for v in ov_div.values()
            if v["name"] == "Nizami rayonu" and v.get("parent") == ov_region["id"]
        ),
        None,
    )
    if not ov_kapaz or not ov_nizami:
        raise SystemExit("Overture Kəpəz/Nizami under Gəncə missing")

    gence_child_ov_ids = {ov_kapaz["id"], ov_nizami["id"]}
    for v in ov_div.values():
        if v.get("parent") in (ov_kapaz["id"], ov_nizami["id"]):
            gence_child_ov_ids.add(v["id"])

    # Drop previous Gəncə tree + Bakı-misparented Gəncə Overture ids
    drop = set()
    for a in areas:
        notes = a.get("notes") or ""
        bf = a.get("boundary_file") or ""
        if "WORKER 2.6" in notes or "gence" in bf or a.get("name") == "Gəncə":
            if a.get("type") == "city" or "gence" in bf or "WORKER 2.6" in notes:
                drop.add(a["id"])
        if overture_ids_of(a) & gence_child_ov_ids:
            # Keep if already under a Gəncə city we are about to drop; else strip Bakı orphans
            drop.add(a["id"])
    changed = True
    while changed:
        changed = False
        for a in areas:
            if a.get("parent_id") in drop and a["id"] not in drop:
                drop.add(a["id"])
                changed = True
    for a in areas:
        if a["id"] in drop and a.get("boundary_file") and "gence" in (a.get("boundary_file") or ""):
            p = OUT / a["boundary_file"]
            if p.exists():
                p.unlink()
    print(f"Removed previous Gəncə / mis-parented areas: {len(drop)}")
    areas = [a for a in areas if a["id"] not in drop]

    print("Reading OSM boundaries…")
    want = {OSM_CITY_REL, OSM_KAPAZ_REL, OSM_NIZAMI_REL}
    osm_h = OsmAreaExtractor(want)
    osm_h.apply_file(str(OSM_PBF), locations=True, idx="flex_mem")
    city_geom = osm_h.geoms.get(OSM_CITY_REL) or ov_areas.get(ov_region["id"])
    kapaz_geom = osm_h.geoms.get(OSM_KAPAZ_REL) or ov_areas.get(ov_kapaz["id"])
    nizami_geom = osm_h.geoms.get(OSM_NIZAMI_REL) or ov_areas.get(ov_nizami["id"])
    if city_geom is None:
        raise SystemExit("Gəncə city geometry missing")
    print(
        f"OSM geoms city={OSM_CITY_REL in osm_h.geoms} "
        f"kapaz={OSM_KAPAZ_REL in osm_h.geoms} nizami={OSM_NIZAMI_REL in osm_h.geoms}"
    )

    city_rec, city_id = make_area(
        key="city:gence",
        name="Gəncə",
        type_="city",
        subtype="city",
        parent_id=country["id"],
        parent_status="verified",
        geom=city_geom,
        geom_status="verified",
        center=None,
        wikidata="Q131290",
        source_refs=[
            {
                "source": "osm",
                "source_id": f"relation/{OSM_CITY_REL}",
                "release": OSM_RELEASE,
                "role": "boundary",
                "match_method": "id",
            },
            {
                "source": "overture",
                "source_id": ov_region["id"],
                "release": OVERTURE_RELEASE,
                "role": "admin",
                "match_method": "wikidata",
            },
        ],
        notes="WORKER 2.6 · Gəncə İnzibati Ərazisi (city). Rayons: Kəpəz, Nizami.",
        alt_names=["Ganja", "Gəncə İnzibati Ərazisi"],
        boundary_name="city_gence",
    )
    areas.append(city_rec)
    write_boundary(
        city_id,
        "Gəncə",
        city_geom,
        "boundaries/city_gence.geojson",
        {"type": "city", "parent_id": country["id"]},
    )

    rayons_spec = [
        {
            "key": "gence_kapaz",
            "name": "Kəpəz rayonu",
            "ov": ov_kapaz,
            "geom": kapaz_geom,
            "osm_rel": OSM_KAPAZ_REL,
            "wikidata": "Q16418369",
            "places_key": "gence_kapaz",
        },
        {
            "key": "gence_nizami",
            "name": "Nizami rayonu",
            "ov": ov_nizami,
            "geom": nizami_geom,
            "osm_rel": OSM_NIZAMI_REL,
            "wikidata": "Q15623482",
            "places_key": "gence_nizami",
        },
    ]

    report = {"city": "Gəncə", "rayons": {}, "places": {}, "reparented_from_baki_nizami": sorted(
        n for n in (
            "1-ci mikrorayon",
            "3-cü mikrorayon",
            "4-cü mikrorayon",
            "5-ci mikrorayon",
            "Bəstə qəsəbəsi",
            "Gülüstan",
            "Mahrasa Bağı",
        )
    )}
    existing_place_ids: set[str] = set()
    pdir = OUT / "places"
    index_path = pdir / "index.json"
    if index_path.exists():
        for f in load_json(index_path).get("files") or []:
            if "gence" in f:
                continue
            fp = OUT / f
            if fp.exists():
                for pl in load_json(fp).get("places") or []:
                    if pl.get("id"):
                        existing_place_ids.add(pl["id"])

    place_files_meta = []

    for rs in rayons_spec:
        rgeom = rs["geom"]
        if rgeom is None:
            print(f"SKIP rayon {rs['name']} — no geometry")
            continue
        r_status = "verified"
        r_notes = "WORKER 2.6 · rayon under Gəncə"
        if not contained(rgeom, city_geom):
            r_status = "conflict"
            r_notes = "Rayon geometry not contained in Gəncə city polygon"
            reviews.append(
                {
                    "id": cid("review", "gence-rayon", rs["key"]),
                    "kind": "hierarchy_conflict",
                    "entity": rs["name"],
                    "detail": r_notes,
                    "status": "open",
                }
            )
        r_rec, r_id = make_area(
            key=f"rayon:{rs['key']}",
            name=rs["name"],
            type_="rayon",
            subtype="rayon",
            parent_id=city_id,
            parent_status=r_status,
            geom=rgeom,
            geom_status="verified",
            center=None,
            wikidata=rs["wikidata"],
            source_refs=[
                {
                    "source": "osm",
                    "source_id": f"relation/{rs['osm_rel']}",
                    "release": OSM_RELEASE,
                    "role": "boundary",
                    "match_method": "id",
                },
                {
                    "source": "overture",
                    "source_id": rs["ov"]["id"],
                    "release": OVERTURE_RELEASE,
                    "role": "boundary",
                    "match_method": "id",
                    "overture_parent_id": rs["ov"].get("parent"),
                },
            ],
            notes=r_notes,
            boundary_name=f"rayon_{rs['key']}",
        )
        areas.append(r_rec)
        write_boundary(
            r_id,
            rs["name"],
            rgeom,
            r_rec["boundary_file"],
            {"type": "rayon", "parent_id": city_id, "parent_status": r_status},
        )

        verified = []
        conflicts = []
        used = set()
        for child in sorted(
            (v for v in ov_div.values() if v.get("parent") == rs["ov"]["id"]),
            key=lambda z: z["name"] or "",
        ):
            if (child.get("subtype") or "") not in ALLOWED:
                continue
            if not child.get("name") or not child["name"].strip():
                continue
            # Skip "* rayonu" / city name
            if child["name"].endswith(" rayonu") or child["name"] in ("Gəncə", "Bakı"):
                continue
            geom = ov_areas.get(child["id"])
            if geom is None:
                continue
            key = f"{rs['key']}_{slug(child['name'])}"
            base = key
            n = 2
            while key in used:
                key = f"{base}_{n}"
                n += 1
            used.add(key)
            st = "verified"
            cnotes = f"WORKER 2.6 · Overture child of {rs['name']}"
            if not contained(geom, rgeom):
                st = "conflict"
                cnotes = f"Not contained in {rs['name']}"
                conflicts.append(child["name"])
                reviews.append(
                    {
                        "id": cid("review", "gence-hood", key),
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
                parent_id=r_id,
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
                    "parent_id": r_id,
                    "parent_status": st,
                    "subtype": child["subtype"],
                },
            )
            if st == "verified":
                verified.append(child["name"])

        places = []
        skipped = 0
        for p in extract_places_in(rgeom, max_places=500):
            pid = cid("place", "overture", p["overture_id"])
            if pid in existing_place_ids:
                skipped += 1
                continue
            existing_place_ids.add(pid)
            places.append(
                {
                    "id": pid,
                    "name": p["name"],
                    "name_normalized": norm(p["name"]),
                    "alt_names": [],
                    "category": p["category"],
                    "coordinates": {"lat": p["lat"], "lon": p["lon"]},
                    "area_id": r_id,
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
        pfile = f"places/{rs['places_key']}_all.json"
        write_json(pdir / f"{rs['places_key']}_all.json", {"area_id": r_id, "parent_area_id": city_id, "places": places})
        place_files_meta.append((rs["places_key"], rs["name"], r_id, len(places), pfile))
        report["rayons"][rs["name"]] = {
            "parent_status": r_status,
            "verified_hoods": verified,
            "conflicts": conflicts,
            "places": len(places),
            "places_skipped_dup": skipped,
        }
        print(f"{rs['name']}: verified={len(verified)} conflict={len(conflicts)} places={len(places)}")

    # places index
    index = load_json(index_path) if index_path.exists() else {}
    files = [f for f in (index.get("files") or []) if "gence" not in f]
    by_rayon = {k: v for k, v in (index.get("by_rayon") or {}).items() if "gence" not in k}
    for key, name, aid, count, pfile in place_files_meta:
        if pfile not in files:
            files.append(pfile)
        by_rayon[key] = {"name": name, "area_id": aid, "count": count, "file": pfile}
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
    report["places_total_index"] = total

    write_json(areas_path, {"type": "AreaCollection", "areas": areas})
    b_index = [
        {"file": a["boundary_file"], "area_id": a["id"], "name": a["name"]}
        for a in areas
        if a.get("boundary_file")
    ]
    write_json(OUT / "boundaries" / "index.json", {"boundaries": b_index})
    write_json(reviews_path, {"reviews": reviews})
    report["areas_total"] = len(areas)
    report["generated_at"] = datetime.now(timezone.utc).isoformat()
    report["osm_release"] = OSM_RELEASE
    report["overture_release"] = OVERTURE_RELEASE
    write_json(OUT / "reviews" / "gence_extract.json", report)

    man_path = OUT / "manifest.json"
    if man_path.exists():
        m = load_json(man_path)
        m["dataset_version"] = "0.1.8-pilot"
        m.setdefault("coverage", {})
        m["coverage"]["areas"] = len(areas)
        m["coverage"]["places"] = total
        m["coverage"]["boundaries"] = len(b_index)
        m["description"] = (
            "Country + Bakı + Sumqayıt + Abşeron + Gəncə (Kəpəz/Nizami). Hierarchy.md / WORKER.md."
        )
        write_json(man_path, m)

    print(json.dumps(
        {
            "city_id": city_id,
            "areas_total": len(areas),
            "places_index": total,
            "rayons": {k: {"verified": len(v["verified_hoods"]), "places": v["places"]} for k, v in report["rayons"].items()},
        },
        ensure_ascii=False,
        indent=2,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
