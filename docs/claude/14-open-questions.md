# 14 — Open questions (closeout)

Resolved at [CLOSEOUT](./CLOSEOUT.md). Deferred items are ops/RUM, not architecture blockers.

| ID | Question | Resolution |
|---|---|---|
| Q1 | Tag RACI — Data lead for `vX.Y.Z-national`? | **Closed** — role = Data lead (named person optional). Tags shipped. |
| Q2 | Pin PR RACI — Eng lead? | **Closed** — role = Eng lead. Pin to derived shipped. |
| Q3 | Compressed sizes | **Closed** — [MEASUREMENTS](./worker/MEASUREMENTS.md) local raw/gzip/br filled. CDN Content-Length optional later. |
| Q4 | AZ RUM / day-1 mirror? | **Deferred** — no mirror until measured; jsDelivr-only. |
| Q5 | PIP ms on complex hoods (mobile) | **Deferred** — PIP shipped; profile only if hood select jank reported. |
| Q6 | bbox_approx UI notice? | **Closed** — show notice (draft strings). |
| Q7 | `pin.json` vs env-only? | **Closed** — `pin.json` in derived root (+ env override OK). |
| Q8 | Partial/conflict boundary label az/en | **Closed** — working copy below (demo wired). |
| Q9 | jsDelivr per-file limit | **Deferred** — watch packaging; no file over practical CDN limits in derive. |
| Q10 | 60–150 KB cold budget realistic? | **Closed** — yes with derived lazy (~13.5 KB br); no with fat `areas.json` (~344 KB br alone). |

## Approved working UI copy

**Partial boundary**  
- az: `Sərhəd natamam və ya conflict — rəsmi dəqiqlik hesab edilmir.`  
- en: `Boundary is partial or in conflict — not treated as authoritative.`

**bbox_approx places**  
- az: `Məkanlar təxmini (bbox); qonşu məhəlləyə düşə bilər.`  
- en: `Places filtered by approximate bbox; neighboring hoods may appear.`
