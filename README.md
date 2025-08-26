# Amara Core

**Amara Core** is the orchestrator for the Amara Assistant. It ingests and syncs project documentation, embeds content into a vector store (Qdrant), and enforces quality via pre-commit hooks and CI checks. It is designed to work in tandem with [Amara Gateway](https://github.com/bodyhigh/amara-gateway), which exposes the UI and API.

---

## Features

- **Context ingestion & sync**

  - `sources.yaml` allowlist controls what files are staged.
  - `make sync` stages sources into `docs/context/sources`.

- **Vector embeddings**

  - `scripts/embed.py` chunks and embeds docs.
  - Supports dry-run, OpenAI API, local sentence-transformers, and optional Qdrant upsert.

- **Project memory**

  - Append-only `context_delta.log.yaml` under `docs/context`.
  - Validated on every commit and in CI.

- **Quality enforcement**
  - `pre-commit` hooks validate script headers, context_delta schema, and forbidden patterns.
  - GitHub Actions required check named `pre-commit`.
  - All commits must be SSH-signed.

---

## Requirements

- **Python**: 3.11 (use a virtualenv in `.venv`)
- **Node.js**: v20 LTS (pinned by `.nvmrc`)
- **Docker Compose**: v2 CLI (no `legacy compose v1 CLI` v1)
- **Qdrant**: v1.12.4 (containerized in Compose)

---

## Quickstart

Clone and set up the repo:

```bash
git clone git@github.com:bodyhigh/amara-core.git
cd amara-core

# Python venv
python3.11 -m venv .venv
source .venv/bin/activate

# IMPORTANT: Always activate your venv before installing packages.
# This avoids the "externally managed environment" pip error on Debian/Ubuntu.

# Install dependencies (pre-commit + optional embed deps)
pip install -r requirements.txt
pre-commit install

# Node
nvm use
```

Run initial checks:

```bash
make test-log     # run context_delta log test
make sync DRY=1   # dry-run repo sync
make embed DRY=1  # dry-run embeddings
```

---

## Makefile Targets

- `make seed-log` — create a starter context_delta log
- `make test-log` — validate the log schema
- `make sync` — stage sources from allowlist (`docs/sources.yaml`)
- `make embed` — chunk + embed docs (dry, OpenAI, or local modes)
- `make qdrant-upsert` — optional, push embeddings to Qdrant

---

## Continuous Integration

This repo enforces quality via GitHub Actions:

- **`pre-commit` (required check):** Validates script headers, forbidden patterns, and context_delta schema.
- **`sync` (dry run):** Ensures `sources.yaml` allowlist works; review `sync.report.json`.
- **`embed` (dry run):** Runs embeddings without upserting into Qdrant.

CI workflow is defined in [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

---

## Secrets

For embedding with OpenAI:

- **Local**: copy `.env.example` to `.env` and fill in values:
  ```bash
  cp .env.example .env
  ```
- **CI**: add a GitHub Actions Secret named **`OPENAI_API_KEY`**.
  It will be available as `secrets.OPENAI_API_KEY` inside workflows.

---

## Repository Structure

```
amara-core/
├── amara_core/               # Python package
├── artifacts/                # outputs (chunks, reports, embeddings)
├── docs/
│   └── context/              # context_delta log + staged sources
├── scripts/                  # helper scripts (embed, sync, append log)
├── .github/workflows/        # CI configs
├── .editorconfig             # enforce tabs in Makefiles
├── Makefile                  # DX commands
└── requirements.txt          # Python deps
```

---

## Development Standards

- All commits must be **SSH-signed**.
- Branch protection requires PRs + passing `pre-commit` check.
- Pre-commit hooks include:
  - `validate-amara-script-headers`
  - `forbid-legacy compose v1 CLI-v1-cli`
  - `forbid-secret-patterns`
  - `validate-context-delta-log`

---

## Related Repos

- [Amara Gateway](https://github.com/bodyhigh/amara-gateway) — UI and API surface.

---

## License

MIT / Apache-2.0 dual-license. See [docs/oss/](docs/oss) for details.
