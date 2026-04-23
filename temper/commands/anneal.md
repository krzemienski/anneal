---
description: Run Temper (fixed-point deepen) against a task. Inline red team every depth, Momus 0-100 scoring, convergence by variance/delta/cap. Emits XML prompt + plan directory.
argument-hint: "<task description> [--depth N] [--deepen] [--type ultrabrain|deep|quick] [--loop]"
---

# /anneal-temper:anneal

You are invoking the **Temper** architecture — fixed-point deepen plan generation with **inline red team at every depth**, Momus 0-100 scoring, and deterministic convergence (variance / delta / cap).

## Input

The user's task and flags are passed as `$1` (and optionally further args). If empty, prompt for the task.

**Supported flags:**
- `--depth N` — override default depth cap (default 3, range 1-5).
- `--deepen` — explicit alias for Temper mode (redundant; this plugin is Temper).
- `--type ultrabrain|deep|quick` — category routing for model selection.
- `--loop` — signal acceptance of unbounded validate re-loops (Temper already allows this; `--loop` is informational).

**Refused flags (log and ignore):**
- `--no-red-team` — red team is non-negotiable.
- `--no-validate` — validation is non-negotiable.

## Invariants (non-negotiable)

1. Red team always runs — **at every depth**, not just once.
2. Validate always runs. Hephaestus builds and exercises the real artifact.
3. Dual output: XML prompt + plan directory.
4. Skill enrichment is always on.
5. Re-loop on validate FAIL routes back to Seed (depth 0) with failure folded into Metis directives.
6. Parallelization by default — Red Team Trinity spawns in parallel even inside the loop.
7. Category routing, not model picking.
8. Dual prompts by model family.
9. **Temper-specific:** Momus emits `score: 0-100` at every depth.
10. **Temper-specific:** Convergence is deterministic — `convergence-check.py` decides, not the LLM.

## Flow

### Stage 1 — Intent Gate

Reject unsafe inputs (secrets in task, outside scope of the project root). If task is empty, prompt user.

### Stage 2 — Probe

Invoke the `explore` agent to scan the codebase. Enumerate:
- Files matching the task keywords
- Existing skills in `~/.claude/skills/` and `<project>/.claude/skills/`
- Recent commits touching relevant areas
- Existing plans under `plans/` or `.planning/`

Output: a **probe report** passed to Metis.

### Stage 3 — Enrich (Metis)

Spawn **Metis** (see `agents/metis.md`). Metis returns an envelope with directives. If Metis emits BLOCK, surface the clarifying questions to the user and ABORT.

### Stage 4 — Deepen Loop (the Temper core)

Initialize state:
```
depth = 0
depth_scores = []
depth_cap = <N from --depth, default 3>
```

**Seed (depth 0):**
1. Spawn **prometheus-temper** with input `{metis_directives, probe_report}`. Output: `plan_0.md`.
2. Spawn **Red-Team Trinity** in parallel on `plan_0.md`:
   - `redteam-security`
   - `redteam-scope`
   - `redteam-assumptions`
3. Spawn **momus** on `plan_0.md`. Momus returns envelope with `score: 0-100`.
4. Append score to `depth_scores`. Write state file.
5. Invoke `${CLAUDE_PLUGIN_ROOT}/scripts/convergence-check.py --depth 0 --scores "[score_0]" --cap N`. Capture exit code.
   - Exit 0 (converged) → exit loop.
   - Exit 1 (continue) → next iteration.

**Iteration (depth N, N≥1):**
1. Spawn **prometheus-temper** with inputs `{plan_{N-1}, momus_envelope_{N-1}, redteam_envelopes_{N-1}, metis_directives, depth_scores}`. Output: `plan_N.md` — a full rewrite.
2. Spawn **Red-Team Trinity** in parallel on `plan_N.md` (3 agents).
3. Spawn **momus** on `plan_N.md`. Get `score_N`.
4. Append `score_N` to `depth_scores`. Write state.
5. Invoke `convergence-check.py --depth N --scores "depth_scores" --cap N`. Capture exit code + stdout.
   - Exit 0 → break, log reason (`variance | delta | cap`).
   - Exit 1 → `N = N + 1`, continue.

**Exit:** `plan_final` = `plan_N` (the last depth's plan). `final_score` = `depth_scores[-1]`.

### Stage 5 — Oracle

Spawn **oracle** on `plan_final` with all accumulated envelopes (Metis + per-depth Momus + per-depth Red Team + convergence reason). Oracle returns bird's-eye verdict.

If Oracle returns BLOCK → ABORT with reason.
If Oracle returns RISKY → surface to user for explicit override before proceeding.
If Oracle returns SAFE or CAUTION → proceed to Validate.

### Stage 6 — Validate (Hephaestus)

Spawn **hephaestus** on `plan_final`. Hephaestus builds and exercises the real artifact described in the plan. Returns PASS or FAIL with evidence.

**On FAIL:**
1. Parse the FAIL evidence into a new Metis directive.
2. Reset: `depth = 0`, `depth_scores = []`, `validate_attempts += 1`.
3. Route back to Stage 3 (Enrich) with the augmented directives.
4. The deepen loop re-runs from Seed.

**On PASS:** proceed to Emit.

### Stage 7 — Emit (Atlas)

Compute the rollup:
```yaml
rollup:
  architecture: temper
  run_id: anneal-temper-YYYYMMDD-HHMMSS-{slug}
  depth_final: N
  depth_scores: [s_0, s_1, ..., s_N]
  convergence_reason: variance | delta | cap
  overall_verdict: worst(metis, momus_final, redteam_final, oracle)
  gate_status:
    metis: ...
    momus: ...
    red_team_trinity: "3/3 PASS | 2/3 PASS | ..."
    oracle: ...
    hephaestus: PASS
  simultaneous_pass: true (if we reached here)
  emission_decision: EMIT
  iteration_count: validate_attempts
```

Invoke **atlas** to serialize:
- `~/Desktop/anneal-runs/{run_id}/temper-{run_id}.xml`
- `~/Desktop/anneal-runs/{run_id}/plan/plan.md`
- `~/Desktop/anneal-runs/{run_id}/plan/phase-00-*.md` ... `phase-NN-*.md`
- `~/Desktop/anneal-runs/{run_id}/depth-history.json` — per-depth plans, envelopes, scores

The XML follows `_shared/opus-47-xml-schema.md`. The plan directory is markdown.

## Execution guidance

- **Always use the Task tool** to spawn agents. Do not inline the agent prompts.
- **Red Team Trinity must fan out in a single parallel block.** Spawn three Task calls in one message. Do NOT set `run_in_background: true` — that makes the dispatches fire-and-forget and stops the pipeline after dispatch. Parallelism comes from batching three synchronous Task calls in one message; wait for all three envelope responses before proceeding.
- **Never skip a depth.** If `convergence-check.py` says continue, run the next depth.
- **Never synthesize scores.** Scores come from Momus envelopes only. The orchestrator parses, does not compute.
- **Always write the state file** at every phase transition. If the run is interrupted, the state file is the source of truth.
- **Emit only on `simultaneous_pass: true`.** If any gate is not green in the same iteration, re-loop.

## Output summary (stdout after emit)

```
Run: {run_id}
Architecture: temper
Depth: {final_depth} of {depth_cap}
Scores: [s_0, s_1, ..., s_N]
Convergence: {reason}
Verdict: {overall_verdict}
Validate: PASS
Emitted: {xml_path}
Plan: {plan_dir}

Next: open a fresh Claude Code session and paste:
  cat {xml_path} | claude
```
