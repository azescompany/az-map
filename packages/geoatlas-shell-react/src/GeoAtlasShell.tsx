import { useEffect, useMemo, useState } from "react";
import { CategoryChips } from "./CategoryChips";
import { ControlCard } from "./ControlCard";
import { DeveloperDrawer } from "./DeveloperDrawer";
import { MapToolbar } from "./MapToolbar";
import { ResultsPanel } from "./ResultsPanel";
import {
  DEFAULT_LABELS,
  type DeveloperTab,
  type GeoAtlasShellProps,
} from "./types";

function resolveSearchHint(): string {
  if (typeof navigator === "undefined") return "Ctrl K";
  const mac = /Mac|iPhone|iPad|iPod/.test(navigator.platform);
  return mac ? "⌘K" : "Ctrl K";
}

export function GeoAtlasShell({
  map,
  search,
  cascade,
  theme = "dark",
  accentColor,
  className = "",
  classNames,
  style,
  labels: labelsProp,
  brand,
  controlCollapsed: controlCollapsedProp,
  defaultControlCollapsed = false,
  onControlCollapsedChange,
  chips = [],
  results = null,
  resultsLoading = false,
  showResults,
  status,
  legend,
  showDeveloperPanel = true,
  developerOpen: developerOpenProp,
  defaultDeveloperOpen = false,
  onDeveloperOpenChange,
  developerTab: developerTabProp,
  onDeveloperTabChange,
  developerBadges,
  metadataPanel,
  reviewPanel,
  geojsonText,
  geojsonPanel,
  onZoomIn,
  onZoomOut,
  onLocate,
  onLayers,
  onFullscreen,
  showToolbar = true,
}: GeoAtlasShellProps) {
  const [controlCollapsed, setControlCollapsed] = useState(
    defaultControlCollapsed,
  );
  const [developerOpen, setDeveloperOpen] = useState(defaultDeveloperOpen);
  const [developerTab, setDeveloperTab] = useState<DeveloperTab>("metadata");

  const collapsed = controlCollapsedProp ?? controlCollapsed;
  const drawerOpen = developerOpenProp ?? developerOpen;
  const tab = developerTabProp ?? developerTab;

  const labels = useMemo(
    () => ({
      ...DEFAULT_LABELS,
      searchHint: resolveSearchHint(),
      ...labelsProp,
    }),
    [labelsProp],
  );

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        const root = document.querySelector(
          ".geoatlas-control__search input",
        ) as HTMLInputElement | null;
        root?.focus();
        if (collapsed) {
          onControlCollapsedChange?.(false);
          if (controlCollapsedProp === undefined) setControlCollapsed(false);
        }
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [collapsed, controlCollapsedProp, onControlCollapsedChange]);

  const rootStyle = {
    ...style,
    ...(accentColor
      ? ({ ["--geoatlas-color-accent" as string]: accentColor } as const)
      : null),
  };

  const resultsVisible =
    showResults ?? (results != null || resultsLoading);

  const hasToolbar =
    showToolbar &&
    !!(onZoomIn || onZoomOut || onLocate || onLayers || onFullscreen);

  return (
    <div
      className={`geoatlas-shell ${className} ${classNames?.root ?? ""}`.trim()}
      data-theme={theme}
      style={rootStyle}
    >
      <div className={`geoatlas-shell__map ${classNames?.map ?? ""}`.trim()}>
        {map}
      </div>

      <div
        className={`geoatlas-left${collapsed ? " is-collapsed" : ""}`.trim()}
      >
        <ControlCard
          className={classNames?.control}
          collapsed={collapsed}
          onCollapsedChange={(v) => {
            onControlCollapsedChange?.(v);
            if (controlCollapsedProp === undefined) setControlCollapsed(v);
          }}
          labels={labels}
          brand={brand}
          search={search}
          cascade={cascade}
        />

        {!!chips.length && (
          <CategoryChips className={classNames?.chips} chips={chips} />
        )}
      </div>

      {hasToolbar && (
        <MapToolbar
          className={classNames?.toolbar}
          labels={labels}
          onZoomIn={onZoomIn}
          onZoomOut={onZoomOut}
          onLocate={onLocate}
          onLayers={onLayers}
          onFullscreen={onFullscreen}
        />
      )}

      {resultsVisible && (
        <ResultsPanel
          className={classNames?.results}
          labels={labels}
          items={results ?? []}
          loading={resultsLoading}
        />
      )}

      {(status || legend) && (
        <div className={`geoatlas-status ${classNames?.status ?? ""}`.trim()}>
          {status}
          {legend}
        </div>
      )}

      {showDeveloperPanel && (
        <DeveloperDrawer
          className={classNames?.drawer}
          open={drawerOpen}
          onOpenChange={(v) => {
            onDeveloperOpenChange?.(v);
            if (developerOpenProp === undefined) setDeveloperOpen(v);
          }}
          tab={tab}
          onTabChange={(t) => {
            onDeveloperTabChange?.(t);
            if (developerTabProp === undefined) setDeveloperTab(t);
          }}
          labels={labels}
          badges={developerBadges}
          metadataPanel={metadataPanel}
          reviewPanel={reviewPanel}
          geojsonText={geojsonText}
          geojsonPanel={geojsonPanel}
        />
      )}
    </div>
  );
}
