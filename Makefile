.PHONY: help venv-install sync verify context-delta validate-log seed-log test-log \
	qdrant-up qdrant-down qdrant-logs embed embed-dry env-check \
	llm-up llm-pull llm-smoke mcp-github-up mcp-github-smoke validate-agent-handoff venv-which validate-agent-handoff \
	sync-dry sync-apply embed-openai qdrant-wipe qdrant-init qdrant-list qdrant-info qdrant-count \
	print-env embed-openai-upsert embed-logs

# Defaults (override like: make PY=python3.11)
SHELL := /bin/sh
PY ?= python3
COMPOSE ?= docker compose
VENV ?= .venv

ifneq (,$(wildcard .env))
  include .env
  export
endif


help:
	@echo "Targets:"
	@echo "  venv-install    - create venv, install dev deps, install pre-commit"
	@echo "  sync            - run scripts/sync_repos.py (from venv)"
	@echo "  verify          - run pre-commit against all files"
	@echo "  context-delta   - append a context_delta YAML via stdin to the log"
	@echo "  validate-log    - schema/syntax check for context_delta.log.yaml"
	@echo "  seed-log        - create a minimal context_delta log (safe in fresh repo)"
	@echo "  test-log        - append a valid entry, then intentionally fail one"
	@echo "  qdrant-up       - start Qdrant service"
	@echo "  qdrant-down     - stop Qdrant"
	@echo "  qdrant-logs     - follow Qdrant logs"
	@echo "  embed-dry       - run embed.py in dry mode (manifest only)"
	@echo "  embed           - run embed.py in OpenAI mode (requires OPENAI_API_KEY)"
	@echo "  llm-up          - start Ollama + LiteLLM"
	@echo "  llm-pull        - pull local model into Ollama (OLLAMA_MODELS env)"
	@echo "  llm-smoke       - quick POST to LiteLLM /v1/chat/completions"
	@echo "  mcp-github-up   - start GitHub MCP adapter"
	@echo "  mcp-github-smoke- health + list issues smoke test"
	@echo "  embed-logs      - list the most recent embed logs"

venv-install:
	$(PY) -m venv $(VENV)
	. $(VENV)/bin/activate && pip install -U pip -r requirements-dev.txt && pre-commit install

# Allow 'make sync DRY=1' or 'make sync SYNC_DRY=0'
sync:
	. $(VENV)/bin/activate && SYNC_DRY=$(DRY) $(PY) scripts/sync_repos.py

verify:
	pre-commit run --all-files

context-delta:
	./scripts/append_context_delta.sh

validate-log:
	$(PY) scripts/validate_context_delta.py

seed-log:
	mkdir -p docs/context
	@{ \
	printf '%s\n' \
'entries:' \
'  - context_delta:' \
'      status:' \
'        summary: >' \
'          Seed entry: initialized orchestrator repo (amara-core).' \
'        last_updated: 2025-08-26' \
'      decisions:' \
'        - date: 2025-08-26' \
'          what: "Split into amara-core and amara-gateway."' \
'          why: "Separate concerns for orchestration vs. gateway."' \
'      next_actions:' \
'        - who: me' \
'          what: "Add schema validator and append helper"' \
'          due: 2025-08-26' \
'      risks:' \
'        - "Accidental schema drift; mitigation: pre-commit validator"'; \
	} > docs/context/context_delta.log.yaml
	$(MAKE) validate-log

test-log:
	@echo ">> Appending a valid test entry"
	@{ \
	printf '%s\n' \
'status:' \
'  summary: >' \
'    Test append entry via Makefile.' \
'  last_updated: 2025-08-26' \
'decisions:' \
'  - date: 2025-08-26' \
'    what: "Validator accepted YAML dates"' \
'    why: "PyYAML auto-converts ISO strings"' \
'next_actions:' \
'  - who: me' \
'    what: "Append a new test entry"' \
'    due: 2025-08-26' \
'  - who: assistant' \
'    what: "Check that schema passes"' \
'    due: 2025-08-26' \
'risks:' \
'  - "None — test only"'; \
	} > /tmp/_delta_ok.yaml
	./scripts/append_context_delta.sh < /tmp/_delta_ok.yaml
	@echo ">> Attempting an invalid append (should FAIL)"
	@set -e; { \
	printf '%s\n' \
'status:' \
'  summary: >' \
'    Invalid entry (missing risks).' \
'  last_updated: 2025-08-26' \
'decisions:' \
'  - date: 2025-08-26' \
'    what: "Bad entry for test"' \
'    why: "Missing risks"' \
'next_actions:' \
'  - who: me' \
'    what: "This should fail schema"' \
'    due: 2025-08-26'; \
	} > /tmp/_delta_bad.yaml; \
	if ./scripts/append_context_delta.sh < /tmp/_delta_bad.yaml; then \
		echo "ERROR: invalid append unexpectedly passed" && exit 1; \
	else \
		echo "OK: invalid append was correctly rejected"; \
	fi

qdrant-up:
	$(COMPOSE) up -d qdrant

qdrant-down:
	$(COMPOSE) down qdrant

qdrant-logs:
	$(COMPOSE) logs -f qdrant

embed-dry:
	$(PY) scripts/embed.py

embed:
	EMBED_MODE=openai $(PY) scripts/embed.py

env-check:
	$(PY) scripts/check_env.py

# ---- Local LLM / LiteLLM helpers ----
llm-up:
	$(COMPOSE) up -d ollama litellm

llm-pull:
	docker exec -it amara-ollama ollama pull $${OLLAMA_MODELS:-llama3.1:8b}

llm-smoke:
	curl -s -X POST "http://localhost:$${LITELLM_PORT:-4000}/v1/chat/completions" \
		-H "Authorization: Bearer $${LITELLM_PROXY_KEY}" \
		-H "Content-Type: application/json" \
		-d '{"model":"local/llama3.1-8b","messages":[{"role":"user","content":"Say hi in one sentence."}]}' | jq '.choices[0].message.content'

# ---- MCP: GitHub adapter ----
mcp-github-up:
	$(COMPOSE) up -d mcp-github

mcp-github-smoke:
	curl -fsS http://localhost:$${MCP_GITHUB_PORT:-8088}/health | jq .
	curl -fsS -X POST http://localhost:$${MCP_GITHUB_PORT:-8088}/tools/listIssues \
		-H "Content-Type: application/json" \
		-d '{"state":"open","per_page":5}' | jq '.[].number, .[].title' | head -n 10

venv-which:
	@echo "VIRTUAL_ENV=$(VIRTUAL_ENV)"
	@echo "python -> $$(command -v python)"
	@python -c "import sys; print('sys.executable =', sys.executable)"
	@pip -V

validate-agent-handoff:
	. $(VENV)/bin/activate && $(PY) -c "import json; from jsonschema import Draft7Validator as V; s=json.load(open('docs/contracts/agent_handoff.schema.json','r',encoding='utf-8')); V.check_schema(s); print('agent_handoff.schema.json OK')"

sync-dry:
	. $(VENV)/bin/activate && SYNC_DRY=1 $(PY) scripts/sync_repos.py && jq . artifacts/sync.report.json | head -n 60

sync-apply:
	. $(VENV)/bin/activate && SYNC_DRY=0 $(PY) scripts/sync_repos.py

embed-openai:
	EMBED_MODE=openai $(PY) scripts/embed.py

# Danger: wipes staged sources (not Qdrant data)
qdrant-wipe:
	rm -rf docs/context/sources && mkdir -p docs/context/sources

qdrant-init:
	. $(VENV)/bin/activate && $(PY) scripts/qdrant_init.py

qdrant-list:
	curl -fsS http://localhost:$${QDRANT_PORT:-6333}/collections | jq .

qdrant-info:
	@curl -fsS "$${QDRANT_URL:-http://localhost:6333}/collections/$${QDRANT_COLLECTION:-amara_docs}" | jq .

qdrant-count:
	@curl -fsS -X POST \
	  "$${QDRANT_URL:-http://localhost:6333}/collections/$${QDRANT_COLLECTION:-amara_docs}/points/count" \
	  -H "Content-Type: application/json" \
	  -d '{"exact":true}' | jq .

print-env:
	@echo "From make (autoloaded .env):"
	@echo "OPENAI_API_KEY=$${OPENAI_API_KEY:+ }"
	@echo "EMBED_MODE=$(EMBED_MODE)"
	@echo "EMBED_QDRANT_UPSERT=$(EMBED_QDRANT_UPSERT)"
	@echo "QDRANT_URL=$(QDRANT_URL)"
	@echo "QDRANT_COLLECTION=$(QDRANT_COLLECTION)"

embed-openai-upsert:
	@mkdir -p artifacts/logs
	@echo "[embed] starting at $$(date)"
	@EMBED_MODE=openai EMBED_QDRANT_UPSERT=1 $(PY) scripts/embed.py 2>&1 | tee artifacts/logs/embed.$$(date +%Y%m%d-%H%M%S).log

embed-logs:
	@ls -1 artifacts/logs 2>/dev/null | tail -n 5 | sed 's#^#artifacts/logs/#'
	@echo "Tip: tail -f artifacts/logs/<latest>"
