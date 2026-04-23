#!/usr/bin/env bash
# orchestrate.sh — anneal-alloy pipeline implementation.
# Implements the 7-stage pipeline with N parallel Prometheus-Alloy variants +
# Synthesizer.
#
# Invocation:
#   orchestrate.sh <task> [--versions N] [--loop] [--type <category>]
#
# Behavior:
#   - Parse CLI args
#   - Create run directory under ${ANNEAL_RUNS_ROOT:-./.anneal/runs}/{run_id}/
#   - Delegate the actual agent dispatch to the Claude Code harness via the
#     command/skill contract. This script's job is to serialize the stages and
#     enforce the N-parallel discipline for Stage 4.
#
# This script deliberately does NOT call the `claude` CLI directly — in the
# anneal-alloy model, the slash command (/anneal-alloy:anneal) is invoked
# inside a Claude Code session, and the session's harness dispatches the
# agents. This script exists to:
#   1. Validate input
#   2. Compute run_id + directory layout
#   3. Define the parallel fan-out contract the harness should honor
#   4. Provide the exact xargs invocation that produces N concurrent planner
#      jobs (the harness translates this into its own agent-spawn machinery)
#
# The Stage 4 fan-out command is emitted to stdout for the harness to execute.

set -euo pipefail

# ----------------------------- input parsing ---------------------------------

TASK=""
VERSIONS=5
LOOP=0
TYPE=""
MAX_ITERATIONS=3

while [[ $# -gt 0 ]]; do
  case "$1" in
    --versions)
      VERSIONS="$2"
      shift 2
      ;;
    --loop)
      LOOP=1
      shift
      ;;
    --type)
      TYPE="$2"
      shift 2
      ;;
    --no-red-team|--no-validate)
      echo "[warn] refused flag: $1 (invariant enforcement — ignored)" >&2
      shift
      ;;
    *)
      # First non-flag argument is the task
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
  echo "[error] task is required. Usage: orchestrate.sh <task> [--versions N]" >&2
  exit 2
fi

# Range check: --versions must be in [2, 7]
if ! [[ "$VERSIONS" =~ ^[0-9]+$ ]]; then
  echo "[error] --versions must be an integer, got '$VERSIONS'" >&2
  exit 2
fi
if (( VERSIONS < 2 )); then
  echo "[error] --versions 1 is not a tournament. Use /anneal-cast:anneal for single-planner work." >&2
  exit 2
fi
if (( VERSIONS > 7 )); then
  echo "[error] --versions $VERSIONS exceeds cap of 7. Synthesizer signal-to-noise collapses beyond 7." >&2
  exit 2
fi

# Unbounded loop flag
if (( LOOP == 1 )); then
  MAX_ITERATIONS=999999
fi

# ----------------------------- bias selection --------------------------------

case "$VERSIONS" in
  2)
    BIASES=(correctness minimalist)
    ;;
  3)
    BIASES=(correctness minimalist defensive)
    ;;
  4)
    BIASES=(correctness minimalist defensive performance)
    ;;
  5)
    BIASES=(correctness minimalist defensive performance ux)
    ;;
  6)
    BIASES=(correctness minimalist defensive performance ux verification)
    ;;
  7)
    BIASES=(correctness minimalist defensive performance ux verification migration)
    ;;
esac

# ----------------------------- run setup -------------------------------------

TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
# Slug from task: first 32 chars, lowercase, only alnum and hyphens
SLUG="$(echo "$TASK" | tr '[:upper:]' '[:lower:]' | tr -c 'a-z0-9' '-' | sed 's/--*/-/g; s/^-//; s/-$//' | cut -c1-32)"
RUN_ID="anneal-${TIMESTAMP}-${SLUG}"
RUNS_ROOT="${ANNEAL_RUNS_ROOT:-${PWD}/.anneal/runs}"
RUN_ROOT="${RUNS_ROOT}/${RUN_ID}"

mkdir -p "${RUN_ROOT}"/{plan,variants,reviews/hephaestus-evidence}

# Write initial state.json
cat > "${RUN_ROOT}/state.json" <<EOF
{
  "run_id": "${RUN_ID}",
  "architecture": "alloy",
  "task": $(printf '%s' "$TASK" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))'),
  "versions": ${VERSIONS},
  "biases": $(printf '%s\n' "${BIASES[@]}" | python3 -c 'import json,sys; print(json.dumps([l.strip() for l in sys.stdin if l.strip()]))'),
  "type": "${TYPE:-auto}",
  "max_iterations": ${MAX_ITERATIONS},
  "iteration": 1,
  "stage": 1,
  "started_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF

# ----------------------------- pipeline contract -----------------------------
# Output the contract the harness should execute. This is the "plan" the
# Claude Code session should follow when processing /anneal-alloy:anneal.

cat <<ORCHESTRATION_PLAN
ANNEAL-ALLOY ORCHESTRATION PLAN
===============================
run_id:        ${RUN_ID}
architecture:  alloy
task:          ${TASK}
versions:      ${VERSIONS}
biases:        ${BIASES[*]}
output:        ${RUN_ROOT}/
max_iter:      ${MAX_ITERATIONS}

STAGE 1 · Intent Gate
  - Classify task shape; reject unsafe inputs
  - Write ${RUN_ROOT}/state.json (already initialized)

STAGE 2 · Probe
  - Enumerate ~/.claude/skills/*/SKILL.md and .claude/skills/*/SKILL.md
  - Scan project repo surface
  - Write ${RUN_ROOT}/reviews/probe.md

STAGE 3 · Enrich (Metis)
  - Invoke agent 'metis' with task + probe
  - Envelope → ${RUN_ROOT}/reviews/metis-envelope.yaml
  - On BLOCK with clarifying_questions: halt + ABORT

STAGE 4 · Plan (Tournament)
  - Spawn ${VERSIONS} parallel Prometheus-Alloy agents, one per bias.
  - Parallel invocation contract (xargs-compatible):

      printf '%s\\n' ${BIASES[*]} | xargs -P \$(sysctl -n hw.ncpu 2>/dev/null || nproc) -I {} \\
        claude-agent-spawn prometheus-alloy \\
          --bias {} \\
          --task "${TASK}" \\
          --metis ${RUN_ROOT}/reviews/metis-envelope.yaml \\
          --probe ${RUN_ROOT}/reviews/probe.md \\
          --output ${RUN_ROOT}/variants/variant-\$(bias_index {})-{}.md

    (The harness translates claude-agent-spawn into its own dispatch.)
  - Wait for all ${VERSIONS} variant files to exist.
  - Invoke agent 'synthesizer' with all variants + metis + probe.
    Outputs: ${RUN_ROOT}/plan/plan.md, phase-NN-*.md, synthesis-provenance.md
  - Invoke agent 'momus' with the BLENDED plan + provenance.
    Envelope → ${RUN_ROOT}/reviews/momus-envelope.yaml

STAGE 5 · Review (parallel)
  - Spawn 3 Red-Team agents in parallel:
      redteam-security, redteam-scope, redteam-assumptions
    Each reads plan/*.md + prior envelopes.
    Envelopes → ${RUN_ROOT}/reviews/redteam-{role}-envelope.yaml
  - Wait for all 3.
  - Invoke agent 'oracle' with all prior envelopes + provenance.
    Envelope → ${RUN_ROOT}/reviews/oracle-envelope.yaml

STAGE 6 · Validate (Hephaestus)
  - Only if Oracle returned SAFE or CAUTION.
  - Invoke agent 'hephaestus' with approved plan.
    Evidence → ${RUN_ROOT}/reviews/hephaestus-evidence/
    Verdict → ${RUN_ROOT}/reviews/hephaestus-verdict.yaml

STAGE 7 · Emit / Re-loop (Atlas)
  - Invoke agent 'atlas' with all envelopes + evidence.
  - Atlas computes rollup and either:
      EMIT    → write XML + plan dir; print next-step command
      RE_LOOP → fold blocking_issues into next Metis directives, route to
                Stage 1 (not Synthesizer). Increment iteration.
      ABORT   → print irreducible BLOCK reasons, exit non-zero.

Re-loop routing:
  On FAIL, Alloy routes to STAGE 1 (Intent Gate) — NOT to Synthesizer.
  A failed synthesis suggests the bias mix was wrong; regenerate the whole
  tournament with the failure as a new Metis constraint.

END OF PLAN
ORCHESTRATION_PLAN

exit 0
