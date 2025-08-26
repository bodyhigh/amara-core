#!/usr/bin/env python3
# --- Amara Script Metadata ---
# Repo: amara-core
# Role: Ensure every .py/.sh/.js script starts with the standard Amara metadata header
# Owner: core
# Secrets: none
# Notes: Used by pre-commit (validate-amara-script-headers)
# --------------------------------

import sys
import re
from pathlib import Path
from typing import Iterable

HEADER = (
    r"# --- Amara Script Metadata ---\n"
    r"# Repo:\s*(amara-core|amara-gateway)\n"
)

HEADER_RE = re.compile(HEADER, re.MULTILINE)

CHECK_EXTS = {".py", ".sh", ".js"}

def iter_files(argv: Iterable[str]):
    for a in argv:
        p = Path(a)
        if p.is_file() and p.suffix in CHECK_EXTS:
            yield p

def main(argv: list[str]) -> int:
    failed = False
    files = list(iter_files(argv))
    if not files:
        return 0  # nothing to check (OK)

    for fp in files:
        try:
            text = fp.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            # unreadable files are ignored
            continue

        if not HEADER_RE.search(text):
            print(f"{fp}: missing or malformed Amara script metadata header")
            failed = True

    return 1 if failed else 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
