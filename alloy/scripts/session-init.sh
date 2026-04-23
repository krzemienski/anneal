#!/usr/bin/env bash
# session-init.sh — SessionStart hook.
# Non-blocking announcement that anneal-alloy is loaded. Exits 0 silently
# unless DEBUG_ANNEAL=1 is set.

set -e

if [[ "${DEBUG_ANNEAL:-0}" == "1" ]]; then
  echo "[anneal-alloy] loaded — /anneal-alloy:anneal <task> --versions N" >&2
fi

exit 0
