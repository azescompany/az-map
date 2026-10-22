# Landmark taxonomy (named POI)

Canonical **normalized `category`** values for `data/places/*`.  
Source: `source_files/` OSM tags + Overture `taxonomy.primary` / `basic_category`.  
**Named only** — empty `name` / `names.primary` → skip.

Agent qaydaları: [`.cursor/rules/landmark-agent.mdc`](../.cursor/rules/landmark-agent.mdc) ·
[`LANDMARK.md`](../LANDMARK.md).

**Dublikat:** eyni `source_id` / `place.id` / Wikidata / (≤~30 m + eyni normalize ad) → bir
record. Eyni ad, fərqli yer → saxla; ada görə merge yox.

**Eyni ad:** eyni rayon içində ≥2 → display `Ad (Küçə)`; `addr:street` / Overture address;
`alt_names` = qısa ad; uydurma küçə yox.

`market` = marketplace / bazar; supermarket & grocery → **`shop`** (sabit qayda).

| category | OSM (nümunə) | Overture (nümunə) |
| --- | --- | --- |
| education | amenity=school, kindergarten, college, university, language_school | school, preschool, college_university, education, language_school |
| shop | shop=* (supermarket, convenience, mall, clothes, …) | shopping, grocery_store, clothing_store, shopping_mall, electronics_store, … |
| market | amenity=marketplace; shop=marketplace | marketplace (əgər varsa) |
| healthcare | amenity=hospital, clinic, doctors, pharmacy, dentist | hospital, health_care, pharmacy, dental_clinic, doctors_office |
| food | amenity=restaurant, cafe, fast_food, bakery, bar, pub | restaurant, cafe, coffee_shop, fast_food_restaurant, bakery, bar, pub |
| services | amenity=hairdresser, bank, atm; shop=hairdresser, beauty | beauty_salon, spa, bank_or_credit_union, laundry, … |
| transport | amenity=bus_station, ferry_terminal, parking; aeroway=aerodrome | *(named only)* |
| religious | amenity=place_of_worship | muslim_place_of_worship, christian_*, … |
| culture | amenity=theatre, cinema, library, arts_centre | arts_and_entertainment, theater, cinema, library, art_gallery |
| historic | historic=* | historic_site, castle |
| park | leisure=park, garden, nature_reserve | park, garden, beach, plaza |
| museum | tourism=museum | museum |
| monument | historic=monument / memorial; tourism=artwork | monument, landmark |
| tourism | tourism=attraction, viewpoint, zoo, hotel | tourist_attraction, viewpoint, hotel, lodging |
| sport | leisure=stadium, sports_centre, pitch (named) | stadium_arena, gym |
| government | amenity=townhall, courthouse, police, fire_station | government_office |
| other_poi | digər adlı amenity/tourism/leisure/office (map-ə düşən) | digər map-li primary |

Implementasiya: `scripts/landmark_taxonomy.py` · enrich: `scripts/enrich_landmark_places.py`.
