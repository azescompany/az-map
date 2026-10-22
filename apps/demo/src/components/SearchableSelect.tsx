import {
  useEffect,
  useId,
  useMemo,
  useRef,
  useState,
  type KeyboardEvent,
} from "react";
import { normalize } from "@geoatlas/data";
import TruncatedText from "./TruncatedText";

export type SelectOption = { id: string; label: string };

type Props = {
  label: string;
  options: SelectOption[];
  value: string;
  onChange: (id: string) => void;
  disabled?: boolean;
  placeholder?: string;
  emptyHint?: string;
};

export default function SearchableSelect({
  label,
  options,
  value,
  onChange,
  disabled = false,
  placeholder = "— seçin —",
  emptyHint,
}: Props) {
  const listId = useId();
  const rootRef = useRef<HTMLDivElement>(null);
  const [open, setOpen] = useState(false);
  const [filter, setFilter] = useState("");
  const [highlight, setHighlight] = useState(0);
  const [previousValue, setPreviousValue] = useState<string | null>(null);

  const selected = options.find((o) => o.id === value);
  const displayLabel = selected?.label ?? "";

  const filtered = useMemo(() => {
    const q = normalize(filter);
    if (!q) return options;
    return options.filter((o) => normalize(o.label).includes(q));
  }, [options, filter]);

  useEffect(() => {
    if (!open) {
      setFilter("");
      setHighlight(0);
    }
  }, [open]);

  useEffect(() => {
    setHighlight(0);
  }, [filter]);

  useEffect(() => {
    if (!open) return;
    const onDoc = (e: MouseEvent) => {
      if (!rootRef.current?.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, [open]);

  function commit(next: string) {
    if (next === value) {
      setOpen(false);
      return;
    }
    setPreviousValue(value);
    onChange(next);
    setOpen(false);
  }

  function undo() {
    if (previousValue == null || previousValue === value || disabled) return;
    const prev = previousValue;
    setPreviousValue(value);
    onChange(prev);
    setOpen(false);
  }

  const canUndo =
    !disabled && previousValue != null && previousValue !== value;

  function onKeyDown(e: KeyboardEvent) {
    if (disabled) return;
    if (!open && (e.key === "ArrowDown" || e.key === "Enter" || e.key === " ")) {
      e.preventDefault();
      setOpen(true);
      return;
    }
    if (!open) return;
    if (e.key === "Escape") {
      e.preventDefault();
      setOpen(false);
      return;
    }
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setHighlight((h) => Math.min(h + 1, Math.max(filtered.length - 1, 0)));
      return;
    }
    if (e.key === "ArrowUp") {
      e.preventDefault();
      setHighlight((h) => Math.max(h - 1, 0));
      return;
    }
    if (e.key === "Enter") {
      e.preventDefault();
      const opt = filtered[highlight];
      if (opt) commit(opt.id);
      else if (!filter.trim()) commit("");
    }
  }

  return (
    <div className={`field combobox ${disabled ? "disabled" : ""}`} ref={rootRef}>
      <label>{label}</label>
      <div className="combobox-row">
        <button
          type="button"
          className="combobox-trigger"
          disabled={disabled}
          aria-haspopup="listbox"
          aria-expanded={open}
          aria-controls={listId}
          onClick={() => !disabled && setOpen((v) => !v)}
          onKeyDown={onKeyDown}
        >
          <TruncatedText
            text={displayLabel || placeholder}
            className={displayLabel ? undefined : "placeholder"}
          />
          <span className="combobox-caret" aria-hidden>
            ▾
          </span>
        </button>
        <button
          type="button"
          className="combobox-undo"
          disabled={!canUndo}
          title="Əvvəlki seçimə qayıt"
          aria-label="Əvvəlki seçimə qayıt"
          onClick={undo}
        >
          ×
        </button>
      </div>

      {open && !disabled && (
        <div className="combobox-panel">
          <input
            className="combobox-filter"
            value={filter}
            autoFocus
            placeholder="Yazaraq axtar…"
            aria-label={`${label} axtarış`}
            onChange={(e) => setFilter(e.target.value)}
            onKeyDown={onKeyDown}
          />
          <ul id={listId} className="combobox-list" role="listbox">
            <li role="option" aria-selected={value === ""}>
              <button
                type="button"
                className={value === "" ? "on" : ""}
                onClick={() => commit("")}
              >
                <TruncatedText text={placeholder} />
              </button>
            </li>
            {filtered.map((o, i) => (
              <li key={o.id} role="option" aria-selected={o.id === value}>
                <button
                  type="button"
                  className={[
                    o.id === value ? "on" : "",
                    i === highlight ? "hl" : "",
                  ]
                    .filter(Boolean)
                    .join(" ")}
                  onMouseEnter={() => setHighlight(i)}
                  onClick={() => commit(o.id)}
                >
                  <TruncatedText text={o.label} />
                </button>
              </li>
            ))}
            {!filtered.length && (
              <li>
                <div className="empty" style={{ padding: "0.55rem 0.75rem" }}>
                  Nəticə yoxdur
                </div>
              </li>
            )}
          </ul>
        </div>
      )}
      {emptyHint ? <span className="empty">{emptyHint}</span> : null}
    </div>
  );
}
