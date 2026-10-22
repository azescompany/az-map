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
import PortalMenu, { isInsideCombo } from "./PortalMenu";

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

/**
 * MUI Autocomplete–style control: type-in-field filter, live list,
 * keyboard ↑↓ Enter Esc, clear ×, popup caret.
 * Menu is portaled above the control card (no card scroll).
 */
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
  const inputId = useId();
  const rootRef = useRef<HTMLDivElement>(null);
  const anchorRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const listRef = useRef<HTMLUListElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const [open, setOpen] = useState(false);
  const [inputValue, setInputValue] = useState("");
  const [highlight, setHighlight] = useState(0);
  const [previousValue, setPreviousValue] = useState<string | null>(null);

  const selected = options.find((o) => o.id === value);
  const selectedLabel = selected?.label ?? "";

  const filtered = useMemo(() => {
    const q = normalize(inputValue);
    if (!q) return options;
    return options.filter((o) => normalize(o.label).includes(q));
  }, [options, inputValue]);

  useEffect(() => {
    if (!open) setInputValue(selectedLabel);
  }, [selectedLabel, open, value]);

  useEffect(() => {
    setHighlight(0);
  }, [inputValue, open]);

  useEffect(() => {
    if (!open) return;
    const onDoc = (e: MouseEvent) => {
      if (
        !isInsideCombo(
          e.target as Node,
          rootRef.current,
          panelRef.current,
        )
      ) {
        setOpen(false);
        setInputValue(selectedLabel);
      }
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, [open, selectedLabel]);

  useEffect(() => {
    if (!open || !listRef.current) return;
    const el = listRef.current.querySelector<HTMLElement>(
      `[data-idx="${highlight}"]`,
    );
    el?.scrollIntoView({ block: "nearest" });
  }, [highlight, open]);

  function commit(next: string) {
    if (next !== value) {
      setPreviousValue(value);
      onChange(next);
    }
    const labelText = options.find((o) => o.id === next)?.label ?? "";
    setInputValue(labelText);
    setOpen(false);
  }

  function clear() {
    if (disabled) return;
    if (value) {
      setPreviousValue(value);
      onChange("");
    }
    setInputValue("");
    setOpen(true);
    inputRef.current?.focus();
  }

  function undo() {
    if (previousValue == null || previousValue === value || disabled) return;
    const prev = previousValue;
    setPreviousValue(value);
    onChange(prev);
    setInputValue(options.find((o) => o.id === prev)?.label ?? "");
    setOpen(false);
  }

  const canClear = !disabled && (!!value || !!inputValue);
  const canUndo =
    !disabled && previousValue != null && previousValue !== value;

  function onKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (disabled) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      if (!open) {
        setOpen(true);
        return;
      }
      setHighlight((h) => Math.min(h + 1, Math.max(filtered.length - 1, 0)));
      return;
    }
    if (e.key === "ArrowUp") {
      e.preventDefault();
      if (!open) {
        setOpen(true);
        return;
      }
      setHighlight((h) => Math.max(h - 1, 0));
      return;
    }
    if (e.key === "Escape") {
      e.preventDefault();
      setOpen(false);
      setInputValue(selectedLabel);
      return;
    }
    if (e.key === "Enter") {
      e.preventDefault();
      if (!open) {
        setOpen(true);
        return;
      }
      const opt = filtered[highlight];
      if (opt) commit(opt.id);
    }
  }

  return (
    <div
      className={`field combobox autocomplete ${disabled ? "disabled" : ""}`}
      ref={rootRef}
    >
      <label htmlFor={inputId}>{label}</label>
      <div
        ref={anchorRef}
        className={`combobox-row ${open ? "open" : ""}`}
      >
        <div className="autocomplete-input-wrap">
          <input
            ref={inputRef}
            id={inputId}
            className="autocomplete-input"
            disabled={disabled}
            role="combobox"
            aria-expanded={open}
            aria-controls={listId}
            aria-autocomplete="list"
            aria-activedescendant={
              open && filtered[highlight]
                ? `${listId}-opt-${filtered[highlight].id}`
                : undefined
            }
            placeholder={placeholder}
            value={inputValue}
            onChange={(e) => {
              setInputValue(e.target.value);
              if (!open) setOpen(true);
            }}
            onFocus={() => {
              if (!disabled) setOpen(true);
            }}
            onClick={() => {
              if (!disabled) setOpen(true);
            }}
            onKeyDown={onKeyDown}
            autoComplete="off"
            spellCheck={false}
          />
          <div className="autocomplete-adornments">
            {canClear && (
              <button
                type="button"
                className="combobox-icon-btn"
                title="Təmizlə"
                aria-label="Təmizlə"
                tabIndex={-1}
                onMouseDown={(e) => e.preventDefault()}
                onClick={clear}
              >
                ×
              </button>
            )}
            {canUndo && (
              <button
                type="button"
                className="combobox-icon-btn undo"
                title="Əvvəlki seçimə qayıt"
                aria-label="Əvvəlki seçimə qayıt"
                tabIndex={-1}
                onMouseDown={(e) => e.preventDefault()}
                onClick={undo}
              >
                ↺
              </button>
            )}
            <button
              type="button"
              className="combobox-icon-btn caret"
              disabled={disabled}
              title={open ? "Bağla" : "Aç"}
              aria-label={open ? "Siyahını bağla" : "Siyahını aç"}
              tabIndex={-1}
              onMouseDown={(e) => e.preventDefault()}
              onClick={() => {
                if (disabled) return;
                setOpen((v) => {
                  const next = !v;
                  if (next) inputRef.current?.focus();
                  else setInputValue(selectedLabel);
                  return next;
                });
              }}
            >
              {open ? "▴" : "▾"}
            </button>
          </div>
        </div>
      </div>

      <PortalMenu
        open={open && !disabled}
        anchorRef={anchorRef}
        panelRef={panelRef}
      >
        <ul
          id={listId}
          ref={listRef}
          className="combobox-list"
          role="listbox"
          aria-label={label}
        >
          {filtered.map((o, i) => (
            <li
              key={o.id}
              id={`${listId}-opt-${o.id}`}
              role="option"
              aria-selected={o.id === value}
              data-idx={i}
            >
              <button
                type="button"
                className={[
                  o.id === value ? "on" : "",
                  i === highlight ? "hl" : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
                onMouseEnter={() => setHighlight(i)}
                onMouseDown={(e) => e.preventDefault()}
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
      </PortalMenu>
      {emptyHint ? (
        <span className="field-hint" title={emptyHint}>
          {emptyHint}
        </span>
      ) : null}
    </div>
  );
}
