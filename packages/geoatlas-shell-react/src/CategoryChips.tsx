import type { CategoryChip } from "./types";

type Props = {
  className?: string;
  chips: CategoryChip[];
};

export function CategoryChips({ className = "", chips }: Props) {
  if (!chips.length) return null;
  return (
    <div className={`geoatlas-chips ${className}`.trim()} role="toolbar" aria-label="Categories">
      <div className="geoatlas-chips__scroller">
        {chips.map((c) => (
          <button
            key={c.id}
            type="button"
            className={`geoatlas-chip${c.active ? " is-active" : ""}`}
            aria-pressed={!!c.active}
            onClick={c.onClick}
          >
            <span>{c.label}</span>
            {c.count != null && (
              <span className="geoatlas-chip__count">{c.count}</span>
            )}
          </button>
        ))}
      </div>
    </div>
  );
}
