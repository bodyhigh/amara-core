#!/usr/bin/env python3
# --- Amara Script Metadata ---
# Repo: amara-core
# Role: Stage selected files from configured sources into docs/context/
# Owner: core
# Secrets: none
# Notes: Allowlist only; see docs/sources.yaml
# --------------------------------

import sys, os, shutil, fnmatch, subprocess, tempfile, pathlib, yaml
from typing import Dict, Any, List

ROOT = pathlib.Path(__file__).resolve().parents[1]
CFG  = ROOT / "docs" / "sources.yaml"
DEST = ROOT / "docs" / "context"

def log(kind:str, msg:str) -> None:
	prefix = {"info":"[INFO]","ok":"[OK]","warn":"[WARN]","err":"[ERR]"}[kind]
	print(f"{prefix} {msg}")

def load_cfg() -> Dict[str, Any]:
	with CFG.open("r", encoding="utf-8") as f:
		return yaml.safe_load(f)

def matches(path: pathlib.Path, patterns: List[str]) -> bool:
	if not patterns: return True
	rel = str(path)
	return any(fnmatch.fnmatch(rel, pat) for pat in patterns)

def stage_local(src: pathlib.Path, include: List[str], exclude: List[str], outdir: pathlib.Path):
	for p in src.rglob("*"):
		if p.is_dir(): continue
		rel = p.relative_to(src).as_posix()
		if include and not matches(pathlib.Path(rel), include): continue
		if exclude and matches(pathlib.Path(rel), exclude): continue
		dest = outdir / rel
		dest.parent.mkdir(parents=True, exist_ok=True)
		shutil.copy2(p, dest)

def stage_git(url: str, ref: str, include: List[str], exclude: List[str], outdir: pathlib.Path):
	with tempfile.TemporaryDirectory() as td:
		tdp = pathlib.Path(td)
		subprocess.check_call(["git", "clone", "--depth", "1", "--branch", ref, url, str(tdp)], stdout=subprocess.DEVNULL)
		stage_local(tdp, include, exclude, outdir)

def main() -> int:
	if not CFG.exists():
		log("err", f"Missing {CFG}")
		return 1
	conf = load_cfg()
	DEST.mkdir(parents=True, exist_ok=True)

	for src in conf.get("sources", []):
		name = src["name"]
		outdir = DEST / name
		if outdir.exists():
			shutil.rmtree(outdir)
		outdir.mkdir(parents=True, exist_ok=True)
		inc = src.get("include", [])
		exc = src.get("exclude", [])
		if src["type"] == "local":
			path = pathlib.Path(src["path"]).resolve()
			log("info", f"Sync local: {name} ← {path}")
			stage_local(path, inc, exc, outdir)
		elif src["type"] == "git":
			url = src["url"]; ref = src.get("ref", "main")
			log("info", f"Sync git: {name} ← {url}@{ref}")
			stage_git(url, ref, inc, exc, outdir)
		else:
			log("warn", f"Unknown type for {name}: {src['type']}")
		log("ok", f"Staged → {outdir}")
	log("ok", "Sync complete")
	return 0

if __name__ == "__main__":
	raise SystemExit(main())
