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
5. [x] `git commit` `5af7acc` + annotated tag `v0.3.1-national`
6. [x] `git push origin master` + `git push origin v0.3.1-national`
7. [x] Smoke 200 (2026-10-23): `data-derived/manifest.json`, `catalog/top.json`, and canonical `data/manifest.json`

```bash
curl -sI "https://cdn.jsdelivr.net/gh/azescompany/az-map@v0.3.1-national/data-derived/manifest.json"
curl -sI "https://cdn.jsdelivr.net/gh/azescompany/az-map@v0.3.1-national/data-derived/catalog/top.json"
```