# Architecture · Anneal · Temper

One page. The whole plugin in one diagram and one table.

## The Deepen Loop

```
Intent Gate → Probe → Enrich (Metis) → Seed Plan (Prometheus-Temper, depth=0)
                                                    │
                                                    ↓
                    ┌───────────────── DEEPEN LOOP ─────────────────┐
                    │                                                │
                    │  [depth N]                                     │
                    │                                                │
                    │  Prometheus-Temper rewrites plan_{N-1}         │
                    │      │   (inputs: prior plan, Momus score,     │
                    │      │    red-team findings, Metis directives) │
                    │      ↓                                         │
                    │  plan_N                                        │
                    │      │                                         │
                    │      ├───────────────┬──────────────┐          │
                    │      ↓               ↓              ↓          │
                    │  Red-Team-     Red-Team-      Red-Team-        │
                    │  Security      Scope          Assumptions      │
                    │      │               │              │          │
                    │      └───────┬───────┴──────────────┘          │
                    │              ↓                                 │
                    │         Momus                                  │
                    │         (score 0-100, verdict, findings)       │
                    │              │                                 │
                    │              ↓                                 │
                    │       Deepen-Loop (orchestrator)               │
                    │              │                                 │
                    │       convergence-check.py                     │
                    │       ├── variance(top-3) < 0.3  → exit        │
                    │       ├── |Δ| < 0.15             → exit        │
                    │       └── depth == cap           → exit        │
                    │              │                                 │
                    │              ↓ (no → depth++; yes → break)     │
                    └────────────────────────────────────────────────┘
                                    │
                                    ↓
                              Oracle (final plan)
                                    │
                                    ↓
                            Hephaestus (validate)
                                    │
                        ┌───────────┴───────────┐
                        ↓                       ↓
                    PASS → Atlas            FAIL → Seed (depth=0)
                                              with failure folded
                                              into Metis directives
```

## Agent table

| Stage | Agent | Spawns per run | Runs in parallel? |
|-------|-------|----------------|-------------------|
| 3 | Metis | 1 | No |
| 4 (depth 0) | Prometheus-Temper | 1 | No |
| 4 (depth N, N≥1) | Prometheus-Temper | 1 per iteration | No |
| 4 (each depth) | Red-Team-Security | 1 per depth | **Yes** (with Scope, Assumptions) |
| 4 (each depth) | Red-Team-Scope | 1 per depth | **Yes** (with Security, Assumptions) |
| 4 (each depth) | Red-Team-Assumptions | 1 per depth | **Yes** (with Security, Scope) |
| 4 (each depth) | Momus | 1 per depth | No (runs after Red Team) |
| 4 | Deepen-Loop | 1 | No (orchestrator only) |
| 5 | Oracle | 1 | No |
| 6 | Hephaestus | 1 | No |
| 7 | Atlas | 1 | No (only on EMIT) |

At default depth cap 3, assuming convergence at depth 2: `Metis + (Prometheus + 3 RedTeam + Momus) × 3 + Oracle + Hephaestus + Atlas = 1 + 5×3 + 3 = 19 agent spawns` — matches the architecture contract's "~8 × depth" band when depth is the number of *effective* iterations (depth 0 seed + depth 1 + depth 2 ≈ 8 + 8 + 8 = 24 = 8 × 3).

## State file layout

Temper writes state to `.anneal/temper-state.json` at every phase transition. Minimal schema:

```json
{
  "run_id": "anneal-temper-YYYYMMDD-HHMMSS-{slug}",
  "architecture": "temper",
  "task": "<verbatim user input>",
  "depth_cap": 3,
  "current_depth": 2,
  "depth_scores": [62.0, 78.0, 85.0],
  "depth_verdicts": ["CAUTION", "CAUTION", "SAFE"],
  "convergence": {
    "reason": "variance",
    "variance_top3": 0.18,
    "abs_delta": 7.0
  },
  "phase": "oracle",
  "validate_attempts": 0
}
```

## Data flow — what each depth receives

At depth N (N≥1), Prometheus-Temper receives:

1. **Prior plan** (`plan_{N-1}.md`) — the full markdown of the last depth.
2. **Momus envelope** from depth N-1 — verdict, score, findings, blocking_issues_count.
3. **Red-Team envelopes** from depth N-1 — three envelopes, one per adversary.
4. **Metis directives** — unchanged from stage 3.
5. **Probe report** — unchanged from stage 2.
6. **Depth score history** — `[s_0, s_1, ..., s_{N-1}]` so the planner can see the trajectory.

Prometheus-Temper's output is `plan_N.md` — a fresh rewrite, not a diff. The loop is not a patch-application loop; it is a rewrite loop where the prior plan is context, not the starting artifact.

## Re-loop on validate FAIL

When Hephaestus returns FAIL:

1. Parse the FAIL evidence into a new Metis directive:
   > "The previous plan's phase-NN failed validation because {evidence summary}. Any new plan must include explicit mitigation for {root-cause category}."
2. Reset state: `current_depth = 0`, `depth_scores = []`.
3. Re-enter the deepen loop from Seed.

This is **not** a Ralph-style "try again with same input." The failure reshapes the input. The loop learns.

No iteration cap on validate re-loops (matches Invariant 5). If the user passes `--loop`, that's a signal to accept even more retries; the default already allows unbounded retries on validate FAIL, so `--loop` is largely a status-line flag in Temper.

## Why rewrites (not diffs)

Rewrites force the planner to re-commit to each decision. Diffs let bad decisions persist invisibly across depths. Momus scoring is only meaningful if each depth's plan is fully responsible for its score.

Cost of rewrites: more tokens per planner call. Benefit: no decision cruft accumulates. Temper's ~8 × depth spawn profile already assumes full rewrites.

## Why inline red team

In Cast, red team runs once on a finished plan. In Alloy, red team runs once after synthesizer blending. In Temper, red team runs at every depth because the rewrite is the point — if red team only saw the final depth, early-depth weaknesses would flow into rewrites uncontested.

Inline red team is the defining property. Remove it and Temper degenerates into Cast-with-retry.
