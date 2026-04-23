#!/usr/bin/env bash
#
# orchestrate.sh — Driver script for the Temper deepen loop.
#
# Usage:
#   orchestrate.sh session-init
#     Called by the SessionStart hook. Ensures .anneal/ exists, no-op if state is fresh.
#
#   orchestrate.sh guard-test-files
#     Called by the PreToolUse (Write|Edit) hook. Aborts if an agent tries to create
#     *.test.*, *.spec.*, or *_test.* files (Iron Rule: no tests).
#
#   orchestrate.sh deepen <run_id> <task> <depth_cap>
#     Runs the Temper deepen loop. Expected to be invoked by the /anneal-temper:anneal
#     command after Metis completes. Emits state updates and delegates to the
#     claude CLI for agent spawns.
#
#   orchestrate.sh converge-check <depth> <scores_json> <cap>
#     Thin wrapper over convergence-check.py. Returns its exit code (0/1/2).
#
# Design notes:
#   - This script does NOT spawn LLM agents directly. In Claude Code, agent
#     invocation is the harness's job (via the Task tool, invoked from the
#     /anneal-temper:anneal command). This script provides filesystem glue,
#     state persistence, and the convergence-check shell wrapper.
#   - All state lives under .anneal/ at the project root.
#   - ${CLAUDE_PLUGIN_ROOT} is the plugin's absolute path, injected by the harness.

set -euo pipefail

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
STATE_DIR=".anneal"
STATE_FILE="${STATE_DIR}/temper-state.json"
CONVERGENCE_CHECK="${PLUGIN_ROOT}/scripts/convergence-check.py"

log() {
  printf '[orchestrate.sh] %s\n' "$*" >&2
}

cmd_session_init() {
  mkdir -p "${STATE_DIR}"
  if [[ ! -f "${STATE_FILE}" ]]; then
    cat > "${STATE_FILE}" <<EOF
{
  "architecture": "temper",
  "phase": "idle",
  "current_depth": 0,
  "depth_scores": [],
  "depth_cap": 3,
  "convergence": null
}
EOF
    log "initialized ${STATE_FILE}"
  fi
}

cmd_guard_test_files() {
  # Read tool call JSON from stdin. Harness passes it on PreToolUse hook.
  # If we can't parse stdin, fail open (the plugin's Iron Rules are advisory,
  # not a hard block).
  local payload
  payload="$(cat || true)"
  if [[ -z "${payload}" ]]; then
    exit 0
  fi
  local file_path
  file_path="$(printf '%s' "${payload}" | python3 -c '
import json, sys
try:
    d = json.load(sys.stdin)
    print(d.get("tool_input", {}).get("file_path", ""))
except Exception:
    pass
' 2>/dev/null || true)"
  if [[ -z "${file_path}" ]]; then
    exit 0
  fi
  if [[ "${file_path}" =~ \.(test|spec)\.(ts|tsx|js|jsx|py|rb|go|rs)$ ]] \
    || [[ "${file_path}" =~ _test\.(py|go|rs)$ ]]; then
    printf 'BLOCKED: anneal-temper forbids test files (Iron Rule). File: %s\n' "${file_path}" >&2
    exit 2
  fi
  exit 0
}

cmd_converge_check() {
  local depth="$1"
  local scores_json="$2"
  local cap="$3"
  local payload
  payload=$(printf '{"depth": %s, "scores": %s, "cap": %s}' "${depth}" "${scores_json}" "${cap}")
  printf '%s' "${payload}" | python3 "${CONVERGENCE_CHECK}"
}

cmd_deepen() {
  local run_id="$1"
  local task="$2"
  local cap="${3:-3}"
  mkdir -p "${STATE_DIR}"
  cat > "${STATE_FILE}" <<EOF
{
  "architecture": "temper",
  "run_id": "${run_id}",
  "task": "${task}",
  "phase": "deepen-loop",
  "current_depth": 0,
  "depth_scores": [],
  "depth_cap": ${cap},
  "convergence": null
}
EOF
  log "deepen loop initialized for run_id=${run_id} task=${task} cap=${cap}"
  log "state written to ${STATE_FILE}"
  log ""
  log "NOTE: The actual agent spawns (Prometheus-Temper, Red-Team Trinity,"
  log "Momus, Deepen-Loop orchestrator) are issued by Claude Code via the Task"
  log "tool from the /anneal-temper:anneal command. This script only seeds the"
  log "state file and exposes the convergence-check wrapper."
  log ""
  log "Next: the orchestrator calls back into this script with:"
  log "  ${0} converge-check <depth> '[s_0, s_1, ...]' ${cap}"
}

usage() {
  cat <<EOF
Usage: ${0} <command> [args...]

Commands:
  session-init
  guard-test-files
  deepen <run_id> <task> <depth_cap>
  converge-check <depth> <scores_json_array> <cap>
EOF
}

main() {
  local cmd="${1:-}"
  shift || true
  case "${cmd}" in
    session-init)
      cmd_session_init "$@"
      ;;
    guard-test-files)
      cmd_guard_test_files "$@"
      ;;
    deepen)
      cmd_deepen "$@"
      ;;
    converge-check)
      cmd_converge_check "$@"
      ;;
    ""|-h|--help)
      usage
      exit 0
      ;;
    *)
      usage
      log "unknown command: ${cmd}"
      exit 1
      ;;
  esac
}

main "$@"
