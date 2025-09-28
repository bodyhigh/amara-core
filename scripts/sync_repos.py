#!/usr/bin/env python3
# --- Amara Script Metadata ---
# Repo: amara-core
# Role: Sync/Stage allowed files from external sources into docs/context/
# Owner: core
# Secrets: none (reads public paths only; optional GITHUB_TOKEN for HTTPS)
# Notes: Controlled by docs/sources.yaml; dry-run by default; writes artifacts/sync.report.json
# --------------------------------
"""
sync_repos.py

Supported "sources.yaml" shapes:

List form (recommended):
  sources:
    - name: amara-core
      type: local
      path: .
      include: ["README.md", "docs/**/*.md"]
      exclude: ["**/.venv/**", ".git/**"]
    - name: some-repo
      type: git
      url: https://github.com/owner/repo.git
      ref: main
      include: ["docs/**/*.md", "README.md"]
      exclude: ["**/node_modules/**", ".git/**"]

Mapping form (legacy/compatible):
  sources:
    amara-core:
      type: local
      path: .
      include: [...]
      exclude: [...]

Environment:
  SYNC_DRY=1 (default)  → plan only, no file copies
  SYNC_DRY=0            → actually copy files
  DRY=1/0               → alias for SYNC_DRY
  GITHUB_TOKEN / GH_TOKEN → used for HTTPS git clone auth (http.extraheader)
"""

from __future__ import annotations
import os
import sys
import json
import shutil
import fnmatch
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

def ensure_dir(p: Path) -> None:
    """
    Ensure p is a directory.
    - If p is a symlink, create the target dir (resolving relative link).
    - If p is a regular file, remove and replace with a directory.
    - If p doesn't exist, create it.
    """
    if p.exists():
        if p.is_dir():
            return
        if p.is_symlink():
            # Resolve relative or absolute link WITHOUT requiring it to exist
            link_target = os.readlink(p)  # may be relative
            target_path = (p.parent / link_target).resolve()
            Path(target_path).mkdir(parents=True, exist_ok=True)
            return
        # Regular file (or something else): replace with a dir
        p.unlink()
        p.mkdir(parents=True, exist_ok=True)
        return
    p.mkdir(parents=True, exist_ok=True)


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
DEST_ROOT.mkdir(parents=True, exist_ok=True)


def sha1_bytes(b: bytes) -> str:
    import hashlib as _h
    h = _h.sha1()
    h.update(b)
    return h.hexdigest()


def load_yaml(p: Path) -> Dict[str, Any]:
    return yaml.safe_load(p.read_text(encoding="utf-8")) or {}


def collect_files(base: Path, includes: List[str], excludes: List[str]) -> List[Path]:
    # inclusive: union of include globs
    matched: set[Path] = set()
    for patt in includes or []:
        for path in base.rglob("*"):
            if path.is_file():
                rel = path.relative_to(base).as_posix()
                if fnmatch.fnmatch(rel, patt):
                    matched.add(path)
    # apply excludes
    results: List[Path] = []
    for p in sorted(matched):
        rel = p.relative_to(base).as_posix()
        if any(fnmatch.fnmatch(rel, ex) for ex in (excludes or [])):
            continue
        results.append(p)
    return results


def copy_one(src: Path, dst: Path, *, dry: bool) -> Tuple[str, str]:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dry:
        return ("DRY", "")
    if dst.exists():
        s = src.read_bytes()
        d = dst.read_bytes()
        if len(s) == len(d) and sha1_bytes(s) == sha1_bytes(d):
            return ("SKIP", "identical")
    shutil.copy2(src, dst)
    return ("COPIED", "")


def stage_from_base(name: str, base: Path, includes: List[str], excludes: List[str], dest_name: str, *, dry: bool) -> Dict[str, Any]:
    dest_base = DEST_ROOT / dest_name
    if not dry and dest_base.exists():
        shutil.rmtree(dest_base)
    files = collect_files(base, includes, excludes)
    copied, skipped, denied = [], [], []

    for f in files:
        # (Excludes already applied in collect; keep placeholder for symmetry)
        rel = f.relative_to(base)
        dst = dest_base / rel
        status, note = copy_one(f, dst, dry=dry)
        (copied if status == "COPIED" else skipped).append(
            {"src": f.as_posix(), "dst": dst.as_posix(), "note": note}
        )

    return {
        "name": name,
        "base": base.as_posix(),
        "dest": dest_base.as_posix(),
        "dry_run": dry,
        "counts": {
            "included": len(files),
            "copied": len([c for c in copied]),
            "skipped": len(skipped),
            "denied": len(denied),
        },
        "copied": copied,
        "skipped": skipped,
        "denied": denied,
    }


def shallow_clone(url: str, ref: str | None, dest: Path, extra_http_header: str | None = None) -> None:
    """Shallow clone repo to dest; optionally pass an extra HTTP header for HTTPS token auth."""
    if dest.exists():
        shutil.rmtree(dest)
    cmd = ["git"]
    if extra_http_header:
        cmd += ["-c", f"http.extraheader={extra_http_header}"]
    cmd += ["clone", "--depth", "1"]
    if ref:
        cmd += ["--branch", ref]
    cmd += [url, str(dest)]
    subprocess.check_call(cmd, env=os.environ)


def normalize_entry(entry: Dict[str, Any], name_fallback: str | None = None) -> tuple[str, Dict[str, Any], str]:
    """
    Returns (name, normalized_cfg, kind)
      kind ∈ {"local","git"}
    Normalized cfg for "staging step" always contains:
      base: <local path to read from>
      include: [...]
      exclude: [...]
      dest: <folder name under docs/context/sources/>
    """
    typ = entry.get("type", "local")
    name = entry.get("name") or name_fallback or "source"
    include = entry.get("include", [])
    exclude = entry.get("exclude", [])
    dest = entry.get("dest", name)

    if typ == "local":
        base = entry.get("path") or entry.get("base")
        if not base:
            raise ValueError(f"{name}: local source requires 'path' (or 'base')")
        return name, {"base": base, "include": include, "exclude": exclude, "dest": dest}, "local"

    if typ == "git":
        url = entry.get("url")
        ref = entry.get("ref", "main")
        if not url:
            raise ValueError(f"{name}: git source requires 'url'")
        # we materialize the repo into a temp dir in main()
        return name, {"_git_url": url, "_git_ref": ref, "include": include, "exclude": exclude, "dest": dest}, "git"

    raise ValueError(f"{name}: unsupported source type: {typ}")


def iter_sources(spec: Any) -> Iterable[tuple[str, Dict[str, Any]]]:
    """Yield (name, cfg) from either a list or mapping format."""
    if isinstance(spec, dict):
        for k, v in spec.items():
            if isinstance(v, dict):
                v = dict(v)
                v.setdefault("name", k)
                yield k, v
    elif isinstance(spec, list):
        for item in spec:
            if isinstance(item, dict) and ("name" in item):
                yield item["name"], item
    else:
        return


def main() -> int:
    if not SOURCES_FILE.exists():
        print(f"[ERR] missing config: {SOURCES_FILE}", file=sys.stderr)
        return 1

    cfg = load_yaml(SOURCES_FILE)
    sources_spec = cfg.get("sources")
    if not sources_spec:
        print("[ERR] docs/sources.yaml missing 'sources'", file=sys.stderr)
        return 1

    # Respect SYNC_DRY (preferred) or DRY (compat). Default: DRY (plan only).
    dry = (os.getenv("SYNC_DRY") or os.getenv("DRY") or "1") != "0"

    report: Dict[str, Any] = {"dry_run": dry, "results": []}

    # Prepare HTTPS token header if available (GitHub Actions provides GITHUB_TOKEN)
    gh_token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    http_header = f"AUTHORIZATION: bearer {gh_token}" if gh_token else None

    for raw_name, raw_cfg in iter_sources(sources_spec):
        try:
            name, norm, kind = normalize_entry(raw_cfg or {}, name_fallback=raw_name)
            if kind == "git":
                with tempfile.TemporaryDirectory(prefix=f"sync_{name}_") as td:
                    repo_dir = Path(td) / "repo"
                    url = norm["_git_url"]
                    ref = norm["_git_ref"]
                    shallow_clone(
                        url, ref, repo_dir,
                        extra_http_header=(http_header if url.startswith("http") else None),
                    )
                    res = stage_from_base(name, repo_dir, norm["include"], norm["exclude"], norm["dest"], dry=dry)
            else:
                base = Path(norm["base"]).expanduser().resolve()
                res = stage_from_base(name, base, norm["include"], norm["exclude"], norm["dest"], dry=dry)

            print(f"[OK] {name}: copied={res['counts']['copied']} skipped={res['counts']['skipped']} denied={res['counts']['denied']}")
            report["results"].append(res)

        except Exception as e:
            print(f"[ERR] {raw_name}: {e}", file=sys.stderr)
            report["results"].append({"name": raw_name, "error": str(e)})

    out = ARTIFACTS / "sync.report.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"[OK] wrote {out}")
    if dry:
        print("[sync] DRY mode (no files copied). Set SYNC_DRY=0 to write files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
