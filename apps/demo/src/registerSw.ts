/**
 * Register GeoAtlas L2 service worker (Cache Storage, pin-namespaced).
 * Enabled in production, or when VITE_GEOATLAS_SW=1 (e.g. derived mode).
 */

function swEnabled(): boolean {
  if (typeof window === "undefined" || !("serviceWorker" in navigator)) {
    return false;
  }
  const flag = (import.meta.env.VITE_GEOATLAS_SW ?? "").trim().toLowerCase();
  if (flag === "0" || flag === "false" || flag === "off") return false;
  if (flag === "1" || flag === "true" || flag === "on") return true;
  return import.meta.env.PROD;
}

export async function registerGeoAtlasServiceWorker(): Promise<void> {
  if (!swEnabled()) return;
  try {
    const reg = await navigator.serviceWorker.register("/sw.js", {
      scope: "/",
    });
    await navigator.serviceWorker.ready;
    // Ensure controlling client after first register
    if (reg.waiting) {
      reg.waiting.postMessage({ type: "SET_PIN", pin: "local" });
    }
  } catch (e) {
    console.warn("[geoatlas] service worker register failed", e);
  }
}

/** Tell SW the active dataset_version so old pin caches are purged. */
export function notifyServiceWorkerPin(datasetVersion: string | null | undefined): void {
  if (!swEnabled() || !datasetVersion) return;
  const pin = datasetVersion.trim();
  if (!pin) return;
  const msg = { type: "SET_PIN" as const, pin };
  navigator.serviceWorker?.controller?.postMessage(msg);
  void navigator.serviceWorker?.ready.then((reg) => {
    reg.active?.postMessage(msg);
  });
}
