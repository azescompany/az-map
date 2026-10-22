import {
  IconLayers,
  IconLocate,
  IconMaximize,
  IconMinus,
  IconPlus,
} from "./icons";
import type { GeoAtlasShellLabels } from "./types";

type Props = {
  className?: string;
  labels: GeoAtlasShellLabels;
  onZoomIn?: () => void;
  onZoomOut?: () => void;
  onLocate?: () => void;
  onLayers?: () => void;
  onFullscreen?: () => void;
};

export function MapToolbar({
  className = "",
  labels,
  onZoomIn,
  onZoomOut,
  onLocate,
  onLayers,
  onFullscreen,
}: Props) {
  return (
    <div className={`geoatlas-toolbar ${className}`.trim()} role="toolbar" aria-label="Map controls">
      {onZoomIn && (
        <button
          type="button"
          className="geoatlas-icon-btn"
          aria-label={labels.zoomIn}
          onClick={onZoomIn}
        >
          <IconPlus />
        </button>
      )}
      {onZoomOut && (
        <button
          type="button"
          className="geoatlas-icon-btn"
          aria-label={labels.zoomOut}
          onClick={onZoomOut}
        >
          <IconMinus />
        </button>
      )}
      {onLocate && (
        <button
          type="button"
          className="geoatlas-icon-btn"
          aria-label={labels.locate}
          onClick={onLocate}
        >
          <IconLocate />
        </button>
      )}
      {onLayers && (
        <button
          type="button"
          className="geoatlas-icon-btn"
          aria-label={labels.layers}
          onClick={onLayers}
        >
          <IconLayers />
        </button>
      )}
      {onFullscreen && (
        <button
          type="button"
          className="geoatlas-icon-btn"
          aria-label={labels.fullscreen}
          onClick={onFullscreen}
        >
          <IconMaximize />
        </button>
      )}
    </div>
  );
}
