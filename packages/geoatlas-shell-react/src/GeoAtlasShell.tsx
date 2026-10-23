import { useEffect, useMemo, useRef, useState } from "react";
import { CategoryChips } from "./CategoryChips";
import { ControlCard } from "./ControlCard";
import { DeveloperDrawer } from "./DeveloperDrawer";
import { FormBar } from "./FormBar";
import { MapToolbar } from "./MapToolbar";
import { ResultsPanel } from "./ResultsPanel";
import {
  DEFAULT_LABELS,
  type DeveloperTab,
  type GeoAtlasShellProps,
} from "./types";

/** Host width ≤ this → form filters move into side panel */
const FORM_COMPACT_MAX = 960;

function resolveSearchHint(): string {
  if (typeof navigator === "undefined") return "Ctrl K";
  const mac = /Mac|iPhone|iPad|iPod/.test(navigator.platform);
  return mac ? "⌘K" : "Ctrl K";
}

export function GeoAtlasShell({
  map,
  search,
  cascade,
  variant = "default",
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
  showDeveloperPanel: showDeveloperPanelProp,
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
  const isForm = variant === "form";
  const showDeveloperPanel =
    showDeveloperPanelProp ?? !isForm;

  const rootRef = useRef<HTMLDivElement | null>(null);
  const [compactFilters, setCompactFilters] = useState(false);

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
    if (!isForm) {
      setCompactFilters(false);
      return;
    }
    const el = rootRef.current;
    if (!el || typeof ResizeObserver === "undefined") return;
    const sync = () => {
      setCompactFilters(el.clientWidth <= FORM_COMPACT_MAX);
    };
    sync();
    const ro = new ResizeObserver(sync);
    ro.observe(el);
    return () => ro.disconnect();
  }, [isForm]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        const root = document.querySelector(
          ".geoatlas-control__search input, .geoatlas-form-bar__search input",
        ) as HTMLInputElement | null;
        root?.focus();
        if (!isForm && collapsed) {
          onControlCollapsedChange?.(false);
          if (controlCollapsedProp === undefined) setControlCollapsed(false);
        }
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [collapsed, controlCollapsedProp, onControlCollapsedChange, isForm]);

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
      ref={rootRef}
      className={`geoatlas-shell ${className} ${classNames?.root ?? ""}`.trim()}
      data-theme={theme}
      data-variant={variant}
      data-compact-filters={isForm && compactFilters ? "true" : undefined}
      style={rootStyle}
    >
      {isForm && (
        <FormBar
          className={classNames?.formBar}
          asideClassName={classNames?.formAside}
          labels={labels}
          brand={brand}
          search={search}
          cascade={cascade}
          chips={chips}
          chipsClassName={classNames?.chips}
          compactFilters={compactFilters}
        />
      )}

      <div className="geoatlas-shell__stage">
        <div className={`geoatlas-shell__map ${classNames?.map ?? ""}`.trim()}>
          {map}
        </div>

        {!isForm && (
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
        )}

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
    </div>
  );
}
