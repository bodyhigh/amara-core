#!/usr/bin/env python3
# --- Amara Script Metadata ---
# Repo: amara-core
# Role: Fail the commit if any target files contain a forbidden string/pattern
# Owner: core
# Secrets: none
# Notes: Used by multiple hooks with different --pattern/--message
# --------------------------------

import sys
import argparse
import re
from pathlib import Path
from typing import List

def read_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""

def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pattern", required=True, help="Regex to search for")
    parser.add_argument("--message", required=True, help="Message to print on match")
    parser.add_argument("files", nargs="*", help="Files to scan (pre-commit passes these)")
    args = parser.parse_args(argv)

    pat = re.compile(args.pattern, re.MULTILINE)
    failed = False

    files = [Path(f) for f in args.files] if args.files else []
    # If no files were passed (rare), bail out cleanly
    if not files:
        return 0

    for f in files:
        if not f.is_file():
            continue
        text = read_file(f)
        if not text:
            continue
        if pat.search(text):
            print(f"{f}: {args.message}")
            failed = True

    return 1 if failed else 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
