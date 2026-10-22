import { useEffect, useRef, useState } from "react";

type Props = {
  text: string;
  className?: string;
  as?: "span" | "strong" | "div";
};

/** Ellipsis truncate; native tooltip only when actually overflowing. */
export default function TruncatedText({
  text,
  className,
  as: Tag = "span",
}: Props) {
  const ref = useRef<HTMLElement>(null);
  const [truncated, setTruncated] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const measure = () => {
      setTruncated(el.scrollWidth > el.clientWidth + 1);
    };
    measure();
    const ro = new ResizeObserver(measure);
    ro.observe(el);
    return () => ro.disconnect();
  }, [text]);

  return (
    <Tag
      ref={ref as never}
      className={["truncated-text", className].filter(Boolean).join(" ")}
      title={truncated ? text : undefined}
      aria-label={truncated ? text : undefined}
    >
      {text}
    </Tag>
  );
}
