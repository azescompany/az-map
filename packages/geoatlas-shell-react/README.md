# @geoatlas/shell-react

Floating glass UI shell for GeoAtlas maps (Apple Maps / Linear style).  
Sizes to its **parent** (`width/height: 100%`) — not the viewport. CSS is prefixed (`.geoatlas-*`) and uses design tokens + container queries.

## Install

```bash
pnpm add @geoatlas/shell-react @geoatlas/map-react maplibre-gl react react-dom
```

## Minimal usage

```tsx
import { GeoAtlasShell } from "@geoatlas/shell-react";
import "@geoatlas/shell-react/styles.css"; // or import tokens + shell separately
import { GeoAtlasMap } from "@geoatlas/map-react";
import "maplibre-gl/dist/maplibre-gl.css";

export function MapApp() {
  return (
    <div style={{ width: "100%", height: 600 }}>
      <GeoAtlasShell
        theme="dark"
        accentColor="#3d9cf0"
        map={
          <GeoAtlasMap
            clipToCountry
            showNavigationControl={false}
            /* … */
          />
        }
        search={<YourSearch />}
        cascade={<YourCascadeSelects />}
        chips={[
          { id: "all", label: "All", active: true, onClick: () => {} },
        ]}
        showDeveloperPanel
        metadataPanel={<div>…</div>}
        reviewPanel={<div>…</div>}
        geojsonText={jsonStringOrNull}
        onZoomIn={() => map?.zoomIn()}
        onZoomOut={() => map?.zoomOut()}
      />
    </div>
  );
}
```

## Props (high level)

| Prop | Type | Default | Notes |
|------|------|---------|--------|
| `map` | `ReactNode` | required | Hero layer |
| `search` | `ReactNode` | required | Search slot |
| `cascade` | `ReactNode` | required | 2-col grid of selects |
| `variant` | `'default' \| 'form'` | `'default'` | `form` = top toolbar + map; ≤960px host → filters aside |
| `theme` | `'light' \| 'dark' \| 'system'` | `'dark'` | `data-theme` |
| `accentColor` | `string` | — | Sets `--geoatlas-color-accent` |
| `chips` | `CategoryChip[]` | `[]` | Scroll-snap chip row |
| `results` / `resultsLoading` / `showResults` | … | — | Floating list |
| `showDeveloperPanel` | `boolean` | `true` | Bottom sheet + pill |
| `developerOpen` | `boolean` | uncontrolled | Controlled open state |
| `metadataPanel` / `reviewPanel` / `geojsonText` | … | — | Drawer tabs |
| `onZoomIn` / `onZoomOut` / `onLocate` / `onFullscreen` | `() => void` | — | Right toolbar |
| `labels` | `Partial<GeoAtlasShellLabels>` | AZ/EN defaults | i18n |
| `classNames` | object | — | Slot class overrides |

## Theming

```css
.geoatlas-shell {
  --geoatlas-color-accent: #2563eb;
  --geoatlas-radius-lg: 18px;
  --geoatlas-blur: 20px;
}
```

Or:

```tsx
<GeoAtlasShell theme="light" accentColor="#2563eb" … />
```

Tokens live in `@geoatlas/shell-react/tokens.css` (imported by `styles.css`).

## CSS opt-out

Import only tokens and write your own chrome, or override via `classNames` / CSS variables. No global `*` reset escapes the `.geoatlas-shell` root (scoped box-sizing only under the shell).

## Changed vs old demo topbar

| Removed / changed | Why |
|-------------------|-----|
| `height: 120px; overflow: hidden` on topbar | Clipped search + dropdowns + chips |
| Absolute brand overlapping center panel | Collided with controls |
| Full-width top bar pushing the map down | Map is now edge-to-edge hero |
| Fixed bottom developer strip always eating space | Drawer slides up; default closed pill |

## Peer deps

`react`, `react-dom` >= 18. No lucide required (inline SVG icons).
