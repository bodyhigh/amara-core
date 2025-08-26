# Context Staging

- Spec: `docs/sources.yaml`
- Dry run: `make sync DRY=1` → writes `artifacts/sync.report.json`
- Apply: `make sync DRY=0` → copies into `docs/context/sources/<name>/`
- Embed: `make embed-dry` then `EMBED_MODE=openai make embed`

**Flags**

- `SYNC_DRY=1|0`: plan vs copy
- `EMBED_QDRANT_UPSERT=1|0`: control Qdrant writes
