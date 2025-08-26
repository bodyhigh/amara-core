#!/usr/bin/env python3
# --- Amara Script Metadata ---
# Repo: amara-core
# Role: Check env & optional deps for embeddings/upsert flows
# Owner: core
# Secrets: none (only checks presence)
# Notes: exits non-zero on hard blockers; warns for optional bits
# --------------------------------
import os, sys, importlib

def ok(msg): print(f"[OK] {msg}")
def warn(msg): print(f"[WARN] {msg}")
def err(msg): print(f"[ERR] {msg}")

def have_pkg(name: str) -> bool:
    try:
        importlib.import_module(name); return True
    except Exception: return False

def main() -> int:
    rc = 0
    # OpenAI path
    if os.getenv("OPENAI_API_KEY"):
        ok("OPENAI_API_KEY present")
        if have_pkg("openai"): ok("openai package installed")
        else: warn("openai package not installed (pip install openai)")
    else:
        warn("OPENAI_API_KEY not set (embed.py will default to DRY unless EMBED_MODE=local)")

    # Local mode
    if os.getenv("EMBED_MODE", "") == "local":
        if have_pkg("sentence_transformers"): ok("sentence-transformers installed for local mode")
        else: err("EMBED_MODE=local but sentence-transformers not installed"); rc = 1

    # Qdrant path
    if os.getenv("QDRANT_UPSERT", "") == "1":
        if have_pkg("qdrant_client"): ok("qdrant-client installed for upsert")
        else: err("QDRANT_UPSERT=1 but qdrant-client not installed"); rc = 1

    return rc

if __name__ == "__main__":
    sys.exit(main())
