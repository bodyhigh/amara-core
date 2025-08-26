#!/usr/bin/env python3
# --- Amara Script Metadata ---
# Repo: amara-core
# Role: Sync/Stage allowed files from external sources into docs/context/
# Owner: core
# Secrets: none (reads public paths only)
# Notes: Controlled by docs/sources.yaml; dry-run by default; idempotent; writes a JSON report.
# --------------------------------
import os, sys, json, shutil, fnmatch, hashlib
from pathlib import Path
from typing import Dict, Any, List, Tuple

try:
    import yaml  # PyYAML
except Exception:
    print("[ERR] PyYAML not installed. Run: pip install pyyaml", file=sys.stderr)
    sys.exit(2)

ROOT = Path(__file__).resolve().parents[1]
SOURCES_FILE = ROOT / "docs" / "sources.yaml"
DEST_ROOT = ROOT / "docs" / "context" / "sources"
ARTIFACTS = ROOT / "artifacts"
ARTIFACTS.mkdir(parents=True, exist_ok=True)

def sha1_bytes(b: bytes) -> str:
    import hashlib as _h
    h = _h.sha1(); h.update(b); return h.hexdigest()

def load_yaml(p: Path) -> Dict[str, Any]:
    return yaml.safe_load(p.read_text(encoding="utf-8"))

def expand_globs(base: Path, patterns: List[str]) -> List[Path]:
    out: List[Path] = []
    for pat in patterns:
        # support both recursive ** and simple globs
        out += list(base.glob(pat))
    # flatten directories into their files
    files: List[Path] = []
    for p in out:
        if p.is_file(): files.append(p)
        elif p.is_dir(): files += [q for q in p.rglob("*") if q.is_file()]
    return sorted(set(files))

def is_denied(path: Path, denies: List[str], base: Path) -> bool:
    rel = path.relative_to(base).as_posix()
    for pat in denies:
        if fnmatch.fnmatch(rel, pat):
            return True
    return False

def copy_one(src: Path, dst: Path, *, dry: bool) -> Tuple[str, str]:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dry:
        return ("DRY", "")
    # short-circuit if content equal
    if dst.exists():
        s = src.read_bytes(); d = dst.read_bytes()
        if len(s) == len(d) and sha1_bytes(s) == sha1_bytes(d):
            return ("SKIP", "identical")
    shutil.copy2(src, dst)
    return ("COPIED", "")

def sync_source(name: str, cfg: Dict[str, Any], *, dry: bool) -> Dict[str, Any]:
    """
    cfg:
      type: local
      base: /path/to/repo-or-folder
      include: [ "README.md", "docs/**/*.md", ... ]
      exclude: [ "node_modules/**", ".git/**", ... ]
      dest:    "gateway"   (folder name under docs/context/sources/)
    """
    stype = cfg.get("type", "local")
    if stype != "local":
        raise ValueError(f"Unsupported source.type={stype}; start with 'local'")

    base = Path(cfg["base"]).expanduser().resolve()
    if not base.exists():
        raise FileNotFoundError(f"source base not found: {base}")
    include = cfg.get("include", [])
    exclude = cfg.get("exclude", [])
    dest_name = cfg.get("dest", name)

    dest_base = DEST_ROOT / dest_name
    files = expand_globs(base, include)
    copied = []; skipped = []; denied = []

    for f in files:
        if is_denied(f, exclude, base=base):
            denied.append(f.as_posix()); continue
        rel = f.relative_to(base)
        dst = dest_base / rel
        status, note = copy_one(f, dst, dry=dry)
        (copied if status == "COPIED" else skipped).append({"src": f.as_posix(), "dst": dst.as_posix(), "note": note})

    return {
        "name": name,
        "base": base.as_posix(),
        "dest": dest_base.as_posix(),
        "dry_run": dry,
        "copied": copied,
        "skipped": skipped,
        "denied": denied,
        "counts": {
            "included": len(files),
            "copied": len([c for c in copied if True]),
            "skipped": len(skipped),
            "denied": len(denied),
        },
    }

def main() -> int:
    if not SOURCES_FILE.exists():
        print(f"[ERR] missing config: {SOURCES_FILE}", file=sys.stderr)
        return 1
    cfg = load_yaml(SOURCES_FILE)
    sources = cfg.get("sources", {})
    if not isinstance(sources, dict) or not sources:
        print("[ERR] docs/sources.yaml missing 'sources' mapping", file=sys.stderr)
        return 1

    DEST_ROOT.mkdir(parents=True, exist_ok=True)
    dry = os.getenv("SYNC_DRY", "1") != "0"

    report = {"dry_run": dry, "results": []}
    for name, scfg in sources.items():
        try:
            res = sync_source(name, scfg or {}, dry=dry)
            print(f"[OK] {name}: copied={res['counts']['copied']} skipped={res['counts']['skipped']} denied={res['counts']['denied']}")
            report["results"].append(res)
        except Exception as e:
            print(f"[ERR] {name}: {e}", file=sys.stderr)
            report["results"].append({"name": name, "error": str(e)})

    (ARTIFACTS / "sync.report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"[OK] wrote {ARTIFACTS / 'sync.report.json'}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
