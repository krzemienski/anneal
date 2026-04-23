# PRD · Anneal · Temper

**Product:** `anneal-temper` · Claude Code plugin · v0.1.0
**Architecture:** Fixed-Point Deepen (Proposal C of the Anneal family)
**Author:** Nick Krzemienski
**Date:** 2026-04-22

---

## 1. Problem

Plan-review workflows in multi-agent systems fall into two failure modes.

**Mode A (single-pour):** one planner writes a plan, reviewers audit once, you ship. Great for well-understood tasks. Bad for complex ones: the planner never sees its own blind spots.

**Mode B (tournament):** N planners compete, a synthesizer blends. Good for exploration. But each planner is a cold start — none learns from the others within the run.

Temper solves a third problem: **iteration learning**. When the task is complex but the shape is roughly known, the bottleneck isn't breadth (tournament solves that) — it's whether each rewrite genuinely improves on the prior. The failure mode Temper prevents is "polish plateau," where a plan looks good but nobody has stress-tested it with adversaries *inside* the rewrite loop.

## 2. Solution

One planner runs in a deepen loop. At each depth:

1. **Planner** rewrites the prior depth's plan using Momus's score and the Red-Team Trinity's findings as explicit input.
2. **Red-Team Trinity** runs in parallel — Security, Scope, Assumptions — against the fresh rewrite.
3. **Momus** scores 0-100. The score, the findings, and the rewrite all flow into depth N+1.
4. Loop exits when scores stabilize (variance < 0.3), improvement marginalizes (|Δ| < 0.15), or depth hits the hard cap (default 3).

After convergence, Oracle runs on the final depth's plan. Hephaestus validates. Atlas emits.

On validate FAIL, the run routes back to Seed (depth 0) — not to the prior depth. Failure becomes a new Metis directive; the whole deepen loop re-runs with the constraint folded in.

## 3. Non-goals

- Temper does **not** explore alternative plan shapes. It refines one line of thought. For breadth, use `anneal-alloy`.
- Temper does **not** replace `anneal-cast` for simple tasks. At depth 3, Temper costs ~3× more than Cast. Use Cast when the plan is obvious.
- Temper does **not** write code. It produces a plan + XML prompt. A different session executes.
- Temper does **not** write tests. The Iron Rules forbid mocks, stubs, and test files. Hephaestus validates by building and exercising the real artifact.

## 4. Invariants (non-negotiable)

These are inherited from the Anneal family and extended with two Temper-specific rules.

| # | Invariant | Temper-specific note |
|---|-----------|----------------------|
| 1 | Red team always runs | **At every depth.** Not once. Not after synthesis. Every iteration. |
| 2 | Validate always runs | Hephaestus builds and exercises the real artifact. |
| 3 | Dual output | XML prompt + plan directory. |
| 4 | Skill enrichment | Probe scans `~/.claude/skills/` + project `.claude/skills/`. |
| 5 | Unbounded re-loop on FAIL | Routes back to **Seed (depth 0)**, not to the prior depth. |
| 6 | Parallelization by default | Red Team Trinity spawns in parallel, always — including inside the loop. |
| 7 | Category routing | User specifies work-type; harness maps to model. |
| 8 | Dual prompts by model family | Claude-flavored and GPT-flavored prompts. |
| T1 | Momus emits `score: 0-100` | In Cast/Alloy, Momus emits only a verdict. In Temper, it must also emit a numeric score. |
| T2 | Convergence is deterministic | No LLM decides when to exit. `convergence-check.py` computes variance/delta/cap and returns a decision. |

## 5. CLI contract

```
/anneal-temper:anneal "<task>"                 # deepen, default cap=3
/anneal-temper:anneal "<task>" --depth N       # override cap (range 1-5)
/anneal-temper:anneal "<task>" --deepen        # explicit alias for Temper mode
/anneal-temper:anneal "<task>" --type ultrabrain|deep|quick   # category routing
/anneal-temper:anneal "<task>" --loop          # unbounded validate re-loop
```

Refused flags (logged):
- `--no-red-team`
- `--no-validate`

## 6. Roster

Nine agents. Seven inherited from the Anneal roster + two Temper-specific.

| Agent | Role | Invocations per run |
|-------|------|---------------------|
| Metis | Pre-plan consultant | 1 |
| Prometheus-Temper | Planner (rewrites from prior depth) | 1 per depth |
| Deepen-Loop | Orchestrator (tracks scores, checks convergence) | 1 per run |
| Red-Team Trinity (×3) | Security · Scope · Assumptions | **3 per depth** |
| Momus | Post-plan reviewer + 0-100 scorer | 1 per depth |
| Oracle | Architecture synthesizer | 1 |
| Hephaestus | Functional validator | 1 |
| Atlas | Emitter | 1 |

At depth 3 (default): 1 + 3 + 1 + (3+1)×3 + 1 + 1 + 1 = **~20 agent spawns** plus the orchestrator overhead. Architecture contract states "~8 × depth" as the spawn count; this reflects Metis + Seed Planner (2) + loop spawns (7 per depth: planner, 3 red team, Momus, Deepen-Loop check, Oracle-final) + Hephaestus + Atlas. Different counting granularity, same wall-clock.

## 7. Convergence semantics (formal)

Given a sequence `S = [s_0, s_1, ..., s_k]` of Momus scores from depth 0 through depth k:

**Rule 1 — Variance of top-3:**
Let `T = sorted(S, descending)[:3]`. Exit if `variance(T) < 0.3` AND `len(S) >= 3`.

**Rule 2 — Delta:**
Exit if `len(S) >= 2` AND `abs(s_k - s_{k-1}) < 0.15`.

**Rule 3 — Cap:**
Exit if `k >= depth_cap` (default 3, range 1-5).

The loop exits when any rule fires. Multiple rules may fire on the same depth; the first matching rule is reported.

Scores are floats in `[0.0, 100.0]`. The 0.3 and 0.15 thresholds are on that scale (so 0.3 variance means standard deviation ~0.55, and 0.15 delta means one-seventh of a percentage point). These are intentionally tight — we want the loop to keep working unless scores are genuinely flat.

## 8. Success criteria

Temper v0.1.0 ships when:

- [ ] `validate-plugin.py` passes on the shipped directory.
- [ ] `convergence-check.py` returns correct exit codes for the three canonical inputs (variance-triggered, delta-triggered, cap-triggered) — verified via inline doctests.
- [ ] `/plugin marketplace add /Users/nick/Desktop/anneal/temper` succeeds.
- [ ] `/plugin install anneal-temper@anneal-temper-dev` succeeds.
- [ ] `/anneal-temper:anneal "<any task>"` invokes without crashing.
- [ ] The 10 agent files and 8 skill directories are all present with valid YAML frontmatter.
- [ ] `hooks/hooks.json` parses as valid JSON.
- [ ] README documents `--depth N` and the three convergence rules.

## 9. Out of scope (explicit)

- **Not in v0.1.0:** live telemetry, benchmark scripts, skill auto-update, marketplace publication.
- **Not in v0.1.0:** integration with `anneal-alloy` for `--ultra` mode. That's a separate plugin composition.
- **Not in v0.1.0:** persistent state beyond the single run. Each invocation is fresh.

## 10. Open questions

- Whether to surface per-depth score history to the user in the final XML emission, or only the final score. (Current plan: show the history — transparency wins.)
- Whether to let the user override convergence thresholds via CLI (`--variance-threshold`, `--delta-threshold`). (Current plan: no, these are architecture constants. If users want shallower convergence, they use `--depth 2`.)
