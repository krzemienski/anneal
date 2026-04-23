---
description: Run the Alloy Tournament Consensus architecture — N parallel biased planners, synthesized into one plan, with always-on red team and functional validation.
argument-hint: "<task description> [--versions N] [--loop] [--type ultrabrain|deep|quick]"
---

# /anneal-alloy:anneal

You are invoking the **Alloy** architecture — the Tournament Consensus proposal of the Anneal plugin family. N parallel Prometheus-Alloy variants compete with different biases; a Synthesizer blends their best material into one plan; Momus audits the blend; Red-Team Trinity attacks it from three angles; Oracle renders the bird's-eye verdict; Hephaestus builds the artifact for real; Atlas emits XML + plan directory.

## Invariants (non-negotiable — refuse to start if violated)

1. **Red team always runs.** Security · Scope · Assumptions in parallel.
2. **Validation always runs.** Hephaestus builds the real artifact.
3. **Dual output.** XML prompt + plan directory.
4. **Skill enrichment.** Probe scans user + project skills.
5. **Unbounded re-loop on FAIL.** Failure folds into constraints.
6. **Parallelization by default.** Planners, red team, validators fan out.
7. **Category routing, not model picking.**

## Input parsing

- `$1`: the task string. If empty, prompt the user for a task and abort if still empty.
- `--versions N`: sets parallel planner count. Default **5**. Range **[2, 7]**. Refuse `--versions 1` (that's Cast) and `--versions 8+` (signal-to-noise collapses).
- `--loop`: unbounded re-loop (no cap on retries). Default caps at 3 iterations.
- `--type <category>`: `ultrabrain` (most thought), `deep` (standard), `quick` (fast path). Default inferred from task shape.

## Execution — the 7 stages

Run `${CLAUDE_PLUGIN_ROOT}/scripts/orchestrate.sh` with the parsed arguments. The orchestrator implements:

### Stage 1 · Intent Gate
- Classify task shape (code, docs, plan, infrastructure, unknown).
- Reject unsafe inputs (secrets leaked, destructive commands without scope).
- Write `~/Desktop/anneal-runs/{run_id}/state.json` with initial state.

### Stage 2 · Probe
- Invoke the **Explore** capability (or `explore` skill if available) over the project root.
- Enumerate `~/.claude/skills/*/SKILL.md` and `.claude/skills/*/SKILL.md`.
- Write probe report to `reviews/probe.md`.

### Stage 3 · Enrich (Metis)
- Spawn the `metis` agent with the task + probe report.
- Metis returns an envelope per `_shared/plan-reviewer-schema.md`.
- If verdict is **BLOCK** with clarifying questions → halt, surface questions, **ABORT**.
- Otherwise persist envelope to `reviews/metis-envelope.yaml` and extract directives.

### Stage 4 · Plan (Tournament — Alloy-specific)

This is the stage that differentiates Alloy from Cast and Temper.

1. **Bias selection** (see `docs/synthesis-algorithm.md` § Bias Selection):
   - N=2 → correctness, minimalist
   - N=3 → correctness, minimalist, defensive
   - N=5 → correctness, minimalist, defensive, performance, ux
   - N=7 → all five plus verification, migration

2. **Parallel fan-out.** Spawn N instances of the `prometheus-alloy` agent using `xargs -P $(sysctl -n hw.ncpu 2>/dev/null || nproc)`. Each receives:
   - Same Metis directives
   - Same probe report
   - Different `bias` parameter from step 1
   - Output path: `variants/variant-{I}-{bias}.md`

3. **Wait for all N to complete.** Use `wait` in the orchestrator script. Do not proceed until every variant file exists.

4. **Invoke Synthesizer.** Spawn the `synthesizer` agent with:
   - All N variant markdown files
   - The Metis directives (for contradiction resolution)
   - The probe report
   Synthesizer outputs:
   - `plan/plan.md` and `plan/phase-NN-*.md` (the blended plan)
   - `synthesis-provenance.md` (per-phase attribution)

5. **Invoke Momus** on the BLENDED plan (not on variants). Momus reads `plan/*.md`. Output: `reviews/momus-envelope.yaml`.

6. If Momus returns **BLOCK**: route to stage-4 re-loop — regenerate the tournament with Momus's findings added as constraints. Max 2 stage-4 re-loops (then escalate to full re-loop via Intent Gate).

### Stage 5 · Review (parallel)

Spawn the three Red-Team agents in parallel:
- `redteam-security`
- `redteam-scope`
- `redteam-assumptions`

**Dispatch mechanics (load-bearing):** In a SINGLE assistant message, emit three Task tool calls (one per adversary). Do NOT set `run_in_background: true` — that makes the dispatches fire-and-forget and the pipeline stops. Parallelism comes from batching Task calls in one message, which the runtime executes concurrently. Wait for all three envelope responses before invoking Oracle. Persist envelopes to `reviews/redteam-*-envelope.yaml`.

Then spawn **Oracle** with all four prior envelopes (metis, momus, three redteam). Oracle outputs `reviews/oracle-envelope.yaml`.

### Stage 6 · Validate (Hephaestus)
Spawn `hephaestus` with the approved plan. Hephaestus:
- Builds the real artifact in a scratch worktree
- Captures build + runtime evidence (no mocks, no test files)
- Writes evidence under `reviews/hephaestus-evidence/`
- Returns PASS or FAIL

### Stage 7 · Emit / Re-loop (Atlas)
Spawn `atlas` with all envelopes + evidence. Atlas computes the rollup:

```yaml
rollup:
  overall_verdict: <worst-of-all-envelopes>
  gate_status:
    metis: ...
    momus: ...
    red_team_trinity: N/3 PASS
    oracle: ...
    hephaestus: PASS|FAIL
  simultaneous_pass: <bool>
  emission_decision: EMIT|RE_LOOP|ABORT
```

**EMIT** iff `simultaneous_pass == true` AND `overall_verdict ∈ {SAFE, CAUTION}`.

If EMIT:
- Atlas writes `~/Desktop/anneal-runs/{run_id}/alloy-{run_id}.xml` per `docs/emission-format.md`.
- Atlas writes `~/Desktop/anneal-runs/{run_id}/plan/plan.md` and phase files.
- Print to stdout: run_id, architecture=alloy, verdict, files written, next-step command for the fresh Claude Code session.

If RE_LOOP:
- **Route back to Stage 1 (Intent Gate)** — NOT to Synthesizer. A failed synthesis suggests the bias mix was wrong, so the whole tournament re-runs.
- Fold all blocking_issues into the next iteration's Metis directives.
- Increment iteration counter. Respect `--loop` cap if not set to unbounded.

If ABORT:
- Print the irreducible BLOCK reasons and exit non-zero.

## Success criteria

- XML file under `~/Desktop/anneal-runs/{run_id}/alloy-{run_id}.xml` following the semantic-XML schema
- Plan directory with `plan.md` + phase-NN-*.md files
- `synthesis-provenance.md` showing per-phase variant attribution
- All N variant files preserved under `variants/`
- `rollup.yaml` with `emission_decision: EMIT`
- Hephaestus evidence is non-empty, non-fabricated

## Refused flags

- `--no-red-team` — logged, ignored. Red team is invariant 1.
- `--no-validate` — logged, ignored. Validation is invariant 2.
- `--versions 1` — "use `/anneal-cast:anneal` for single-planner work."
- `--versions 8` or higher — "synthesizer signal-to-noise collapses beyond 7."
