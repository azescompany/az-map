export type SourceName = "overture" | "osm" | "geonames";

export type ParentStatus =
  | "verified"
  | "inferred_spatial"
  | "conflict"
  | "missing"
  | "partial";

export type GeomStatus = "verified" | "partial" | "missing" | "conflict";

export type CenterStatus =
  | "verified"
  | "label_fallback"
  | "unverified"
  | "conflict"
  | "missing";

export type AreaType =
  | "country"
  | "region"
  | "city"
  | "rayon"
  | "settlement"
  | "neighborhood"
  | "other";

export type CenterMethod =
  | "interior_representative_point"
  | "rep_point"
  | "centroid"
  | "osm_place_node"
  | "geonames"
  | "source_label_point"
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

/** Area centers prefer latitude/longitude; lat/lon kept for compatibility. */
export interface Coordinates {
  latitude?: number;
  longitude?: number;
  lat?: number;
  lon?: number;
}

export interface PlaceCoordinates {
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
  geom_status_reason?: string | null;
  crs?: string | null;
  geometry_type?: string | null;
  geometry_valid?: boolean | null;
  center: Coordinates | null;
  center_method: CenterMethod | string | null;
  center_status?: CenterStatus | string | null;
  center_within_boundary?: boolean | null;
  wikidata: string | null;
  population: number | null;
  population_source: string | null;
  /** [minLon, minLat, maxLon, maxLat] */
  bbox: number[] | null;
  source_refs: SourceRef[];
  notes: string | null;
  /** Relative path under data/ — prefer this over inlining large polygons */
  boundary_file: string | null;
}

export interface AreaDetail {
  id: string;
  name: string;
  type: AreaType;
  subtype: string | null;
  parent_id: string | null;
  parent_status: ParentStatus;
  geom_status: GeomStatus;
  geom_status_reason?: string | null;
  center: {
    latitude: number;
    longitude: number;
    method: string | null;
    status: string | null;
    within_boundary: boolean | null;
  } | null;
  boundary_url: string | null;
  wikidata: string | null;
  source_refs: SourceRef[];
  children: Area[];
  places: Place[];
  notes: string | null;
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
  coordinates: PlaceCoordinates;
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
