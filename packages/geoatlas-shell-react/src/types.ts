import type { CSSProperties, ReactNode } from "react";

export type GeoAtlasTheme = "light" | "dark" | "system";

/** `default` = floating glass; `form` = top toolbar + map below (real estate). */
export type GeoAtlasShellVariant = "default" | "form";

export type GeoAtlasShellLabels = {
  brand: string;
  collapse: string;
  expand: string;
  searchHint: string;
  developer: string;
  tabMetadata: string;
  tabReview: string;
  tabGeojson: string;
  copy: string;
  copied: string;
  results: string;
  resultsEmpty: string;
  resultsLoading: string;
  zoomIn: string;
  zoomOut: string;
  locate: string;
  layers: string;
  fullscreen: string;
  /** Form variant: open filters aside (medium/mobile) */
  filters: string;
  applyFilters: string;
  closeFilters: string;
};

export const DEFAULT_LABELS: GeoAtlasShellLabels = {
  brand: "GeoAtlas",
  collapse: "Collapse panel",
  expand: "Expand panel",
  searchHint: "⌘K",
  developer: "Developer",
  tabMetadata: "Metadata",
  tabReview: "Review",
  tabGeojson: "GeoJSON",
  copy: "Copy",
  copied: "Copied",
  results: "Places",
  resultsEmpty: "No places in this area",
  resultsLoading: "Loading places…",
  zoomIn: "Zoom in",
  zoomOut: "Zoom out",
  locate: "Locate",
  layers: "Layers",
  fullscreen: "Fullscreen",
  filters: "Filters",
  applyFilters: "Apply",
  closeFilters: "Close filters",
};

export type GeoAtlasShellClassNames = {
  root?: string;
  map?: string;
  control?: string;
  /** Form variant top bar */
  formBar?: string;
  /** Form variant medium/mobile filters aside */
  formAside?: string;
  chips?: string;
  toolbar?: string;
  results?: string;
  status?: string;
  drawer?: string;
};

export type CategoryChip = {
  id: string;
  label: string;
  active?: boolean;
  count?: number;
  onClick: () => void;
};

export type ResultItem = {
  id: string;
  title: string;
  subtitle?: string;
  active?: boolean;
  onClick: () => void;
  onHover?: () => void;
};

export type DeveloperTab = "metadata" | "review" | "geojson";

export type GeoAtlasShellProps = {
  /** Fills parent; map is the hero layer */
  map: ReactNode;
  /** Search field (GlobalSearch etc.) */
  search: ReactNode;
  /** Cascade selects — rendered in 2-col grid */
  cascade: ReactNode;
  /** `default` floating UI; `form` = top toolbar + map (real estate) */
  variant?: GeoAtlasShellVariant;
  theme?: GeoAtlasTheme;
  accentColor?: string;
  className?: string;
  classNames?: GeoAtlasShellClassNames;
  style?: CSSProperties;
  labels?: Partial<GeoAtlasShellLabels>;
  brand?: ReactNode;
  controlCollapsed?: boolean;
  defaultControlCollapsed?: boolean;
  onControlCollapsedChange?: (collapsed: boolean) => void;
  chips?: CategoryChip[];
  /** When set, shows floating results list */
  results?: ResultItem[] | null;
  resultsLoading?: boolean;
  showResults?: boolean;
  status?: ReactNode;
  legend?: ReactNode;
  showDeveloperPanel?: boolean;
  developerOpen?: boolean;
  defaultDeveloperOpen?: boolean;
  onDeveloperOpenChange?: (open: boolean) => void;
  developerTab?: DeveloperTab;
  onDeveloperTabChange?: (tab: DeveloperTab) => void;
  developerBadges?: ReactNode;
  metadataPanel?: ReactNode;
  reviewPanel?: ReactNode;
  geojsonText?: string | null;
  geojsonPanel?: ReactNode;
  onZoomIn?: () => void;
  onZoomOut?: () => void;
  onLocate?: () => void;
  onLayers?: () => void;
  onFullscreen?: () => void;
  showToolbar?: boolean;
};
