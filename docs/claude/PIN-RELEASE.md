# Pin release v0.3.1-national (derived CDN)

## Default consumer pin

```
https://cdn.jsdelivr.net/gh/azescompany/az-map@v0.3.1-national/data-derived/
```

Canonical fat tree (same tag):

```
https://cdn.jsdelivr.net/gh/azescompany/az-map@v0.3.1-national/data/
```

Code: `DEFAULT_DATA_BASE` → derived; `DEFAULT_DATA_BASE_CANONICAL` → `data/`.

## Checklist

1. [x] `pnpm derive:publish` + `pnpm validate:derived`
2. [x] `data-derived/` tracked (gitignore exception removed)
3. [x] `dataset_version` → `0.3.1-national`
4. [x] Pin constants + demo `.env.example`
5. [ ] `git commit` + annotated tag `v0.3.1-national`
6. [ ] `git push origin master` + `git push origin v0.3.1-national`
7. [ ] Smoke (after jsDelivr indexes, ~1–5 min):

```bash
curl -sI "https://cdn.jsdelivr.net/gh/azescompany/az-map@v0.3.1-national/data-derived/manifest.json"
curl -sI "https://cdn.jsdelivr.net/gh/azescompany/az-map@v0.3.1-national/data-derived/catalog/top.json"
```

Expect HTTP 200.