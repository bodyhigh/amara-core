.PHONY: help venv-install sync verify context-delta validate-log seed-log test-log qdrant-up qdrant-down qdrant-logs

# Defaults (override like: make PY=python3.11)
SHELL := /bin/sh
PY ?= python3
COMPOSE ?= docker compose
VENV ?= .venv

help:
	@echo "Targets:"
	@echo "  venv-install   - create venv, install dev deps, install pre-commit"
	@echo "  sync           - run scripts/sync_repos.py (from venv)"
	@echo "  verify         - run pre-commit against all files"
	@echo "  context-delta  - append a context_delta YAML via stdin to the log"
	@echo "  validate-log   - schema/syntax check for context_delta.log.yaml"
	@echo "  seed-log       - create a minimal context_delta log (safe in fresh repo)"
	@echo "  test-log       - append a valid entry, then intentionally fail one"
	@echo "  qdrant-up      - start Qdrant service from docker compose"
	@echo "  qdrant-down    - stop Qdrant"
	@echo "  qdrant-logs    - follow Qdrant logs"

venv-install:
	$(PY) -m venv $(VENV)
	. $(VENV)/bin/activate && pip install -U pip -r requirements-dev.txt && pre-commit install

sync:
	. $(VENV)/bin/activate && $(PY) scripts/sync_repos.py

verify:
	pre-commit run --all-files

context-delta:
	./scripts/append_context_delta.sh

validate-log:
	$(PY) scripts/validate_context_delta.py

seed-log:
	mkdir -p docs/context
	cat > docs/context/context_delta.log.yaml <<'YAML'
entries:
  - context_delta:
      status:
        summary: >
          Seed entry: initialized orchestrator repo (amara-core).
        last_updated: 2025-08-26
      decisions:
        - date: 2025-08-26
          what: "Split into amara-core and amara-gateway."
          why: "Separate concerns for orchestration vs. gateway."
      next_actions:
        - who: me
          what: "Add schema validator and append helper"
          due: 2025-08-26
      risks:
        - "Accidental schema drift; mitigation: pre-commit validator"
YAML
	$(MAKE) validate-log

test-log:
	@echo ">> Appending a valid test entry"
	cat > /tmp/_delta_ok.yaml <<'YAML'
status:
  summary: >
    Test append entry via Makefile.
  last_updated: 2025-08-26
decisions:
  - date: 2025-08-26
    what: "Validator accepted YAML dates"
    why: "PyYAML auto-converts ISO strings"
next_actions:
  - who: me
    what: "Append a new test entry"
    due: 2025-08-26
  - who: assistant
    what: "Check that schema passes"
    due: 2025-08-26
risks:
  - "None — test only"
YAML
	./scripts/append_context_delta.sh < /tmp/_delta_ok.yaml

	@echo ">> Attempting an invalid append (should FAIL)"
	@set -e; \
	cat > /tmp/_delta_bad.yaml <<'YAML'; \
status:
  summary: >
    Invalid entry (missing risks).
  last_updated: 2025-08-26
decisions:
  - date: 2025-08-26
    what: "Bad entry for test"
    why: "Missing risks"
next_actions:
  - who: me
    what: "This should fail schema"
    due: 2025-08-26
YAML
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
