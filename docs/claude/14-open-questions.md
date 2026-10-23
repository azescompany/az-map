# 14 — Open questions (real unknowns only)

Do not guess. Answers unblock copy, RACI, and P2 ops.

| ID | Question | Needed by |
|---|---|---|
| Q1 | **Tag RACI:** Confirm Data lead accountable for approving/creating annotated tags `vX.Y.Z-national`. Named person? | P1-H1 |
| Q2 | **Pin PR RACI:** Confirm Eng lead accountable for merging `DEFAULT_DATA_BASE` / demo CDN pin PR. Named person? | P1-H2 |
| Q3 | **Compressed sizes:** Fill [MEASUREMENTS](./worker/MEASUREMENTS.md) (raw/gzip/br or CDN Content-Length + Encoding). | P0-01 |
| Q4 | **AZ RUM:** p50/p95 latency from Azerbaijan ISPs to jsDelivr; brotli behavior. Day-1 mirror? | P2-03 |
| Q5 | **PIP cost:** Point-in-polygon ms on most complex neighborhood polygons (mobile). | P1-03 |
| Q6 | **bbox_approx UI:** Show notice to customers or omit hood places until polygon path ships? | P0-06 |
| Q7 | **Pin source for data-only rollout:** Adopt `pin.json` in derived root vs env-only pin? | P2-03 |
| Q8 | **Customer-visible partial/conflict boundary label** — approve az/en wording. Draft below. | P0-06 |
| Q9 | **jsDelivr official per-file limit** for GitHub proxy (confirm current docs; notes conflict ~20 vs ~50 MB). | P1 packaging |
| Q10 | **Cold-start budget revision:** After P0-01, is 60–150 KB br for manifest+top still realistic with ~3486 areas slim rows? | P0-H1 |

### P0-01 / P1-01 finding (for Q10)

Canonical `areas/areas.json` alone is **~344 KB brotli** (**measured**).  
Derived `catalog/top.json` + `manifest.json` ≈ **7.2 KB brotli** (**measured** after `pnpm derive:publish`) — **within** 60–150 KB target. Q10 answer: target is realistic **with derived pin**; not with fat `areas.json`.

## Draft UI copy (pending Human approval)

**Partial boundary**  
- az: `Sərhəd natamam və ya conflict — rəsmi dəqiqlik hesab edilmir.`  
- en: `Boundary is partial or in conflict — not treated as authoritative.`

**bbox_approx places**  
- az: `Məkanlar təxmini (bbox); qonşu məhəlləyə düşə bilər.`  
- en: `Places filtered by approximate bbox; neighboring hoods may appear.`
