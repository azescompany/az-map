import {
  useEffect,
  useId,
  useMemo,
  useRef,
  useState,
  type KeyboardEvent,
} from "react";
import type { Area, Place } from "@geoatlas/types";
import {
  areaBreadcrumb,
  categoryLabel,
  loadSearchNational,
  normalize,
  searchAreas,
  searchPlaces,
} from "@geoatlas/data";
import TruncatedText from "./TruncatedText";
import PortalMenu, { isInsideCombo } from "./PortalMenu";

type Hit =
  | { kind: "area"; area: Area }
  | { kind: "place"; place: Place };

type Props = {
  areas: Area[];
  places: Place[];
  /** When set, first focus lazy-loads search/national.json (derived CDN). */
  dataBase?: string;
  customer?: boolean;
  onSelectArea: (area: Area) => void;
  onSelectPlace: (placeId: string) => void;
};

/** Top-level autocomplete: filters areas + place names on every keystroke. */
export default function GlobalSearch({
  areas,
  places,
  dataBase,
  customer = false,
  onSelectArea,
  onSelectPlace,
}: Props) {
  const listId = useId();
  const inputId = useId();
  const rootRef = useRef<HTMLDivElement>(null);
  const anchorRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const listRef = useRef<HTMLUListElement>(null);
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const [highlight, setHighlight] = useState(0);
  const [nationalPlaces, setNationalPlaces] = useState<Place[]>([]);
  const [nationalLoading, setNationalLoading] = useState(false);
  const nationalLoadedRef = useRef(false);

  const ensureNational = () => {
    if (!dataBase || nationalLoadedRef.current) return;
    nationalLoadedRef.current = true;
    setNationalLoading(true);
    void loadSearchNational(dataBase)
      .then((list) => setNationalPlaces(list))
      .finally(() => setNationalLoading(false));
  };

  const searchPool = useMemo(() => {
    if (!nationalPlaces.length) return places;
    const byId = new Map(places.map((p) => [p.id, p]));
    for (const p of nationalPlaces) {
      if (!byId.has(p.id)) byId.set(p.id, p);
    }
    return [...byId.values()];
  }, [places, nationalPlaces]);

  const hits = useMemo((): Hit[] => {
    const q = normalize(query);
    if (!q) return [];
    const areaHits = searchAreas(areas, query, 8).map(
      (area): Hit => ({ kind: "area", area }),
    );
    const placeHits = searchPlaces(searchPool, query, 24).map(
      (place): Hit => ({ kind: "place", place }),
    );
    return [...placeHits, ...areaHits];
  }, [areas, searchPool, query]);

  useEffect(() => {
    setHighlight(0);
  }, [query]);

  useEffect(() => {
    if (!open) return;
    const onDoc = (e: MouseEvent) => {
      if (
        !isInsideCombo(e.target as Node, rootRef.current, panelRef.current)
      ) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, [open]);

  useEffect(() => {
    if (!open || !listRef.current) return;
    const el = listRef.current.querySelector<HTMLElement>(
      `[data-idx="${highlight}"]`,
    );
    el?.scrollIntoView({ block: "nearest" });
  }, [highlight, open, hits.length]);

  function pick(hit: Hit) {
    if (hit.kind === "area") onSelectArea(hit.area);
    else onSelectPlace(hit.place.id);
    setQuery("");
    setOpen(false);
  }

  function onKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Escape") {
      e.preventDefault();
      setOpen(false);
      return;
    }
    if (!hits.length) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setOpen(true);
      setHighlight((h) => Math.min(h + 1, hits.length - 1));
      return;
    }
    if (e.key === "ArrowUp") {
      e.preventDefault();
      setHighlight((h) => Math.max(h - 1, 0));
      return;
    }
    if (e.key === "Enter") {
      e.preventDefault();
      const hit = hits[highlight];
      if (hit) pick(hit);
    }
  }

  const showPanel = open && normalize(query).length > 0;

  return (
    <div className="field combobox autocomplete global-search" ref={rootRef}>
      <label htmlFor={inputId}>Axtarış</label>
      <div
        ref={anchorRef}
        className={`combobox-row ${showPanel ? "open" : ""}`}
      >
        <div className="autocomplete-input-wrap">
          <input
            id={inputId}
            className="autocomplete-input"
            role="combobox"
            aria-expanded={showPanel}
            aria-controls={listId}
            aria-autocomplete="list"
            placeholder={
              nationalLoading
                ? "Milli indeks yüklənir…"
                : "Məkan və ya ərazi adı yazın…"
            }
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setOpen(true);
              ensureNational();
            }}
            onFocus={() => {
              setOpen(true);
              ensureNational();
            }}
            onKeyDown={onKeyDown}
            autoComplete="off"
            spellCheck={false}
          />
          <div className="autocomplete-adornments">
            {!!query && (
              <button
                type="button"
                className="combobox-icon-btn"
                title="Təmizlə"
                aria-label="Təmizlə"
                tabIndex={-1}
                onMouseDown={(e) => e.preventDefault()}
                onClick={() => {
                  setQuery("");
                  setOpen(false);
                }}
              >
                ×
              </button>
            )}
          </div>
        </div>
      </div>

      <PortalMenu
        open={showPanel}
        anchorRef={anchorRef}
        panelRef={panelRef}
        maxHeight={320}
      >
        <ul
          id={listId}
          ref={listRef}
          className="combobox-list search-hit-list"
          role="listbox"
          aria-label="Axtarış nəticələri"
        >
          {hits.map((hit, i) => {
            if (hit.kind === "place") {
              const p = hit.place;
              const title = p.displayName ?? p.name;
              return (
                <li
                  key={`p-${p.id}`}
                  role="option"
                  aria-selected={i === highlight}
                  data-idx={i}
                >
                  <button
                    type="button"
                    className={i === highlight ? "hl" : ""}
                    onMouseEnter={() => setHighlight(i)}
                    onMouseDown={(e) => e.preventDefault()}
                    onClick={() => pick(hit)}
                  >
                    <TruncatedText text={title} as="strong" />
                    <div className="meta">
                      <TruncatedText
                        text={
                          customer
                            ? areaBreadcrumb(areas, p.area_id)
                            : `məkan · ${categoryLabel(String(p.category))} · ${areaBreadcrumb(areas, p.area_id)}`
                        }
                      />
                    </div>
                  </button>
                </li>
              );
            }
            const a = hit.area;
            return (
              <li
                key={`a-${a.id}`}
                role="option"
                aria-selected={i === highlight}
                data-idx={i}
              >
                <button
                  type="button"
                  className={i === highlight ? "hl" : ""}
                  onMouseEnter={() => setHighlight(i)}
                  onMouseDown={(e) => e.preventDefault()}
                  onClick={() => pick(hit)}
                >
                  <TruncatedText text={a.name} as="strong" />
                  <div className="meta">
                    <TruncatedText
                      text={
                        customer
                          ? areaBreadcrumb(areas, a.id)
                          : `ərazi · ${a.type} · ${areaBreadcrumb(areas, a.id)}`
                      }
                    />
                  </div>
                </button>
              </li>
            );
          })}
          {!hits.length && (
            <li>
              <div className="empty" style={{ padding: "0.65rem 0.75rem" }}>
                Nəticə yoxdur
              </div>
            </li>
          )}
        </ul>
      </PortalMenu>
    </div>
  );
}
