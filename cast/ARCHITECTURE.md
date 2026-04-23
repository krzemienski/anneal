# Anneal · Cast — Architecture

**One page.** Derived from `ARCHITECTURE-PROPOSALS.md` Proposal A.

---

## The pipeline

```
+----------------+
|  user task     |
+--------+-------+
         |
         v
+----------------+     stage 1: reject unsafe inputs, classify shape
|  Intent Gate   |
+--------+-------+
         |
         v
+----------------+     stage 2: scan codebase, enumerate skills, read docs
|     Probe      |
+--------+-------+
         |
         v
+----------------+     stage 3: Metis — directives + ambiguity flags
|    Enrich      |
+--------+-------+
         |
         v
+----------------+     stage 4: Prometheus — one pass, produces plan
|      Plan      |     then Momus — post-plan audit
+--------+-------+
         |
         v
+-------------------------------+    stage 5: parallel fan-out
|        Red-Team Trinity       |
|  Security | Scope | Assumptions |
+-------------+-----------------+
         |
         v
+----------------+    stage 5 close-out: bird's-eye verdict
|     Oracle     |
+--------+-------+
         |
         v
+----------------+    stage 6: Hephaestus — build + exercise + evidence
|   Validate     |
+--------+-------+
         |
    (PASS)|  (FAIL ----> back to Enrich, failure carried as new constraint)
         v
+----------------+    stage 7: Atlas — XML + plan directory
|     Emit       |
+----------------+
```

## Key invariant · Single planner

Stage 4 is a **single Prometheus call**. No tournament. No deepen loop. If the plan is wrong, the fix is not "run the planner again" — the fix is "route the failure through Metis as a new directive."

This is the one-line description of Cast: *linear, single-pour, fail-constrained re-loop*.

## Parallelism

The only parallel stage is stage 5 — Red-Team Trinity members (Security, Scope, Assumptions) fan out simultaneously and return envelopes independently. Oracle reads all three plus Momus plus Metis and synthesizes the bird's-eye verdict.

Everything else is sequential. Cast values clarity-of-trace over throughput.

## Data shapes

Every reviewer emits an envelope (`_shared/plan-reviewer-schema.md`):

```yaml
reviewer: <name>
verdict: SAFE | CAUTION | RISKY | BLOCK
summary: "2-3 sentence assessment"
confidence: HIGH | MEDIUM | LOW
findings: [ ... per-finding records ... ]
blocking_issues_count: <int>
```

Atlas aggregates to a rollup:

```yaml
rollup:
  architecture: cast
  run_id: anneal-YYYYMMDD-HHMMSS-{slug}
  overall_verdict: <worst across reviewers>
  gate_status:
    metis: <verdict>
    momus: <verdict>
    red_team_trinity: "N/3 PASS"
    oracle: <verdict>
    hephaestus: PASS | FAIL
  simultaneous_pass: true | false
  emission_decision: EMIT | RE_LOOP | ABORT
  iteration_count: <int>
```

A run emits iff `simultaneous_pass == true` AND `overall_verdict in [SAFE, CAUTION]`.

## File layout produced per run

```
${ANNEAL_RUNS_ROOT:-./.anneal/runs}/
  cast-anneal-260422-1440-{slug}/
    cast-{run_id}.xml        <- Opus 4.7 semantic-XML prompt
    plan/
      plan.md
      phase-00-*.md
      phase-01-*.md
      ...
      fixtures/
    rollup.yaml
    evidence/
      build-log.txt
      runtime-*.{txt,png,json}
```

## Cost profile

| Metric | Target |
|--------|--------|
| Agent spawns per successful run | ~8 |
| Wall-clock per run | ~4 min |
| Worst-case with 3 re-loops | ~12 min |

## Relationship to Alloy and Temper

Cast is the fastest and cheapest of the three Anneal architectures. Alloy spends 2.5x more for breadth of plan shape. Temper spends 3x more for depth of refinement. Cast spends the minimum needed to keep all invariants intact while producing a solid single-shot plan.

See `/Users/nick/Desktop/anneal/ARCHITECTURE-PROPOSALS.md` for the full comparison.
