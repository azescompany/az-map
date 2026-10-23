# 04 — Selection contract

TypeScript-like sketches only (not production code). Implement later in `@geoatlas/data` / cascade.

Hard rules: [PROMPT](./PROMPT.md). Places loading: [05](./05-place-sources-and-neighborhoods.md).

## Types

```ts
type EntityRef =
  | { kind: "area"; id: string }
  | { kind: "place"; id: string; parentAreaId: string };

type LatLon = { lat: number; lon: number };

/** Center always required on resolved AreaRecord for selectable entities. */
type AreaRecord = {
  id: string;
  name: string;
  type: string;
  parent_id: string | null;
  parent_status: string;
  geom_status: "verified" | "partial" | "conflict" | "missing" | string;
  center: LatLon; // required — CenterMissing if absent
  center_status: string | null;
  bbox: [number, number, number, number] | null;
  boundary_ref: string | null;
};

type BoundaryState =
  | { mode: "exact"; geojson: GeoJSON.FeatureCollection }   // geom_status verified
  | { mode: "partial"; geojson: GeoJSON.FeatureCollection } // partial/conflict with file
  | { mode: "none"; reason: "missing_geometry" };           // source has no geometry

type PlacesBasis = "area_id" | "polygon" | "bbox_approx" | "unavailable";

type PlacesStatus =
  | { state: "ready"; places: PlaceRecord[]; basis: PlacesBasis; failedAreaIds: string[] }
  | { state: "loading" }
  | { state: "failed"; failedAreaIds: string[]; error: string };

type AreaSelection = {
  area: AreaRecord;
  boundary: BoundaryState;
  places: PlacesStatus;
  display: {
    /** Customer-visible when mode is partial or basis is bbox_approx — see open questions for copy */
    boundaryNotice: { az: string; en: string } | null;
    placesBasisNotice: { az: string; en: string } | null;
  };
  ready: boolean; // true only when boundary resolved (exact|partial|none) AND places not loading
};

type PlaceRecord = {
  id: string;
  name: string;
  category: string | null;
  coordinates: LatLon;
  area_id: string;
};

type PlaceSelection = {
  place: PlaceRecord;
  parentArea: AreaSelection; // MUST include parent center + full boundary state
};

type SelectError =
  | { code: "BoundaryUnavailable"; areaId: string; cause: string }
  | { code: "PinMismatch"; expected: string; actual: string }
  | { code: "CenterMissing"; areaId: string }
  | { code: "Aborted" }
  | { code: "NotFound"; ref: EntityRef };

type SelectProgress =
  | { phase: "catalog" }
  | { phase: "boundary"; areaId: string }
  | { phase: "places"; areaId: string; shard?: string }
  | { phase: "filter"; basis: PlacesBasis };

declare function selectEntity(
  ref: EntityRef,
  opts: {
    signal?: AbortSignal;
    onProgress?: (p: SelectProgress) => void;
  },
): Promise<AreaSelection | PlaceSelection>;
```

## Resolution rules

1. **Await semantics:** The Promise resolves only when boundary is fully loaded into `BoundaryState` (`exact` / `partial` with complete GeoJSON bytes, or `none`). It **rejects** with `BoundaryUnavailable` on fetch/parse failure when a boundary file was expected. `none` is allowed **only** when the source area has no geometry (`geom_status=missing` or no `boundary_ref`).
2. **Partial vs exact:** Verbatim GeoJSON in both; UI must surface incomplete trust via `display.boundaryNotice` and map paint ([02](./02-architecture.md)).
3. **Center:** If catalog center missing for a selectable area → reject `CenterMissing` (data bug; log in [DATA-ISSUES](./worker/DATA-ISSUES.md), do not invent).
4. **Place selection:** Always embed `parentArea` with parent `center` + boundary state. Place `coordinates` required (finite lat/lon).
5. **Places `basis`:** Prefer `area_id` match; P1+ hoods use `polygon` after bbox prefilter; if only AABB used, `bbox_approx` (never present as exact). Union shard failures → `failedAreaIds` (partial union must not look complete — see [10](./10-risks.md)).
6. **Abort:** In-flight select aborted → `Aborted`; no state tear from stale responses.
7. **Pin:** Manifest `dataset_version` must match pin context or `PinMismatch`.

## UI mapping (existing demo)

Today: `boundaryDisplayMode` → exact / partial_outline / none. Contract `BoundaryState.mode` aligns. Customer mode must show notices, not only developer badges ([14](./14-open-questions.md)).
