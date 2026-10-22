# -*- coding: utf-8 -*-
"""List Abşeron verified children and whether they have a places file."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from enrich_landmark_places import rayon_key_from_boundary  # noqa: E402

areas = json.loads((ROOT / "data/areas/areas.json").read_text(encoding="utf-8"))["areas"]
idx = json.loads((ROOT / "data/places/index.json").read_text(encoding="utf-8"))["by_rayon"]

parent = next(
    a
    for a in areas
    if (a.get("boundary_file") or "").replace("\\", "/").endswith("rayon_absheron.geojson")
)
kids = [
    a
    for a in areas
    if a.get("parent_id") == parent["id"]
    and a.get("parent_status") == "verified"
    and a.get("geom_status") == "verified"
]
kids.sort(key=lambda a: a["name"])

print(f"parent={parent['name']} id={parent['id']}")
print(f"verified+geom children={len(kids)}")
print("---")
rows = []
for a in kids:
    key = rayon_key_from_boundary(a.get("boundary_file"))
    meta = idx.get(key) if key else None
    by_id = [(k, v) for k, v in idx.items() if v.get("area_id") == a["id"]]
    places_path = ROOT / "data" / "places" / f"{key}_all.json" if key else None
    exists = bool(places_path and places_path.exists())
    count = meta["count"] if meta else (by_id[0][1]["count"] if by_id else 0)
    print(
        f"{a['name']:32} type={a['type']:12} key={key or '-':24} "
        f"file={'yes' if exists else 'no':3} count={count}"
    )
    rows.append(
        {
            "name": a["name"],
            "id": a["id"],
            "type": a["type"],
            "key": key,
            "boundary_file": a.get("boundary_file"),
            "has_file": exists,
            "count": count,
            "skip_done": key in ("masazir", "xirdalan"),
        }
    )

out = ROOT / "data/reviews/absheron_children_places_inventory.json"
out.write_text(
    json.dumps({"parent": parent["name"], "children": rows}, ensure_ascii=False, indent=2)
    + "\n",
    encoding="utf-8",
)
print(f"wrote {out}")
