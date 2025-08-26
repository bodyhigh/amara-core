#!/bin/sh
# --- Amara Script Metadata ---
# Repo: amara-core
# Role: Append a context_delta snippet to docs/context/context_delta.log.yaml (entries list) + validate
# Owner: core
# Secrets: none
# Notes: Treats stdin as the *body* of context_delta (status/decisions/next_actions/risks)
# --------------------------------

set -eu
DEST="docs/context/context_delta.log.yaml"
mkdir -p "$(dirname "$DEST")"

# Ensure the file has the proper root
if [ ! -s "$DEST" ]; then
	printf "entries:\n" > "$DEST"
fi

TMP="$(mktemp)"
cat > "$TMP"

# Always wrap as a new list item under entries
{
	printf "  - context_delta:\n"
	# indent the snippet by 6 spaces
	sed 's/^/      /' "$TMP"
	echo
} >> "$DEST"

rm -f "$TMP"

# Validate syntax + schema
if command -v python3 >/dev/null 2>&1; then
	python3 scripts/validate_context_delta.py
fi

echo "[OK] context_delta appended to $DEST and schema is valid"
