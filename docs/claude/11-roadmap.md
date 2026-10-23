# 11 — Roadmap

Owners: **Perf** (docs/client plan execution), **Eng** (code later), **Data lead** (tag), **Human** gates. Cold-start 60–150 KB br = **target**, revise after P0-01.

---

## P0 — Measure + client loading (canonical URLs)

### P0-01 — Baseline measurements
- **Owner:** Perf  
- **Input:** Live pin URL + local `data/`  
- **Output:** Filled [MEASUREMENTS](./worker/MEASUREMENTS.md)  
- **DoD:** raw/gzip/br (or Content-Length + Encoding) for top files; request traces for cold/Bakı/Sumqayıt/rayon/hood; verified-without-center count  
- **Verify:** Tables non-empty; numbers labeled measured  
- **Rollback:** n/a (docs only)

### P0-02 — Parallel boundary ∥ places + AbortSignal
- **Owner:** Eng (code later); Perf documents contract  
- **Input:** [04](./04-selection-contract.md), cascade leaf effect  
- **Output:** Plan verified; implementation tracked outside docs  
- **DoD:** select-district has **zero sequential** boundary→places dependency in design; abort/race specified in [15](./15-test-plan.md)  
- **Verify:** Waterfall diagram in [06](./06-request-waterfall.md)  
- **Rollback:** Revert client PR (future)

### P0-03 — L1 single-flight + active-chain pin
- **Owner:** Eng / Perf spec in [07](./07-caching.md)  
- **DoD:** Repeat selection design = 0 network when L1 warm  
- **Verify:** Test plan cases  
- **Rollback:** Disable L1 flag (future)

### P0-04 — Stop default `loadAllCatalogPlaces`
- **Owner:** Eng  
- **DoD:** Cold start does not fetch all place shards; search scoped to loaded area or deferred  
- **Verify:** Request count cold start ≤ 4 (canonical: manifest+areas ± children)  
- **Rollback:** Feature flag restore catalog load

### P0-05 — MapLibre clustering plan + chunked setData
- **Owner:** Eng  
- **DoD:** Design for Bakı ~7380 named places without main-thread meltdown (**count measured** via index; clustering code later)  
- **Verify:** [15](./15-test-plan.md) map budget notes  
- **Rollback:** Cluster off

### P0-06 — Customer-visible partial / bbox notices (copy pending)
- **Owner:** Eng + Human copy ([14](./14-open-questions.md))  
- **DoD:** Contract fields wired in design; az/en strings approved by Human  
- **Verify:** UI checklist  
- **Rollback:** Hide notices (dev-only) — not ideal

### P0-H1 — HUMAN: Approve P0 measurement baselines
- **Owner:** Human / Data lead + Eng lead  
- **DoD:** Sign-off in [HUMAN-GATES](./worker/HUMAN-GATES.md)  
- **Verify:** Checklist ticked  

---

## P1 — Derived publish + correctness

### P1-01 — Derive pipeline design → `data-derived/`
- **Owner:** Eng + Data  
- **Input:** [03](./03-cdn-file-plan.md)  
- **Output:** Script/CI design (code later); mapping tables  
- **DoD:** Every canonical consumer file has derived counterpart rule  
- **Verify:** Dry-run inventory doc in worker step  
- **Rollback:** Keep serving canonical only

### P1-02 — CI gates implementation plan
- **Owner:** Eng  
- **Input:** [12](./12-ci-gates.md)  
- **DoD:** Fail-the-build list agreed; boundary sha256 100% equality gate specified  
- **Verify:** Gate checklist  
- **Rollback:** Disable gate (block release instead)

### P1-03 — Neighborhood PIP + optional neighborhood_id index
- **Owner:** Eng  
- **DoD:** Hood places `basis=polygon`; index not written to canonical places  
- **Verify:** Hood table in MEASUREMENTS; wrong-neighbor sample  
- **Rollback:** `bbox_approx` + notice

### P1-04 — Scoped search indexes
- **Owner:** Eng  
- **DoD:** `search/{areaId}.json` derive rule; az normalization listed  
- **Verify:** Sample queries  
- **Rollback:** In-memory filter on loaded shard only

### P1-H1 — HUMAN: Tag + push  
### P1-H2 — HUMAN: Pin PR (`DEFAULT_DATA_BASE` → derived root)
- **Owner:** Data lead (tag), Eng lead (pin PR)  
- **DoD:** Smoke 200 catalog/top + sample boundary on live pin  
- **Verify:** [12](./12-ci-gates.md) release smoke  
- **Rollback:** Repoint pin to previous tag

---

## P2 — Warm path + optional ops

### P2-01 — Service Worker L2 pin cache
- **Owner:** Eng  
- **DoD:** Warm second visit ≥ **90%** bytes from cache (**measure**)  
- **Verify:** cache-hit table  
- **Rollback:** Unregister SW

### P2-02 — National search index (if product requires)
- **Owner:** Eng + Product  
- **DoD:** National search without loading all detail shards  
- **Verify:** Bytes + recall  
- **Rollback:** Scoped-only search

### P2-03 — pin.json and/or mirror only if RUM justifies
- **Owner:** Eng lead + Human  
- **DoD:** AZ RUM reviewed; mirror decision recorded  
- **Verify:** [14](./14-open-questions.md) answered  
- **Rollback:** jsDelivr-only

### P2-H1 — HUMAN: Mirror / pin.json decision

---

## Cross-phase DoD metrics

| Metric | Target | Status |
|---|---|---|
| Cold start requests | ≤ 4 | design |
| Cold catalog+manifest br | 60–150 KB | **target / unmeasured** |
| Select-district sequential deps | 0 | design |
| Boundary sha256 equality | 100% | P1 gate |
| Warm revisit bytes from cache | ≥ 90% | P2 measure |
| time-to-boundary / time-to-all-places | fill after P0-01 | unmeasured |
