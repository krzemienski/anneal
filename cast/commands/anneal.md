---
description: Run Cast architecture — single planner, always-on red team, functional validation, emit XML plus plan directory.
argument-hint: "<task description> [--fast]"
---

# /anneal-cast:anneal

You are invoking **Cast** — the linear, single-pour architecture of the Anneal plugin family. One Prometheus call. One Momus audit. Three parallel Red-Team adversaries. One Oracle synthesis. One Hephaestus validate. One Atlas emit. On FAIL, fold the failure into a new Metis directive and loop.

## Input

The user task is passed as the slash command argument. If the argument is empty, ask the user what they want Cast to plan. Do not proceed without a task.

The `--fast` flag is accepted and ignored (Cast is already the fast path in the Anneal family).

## Invariants · non-negotiable

1. Red Team Trinity always runs. Security, Scope, Assumptions — three parallel agents. No flag disables this.
2. Hephaestus functional validation always runs. No mocks, no test files, no stubs. Empty evidence equals FAIL.
3. Output is dual — an Opus 4.7 semantic-XML prompt AND a plan directory.
4. Skill enrichment is on — probe scans `~/.claude/skills/` and the project's `.claude/skills/`.
5. Re-loop on FAIL is unbounded, but routes back through Metis with the failure folded as a new directive (not a fresh restart).
6. Only Atlas writes outside the plugin working directory. Every other agent stages in a temp tree.

## Stage-by-stage execution

### Stage 1 · Intent Gate

- Read the task string.
- Reject if it requests: secret extraction, credential access, destructive filesystem ops on user paths, or any action that does not fit a plan-and-review workflow.
- Classify the task shape: bug-fix, scoped-refactor, infra-change, new-feature, documentation. Record the classification — Metis uses it.
- If the task is ambiguous beyond recovery, ask one clarifying question and stop; do not proceed.

### Stage 2 · Probe

Invoke the `scout` or `explore` skill (if available) or use Glob + Grep directly:
- Enumerate files relevant to the task (by name, by reference, by directory).
- Enumerate skills available in `~/.claude/skills/` and `{project}/.claude/skills/`.
- Read existing docs under `docs/`, `plans/`, `README.md`, `CLAUDE.md`, `AGENTS.md` if present.
- Produce a probe report: discovered files, discovered skills, existing docs, detected platform, detected package manager. Keep it under 60 lines.

### Stage 3 · Enrich via Metis

Invoke the `metis` agent with the task and the probe report as context. Metis returns an envelope with:
- `verdict` (SAFE / CAUTION / RISKY / BLOCK)
- `summary`
- `findings` (per-finding records)
- `directives` (imperative sentences the planner will follow)
- `clarifying_questions` (only if verdict is BLOCK)

If Metis returns BLOCK with clarifying questions, surface them to the user and stop. Do not proceed to stage 4 without answers.

### Stage 4 · Plan via Prometheus (single pass)

Invoke the `prometheus-cast` agent exactly once. Input:
- The user task verbatim
- Metis directives
- Probe report
- Stage-1 task classification

Prometheus writes a markdown plan with phase files:
- `plan.md` (overview, 80 lines max)
- `phase-00-*.md` ... `phase-NN-*.md`
- Each phase has: overview, related code files, implementation steps, success criteria, risk assessment.
- The plan MUST include a functional-validation phase with evidence checkpoints.
- The plan MUST NOT include "write unit tests" or "add test coverage."

After Prometheus returns, invoke the `momus` agent on the finished plan. Momus returns an envelope with ruthless findings. If Momus returns BLOCK, fold findings as new Metis directives and loop once (iteration_count += 1). If Momus returns RISKY, proceed but record the findings; Oracle will aggregate.

### Stage 5 · Review via Red-Team Trinity + Oracle

Fan out in PARALLEL three sub-agents:
- `redteam-security`
- `redteam-scope`
- `redteam-assumptions`

**Dispatch mechanics (load-bearing):** In a SINGLE assistant message, emit three Task tool calls (one per adversary). Do NOT set `run_in_background: true` on any of them — that makes them fire-and-forget and breaks the pipeline. The Task tool already executes multiple calls in one message concurrently; that's where the parallelism comes from. Wait for ALL THREE envelope responses before invoking Oracle. No partial reviews.

After all three return, invoke the `oracle` agent with every reviewer envelope (Metis + Momus + Red-Team Trinity members) as input. Oracle emits the bird's-eye verdict with:
- `verdict`
- `release_coherence` assessment
- `deployment_risk` specific concerns
- `breaking_changes` list
- `monitoring_recommendations`

If Oracle returns BLOCK, do not proceed to stage 6. Fold findings as new Metis directives and loop.

### Stage 6 · Validate via Hephaestus

Invoke the `hephaestus` agent. Input: the approved plan.

Hephaestus:
1. Executes the plan's artifact instructions on a scratch worktree or sandbox.
2. Captures real build output.
3. Captures real runtime output (CLI stdout/stderr, API responses, screenshots if UI).
4. Compares captured evidence against the plan's success criteria.
5. Returns PASS or FAIL with evidence cited.

Evidence quality rules:
- Empty files are INVALID. Zero-byte files fail the check.
- "Build succeeded" without the actual log line is INVALID.
- Screenshots of blank pages are INVALID.

If Hephaestus returns FAIL, compute the failure summary, pass it back through Metis as a new directive, and loop (iteration_count += 1).

### Stage 7 · Emit via Atlas

Invoke the `atlas` agent. Input:
- Final plan (markdown)
- All reviewer envelopes (Metis, Momus, Red-Team Trinity, Oracle)
- Hephaestus evidence
- Rollup computed per `_shared/plan-reviewer-schema.md`

Atlas writes to `${ANNEAL_RUNS_ROOT:-./.anneal/runs}/{run_id}/`:
- `cast-{run_id}.xml` (Opus 4.7 semantic-XML per `_shared/opus-47-xml-schema.md`)
- `plan/plan.md`
- `plan/phase-*.md`
- `plan/fixtures/` if any
- `rollup.yaml`
- `evidence/` directory with Hephaestus captures

Atlas prints to stdout: run_id, architecture, overall_verdict, files written, and the next-step command for a fresh Claude Code session.

## Rollup decision logic

A run emits only if:
- `simultaneous_pass == true` (all three gates green in this iteration)
- `overall_verdict in [SAFE, CAUTION]`

Otherwise:
- If `overall_verdict == BLOCK` and cause is Metis `clarifying_questions`, surface and ABORT.
- Otherwise RE_LOOP through Metis with the failure folded in, and iteration_count += 1.

## Refused flags

- `--no-red-team` — logged and ignored. Red team is non-negotiable.
- `--no-validate` — logged and ignored. Validation is non-negotiable.

## Orchestration script

The full pipeline implementation lives in `${CLAUDE_PLUGIN_ROOT}/scripts/orchestrate.sh`. You may shell out to it for the happy-path execution, but the stage-by-stage prompt above is the authoritative description — the script is a convenience, not the spec.
