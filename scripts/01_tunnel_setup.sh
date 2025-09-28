#!/bin/sh
# --- Amara Script Metadata ---
# Repo: amara-gateway
# Role: Setup Cloudflare Tunnel
# Owner: bodyhigh@github.com
# Notes: Requires CLOUDFLARE_TUNNEL_TOKEN env var (can be loaded from .env alongside script)
# Secrets: reads $CLOUDFLARE_TUNNEL_TOKEN
# --------------------------------

set -euo pipefail
: "${CLOUDFLARE_TUNNEL_TOKEN:?CLOUDFLARE_TUNNEL_TOKEN is required}"

exec cloudflared tunnel run --token "${CLOUDFLARE_TUNNEL_TOKEN}"
