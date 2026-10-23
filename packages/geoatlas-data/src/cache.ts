/**
 * L1 in-memory cache + single-flight dedupe for immutable pin URLs.
 * Active-chain eviction pinning is handled by callers keeping refs; this cache
 * uses a simple byte-budgeted LRU for parsed JSON payloads.
 */
import { responseJson } from "./parseJson";

type CacheEntry = {
  value: unknown;
  bytes: number;
  touched: number;
};

const DEFAULT_BUDGET = 48 * 1024 * 1024; // 48 MiB parsed-estimate budget

const store = new Map<string, CacheEntry>();
const inflight = new Map<string, Promise<unknown>>();
const pinned = new Set<string>();
let budgetBytes = DEFAULT_BUDGET;
let usedBytes = 0;

function estimateBytes(value: unknown): number {
  try {
    return JSON.stringify(value)?.length ?? 256;
  } catch {
    return 1024;
  }
}

function evictIfNeeded(): void {
  if (usedBytes <= budgetBytes) return;
  const victims = [...store.entries()]
    .filter(([key]) => !pinned.has(key))
    .sort((a, b) => a[1].touched - b[1].touched);
  for (const [key, entry] of victims) {
    if (usedBytes <= budgetBytes * 0.85) break;
    store.delete(key);
    usedBytes -= entry.bytes;
  }
}

/** Pin URLs so LRU will not evict them (active selection chain). */
export function pinCacheKeys(keys: string[]): void {
  pinned.clear();
  for (const k of keys) pinned.add(k);
}

export function setCacheByteBudget(bytes: number): void {
  budgetBytes = Math.max(4 * 1024 * 1024, bytes);
  evictIfNeeded();
}

export function clearDataCache(): void {
  store.clear();
  inflight.clear();
  pinned.clear();
  usedBytes = 0;
}

export function getCached<T>(key: string): T | undefined {
  const hit = store.get(key);
  if (!hit) return undefined;
  hit.touched = Date.now();
  return hit.value as T;
}

export function setCached<T>(key: string, value: T): T {
  const prev = store.get(key);
  if (prev) usedBytes -= prev.bytes;
  const bytes = estimateBytes(value);
  store.set(key, { value, bytes, touched: Date.now() });
  usedBytes += bytes;
  evictIfNeeded();
  return value;
}

/**
 * Single-flight fetch: concurrent callers share one Promise; result is L1-cached.
 */
export async function cachedFetchJson<T>(
  url: string,
  loader: () => Promise<T>,
): Promise<T> {
  const hit = getCached<T>(url);
  if (hit !== undefined) return hit;

  const existing = inflight.get(url);
  if (existing) return existing as Promise<T>;

  const p = (async () => {
    try {
      const value = await loader();
      setCached(url, value);
      return value;
    } finally {
      inflight.delete(url);
    }
  })();

  inflight.set(url, p);
  return p;
}

/** jsDelivr gh → raw.githubusercontent.com (403 / edge blocks on large repos). */
function jsdelivrGhToRaw(url: string): string | null {
  const m =
    /^https:\/\/cdn\.jsdelivr\.net\/gh\/([^/]+)\/([^@]+)@([^/]+)\/(.+)$/i.exec(
      url,
    );
  if (!m) return null;
  return `https://raw.githubusercontent.com/${m[1]}/${m[2]}/${m[3]}/${m[4]}`;
}

async function fetchJsonResponse(
  url: string,
  opts?: { acceptGeoJson?: boolean },
): Promise<Response | null> {
  let res = await fetch(url);
  // jsDelivr occasionally 403s existing files on big gh mirrors — try raw.
  if ((res.status === 403 || res.status === 451) && /jsdelivr\.net\/gh\//i.test(url)) {
    const raw = jsdelivrGhToRaw(url);
    if (raw) res = await fetch(raw);
  }
  if (!res.ok) return null;
  const ctype = res.headers.get("content-type") ?? "";
  const okType =
    !ctype ||
    ctype.includes("json") ||
    (opts?.acceptGeoJson && ctype.includes("geo+json"));
  if (!okType) return null;
  return res;
}

/**
 * Fetch URL as JSON with L1 + single-flight; large bodies parse in a Worker.
 * Returns null on non-OK or non-JSON content-type (SPA HTML fallback).
 */
export async function cachedFetchJsonUrl<T>(
  url: string,
  opts?: { acceptGeoJson?: boolean },
): Promise<T | null> {
  return cachedFetchJson(url, async () => {
    const res = await fetchJsonResponse(url, opts);
    if (!res) return null;
    try {
      return await responseJson<T>(res);
    } catch {
      return null;
    }
  });
}
