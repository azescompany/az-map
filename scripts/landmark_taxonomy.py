# -*- coding: utf-8 -*-
"""Shared OSM / Overture → normalized landmark category map."""
from __future__ import annotations

# Normalized categories (UI + Place.category)
CATEGORIES = [
    "education",
    "shop",
    "market",
    "healthcare",
    "food",
    "services",
    "transport",
    "religious",
    "culture",
    "historic",
    "park",
    "museum",
    "monument",
    "tourism",
    "sport",
    "government",
    "other_poi",
]

# Overture taxonomy.primary / basic_category → normalized
OVERTURE_TAXONOMY: dict[str, str] = {
    # legacy / culture
    "historic_site": "historic",
    "castle": "historic",
    "monument": "monument",
    "landmark": "monument",
    "park": "park",
    "garden": "park",
    "beach": "park",
    "plaza": "park",
    "museum": "museum",
    "tourist_attraction": "tourism",
    "viewpoint": "tourism",
    "hotel": "tourism",
    "lodging": "tourism",
    "arts_and_entertainment": "culture",
    "gallery": "culture",
    "art_gallery": "culture",
    "library": "culture",
    "theater": "culture",
    "cinema": "culture",
    "stadium_arena": "sport",
    "gym": "sport",
    "muslim_place_of_worship": "religious",
    "christian_church": "religious",
    "christian_place_of_worship": "religious",
    "place_of_worship": "religious",
    # education
    "school": "education",
    "preschool": "education",
    "college_university": "education",
    "education": "education",
    "language_school": "education",
    # shop / market
    "shopping": "shop",
    "grocery_store": "shop",
    "clothing_store": "shop",
    "womens_clothing_store": "shop",
    "electronics_store": "shop",
    "furniture_store": "shop",
    "shoe_store": "shop",
    "jewelry_store": "shop",
    "beauty_supply_store": "shop",
    "flowers_and_gifts_store": "shop",
    "shopping_mall": "shop",
    "auto_parts_store": "shop",
    "marketplace": "market",
    # healthcare
    "hospital": "healthcare",
    "health_care": "healthcare",
    "pharmacy": "healthcare",
    "dental_clinic": "healthcare",
    "doctors_office": "healthcare",
    # food
    "restaurant": "food",
    "cafe": "food",
    "coffee_shop": "food",
    "fast_food_restaurant": "food",
    "bakery": "food",
    "bar": "food",
    "pub": "food",
    # services
    "beauty_salon": "services",
    "spa": "services",
    "bank_or_credit_union": "services",
    "laundry": "services",
    "hair_salon": "services",
    # government
    "government_office": "government",
    # transport-ish
    "gas_station": "transport",
    "parking": "transport",
}

SHOP_VALUES_MARKET = frozenset({"marketplace", "market"})

AMENITY_MAP: dict[str, str] = {
    "school": "education",
    "kindergarten": "education",
    "college": "education",
    "university": "education",
    "language_school": "education",
    "marketplace": "market",
    "hospital": "healthcare",
    "clinic": "healthcare",
    "doctors": "healthcare",
    "pharmacy": "healthcare",
    "dentist": "healthcare",
    "restaurant": "food",
    "cafe": "food",
    "fast_food": "food",
    "bakery": "food",
    "bar": "food",
    "pub": "food",
    "hairdresser": "services",
    "bank": "services",
    "atm": "services",
    "bus_station": "transport",
    "ferry_terminal": "transport",
    "parking": "transport",
    "place_of_worship": "religious",
    "theatre": "culture",
    "cinema": "culture",
    "library": "culture",
    "arts_centre": "culture",
    "townhall": "government",
    "courthouse": "government",
    "police": "government",
    "fire_station": "government",
}

LEISURE_MAP: dict[str, str] = {
    "park": "park",
    "garden": "park",
    "nature_reserve": "park",
    "stadium": "sport",
    "sports_centre": "sport",
    "pitch": "sport",
}

TOURISM_MAP: dict[str, str] = {
    "museum": "museum",
    "attraction": "tourism",
    "viewpoint": "tourism",
    "zoo": "tourism",
    "theme_park": "tourism",
    "artwork": "monument",
    "hotel": "tourism",
    "guest_house": "tourism",
}


def classify_osm_tags(tags: dict) -> str | None:
    """Return normalized category for named OSM feature tags, or None."""
    if not tags:
        return None
    if "historic" in tags:
        h = tags.get("historic")
        if h in ("monument", "memorial"):
            return "monument"
        return "historic"
    t = tags.get("tourism")
    if t in TOURISM_MAP:
        return TOURISM_MAP[t]
    a = tags.get("amenity")
    if a in AMENITY_MAP:
        return AMENITY_MAP[a]
    shop = tags.get("shop")
    if shop:
        if shop in SHOP_VALUES_MARKET:
            return "market"
        return "shop"
    leisure = tags.get("leisure")
    if leisure in LEISURE_MAP:
        return LEISURE_MAP[leisure]
    if tags.get("aeroway") == "aerodrome":
        return "transport"
    office = tags.get("office")
    if office:
        return "other_poi"
    return None


def classify_overture(raw: str | None) -> str | None:
    if not raw:
        return None
    return OVERTURE_TAXONOMY.get(raw.strip())


# Backward-compatible alias used by extract_baki_district_places
def classify_osm_notable(tags) -> str | None:
    return classify_osm_tags(dict(tags) if tags is not None else {})
