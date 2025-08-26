#!/usr/bin/env bash
# --- Amara Script Metadata ---
# Repo: amara-core
# Role: Pretty logging helpers (info/warn/error/ok) for shell scripts
# Owner: core
# Secrets: none
# Notes: source it: `. scripts/lib/pretty.sh`
# --------------------------------
set -euo pipefail

_color() { local c="$1"; shift; printf "\033[%sm%s\033[0m" "$c" "$*"; }
log_info() { echo -e "$(_color '36' '[INFO]') $*"; }
log_ok()   { echo -e "$(_color '32' '[OK]  ') $*"; }
log_warn() { echo -e "$(_color '33' '[WARN]') $*"; }
log_err()  { echo -e "$(_color '31' '[ERR] ') $*" 1>&2; }
