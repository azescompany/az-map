# -*- coding: utf-8 -*-
"""Standalone OSM node scan for Sumqayıt extract (subprocess)."""
import json
import sys

import osmium

CITY_NODE = 1104258889


def classify(tags):
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


class H(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.node = None
        self.notable = []

    def node(self, n):
        if n.id == CITY_NODE and n.location.valid():
            self.node = {
                "lat": n.location.lat,
                "lon": n.location.lon,
                "wikidata": n.tags.get("wikidata"),
                "population": n.tags.get("population"),
                "name": n.tags.get("name"),
            }
        if not n.tags or not n.location.valid():
            return
        cat = classify(n.tags)
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


def main():
    osm_path, out_path = sys.argv[1], sys.argv[2]
    h = H()
    h.apply_file(osm_path, locations=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"node": h.node, "notable": h.notable}, f, ensure_ascii=False)


if __name__ == "__main__":
    main()
