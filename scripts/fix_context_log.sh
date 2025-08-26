#!/bin/sh
# --- Amara Script Metadata ---
# Repo: amara-core
# Role: Detect a trailing top-level context_delta block and wrap it into entries list
# Owner: core
# Secrets: none
# Notes: Idempotent; validates after fix
# --------------------------------
set -eu
FILE="docs/context/context_delta.log.yaml"
[ -f "$FILE" ] || { echo "[ERR] $FILE not found"; exit 1; }

# Find first line number of an unindented 'status:' that is NOT already part of an entry
# We look for 'status:' at column 1 after the last closed entry block.
ORPHAN_LINE="$(awk '/^status:/{print NR}' "$FILE" | tail -1)"

if [ -z "${ORPHAN_LINE:-}" ]; then
	echo "[OK] No orphan top-level block detected."
	python3 scripts/validate_context_delta.py
	exit 0
fi

# Check if that status line is already indented 6+ spaces (belongs to a wrapped block)
if sed -n "${ORPHAN_LINE}p" "$FILE" | grep -Eq '^[[:space:]]{6}status:'; then
	echo "[OK] No orphan top-level block detected (already wrapped)."
	python3 scripts/validate_context_delta.py
	exit 0
fi

TMP_HEAD="$(mktemp)"; TMP_BODY="$(mktemp)"
sed -n "1,$((ORPHAN_LINE-1))p" "$FILE" > "$TMP_HEAD"
sed -n "${ORPHAN_LINE},\$p" "$FILE" > "$TMP_BODY"

{
	cat "$TMP_HEAD"
	echo "  - context_delta:"
	sed 's/^/      /' "$TMP_BODY"
	echo
} > "$FILE"

rm -f "$TMP_HEAD" "$TMP_BODY"

python3 scripts/validate_context_delta.py
echo "[OK] Rewrapped orphan block and schema is valid."
