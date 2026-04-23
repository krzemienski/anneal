#!/usr/bin/env bash
# orchestrate.sh — Cast pipeline driver.
#
# This script is a convenience wrapper around the seven-stage Cast pipeline.
# The slash command (commands/anneal.md) is the authoritative spec — this
# script implements the same flow end-to-end for shell-driven invocation.
#
# Usage:
#   orchestrate.sh "<task description>" [--fast]
#
# The --fast flag is accepted and ignored (Cast is already the fast path).
#
# Requires: bash 4+, python3, claude CLI on PATH.

set -euo pipefail

# ----- Arg parsing ---------------------------------------------------------

TASK=""
FAST_FLAG=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --fast)
            FAST_FLAG=1
            shift
            ;;
        --help|-h)
            cat <<EOF
Cast — Linear single-pour plan-review pipeline.

Usage:
  $0 "<task>" [--fast]

The --fast flag is a no-op; Cast is already the fast path in the Anneal
family. It exists for CLI symmetry with alloy and temper.

Example:
  $0 "fix pagination bug in src/feed/list.ts"
EOF
            exit 0
            ;;
        *)
            if [[ -z "$TASK" ]]; then
                TASK="$1"
            else
                TASK="$TASK $1"
            fi
            shift
            ;;
    esac
done

if [[ -z "$TASK" ]]; then
    echo "error: no task provided. Usage: $0 \"<task>\"" >&2
    exit 1
fi

# ----- Environment --------------------------------------------------------

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
RUNS_ROOT="${ANNEAL_RUNS_ROOT:-${PWD}/.anneal/runs}"
TIMESTAMP="$(date +%y%m%d-%H%M)"
SLUG="$(echo "$TASK" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g' | sed -E 's/^-+|-+$//g' | cut -c1-40)"
RUN_ID="anneal-${TIMESTAMP}-${SLUG}"
RUN_DIR="${RUNS_ROOT}/${RUN_ID}"
STAGING_DIR="${RUN_DIR}/.staging"
PLAN_DIR="${STAGING_DIR}/plan"
EVIDENCE_DIR="${RUN_DIR}/evidence"

mkdir -p "$RUN_DIR" "$STAGING_DIR" "$PLAN_DIR" "$EVIDENCE_DIR"

# ----- Banner -------------------------------------------------------------

cat <<EOF
========================================================================
 Anneal · Cast · v0.1.0
 task     : $TASK
 run_id   : $RUN_ID
 run_dir  : $RUN_DIR
 fast     : $FAST_FLAG  (ignored — Cast is already the fast path)
========================================================================
EOF

# ----- Stage driver helpers ----------------------------------------------

log_stage() {
    local stage_num="$1"
    local stage_name="$2"
    printf "\n[stage %s] %s\n" "$stage_num" "$stage_name"
}

# In a real invocation, each stage dispatches to a Claude agent using the
# claude CLI. The dispatch below prints the agent and task; the actual
# orchestration is performed by the /anneal-cast:anneal slash command
# which calls Task/agent APIs directly.
#
# This shell script exists for two reasons:
#  1. Document the exact stage order so external tooling can replicate it.
#  2. Provide a dry-run mode where a human can walk the pipeline manually.
#
# The script deliberately does NOT attempt to replace the slash command —
# the slash command has access to Task dispatch, parallel agent launching,
# and hook integration that shell cannot replicate.

dispatch_agent() {
    local agent_name="$1"
    local stage_label="$2"
    printf "  -> dispatch %s (%s)\n" "$agent_name" "$stage_label"
    printf "     (invoke via: claude --agent %s < <task-input>)\n" "$agent_name"
}

# ----- Pipeline -----------------------------------------------------------

log_stage 1 "Intent Gate"
echo "  task classified, routing to probe"

log_stage 2 "Probe"
echo "  enumerate files, skills, docs"

log_stage 3 "Enrich"
dispatch_agent "metis" "pre-plan consultant"

log_stage 4 "Plan"
dispatch_agent "prometheus-cast" "single-pour planner"
dispatch_agent "momus" "post-plan reviewer"

log_stage 5 "Review"
echo "  spawning Red-Team Trinity in parallel:"
dispatch_agent "redteam-security" "parallel"
dispatch_agent "redteam-scope" "parallel"
dispatch_agent "redteam-assumptions" "parallel"
echo "  after trio returns:"
dispatch_agent "oracle" "bird's-eye synthesizer"

log_stage 6 "Validate"
dispatch_agent "hephaestus" "functional validator"

log_stage 7 "Emit"
dispatch_agent "atlas" "XML + plan emitter"

cat <<EOF

------------------------------------------------------------------------
 Cast pipeline dispatch complete.

 For the authoritative execution path with Task-parallel agent launching,
 use the slash command:

   /anneal-cast:anneal "$TASK"

 Emitted artifacts (on successful EMIT) land at:

   $RUN_DIR/
     cast-$RUN_ID.xml
     plan/plan.md
     plan/phase-*.md
     rollup.yaml
     evidence/
------------------------------------------------------------------------
EOF
