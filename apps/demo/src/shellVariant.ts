export type ShellVariant = "default" | "form";

/** URL ?variant= → VITE_SHELL_VARIANT → default */
export function resolveShellVariant(): ShellVariant {
  if (typeof window !== "undefined") {
    const q = new URLSearchParams(window.location.search).get("variant");
    if (q === "form" || q === "default") return q;
  }
  const env = import.meta.env.VITE_SHELL_VARIANT;
  if (env === "form" || env === "default") return env;
  return "default";
}
