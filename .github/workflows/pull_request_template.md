# Amara Core — PR Checklist

## Pre-commit

- [ ] `pre-commit run --all-files` passes locally
- [ ] Added/updated Amara script headers on any `scripts/*.sh` or `scripts/*.py`

## Safe Networking & Ingress

- [ ] Proxy stays SSE-safe: `gzip off; proxy_buffering off; X-Accel-Buffering: no`
- [ ] Cloudflared only for ingress (no public origin ports)
- [ ] Compose v2 (no `docker[dash]]compose` v1 CLI in docs or scripts)

## Embeddings & Artifacts

- [ ] No use of `recreate_collection()`; idempotent create-if-missing only
- [ ] Artifacts under `${AMARA_STORAGE}/amara-artifacts` (repo `artifacts/` is a symlink)

## Secrets Hygiene

- [ ] No tokens in code, logs, or examples (use `<REDACTED: ...>`)
