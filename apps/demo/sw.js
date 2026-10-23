/* GeoAtlas L2 Cache Storage — pin-namespaced. See docs/claude/07-caching.md */
/* eslint-disable no-restricted-globals */

const CACHE_PREFIX = "geoatlas-pin-";
/** @type {string} */
let currentPin = "local";

self.addEventListener("install", (event) => {
  event.waitUntil(self.skipWaiting());
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    (async () => {
      await self.clients.claim();
      await purgeOtherPins(currentPin);
    })(),
  );
});

self.addEventListener("message", (event) => {
  const data = event.data;
  if (!data || typeof data !== "object") return;
  if (data.type === "SET_PIN" && typeof data.pin === "string" && data.pin) {
    currentPin = sanitizePin(data.pin);
    event.waitUntil(purgeOtherPins(currentPin));
  }
  if (data.type === "PURGE_ALL") {
    event.waitUntil(purgeAll());
  }
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (!shouldCache(url)) return;

  const pin = pinFromUrl(url) || currentPin;
  event.respondWith(cacheFirst(req, sanitizePin(pin)));
});

/**
 * @param {string} pin
 */
function sanitizePin(pin) {
  return String(pin).replace(/[^a-zA-Z0-9._-]+/g, "_").slice(0, 80) || "local";
}

/**
 * @param {URL} url
 */
function pinFromUrl(url) {
  // jsDelivr git pin: .../gh/org/repo@v0.3.0-national/...
  const m = url.pathname.match(/@([^/]+)\//);
  if (m) return m[1];
  return null;
}

/**
 * @param {URL} url
 */
function shouldCache(url) {
  // Same-origin curated JSON/GeoJSON (Vite publicDir = data/ or data-derived/)
  if (url.origin === self.location.origin) {
    const p = url.pathname;
    return (
      p === "/manifest.json" ||
      p.startsWith("/catalog/") ||
      p.startsWith("/areas/") ||
      p.startsWith("/boundaries/") ||
      p.startsWith("/places/") ||
      p.startsWith("/search/") ||
      p.startsWith("/reviews/")
    );
  }
  // Immutable jsDelivr az-map pins only (never @main)
  if (url.hostname === "cdn.jsdelivr.net" || url.hostname.endsWith(".jsdelivr.net")) {
    if (!url.pathname.includes("/gh/azescompany/az-map@")) return false;
    if (/az-map@(main|latest|master)\b/i.test(url.pathname)) return false;
    return /\.(json|geojson)$/i.test(url.pathname);
  }
  return false;
}

/**
 * @param {Request} request
 * @param {string} pin
 */
async function cacheFirst(request, pin) {
  const name = CACHE_PREFIX + pin;
  const cache = await caches.open(name);
  const hit = await cache.match(request);
  if (hit) return hit;
  const res = await fetch(request);
  if (res.ok) {
    try {
      await cache.put(request, res.clone());
    } catch {
      /* quota / opaque — ignore */
    }
  }
  return res;
}

/**
 * @param {string} keepPin
 */
async function purgeOtherPins(keepPin) {
  const keep = CACHE_PREFIX + keepPin;
  const keys = await caches.keys();
  await Promise.all(
    keys
      .filter((k) => k.startsWith(CACHE_PREFIX) && k !== keep)
      .map((k) => caches.delete(k)),
  );
}

async function purgeAll() {
  const keys = await caches.keys();
  await Promise.all(
    keys.filter((k) => k.startsWith(CACHE_PREFIX)).map((k) => caches.delete(k)),
  );
}
