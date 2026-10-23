import { useEffect, useId, useState, type ReactNode } from "react";
import { IconMapPin, IconSliders, IconX } from "./icons";
import { CategoryChips } from "./CategoryChips";
import type { CategoryChip, GeoAtlasShellLabels } from "./types";

type Props = {
  className?: string;
  asideClassName?: string;
  labels: GeoAtlasShellLabels;
  brand?: ReactNode;
  search: ReactNode;
  cascade: ReactNode;
  chips: CategoryChip[];
  chipsClassName?: string;
  /** When true (medium/mobile host), cascade+chips live in the side panel */
  compactFilters?: boolean;
};

/** Top toolbar for `variant="form"` — desktop inline; medium/mobile aside. */
export function FormBar({
  className = "",
  asideClassName = "",
  labels,
  brand,
  search,
  cascade,
  chips,
  chipsClassName = "",
  compactFilters = false,
}: Props) {
  const [asideOpen, setAsideOpen] = useState(false);
  const panelId = useId();

  useEffect(() => {
    if (!compactFilters) setAsideOpen(false);
  }, [compactFilters]);

  useEffect(() => {
    if (!asideOpen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setAsideOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [asideOpen]);

  const filtersBody = (
    <>
      <div className="geoatlas-form-bar__cascade">{cascade}</div>
      {!!chips.length && (
        <CategoryChips className={chipsClassName} chips={chips} />
      )}
    </>
  );

  return (
    <>
      <header
        className={`geoatlas-form-bar${compactFilters ? " is-compact" : ""} ${className}`.trim()}
        aria-label={labels.brand}
      >
        <div className="geoatlas-form-bar__top">
          <div className="geoatlas-form-bar__brand">
            {brand ?? (
              <>
                <span className="geoatlas-control__logo" aria-hidden>
                  <IconMapPin size={16} />
                </span>
                <h1 className="geoatlas-control__title">{labels.brand}</h1>
              </>
            )}
          </div>
          <div className="geoatlas-form-bar__search geoatlas-control__search">
            {search}
          </div>
          {compactFilters && (
            <button
              type="button"
              className="geoatlas-form-bar__filters-btn geoatlas-btn"
              aria-expanded={asideOpen}
              aria-controls={panelId}
              onClick={() => setAsideOpen(true)}
            >
              <IconSliders size={16} />
              <span>{labels.filters}</span>
            </button>
          )}
        </div>

        {!compactFilters && (
          <div className="geoatlas-form-bar__inline">{filtersBody}</div>
        )}
      </header>

      {compactFilters && (
        <>
          <div
            className={`geoatlas-form-aside-scrim${asideOpen ? " is-open" : ""}`.trim()}
            aria-hidden={!asideOpen}
            onClick={() => setAsideOpen(false)}
          />

          <aside
            id={panelId}
            className={`geoatlas-form-aside${asideOpen ? " is-open" : ""} ${asideClassName}`.trim()}
            aria-label={labels.filters}
            aria-hidden={!asideOpen}
          >
            <div className="geoatlas-form-aside__header">
              <h2 className="geoatlas-form-aside__title">{labels.filters}</h2>
              <button
                type="button"
                className="geoatlas-icon-btn is-sm"
                aria-label={labels.closeFilters}
                onClick={() => setAsideOpen(false)}
              >
                <IconX size={16} />
              </button>
            </div>

            <div className="geoatlas-form-aside__body">{filtersBody}</div>

            <div className="geoatlas-form-aside__footer">
              <button
                type="button"
                className="geoatlas-form-aside__apply geoatlas-btn"
                onClick={() => setAsideOpen(false)}
              >
                {labels.applyFilters}
              </button>
            </div>
          </aside>
        </>
      )}
    </>
  );
}
