#!/usr/bin/env python3
# --- Amara Script Metadata ---
# Repo: amara-core
# Role: Validate the schema of docs/context/context_delta.log.yaml (append-only log of context_delta entries)
# Owner: core
# Secrets: none
# Notes: Accepts YAML native dates (datetime.date) or ISO strings (YYYY-MM-DD)
# --------------------------------

import sys, re
from pathlib import Path
from typing import Any
from datetime import date, datetime

try:
    import yaml  # PyYAML
except Exception:
    print("[ERR] PyYAML not available; pip install pyyaml", file=sys.stderr)
    sys.exit(2)

LOG_PATH = Path("docs/context/context_delta.log.yaml")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")  # YYYY-MM-DD

def is_date_like(v: Any) -> bool:
    if isinstance(v, (date, datetime)):
        return True
    if isinstance(v, str) and DATE_RE.match(v):
        return True
    return False

def as_iso(v: Any) -> str:
    if isinstance(v, datetime):
        return v.date().isoformat()
    if isinstance(v, date):
        return v.isoformat()
    if isinstance(v, str):
        return v
    return str(v)

def err(msg, *, path="root", index=None):
    loc = f"{path}" + (f"[{index}]" if index is not None else "")
    print(f"[SCHEMA] {loc}: {msg}", file=sys.stderr)

def require(cond, msg, *, path="root", index=None):
    if not cond:
        err(msg, path=path, index=index)
        return False
    return True

def validate_decisions(decisions, *, path):
    ok = True
    if not require(isinstance(decisions, list), "decisions must be a list", path=path):
        return False
    for i, d in enumerate(decisions):
        if not require(isinstance(d, dict), "each decision must be a mapping", path=path, index=i):
            ok = False; continue
        if "date" in d and is_date_like(d["date"]):
            pass
        else:
            ok = False
            got = type(d.get("date")).__name__
            err(f"decision.date must be YYYY-MM-DD or YAML date, got {got}={d.get('date')!r}", path=path, index=i)
        ok &= require("what" in d and isinstance(d["what"], str) and d["what"].strip(),
                      "decision.what must be non-empty string", path=path, index=i)
        ok &= require("why" in d and isinstance(d["why"], str),
                      "decision.why must be string (can be empty)", path=path, index=i)
    return ok

def validate_next_actions(next_actions, *, path):
    ok = True
    if not require(isinstance(next_actions, list), "next_actions must be a list", path=path):
        return False
    for i, a in enumerate(next_actions):
        if not require(isinstance(a, dict), "each next_action must be a mapping", path=path, index=i):
            ok = False; continue
        ok &= require("who" in a and isinstance(a["who"], str) and a["who"] in {"me","assistant"},
                      "next_action.who must be 'me' or 'assistant'", path=path, index=i)
        ok &= require("what" in a and isinstance(a["what"], str) and a["what"].strip(),
                      "next_action.what must be non-empty string", path=path, index=i)
        if "due" in a and is_date_like(a["due"]):
            pass
        else:
            ok = False
            got = type(a.get("due")).__name__
            err(f"next_action.due must be YYYY-MM-DD or YAML date, got {got}={a.get('due')!r}", path=path, index=i)
    return ok

def validate_status(status, *, path):
    ok = True
    if not require(isinstance(status, dict), "status must be a mapping", path=path): return False
    ok &= require("summary" in status and isinstance(status["summary"], str) and status["summary"].strip(),
                  "status.summary must be non-empty string", path=path)
    if "last_updated" in status and is_date_like(status["last_updated"]):
        pass
    else:
        got = type(status.get("last_updated")).__name__
        err(f"status.last_updated must be YYYY-MM-DD or YAML date, got {got}={status.get('last_updated')!r}", path=path)
        ok = False
    return ok

def validate_risks(risks, *, path):
    ok = True
    if not require(isinstance(risks, list), "risks must be a list", path=path): return False
    for i, r in enumerate(risks):
        ok &= require(isinstance(r, str) and r.strip(), "each risk must be a non-empty string", path=path, index=i)
    return ok

def validate_entry(entry, idx):
    path = f"entries[{idx}].context_delta"
    if not require(isinstance(entry, dict) and "context_delta" in entry and isinstance(entry["context_delta"], dict),
                   "each item must be a mapping with key 'context_delta'", path=f"entries[{idx}]"):
        return False
    cd = entry["context_delta"]
    ok = True
    ok &= require("status" in cd, "missing 'status'", path=path)
    ok &= require("decisions" in cd, "missing 'decisions'", path=path)
    ok &= require("next_actions" in cd, "missing 'next_actions'", path=path)
    ok &= require("risks" in cd, "missing 'risks'", path=path)
    if "status" in cd: ok &= validate_status(cd["status"], path=f"{path}.status")
    if "decisions" in cd: ok &= validate_decisions(cd["decisions"], path=f"{path}.decisions")
    if "next_actions" in cd: ok &= validate_next_actions(cd["next_actions"], path=f"{path}.next_actions")
    if "risks" in cd: ok &= validate_risks(cd["risks"], path=f"{path}.risks")
    return ok

def main():
    if not LOG_PATH.exists():
        err(f"{LOG_PATH} not found")
        return 1
    try:
        with LOG_PATH.open("r", encoding="utf-8") as f:
            doc = yaml.safe_load(f)
    except Exception as e:
        err(f"YAML parse error: {e}")
        return 1
    ok = True
    if not (isinstance(doc, dict) and "entries" in doc):
        err("top-level must be a mapping with key 'entries'")
        return 1
    entries = doc["entries"]
    if not (isinstance(entries, list) and len(entries) > 0):
        err("'entries' must be a non-empty list", path="entries")
        return 1
    for i, entry in enumerate(entries):
        ok &= validate_entry(entry, i)
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
