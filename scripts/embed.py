#!/usr/bin/env python3
# --- Amara Script Metadata ---
# Repo: amara-core
# Role: Embed files in docs/context/ and (optionally) upsert to Qdrant
# Owner: core
# Secrets: reads $OPENAI_API_KEY if mode=openai
# Notes: Modes: openai | local | dry. Uses runtime imports to keep deps optional.
# --------------------------------

import os
import sys
import json
import hashlib
import pathlib
import importlib
from typing import List, Dict, Any, Tuple

# Repo paths
ROOT = pathlib.Path(__file__).resolve().parents[1]
CTX = ROOT / "docs" / "context"
OUT = ROOT / "artifacts"
OUT.mkdir(parents=True, exist_ok=True)


# ---------- helpers ----------
def iter_files() -> List[pathlib.Path]:
	"""Collect text-like files under docs/context/ (allowlist)."""
	exts = {".md", ".yaml", ".yml", ".txt", ".conf", ".html", ".js", ".ts", ".sh", ".py"}
	files: List[pathlib.Path] = []
	for p in CTX.rglob("*"):
		if p.is_file() and p.suffix.lower() in exts:
			files.append(p)
	return files


def load_text(p: pathlib.Path) -> str:
	try:
		return p.read_text(encoding="utf-8", errors="ignore")
	except Exception:
		return ""


def chunk_text(text: str, max_tokens: int = 800) -> List[str]:
	"""
	Naive char-based chunker (~4 chars per token heuristic).
	Swap for token-aware logic later.
	"""
	max_chars = max_tokens * 4
	return [text[i : i + max_chars] for i in range(0, len(text), max_chars)] or [""]


def sha1(s: str) -> str:
	return hashlib.sha1(s.encode("utf-8")).hexdigest()


def write_manifest(records: List[Dict[str, Any]], name: str) -> None:
	outp = OUT / name
	outp.write_text(json.dumps(records, indent=2), encoding="utf-8")
	print(f"[OK] wrote {outp}")


# ---------- embedding backends ----------
def try_openai_embed(chunks: List[Tuple[str, str]]) -> List[Dict[str, Any]]:
	"""
	OpenAI embeddings (fast, cheap default).
	Requires: pip install openai; env OPENAI_API_KEY set.
	"""
	api_key = os.getenv("OPENAI_API_KEY")
	if not api_key:
		raise RuntimeError("OPENAI_API_KEY not set")

	try:
		openai_mod = importlib.import_module("openai")
	except Exception as e:
		raise RuntimeError("openai package not installed: pip install openai") from e

	OpenAI = getattr(openai_mod, "OpenAI")
	client = OpenAI(api_key=api_key)
	model = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")

	inputs = [t for _, t in chunks]
	resp = client.embeddings.create(model=model, input=inputs)
	vecs = [d.embedding for d in resp.data]

	out: List[Dict[str, Any]] = []
	for (doc_id, text), vec in zip(chunks, vecs):
		out.append({"id": doc_id, "embedding": vec, "len": len(text)})
	return out


def try_local_embed(chunks: List[Tuple[str, str]]) -> List[Dict[str, Any]]:
	"""
	Local CPU embeddings via sentence-transformers (optional).
	Requires: pip install 'sentence-transformers'
	"""
	try:
		st_mod = importlib.import_module("sentence_transformers")
	except Exception as e:
		raise RuntimeError("sentence-transformers not installed") from e

	SentenceTransformer = getattr(st_mod, "SentenceTransformer")
	model_name = os.getenv("LOCAL_EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
	model = SentenceTransformer(model_name)

	texts = [t for _, t in chunks]
	vecs = model.encode(texts, normalize_embeddings=True).tolist()

	out: List[Dict[str, Any]] = []
	for (doc_id, text), vec in zip(chunks, vecs):
		out.append({"id": doc_id, "embedding": vec, "len": len(text)})
	return out


# ---------- optional Qdrant upsert ----------
def maybe_qdrant_upsert(records: List[Dict[str, Any]]) -> None:
	"""
	Optional Qdrant upsert (requires qdrant-client).
	Controlled by env: EMBED_QDRANT_UPSERT=1  (back-compat: QDRANT_UPSERT=1)
	Honors: QDRANT_URL (preferred, e.g. http://localhost:6333), QDRANT_COLLECTION
	"""
	flag = os.getenv("EMBED_QDRANT_UPSERT", os.getenv("QDRANT_UPSERT", ""))  # back-compat
	if flag != "1":
		print("[INFO] Skipping Qdrant upsert (EMBED_QDRANT_UPSERT!=1)")
		return

	if not records:
		print("[INFO] No embeddings to upsert")
		return

	try:
		qdrant_mod = importlib.import_module("qdrant_client")
		http_mod = importlib.import_module("qdrant_client.http")
	except Exception as e:
		raise RuntimeError("qdrant-client not installed: pip install qdrant-client") from e

	QdrantClient = getattr(qdrant_mod, "QdrantClient")
	qm = getattr(http_mod, "models")

	# Preferred connection via full URL (e.g., http://qdrant:6333)
	qdrant_url = os.getenv("QDRANT_URL", "").strip()
	host = os.getenv("QDRANT_HOST", "qdrant")
	port = int(os.getenv("QDRANT_PORT", "6333"))

	if qdrant_url:
		client = QdrantClient(url=qdrant_url)
	else:
		client = QdrantClient(host=host, port=port)

	collection = os.getenv("QDRANT_COLLECTION", "amara_docs")

	# Ensure collection exists (non-destructive). Avoid recreate_collection.
	try:
		client.get_collection(collection_name=collection)
		created = False
	except Exception:
		# Create collection with vector size inferred from first record
		dim = len(records[0]["embedding"])
		client.create_collection(
			collection_name=collection,
			vectors_config=qm.VectorParams(size=dim, distance=qm.Distance.COSINE),
		)
		created = True

	points = [
		qm.PointStruct(id=r["id"], vector=r["embedding"], payload={"len": r["len"]})
		for r in records
	]
	client.upsert(collection_name=collection, points=points)
	print(f"[OK] Upserted {len(points)} vectors to Qdrant::{collection} ({'created' if created else 'existing'} collection)")


# ---------- main ----------
def main() -> int:
	files = iter_files()
	if not files:
		print("[WARN] No files found under docs/context/")
		return 0

	chunk_records: List[Tuple[str, str]] = []
	manifest: List[Dict[str, Any]] = []

	for p in files:
		text = load_text(p)
		if not text.strip():
			continue
		chunks = chunk_text(text)
		for i, ch in enumerate(chunks):
			doc_id = sha1(f"{p.as_posix()}::{i}")
			chunk_records.append((doc_id, ch))
			manifest.append({"file": p.as_posix(), "chunk": i, "id": doc_id, "len": len(ch)})

	# Always write chunk manifest
	write_manifest(manifest, "chunks.manifest.json")

	# Decide mode
	mode = os.getenv("EMBED_MODE")
	if not mode:
		mode = "openai" if os.getenv("OPENAI_API_KEY") else "dry"

	if mode == "dry":
		print("[INFO] DRY RUN: wrote chunk manifest only (set OPENAI_API_KEY or EMBED_MODE=local to embed)")
		return 0

	if mode == "openai":
		vecs = try_openai_embed(chunk_records)
	elif mode == "local":
		vecs = try_local_embed(chunk_records)
	else:
		print(f"[ERR] Unknown EMBED_MODE={mode}; use: openai | local | dry")
		return 2

	write_manifest(vecs, "chunks.embeddings.json")
	maybe_qdrant_upsert(vecs)
	return 0


if __name__ == "__main__":
	sys.exit(main())
