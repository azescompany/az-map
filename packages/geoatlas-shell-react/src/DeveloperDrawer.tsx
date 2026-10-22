import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import { IconCode, IconCopy } from "./icons";
import type { DeveloperTab, GeoAtlasShellLabels } from "./types";

type Props = {
  className?: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  tab: DeveloperTab;
  onTabChange: (tab: DeveloperTab) => void;
  labels: GeoAtlasShellLabels;
  badges?: ReactNode;
  metadataPanel?: ReactNode;
  reviewPanel?: ReactNode;
  geojsonText?: string | null;
  geojsonPanel?: ReactNode;
};

export function DeveloperDrawer({
  className = "",
  open,
  onOpenChange,
  tab,
  onTabChange,
  labels,
  badges,
  metadataPanel,
  reviewPanel,
  geojsonText,
  geojsonPanel,
}: Props) {
  const [copyState, setCopyState] = useState<"idle" | "ok" | "err">("idle");

  useEffect(() => {
    setCopyState("idle");
  }, [geojsonText, tab]);

  async function copyJson() {
    if (!geojsonText) return;
    try {
      await navigator.clipboard.writeText(geojsonText);
      setCopyState("ok");
    } catch {
      setCopyState("err");
    }
  }

  return (
    <>
      {!open && (
        <button
          type="button"
          className="geoatlas-dev-pill"
          onClick={() => onOpenChange(true)}
        >
          <span className="geoatlas-dev-pill__dot" />
          {labels.developer}
          <IconCode size={16} />
        </button>
      )}

      <aside
        className={`geoatlas-drawer geoatlas-glass${open ? " is-open" : ""} ${className}`.trim()}
        aria-hidden={!open}
        aria-label={labels.developer}
      >
        <div
          className="geoatlas-drawer__handle"
          role="button"
          tabIndex={0}
          aria-label="Close developer panel"
          onClick={() => onOpenChange(false)}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") onOpenChange(false);
          }}
        >
          <div className="geoatlas-drawer__handle-bar" />
        </div>

        <div className="geoatlas-drawer__toolbar">
          <div className="geoatlas-badge-row">{badges}</div>
          <button
            type="button"
            className="geoatlas-btn"
            onClick={() => onOpenChange(false)}
          >
            Hide
          </button>
        </div>

        <div className="geoatlas-drawer__tabs" role="tablist">
          {(
            [
              ["metadata", labels.tabMetadata],
              ["review", labels.tabReview],
              ["geojson", labels.tabGeojson],
            ] as const
          ).map(([id, label]) => (
            <button
              key={id}
              type="button"
              role="tab"
              aria-selected={tab === id}
              className={`geoatlas-drawer__tab${tab === id ? " is-active" : ""}`}
              onClick={() => onTabChange(id)}
            >
              {label}
            </button>
          ))}
        </div>

        <div className="geoatlas-drawer__body" role="tabpanel">
          {tab === "metadata" && metadataPanel}
          {tab === "review" && reviewPanel}
          {tab === "geojson" &&
            (geojsonPanel ?? (
              <div>
                <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: 8 }}>
                  <button
                    type="button"
                    className="geoatlas-btn"
                    onClick={() => void copyJson()}
                    disabled={!geojsonText}
                  >
                    <IconCopy size={14} />
                    {copyState === "ok" ? labels.copied : labels.copy}
                  </button>
                </div>
                {geojsonText ? (
                  <pre className="geoatlas-json">{geojsonText}</pre>
                ) : (
                  <p className="meta">Select an area or place to view GeoJSON.</p>
                )}
              </div>
            ))}
        </div>
      </aside>
    </>
  );
}
