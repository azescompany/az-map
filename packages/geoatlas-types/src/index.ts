export type SourceName = "overture" | "osm" | "geonames";

export type ParentStatus =
  | "verified"
  | "inferred_spatial"
  | "conflict"
  | "missing"
  | "partial";

export type GeomStatus = "verified" | "partial" | "missing";

export type AreaType =
  | "country"
  | "region"
  | "city"
  | "rayon"
  | "settlement"
  | "neighborhood"
  | "other";

export type CenterMethod =
  | "rep_point"
  | "centroid"
  | "osm_place_node"
  | "geonames"
  | "manual";

export interface SourceRef {
  source: SourceName;
  source_id: string;
  release: string;
  role?: string;
  match_method?: string;
  note?: string;
  wikidata?: string;
  source_category?: string;
  overture_parent_id?: string;
}

export interface Coordinates {
  lat: number;
  lon: number;
}

export interface Area {
  id: string;
  name: string;
  name_normalized: string;
  alt_names: string[];
  type: AreaType;
  subtype: string | null;
  parent_id: string | null;
  parent_status: ParentStatus;
  geom_status: GeomStatus;
  center: Coordinates | null;
  center_method: CenterMethod | string | null;
  wikidata: string | null;
  population: number | null;
  population_source: string | null;
  /** [minLon, minLat, maxLon, maxLat] */
  bbox: number[] | null;
  source_refs: SourceRef[];
  notes: string | null;
  boundary_file: string | null;
}

export type PlaceCategory =
  | "historic"
  | "park"
  | "museum"
  | "monument"
  | "tourism"
  | "culture"
  | "religious"
  | "stadium"
  | "education"
  | "government"
  | "other_poi";

export interface Place {
  id: string;
  name: string;
  name_normalized: string;
  alt_names: string[];
  category: PlaceCategory | string;
  coordinates: Coordinates;
  area_id: string | null;
  area_assign_method: string | null;
  area_assign_status: ParentStatus | string | null;
  confidence: number | null;
  status: string;
  source_refs: SourceRef[];
}

export interface ReviewItem {
  id: string;
  kind: string;
  entity: string;
  detail: string;
  status: string;
  overture_id?: string;
  overture_parent_id?: string;
}

export interface Manifest {
  name: string;
  dataset_version: string;
  generated_at: string;
  coverage: {
    scope: string;
    description: string;
    areas: number;
    boundaries: number;
    places: number;
    reviews: number;
  };
  sources: Record<string, Record<string, string>>;
  basemap: {
    provider: string;
    url: string;
    note: string;
  };
  hierarchy_policy: Record<string, unknown>;
}

export interface AreaCollection {
  type: "AreaCollection";
  areas: Area[];
}

export interface PlaceCollection {
  area_id?: string;
  places: Place[];
  category?: string;
}
