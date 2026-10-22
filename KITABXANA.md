# GeoAtlas kitabxana yanaşması

Data Git CDN-də (və ya lokal `data/`); npm-də yalnız kod.

## Paketlər

| Paket | Rol |
|---|---|
| `@geoatlas/types` | Area, Place, Manifest tipləri |
| `@geoatlas/data` | `DEFAULT_DATA_BASE`, loaders, places cascade, verified children |
| `@geoatlas/cascade` | Headless parent→child seçim məntiqi |
| `@geoatlas/cascade-react` | `GeoCascadeProvider`, `useGeoCascade`, `GeoCascadeSelect` |
| `@geoatlas/map-react` | `GeoAtlasMap` — AZ clip, sərhəd, mərkəz, places |
| `@geoatlas/shell-react` | Floating glass UI — control card, chips, toolbar, developer drawer |
| `@geoatlas/demo` | Referans UI (private qala bilər) |

## Consumer (xəritəsiz — real estate)

```tsx
import { DEFAULT_DATA_BASE } from "@geoatlas/data";
import {
  GeoCascadeProvider,
  GeoCascadeSelect,
  useGeoCascade,
} from "@geoatlas/cascade-react";

function Filters() {
  const { leaf, leafCenter, boundary, places } = useGeoCascade();
  // leafCenter.lat/lon · boundary GeoJSON · named places for leaf
  return (
    <>
      <GeoCascadeSelect level="city" />
      <GeoCascadeSelect level="rayon" />
      <GeoCascadeSelect level="neighborhood" />
      <GeoCascadeSelect level="place" />
    </>
  );
}

export function App() {
  return (
    <GeoCascadeProvider dataBase={DEFAULT_DATA_BASE} /* or local "/" */>
      <Filters />
    </GeoCascadeProvider>
  );
}
```

## Consumer (xəritə + premium shell)

```tsx
import { GeoAtlasMap } from "@geoatlas/map-react";
import { GeoAtlasShell } from "@geoatlas/shell-react";
import "maplibre-gl/dist/maplibre-gl.css";
import "@geoatlas/shell-react/styles.css";

<div style={{ height: "100%" }}>
  <GeoAtlasShell
    theme="dark"
    accentColor="#3d9cf0"
    map={
      <GeoAtlasMap
        clipToCountry
        showNavigationControl={false}
        countryBoundary={countryFc}
        selectedBoundary={boundary}
        selectedArea={leaf}
        places={places}
        selectedPlaceId={placeId}
        onPlaceClick={setPlaceId}
        onMapReady={setMap}
      />
    }
    search={<YourSearch />}
    cascade={<YourCascade />}
    chips={chipItems}
    onZoomIn={() => map?.zoomIn()}
    onZoomOut={() => map?.zoomOut()}
    showDeveloperPanel={isDev}
    metadataPanel={…}
    reviewPanel={…}
    geojsonText={json}
  />
</div>
```

See [`packages/geoatlas-shell-react/README.md`](packages/geoatlas-shell-react/README.md) for props + theming.

## Data mənbəyi

- Publish pin: `DEFAULT_DATA_BASE` → jsDelivr `@v0.2.3-national/data/`
- Demo default: CDN; enrich üçün `VITE_GEOATLAS_DATA_BASE=local`

## Davranış

- Dropdown: yalnız `parent_status=verified`
- Places: sonuncu **area** üzrə `loadPlacesForArea` (Bakı=union, rayon=fayl, məhəllə=filter)
- Seçilmiş area: center lat/lon + boundary (lazy)
- Place: coordinates lat/lon
- Map: `clipToCountry` → `maxBounds` Azərbaycan
- Shell: parent-sized container; no `100vh`; `.geoatlas-*` tokens

## UI changelog (shell redesign)

| Removed / changed | Why |
|---|---|
| Top bar `height: 120px; overflow: hidden` | Clipped controls; broken layout |
| Absolute brand over center panel | Collision with dropdowns |
| Map pushed below full-width chrome | Map is edge-to-edge hero; UI floats |
| Always-visible bottom developer strip | Slide-up drawer; default closed pill |

## Publish (sonra)

```bash
pnpm install
pnpm --filter @geoatlas/types typecheck
pnpm --filter @geoatlas/data typecheck
pnpm --filter @geoatlas/cascade typecheck
pnpm --filter @geoatlas/cascade-react typecheck
pnpm --filter @geoatlas/map-react typecheck
pnpm --filter @geoatlas/shell-react typecheck
# npm publish per package (version ≈ data tag)
```
