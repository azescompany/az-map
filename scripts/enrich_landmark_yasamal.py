# -*- coding: utf-8 -*-
"""
LandmarkAgent — Yasamal places enrich (OSM named ways + containment).

Reads source_files/ + existing data/places/yasamal_all.json.
Writes only: places/yasamal_all.json, places/index.json, data/reviews/*.
Never modifies source_files/ or areas/boundaries.
"""
from __future__ import annotations

import json
import re
import uuid
from collections import Counter
from pathlib import Path

import osmium
from shapely.geometry import Point, shape
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
# Relative paths after chdir(ROOT) — absolute paths with non-ASCII dirs break osmium on Windows.
SRC = Path("source_files")
OUT = Path("data")
OSM_PBF = SRC / "azerbaijan-261020.osm.pbf"
OSM_RELEASE = "azerbaijan-261020"
NS = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")
RAYON_KEY = "yasamal"
BASELINE = 170


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


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def classify(tags) -> tuple[str | None, str | None]:
    if "historic" in tags:
        return "historic", tags.get("historic") or "historic"
    t = tags.get("tourism")
    if t == "museum":
        return "museum", t
    if t in ("attraction", "viewpoint", "zoo", "theme_park", "artwork"):
        return "tourism", t
    a = tags.get("amenity")
    if a == "place_of_worship":
        return "religious", a
    if a in ("theatre", "cinema", "library", "arts_centre"):
        return "culture", a
    if a == "university":
        return "education", a
    if a == "townhall":
        return "government", a
    leisure = tags.get("leisure")
    if leisure in ("park", "garden", "nature_reserve"):
        return "park", leisure
    if leisure == "stadium":
        return "stadium", leisure
    return None, None


def load_yasamal_geom():
    areas = load_json(OUT / "areas" / "areas.json")["areas"]
    ya = next(a for a in areas if a.get("name") == "Yasamal rayonu")
    fc = load_json(OUT / ya["boundary_file"])
    geoms = [shape(f["geometry"]) for f in fc.get("features") or [] if f.get("geometry")]
    geom = unary_union(geoms) if len(geoms) > 1 else geoms[0]
    return ya, geom


class OsmWayCollector(osmium.SimpleHandler):
    def __init__(self, geom):
        super().__init__()
        self.geom = geom
        self.minx, self.miny, self.maxx, self.maxy = geom.bounds
        self.ways = []

    def way(self, w):
        if not w.tags:
            return
        cat, raw = classify(w.tags)
        if not cat:
            return
        name = w.tags.get("name") or w.tags.get("name:az")
        if not name or not str(name).strip():
            return
        try:
            locs = [(n.lon, n.lat) for n in w.nodes if n.location.valid()]
        except Exception:
            return
        if len(locs) < 2:
            return
        lon = sum(x for x, _ in locs) / len(locs)
        lat = sum(y for _, y in locs) / len(locs)
        if not (self.minx <= lon <= self.maxx and self.miny <= lat <= self.maxy):
            return
        pt = Point(lon, lat)
        if not (self.geom.covers(pt) or self.geom.intersects(pt)):
            return
        self.ways.append(
            {
                "osm_id": w.id,
                "name": str(name).strip(),
                "category": cat,
                "raw": raw,
                "lat": float(lat),
                "lon": float(lon),
                "wikidata": w.tags.get("wikidata"),
            }
        )


def main() -> int:
    import os

    os.chdir(ROOT)
    assert OSM_PBF.exists(), OSM_PBF
    ya, geom = load_yasamal_geom()
    area_id = ya["id"]

    path = OUT / "places" / "yasamal_all.json"
    existing = load_json(path)
    places = list(existing["places"])
    assert existing.get("rayon_key") == RAYON_KEY
    assert len(places) >= BASELINE

    exist_ids = {p["id"] for p in places}
    exist_src: set[tuple[str, str]] = set()
    exist_wd: set[str] = set()
    for p in places:
        if p.get("wikidata"):
            exist_wd.add(str(p["wikidata"]))
        for r in p.get("source_refs") or []:
            exist_src.add((r.get("source"), str(r.get("source_id"))))
            if r.get("source") == "wikidata":
                exist_wd.add(str(r.get("source_id")))

    print("Scanning OSM named ways in Yasamal…")
    handler = OsmWayCollector(geom)
    handler.apply_file(str(OSM_PBF), locations=True)
    print(f"  ways in polygon: {len(handler.ways)}")

    added = []
    skipped_dup = []
    skipped_wd = []

    for w in handler.ways:
        sid = f"way/{w['osm_id']}"
        pid = cid("place", "osm", "way", str(w["osm_id"]))
        if ("osm", sid) in exist_src or pid in exist_ids:
            skipped_dup.append(sid)
            continue
        wd = w.get("wikidata")
        if wd and wd in exist_wd:
            skipped_wd.append({"sid": sid, "name": w["name"], "wikidata": wd})
            continue

        rec = {
            "id": pid,
            "name": w["name"],
            "name_normalized": norm(w["name"]),
            "alt_names": [],
            "category": w["category"],
            "coordinates": {"lat": w["lat"], "lon": w["lon"]},
            "area_id": area_id,
            "area_assign_method": "containment_verified",
            "area_assign_status": "verified",
            "confidence": None,
            "status": "silver",
            "source_refs": [
                {
                    "source": "osm",
                    "source_id": sid,
                    "release": OSM_RELEASE,
                    "source_category": w["raw"],
                }
            ],
        }
        if wd:
            rec["wikidata"] = wd
            rec["source_refs"].append(
                {
                    "source": "wikidata",
                    "source_id": wd,
                    "release": None,
                    "source_category": None,
                }
            )
            exist_wd.add(wd)

        places.append(rec)
        exist_ids.add(pid)
        exist_src.add(("osm", sid))
        added.append(
            {
                "name": w["name"],
                "category": w["category"],
                "sid": sid,
                "wikidata": wd,
            }
        )

    existing["places"] = places
    write_json(path, existing)

    idx = load_json(OUT / "places" / "index.json")
    old = idx["by_rayon"][RAYON_KEY]["count"]
    delta = len(places) - old
    idx["by_rayon"][RAYON_KEY]["count"] = len(places)
    idx["total"] = idx.get("total", 0) + delta
    bc = idx.setdefault("by_category", {})
    for a in added:
        bc[a["category"]] = bc.get(a["category"], 0) + 1
    write_json(OUT / "places" / "index.json", idx)

    report = {
        "rayon": RAYON_KEY,
        "baseline": BASELINE,
        "before_file_count": old,
        "osm_ways_scanned": len(handler.ways),
        "added_count": len(added),
        "added": added,
        "skipped_dup_source": skipped_dup,
        "skipped_wikidata_match": skipped_wd,
        "after": len(places),
        "by_category_added": dict(Counter(a["category"] for a in added)),
        "index_total": idx["total"],
    }
    write_json(OUT / "reviews" / "landmark_yasamal_candidates.json", report)

    print("=" * 50)
    print(f"Yasamal: {old} -> {len(places)} (+{len(added)})")
    print(f"  skipped source_id dup: {len(skipped_dup)}")
    print(f"  skipped wikidata match: {len(skipped_wd)}")
    print(f"  cats: {report['by_category_added']}")
    for a in added:
        print(f"  + {a['category']:12} {a['sid']:18} {a['name']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
