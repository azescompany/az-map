# data-derived/ (generated)

Consumer publish tree for jsDelivr after P1. **Do not hand-edit.**

```bash
pnpm derive:publish    # build from canonical data/
pnpm validate:derived  # CI gates
pnpm derive:check      # both
pnpm dev:derived       # demo against this tree (Vite publicDir)
```

Loaders dual-read: if `catalog/all-slim.json` + `places/shards.json` exist → derived layout.

Spec: [`docs/claude/03-cdn-file-plan.md`](../docs/claude/03-cdn-file-plan.md).  
Canonical SoT remains [`data/`](../data/). CDN pin (`cdn-derived`) is a **human gate** (Eng lead).
