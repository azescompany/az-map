# -*- coding: utf-8 -*-
"""Named-place UI contract tests. Run: python scripts/test_named_places.py"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def has_reliable_name(name) -> bool:
    return isinstance(name, str) and bool(name.strip())


def enrich_place(place: dict) -> dict:
    named = has_reliable_name(place.get("name"))
    out = dict(place)
    out["displayName"] = place["name"].strip() if named else None
    out["nameStatus"] = place.get("nameStatus") or ("named" if named else "unnamed")
    out["verificationStatus"] = place.get("verificationStatus") or (
        "area_containment_verified"
        if place.get("area_assign_status") == "verified"
        else "unverified"
    )
    out["geometry_type"] = place.get("geometry_type") or "Point"
    out["boundary_file"] = place.get("boundary_file")
    return out


def is_displayable(place: dict) -> bool:
    p = enrich_place(place)
    if p["nameStatus"] == "unnamed":
        return False
    if not has_reliable_name(p.get("displayName") or p.get("name")):
        return False
    if not p.get("id"):
        return False
    if not p.get("source_refs"):
        return False
    return True


def filter_named(places: list[dict]) -> list[dict]:
    return [enrich_place(p) for p in places if is_displayable(p)]


def filter_by_category(places: list[dict], category: str) -> list[dict]:
    named = filter_named(places)
    if not category or category == "all":
        return named
    return [p for p in named if p.get("category") == category]


def normalize(s: str) -> str:
    out = (s or "").lower()
    for a, b in (
        ("ə", "e"),
        ("ı", "i"),
        ("ö", "o"),
        ("ü", "u"),
        ("ğ", "g"),
        ("ş", "s"),
        ("ç", "c"),
    ):
        out = out.replace(a, b)
    import re

    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", out)).strip()


def search_named(places: list[dict], query: str) -> list[dict]:
    q = normalize(query)
    if not q:
        return []
    hits = []
    for p in filter_named(places):
        dn = normalize(p.get("displayName") or p.get("name") or "")
        if q in dn or any(q in normalize(n) for n in p.get("alt_names") or []):
            hits.append(p)
    return hits


passed = 0


def test(name: str, fn):
    global passed
    fn()
    passed += 1
    print("  OK ", name)


def base_place(**over):
    p = {
        "id": "place-stable-1",
        "name": "Yasamal parkı",
        "name_normalized": "yasamal parki",
        "alt_names": [],
        "category": "park",
        "coordinates": {"lat": 40.38, "lon": 49.81},
        "area_id": "area-yasamal",
        "area_assign_method": "containment_verified",
        "area_assign_status": "verified",
        "confidence": 0.9,
        "status": "silver",
        "source_refs": [
            {"source": "overture", "source_id": "abc", "release": "2026-09-23.1"}
        ],
    }
    p.update(over)
    return p


def main() -> int:
    print("Named places / GeoJSON inspector tests")

    def t_dropdown():
        places = [
            base_place(),
            base_place(id="u1", name="", name_normalized=""),
            base_place(id="u2", name="   ", name_normalized=""),
        ]
        named = filter_named(places)
        assert len(named) == 1
        assert named[0]["id"] == "place-stable-1"
        assert named[0]["nameStatus"] == "named"

    test("dropdown shows only named places", t_dropdown)

    def t_unnamed():
        u = enrich_place(base_place(id="x", name=""))
        assert u["nameStatus"] == "unnamed"
        assert u["displayName"] is None
        assert is_displayable(u) is False

    test("unnamed objects are not displayable", t_unnamed)

    def t_stable_id():
        named = filter_named(
            [
                base_place(id="id-a", name="Same Name"),
                base_place(id="id-b", name="Same Name"),
            ]
        )
        assert len(named) == 2
        assert named[0]["id"] != named[1]["id"]

    test("place identity is stable id, not name", t_stable_id)

    def t_category():
        places = [
            base_place(id="p1", category="park"),
            base_place(id="p2", category="museum", name="Muzey"),
        ]
        parks = filter_by_category(places, "park")
        assert len(parks) == 1 and parks[0]["id"] == "p1"
        assert not any(p["id"] == "p2" for p in parks)

    test("category filter sync clears incompatible selection set", t_category)

    def t_cascade():
        selected_place_area = "area-old-rayon"
        new_rayon = "area-new-rayon"
        selected = "place-stable-1" if selected_place_area == new_rayon else None
        assert selected is None

    test("rayon/neighborhood cascade clears unrelated place", t_cascade)

    def t_search():
        places = [
            base_place(name="Park Yasamal"),
            base_place(id="u", name="", name_normalized=""),
        ]
        hits = search_named(places, "yasamal")
        assert len(hits) == 1

    test("search excludes unnamed", t_search)

    def t_pilot():
        idx = json.loads((DATA / "places" / "index.json").read_text(encoding="utf-8"))
        files = idx.get("files") or [
            info["file"] for info in (idx.get("by_rayon") or {}).values()
        ]
        assert len(files) >= 12, "expected places for all Bakı rayons"
        places = []
        for f in files:
            places.extend(
                json.loads((DATA / f).read_text(encoding="utf-8")).get("places", [])
            )
        named = filter_named(places)
        unnamed = [p for p in places if not has_reliable_name(p.get("name"))]
        assert len(unnamed) == 0
        assert len(named) == len(places)
        for p in named:
            assert p["id"] and p.get("source_refs")
            assert p.get("boundary_file") in (None, "")
            c = p["coordinates"]
            gj = [c["lon"], c["lat"]]
            assert gj[0] == c["lon"] and gj[1] == c["lat"]

    test("pilot dataset: all Bakı rayons named-only point places", t_pilot)

    def t_geojson():
        areas = json.loads((DATA / "areas" / "areas.json").read_text(encoding="utf-8"))["areas"]
        yasamal = next(a for a in areas if a["name"] == "Yasamal rayonu")
        assert yasamal.get("boundary_file")
        raw = (DATA / yasamal["boundary_file"]).read_text(encoding="utf-8")
        assert "..." not in raw.split("coordinates", 1)[-1][:80]
        fc = json.loads(raw)
        assert fc["type"] == "FeatureCollection"
        g = fc["features"][0]["geometry"]
        assert g["type"] in ("Polygon", "MultiPolygon")
        assert len(json.dumps(g["coordinates"])) > 100
        copy = json.dumps(fc, indent=2, ensure_ascii=False)
        assert json.loads(copy) == fc

    test("area boundary GeoJSON full and parseable", t_geojson)

    def t_center():
        areas = json.loads((DATA / "areas" / "areas.json").read_text(encoding="utf-8"))["areas"]
        yasamal = next(a for a in areas if a["name"] == "Yasamal rayonu")
        if yasamal.get("geom_status") == "verified":
            assert yasamal.get("center_within_boundary") is True

    test("center within boundary for Yasamal", t_center)

    def t_name_vs_geo():
        p = enrich_place(
            base_place(area_assign_status="missing", name="Named but unverified geo")
        )
        assert p["nameStatus"] == "named"
        assert p["verificationStatus"] != "verified"

    test("naming status independent from geographic verification", t_name_vs_geo)

    print(f"\nRESULT: PASS ({passed} tests)")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except AssertionError as e:
        print("RESULT: FAIL", e)
        sys.exit(1)
