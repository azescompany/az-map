import type { ReactNode } from "react";
import {
  IconChevronDown,
  IconChevronUp,
  IconMapPin,
} from "./icons";
import type { GeoAtlasShellLabels } from "./types";

type Props = {
  className?: string;
  collapsed: boolean;
  onCollapsedChange: (v: boolean) => void;
  labels: GeoAtlasShellLabels;
  brand?: ReactNode;
  search: ReactNode;
  cascade: ReactNode;
};

export function ControlCard({
  className = "",
  collapsed,
  onCollapsedChange,
  labels,
  brand,
  search,
  cascade,
}: Props) {
  return (
    <section
      className={`geoatlas-control geoatlas-glass${collapsed ? " is-collapsed" : ""} ${className}`.trim()}
      aria-label={labels.brand}
    >
      <div className="geoatlas-control__header">
        <div className="geoatlas-control__brand">
          {brand ?? (
            <>
              <span className="geoatlas-control__logo">
                <IconMapPin size={16} />
              </span>
              <h1 className="geoatlas-control__title">{labels.brand}</h1>
            </>
          )}
        </div>
        <button
          type="button"
          className="geoatlas-icon-btn is-sm"
          aria-expanded={!collapsed}
          aria-label={collapsed ? labels.expand : labels.collapse}
          onClick={() => onCollapsedChange(!collapsed)}
        >
          {collapsed ? <IconChevronDown /> : <IconChevronUp />}
        </button>
      </div>

      <div className="geoatlas-control__body">
        <div className="geoatlas-control__search">
          {search}
          {!collapsed && (
            <div className="geoatlas-control__search-hint">
              <kbd className="geoatlas-kbd">{labels.searchHint}</kbd>
            </div>
          )}
        </div>
        <div className="geoatlas-control__body-extra">
          <div className="geoatlas-control__cascade">{cascade}</div>
        </div>
      </div>
    </section>
  );
}
