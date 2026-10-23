# 13 — What NOT to do

- Pin `@main`, `@latest`, or floating branches for production consumers.  
- Invent or hand-edit boundaries, names, parents, or coordinates.  
- Return simplified / truncated / rounded geometry as `boundary` in selection.  
- Create `baki_all.json` or any cross-district aggregate.  
- Write `neighborhood_id` back into canonical `data/places` from Perf/derive without Data lead process (derived-only index is OK).  
- Ship edge/paid API as P0–P2 default ([09](./09-tradeoffs.md)).  
- Load all place shards on cold start (`loadAllCatalogPlaces` default).  
- Treat bbox filter as exact containment.  
- Put `data/reviews` or audit dumps on the consumer CDN contract path.  
- Let PerfDocsArchitect edit `WORKER.md`, `LANDMARK.md`, `data/`, `scripts/`, or app packages while “planning”.  
- Agent-create git tags, push, or change `DEFAULT_DATA_BASE` ([HUMAN-GATES](./worker/HUMAN-GATES.md)).  
- Evict the active selection chain from L1.  
- Use cache-busting query strings on immutable pin URLs.  
- Present partial union (missing shards) as complete coverage.  
- Guess compressed sizes or RUM — measure or mark unmeasured ([14](./14-open-questions.md)).
