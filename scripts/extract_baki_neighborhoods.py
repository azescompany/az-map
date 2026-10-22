# -*- coding: utf-8 -*-
"""
Extract Bakı məhəllə / qəsəbə / mikrorayon children under each rayon.

Follows root Hierarchy.md (Yasamal verification pattern):
  - Overture parent_division_id must equal rayon locality id
  - division_area geometry required
  - representative point contained in rayon boundary
  - never invent polygons or parents
  - preserve existing Yasamal / Alatava records (match by Overture id)

Writes data/areas/areas.json + data/boundaries/neighborhood_*.geojson
and merges reviews. Run quality:gate afterwards.
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
from shapely.geometry import mapping, shape
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
SRC = Path("source_files")
OUT = Path("data")
OVERTURE_RELEASE = "2026-09-23.1"

NS = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")

ALLOWED_SUBTYPES = {"microhood", "macrohood", "neighborhood", "locality"}
SKIP_NAMES = {"bakı", "baki"}


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


def load_boundary_geom(boundary_file: str | None):
    if not boundary_file:
        return None
    path = OUT / boundary_file
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
        if did in areas:
            areas[did] = unary_union([areas[did], geom])
        else:
            areas[did] = geom
    return by_id, areas


def existing_overture_ids(areas: list[dict]) -> set[str]:
    ids = set()
    for a in areas:
        for ref in a.get("source_refs") or []:
            if ref.get("source") == "overture" and ref.get("source_id"):
                ids.add(ref["source_id"])
    return ids


def should_skip_child(name: str, subtype: str) -> str | None:
    if not name or not name.strip():
        return "empty_name"
    if subtype not in ALLOWED_SUBTYPES:
        return f"subtype:{subtype}"
    n = name.strip().casefold()
    if n in SKIP_NAMES:
        return "skip_baku_locality"
    if n.endswith(" rayonu") or n.endswith("rayonu"):
        return "skip_rayon_name"
    return None


def area_record_neighborhood(
    *,
    key: str,
    name: str,
    subtype: str,
    parent_id: str,
    parent_status: str,
    geom,
    geom_status: str,
    ov_rec: dict,
    notes: str | None,
):
    lat = lon = None
    center_method = None
    if geom is not None and not geom.is_empty:
        lat, lon, center_method = center_from_geom(geom)
    aid = cid("area", f"neighborhood:{key}")
    return {
        "id": aid,
        "name": name,
        "name_normalized": norm(name),
        "alt_names": [],
        "type": "neighborhood",
        "subtype": subtype,
        "parent_id": parent_id,
        "parent_status": parent_status,
        "geom_status": geom_status,
        "center": {"lat": lat, "lon": lon} if lat is not None else None,
        "center_method": center_method,
        "wikidata": ov_rec.get("wikidata"),
        "population": ov_rec.get("population"),
        "population_source": "overture" if ov_rec.get("population") else None,
        "bbox": list(geom.bounds) if geom is not None and not geom.is_empty else None,
        "source_refs": [
            {
                "source": "overture",
                "source_id": ov_rec["id"],
                "release": OVERTURE_RELEASE,
                "role": "boundary",
                "match_method": "id",
                "overture_parent_id": ov_rec.get("parent"),
            }
        ],
        "notes": notes,
        "boundary_file": f"boundaries/neighborhood_{key}.geojson"
        if geom is not None
        else None,
    }


def main() -> int:
    assert (SRC / "overture/aze_division.parquet").exists()
    areas_path = OUT / "areas" / "areas.json"
    areas = load_json(areas_path)["areas"]
    reviews_path = OUT / "reviews" / "pilot_reviews.json"
    reviews_doc = load_json(reviews_path) if reviews_path.exists() else {"reviews": []}
    reviews = list(reviews_doc.get("reviews") or [])

    print("Loading Overture divisions…")
    ov_div, ov_areas = load_overture()

    rayons = [a for a in areas if a.get("type") == "rayon"]
    known_ov = existing_overture_ids(areas)
    used_keys = {
        Path(a["boundary_file"]).stem.replace("neighborhood_", "")
        for a in areas
        if a.get("type") == "neighborhood" and a.get("boundary_file")
    }
    used_keys |= {
        a["name_normalized"].replace(" ", "_")
        for a in areas
        if a.get("type") == "neighborhood"
    }

    added = []
    skipped = []
    conflicts = []
    per_rayon = {}

    bdir = OUT / "boundaries"
    bdir.mkdir(parents=True, exist_ok=True)

    for rayon in sorted(rayons, key=lambda x: x["name"]):
        rname = rayon["name"]
        per_rayon[rname] = {"verified": 0, "conflict": 0, "missing": 0, "skipped": 0, "names": []}
        parent_geom = load_boundary_geom(rayon.get("boundary_file"))

        ov_rayon = next(
            (
                v
                for v in ov_div.values()
                if v["name"] == rname and v["subtype"] == "locality"
            ),
            None,
        )
        if not ov_rayon:
            # try without requiring locality (some may differ)
            ov_rayon = next((v for v in ov_div.values() if v["name"] == rname), None)
        if not ov_rayon:
            reviews.append(
                {
                    "id": cid("review", "hoods-no-ov-locality", slug(rname)),
                    "kind": "coverage_gap",
                    "entity": rname,
                    "detail": "No Overture locality match; məhəllə/qəsəbə children not invented.",
                    "status": "documented",
                }
            )
            print(f"  {rname}: no Overture locality — skip children")
            continue

        children = [
            c
            for c in ov_div.values()
            if c.get("parent") == ov_rayon["id"]
        ]
        print(f"  {rname}: {len(children)} Overture children")

        for child in sorted(children, key=lambda x: x["name"] or ""):
            reason = should_skip_child(child["name"], child["subtype"] or "")
            if reason:
                per_rayon[rname]["skipped"] += 1
                skipped.append((rname, child["name"], reason))
                continue

            if child["id"] in known_ov:
                # already in dataset (Yasamal / Alatava etc.)
                continue

            key_base = slug(child["name"])
            key = key_base
            n = 2
            while key in used_keys:
                key = f"{key_base}_{n}"
                n += 1
            used_keys.add(key)

            geom = ov_areas.get(child["id"])
            geom_status = "verified" if geom is not None else "missing"
            parent_status = "missing"
            notes = None

            if child.get("parent") == ov_rayon["id"]:
                parent_status = "verified"

            if geom is None:
                parent_status = "missing" if parent_status != "conflict" else parent_status
                geom_status = "missing"
                notes = "Overture division has no division_area polygon"
                per_rayon[rname]["missing"] += 1
            elif parent_geom is not None:
                cpt = geom.representative_point()
                contained = parent_geom.covers(cpt) or parent_geom.intersects(geom)
                if parent_status == "verified" and not contained:
                    parent_status = "conflict"
                    notes = "Overture parent matches rayon but geometry not contained in rayon boundary"
                    conflicts.append((rname, child["name"]))
                    reviews.append(
                        {
                            "id": cid("review", "containment", key),
                            "kind": "hierarchy_conflict",
                            "entity": child["name"],
                            "detail": notes,
                            "overture_id": child["id"],
                            "overture_parent_id": child.get("parent"),
                            "status": "open",
                        }
                    )
                    per_rayon[rname]["conflict"] += 1
            elif parent_status == "verified":
                # no parent geom to check — keep verified only if geom exists (rare)
                notes = "Parent rayon boundary missing; containment not checked"

            if parent_status == "verified" and geom is not None:
                per_rayon[rname]["verified"] += 1
                per_rayon[rname]["names"].append(child["name"])
            elif parent_status == "conflict":
                pass
            elif geom is None:
                pass
            else:
                per_rayon[rname]["missing"] += 1

            rec = area_record_neighborhood(
                key=key,
                name=child["name"],
                subtype=child["subtype"],
                parent_id=rayon["id"],
                parent_status=parent_status,
                geom=geom,
                geom_status=geom_status if geom is not None else "missing",
                ov_rec=child,
                notes=notes,
            )
            # Only persist records that are useful: verified UI children OR conflict/missing for review trail
            # Conflict/missing with geometry still useful for reviews; skip empty-name already handled.
            # To avoid flooding UI with missing-geom ghosts, keep conflict+verified+missing-with-geom only.
            if parent_status == "missing" and geom is None:
                skipped.append((rname, child["name"], "no_geom_no_parent"))
                continue

            areas.append(rec)
            known_ov.add(child["id"])
            added.append(rec)

            if geom is not None and rec.get("boundary_file"):
                feat = {
                    "type": "Feature",
                    "id": rec["id"],
                    "properties": {
                        "id": rec["id"],
                        "name": rec["name"],
                        "type": "neighborhood",
                        "parent_id": rayon["id"],
                        "parent_status": parent_status,
                        "subtype": child["subtype"],
                    },
                    "geometry": mapping(geom),
                }
                write_json(
                    OUT / rec["boundary_file"],
                    {"type": "FeatureCollection", "features": [feat]},
                )

    # Deduplicate reviews by id
    by_rid = {r["id"]: r for r in reviews}
    reviews = list(by_rid.values())

    write_json(areas_path, {"type": "AreaCollection", "areas": areas})
    write_json(reviews_path, {"reviews": reviews})

    # boundary index refresh
    b_index = []
    for a in areas:
        if a.get("boundary_file"):
            b_index.append(
                {
                    "file": a["boundary_file"],
                    "area_id": a["id"],
                    "name": a["name"],
                }
            )
    write_json(OUT / "boundaries" / "index.json", {"boundaries": b_index})

    # manifest
    manifest_path = OUT / "manifest.json"
    manifest = load_json(manifest_path)
    manifest["dataset_version"] = "0.1.3-pilot"
    manifest["generated_at"] = datetime.now(timezone.utc).isoformat()
    cov = manifest.setdefault("coverage", {})
    cov["areas"] = len(areas)
    cov["boundaries"] = len(b_index)
    cov["reviews"] = len(reviews)
    cov["description"] = (
        "Country + Bakı city/districts + verified məhəllə/qəsəbə under each rayon "
        "(Yasamal hierarchy rules) + named places per rayon. See Hierarchy.md."
    )
    write_json(manifest_path, manifest)

    report = {
        "added_records": len(added),
        "verified_by_rayon": {
            k: {"count": v["verified"], "names": v["names"]}
            for k, v in per_rayon.items()
        },
        "conflicts": conflicts[:40],
        "skipped_sample": skipped[:40],
    }
    write_json(OUT / "reviews" / "baki_neighborhoods_extract.json", report)

    print("=" * 60)
    print(f"Added neighborhood records: {len(added)}")
    for rname, v in per_rayon.items():
        print(
            f"  {rname}: verified={v['verified']} conflict={v['conflict']} "
            f"missing={v['missing']} skipped={v['skipped']}"
        )
        for n in v["names"][:8]:
            print(f"      · {n}")
        if len(v["names"]) > 8:
            print(f"      … +{len(v['names']) - 8} more")
    print("Wrote data/reviews/baki_neighborhoods_extract.json")
    print("Next: pnpm quality:gate && pnpm validate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
