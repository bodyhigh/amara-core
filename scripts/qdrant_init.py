#!/usr/bin/env python3
# --- Amara Script Metadata ---
# Repo: amara-core
# Role: Ensure Qdrant collection exists with sane defaults
# Owner: core
# Secrets: none (reads env only)
# Notes: Run before first embed; idempotent
# --------------------------------
import os, sys, argparse
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, HnswConfigDiff

def env(k, d=None):
    v = os.getenv(k)
    return v if v not in (None, "") else d

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--url", default=env("QDRANT_URL", "http://localhost:6333"))
    p.add_argument("--collection", default=env("QDRANT_COLLECTION", "amara_context_v1"))
    p.add_argument("--dim", type=int, default=int(env("EMBEDDING_DIM", "1536")))
    p.add_argument("--distance", default=env("QDRANT_DISTANCE", "cosine"), choices=["cosine","dot","euclid"])
    args = p.parse_args()

    dist = {"cosine": Distance.COSINE, "dot": Distance.DOT, "euclid": Distance.EUCLID}[args.distance]
    cli = QdrantClient(url=args.url)

    existing = [c.name for c in cli.get_collections().collections]
    if args.collection not in existing:
        print(f"[qdrant] creating collection '{args.collection}' (dim={args.dim}, distance={args.distance})")
        cli.create_collection(
            collection_name=args.collection,
            vectors_config=VectorParams(size=args.dim, distance=dist, on_disk=True),
            hnsw_config=HnswConfigDiff(m=16, ef_construct=128),
        )
    else:
        info = cli.get_collection(args.collection)
        dim = getattr(info.config.params, "size", "n/a")
        print(f"[qdrant] exists: '{args.collection}' dim={dim} distance={args.distance}")

    # brief list
    for c in cli.get_collections().collections:
        print(f"- {c.name}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[qdrant] ERROR: {e}", file=sys.stderr)
        sys.exit(2)
