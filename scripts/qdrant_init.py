#!/usr/bin/env python3
# --- Amara Script Metadata ---
# Repo: amara-core
# Role: Ensure Qdrant collection exists with sane defaults
# Owner: core
# Secrets: none (reads env only)
# Notes: Run before first embed; idempotent. Prints actual dim/distance from server.
# --------------------------------
import os
import sys
import argparse
from typing import Tuple, Any

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, HnswConfigDiff


def env(name: str, default: str | None = None) -> str | None:
	"""Get env var with default (treat empty as missing)."""
	val = os.getenv(name)
	return val if val not in (None, "") else default


def _extract_dim_distance(info: Any) -> Tuple[str, str]:
	"""
	Return (dim, distance) from CollectionInfo in a version-tolerant way.
	Handles both single-vector and multi-vector configs.
	"""
	try:
		params = info.config.params  # pydantic model
	except Exception:
		return "unknown", "unknown"

	# Newer layout: params.vectors may be VectorParams or a dict[str, VectorParams]
	vectors = getattr(params, "vectors", None)
	if vectors is None:
		# Older flat layout: params has .size / .distance
		size = getattr(params, "size", None)
		dist = getattr(params, "distance", None)
		dist = getattr(dist, "value", dist)
		return (str(size) if size is not None else "unknown", str(dist) if dist is not None else "unknown")

	# Dict (multi-vector): pick first entry
	if isinstance(vectors, dict):
		first = next(iter(vectors.values()), None)
		size = getattr(first, "size", None) if first else None
		dist = getattr(first, "distance", None) if first else None
		dist = getattr(dist, "value", dist)
		return (str(size) if size is not None else "unknown", str(dist) if dist is not None else "unknown")

	# Single VectorParams
	size = getattr(vectors, "size", None)
	dist = getattr(vectors, "distance", None)
	dist = getattr(dist, "value", dist)
	return (str(size) if size is not None else "unknown", str(dist) if dist is not None else "unknown")


def main() -> None:
	parser = argparse.ArgumentParser(description="Ensure Qdrant collection exists (idempotent).")
	parser.add_argument("--url", default=env("QDRANT_URL", "http://localhost:6333"))
	parser.add_argument("--collection", default=env("QDRANT_COLLECTION", "amara_context_v1"))
	parser.add_argument("--dim", type=int, default=int(env("EMBEDDING_DIM", "1536") or "1536"))
	parser.add_argument(
		"--distance",
		default=env("QDRANT_DISTANCE", "cosine"),
		choices=["cosine", "dot", "euclid"],
	)
	parser.add_argument(
		"--recreate",
		action="store_true",
		help="Drop & recreate if collection exists with a mismatched vector size/distance.",
	)
	parser.add_argument(
		"--skip-compat-check",
		action="store_true",
		help="Skip client/server version compatibility check (not usually needed if you pin client).",
	)
	args = parser.parse_args()

	dist_map = {"cosine": Distance.COSINE, "dot": Distance.DOT, "euclid": Distance.EUCLID}
	dist_enum = dist_map[args.distance]

	# Build client kwargs compatibly across qdrant-client versions
	cli_kwargs = {"url": args.url}
	if args.skip_compat_check or env("QDRANT_CHECK_COMPAT") in ("0", "false", "False"):
		# Some client versions accept this; try then fallback.
		cli_kwargs["check_compatibility"] = False
	try:
		cli = QdrantClient(**cli_kwargs)
	except TypeError:
		# Older client without check_compatibility arg
		cli_kwargs.pop("check_compatibility", None)
		cli = QdrantClient(**cli_kwargs)

	existing = [c.name for c in cli.get_collections().collections]
	if args.collection not in existing:
		print(f"[qdrant] creating collection '{args.collection}' (dim={args.dim}, distance={args.distance})")
		cli.create_collection(
			collection_name=args.collection,
			vectors_config=VectorParams(size=args.dim, distance=dist_enum, on_disk=True),
			hnsw_config=HnswConfigDiff(m=16, ef_construct=128),
		)
	else:
		info = cli.get_collection(args.collection)
		dim_str, dist_str = _extract_dim_distance(info)
		print(f"[qdrant] exists: '{args.collection}' dim={dim_str} distance={dist_str}")

		# Optionally reconcile on mismatch
		if args.recreate:
			want_dim = str(args.dim)
			want_dist = dist_enum.value if hasattr(dist_enum, "value") else str(dist_enum)
			if dim_str != want_dim or str(dist_str).lower() != want_dist.lower():
				print(f"[qdrant] recreating '{args.collection}' to match dim={want_dim} distance={want_dist}")
				cli.delete_collection(args.collection)
				cli.create_collection(
					collection_name=args.collection,
					vectors_config=VectorParams(size=args.dim, distance=dist_enum, on_disk=True),
					hnsw_config=HnswConfigDiff(m=16, ef_construct=128),
				)

	# Brief list for visibility
	print("[qdrant] collections:")
	for c in cli.get_collections().collections:
		print(f"- {c.name}")


if __name__ == "__main__":
	try:
		main()
	except Exception as e:
		print(f"[qdrant] ERROR: {e}", file=sys.stderr)
		sys.exit(2)
