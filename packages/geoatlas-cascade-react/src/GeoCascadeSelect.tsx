import type { CascadeLevel } from "@geoatlas/cascade";
import { useGeoCascade } from "./context";

const LABELS: Partial<Record<CascadeLevel, string>> = {
  city: "Şəhər / rayon",
  rayon: "Rayon",
  neighborhood: "Məhəllə / qəsəbə",
  microhood: "Mikrorayon / məhəllə",
  place: "Tanınmış məkan",
};

export type GeoCascadeSelectProps = {
  level: CascadeLevel;
  label?: string;
  placeholder?: string;
  className?: string;
  disabled?: boolean;
};

/** Minimal native &lt;select&gt; for consumers; demo may use SearchableSelect + useGeoCascade. */
export function GeoCascadeSelect({
  level,
  label,
  placeholder = "— seçin —",
  className,
  disabled,
}: GeoCascadeSelectProps) {
  const ctx = useGeoCascade();

  if (level === "rayon" && !ctx.showRayon) return null;
  if (level === "microhood" && !ctx.showMicrohood) return null;

  const options =
    level === "city"
      ? ctx.midOptions
      : level === "rayon"
        ? ctx.rayonOptions
        : level === "neighborhood"
          ? ctx.neighborhoodOptions
          : level === "microhood"
            ? ctx.microhoodOptions
            : ctx.placeOptions;

  const value =
    level === "city"
      ? (ctx.selection.cityId ?? "")
      : level === "rayon"
        ? (ctx.selection.rayonId ?? "")
        : level === "neighborhood"
          ? (ctx.selection.neighborhoodId ?? "")
          : level === "microhood"
            ? (ctx.selection.microhoodId ?? "")
            : (ctx.selection.placeId ?? "");

  const isDisabled =
    disabled ||
    ctx.loading ||
    (level === "place" && (ctx.placesLoading || !options.length));

  return (
    <label className={className} style={{ display: "grid", gap: 4 }}>
      <span>{label ?? LABELS[level] ?? level}</span>
      <select
        value={value}
        disabled={isDisabled}
        onChange={(e) => {
          const id = e.target.value || null;
          if (level === "place") ctx.setPlaceId(id);
          else ctx.setLevel(level, id);
        }}
      >
        <option value="">{placeholder}</option>
        {options.map((o) => (
          <option key={o.id} value={o.id}>
            {o.label}
          </option>
        ))}
      </select>
    </label>
  );
}
