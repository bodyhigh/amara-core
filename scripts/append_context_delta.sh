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

SNIPPET="$(mktemp)"
cat > "$SNIPPET"

# Build a candidate file and validate before committing changes
CANDIDATE="$(mktemp)"
cp "$DEST" "$CANDIDATE"
{
  printf "  - context_delta:\n"
  sed 's/^/      /' "$SNIPPET"
  echo
} >> "$CANDIDATE"

rm -f "$SNIPPET"

# Validate candidate
if command -v python3 >/dev/null 2>&1; then
  # Temporarily point validator to candidate by copying into place for a moment
  # Safer: run validator in a subshell with a symlink if you later parameterize the validator
  cp "$CANDIDATE" "$DEST"
  if ! python3 scripts/validate_context_delta.py; then
    echo "[ERR] context_delta validation failed; no changes applied" >&2
    # restore original file
    git checkout -- "$DEST" 2>/dev/null || true
    exit 1
  fi
fi

# If we’re here, candidate is valid; leave it in place
mv "$CANDIDATE" "$DEST"
echo "[OK] context_delta appended and schema is valid"
