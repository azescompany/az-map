import {
  useLayoutEffect,
  useRef,
  useState,
  type CSSProperties,
  type ReactNode,
  type RefObject,
} from "react";
import { createPortal } from "react-dom";

type Props = {
  open: boolean;
  /** Element to align under (usually the input wrap / combobox row) */
  anchorRef: RefObject<HTMLElement | null>;
  children: ReactNode;
  className?: string;
  /** Expose panel node for outside-click checks */
  panelRef?: RefObject<HTMLDivElement | null>;
  maxHeight?: number;
};

/**
 * Renders a dropdown menu in a portal (shell or body) with fixed coords
 * so it is never clipped by card overflow / scroll.
 */
export default function PortalMenu({
  open,
  anchorRef,
  children,
  className = "",
  panelRef,
  maxHeight = 280,
}: Props) {
  const localRef = useRef<HTMLDivElement>(null);
  const ref = panelRef ?? localRef;
  const [style, setStyle] = useState<CSSProperties>({});

  useLayoutEffect(() => {
    if (!open) return;

    const update = () => {
      const anchor = anchorRef.current;
      if (!anchor) return;
      const rect = anchor.getBoundingClientRect();
      const spaceBelow = window.innerHeight - rect.bottom - 8;
      const spaceAbove = rect.top - 8;
      const placeAbove = spaceBelow < 140 && spaceAbove > spaceBelow;
      const avail = placeAbove ? spaceAbove : spaceBelow;
      const height = Math.min(maxHeight, Math.max(96, avail));

      setStyle({
        position: "fixed",
        top: placeAbove ? undefined : rect.bottom + 4,
        bottom: placeAbove ? window.innerHeight - rect.top + 4 : undefined,
        left: rect.left,
        width: Math.max(rect.width, 160),
        maxHeight: height,
        zIndex: 10050,
      });
    };

    update();
    window.addEventListener("resize", update);
    // capture scroll from any ancestor (map, page, etc.)
    window.addEventListener("scroll", update, true);
    return () => {
      window.removeEventListener("resize", update);
      window.removeEventListener("scroll", update, true);
    };
  }, [open, anchorRef, maxHeight]);

  if (!open || typeof document === "undefined") return null;

  // body portal: escapes card + shell overflow; never clips under the map chrome
  return createPortal(
    <div
      ref={ref}
      className={`combobox-panel autocomplete-panel geoatlas-portal-menu ${className}`.trim()}
      style={style}
      data-geoatlas-portal-menu
    >
      {children}
    </div>,
    document.body,
  );
}

/** True if event target is inside root or portaled panel */
export function isInsideCombo(
  target: Node | null,
  root: HTMLElement | null,
  panel: HTMLElement | null,
): boolean {
  if (!target) return false;
  if (root?.contains(target)) return true;
  if (panel?.contains(target)) return true;
  return false;
}
