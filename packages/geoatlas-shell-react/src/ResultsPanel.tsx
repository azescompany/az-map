import type { GeoAtlasShellLabels, ResultItem } from "./types";

type Props = {
  className?: string;
  labels: GeoAtlasShellLabels;
  items: ResultItem[];
  loading?: boolean;
};

export function ResultsPanel({
  className = "",
  labels,
  items,
  loading,
}: Props) {
  return (
    <aside
      className={`geoatlas-results geoatlas-glass ${className}`.trim()}
      aria-label={labels.results}
    >
      <div className="geoatlas-results__header">
        <span>{labels.results}</span>
        <span style={{ fontVariantNumeric: "tabular-nums", opacity: 0.7 }}>
          {loading ? "…" : items.length}
        </span>
      </div>
      {loading ? (
        <div className="geoatlas-results__loading" aria-busy="true">
          <div className="geoatlas-skeleton" />
          <div className="geoatlas-skeleton" />
          <div className="geoatlas-skeleton" />
          <p>{labels.resultsLoading}</p>
        </div>
      ) : !items.length ? (
        <div className="geoatlas-results__empty">{labels.resultsEmpty}</div>
      ) : (
        <ul className="geoatlas-results__list">
          {items.map((item) => (
            <li key={item.id}>
              <button
                type="button"
                className={`geoatlas-results__item${item.active ? " is-active" : ""}`}
                onClick={item.onClick}
                onMouseEnter={item.onHover}
              >
                <div className="geoatlas-results__name">{item.title}</div>
                {item.subtitle && (
                  <div className="geoatlas-results__meta">{item.subtitle}</div>
                )}
              </button>
            </li>
          ))}
        </ul>
      )}
    </aside>
  );
}
