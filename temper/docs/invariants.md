# Invariants · Anneal · Temper

The eight Anneal-family invariants plus two Temper-specific extensions. These are non-negotiable.

## Family invariants

1. **Red team always runs.** Three parallel adversaries (Security · Scope · Assumptions). Not a flag. Cannot be disabled. `--no-red-team` is refused and logged.

2. **Validation always runs.** Hephaestus builds and exercises the real artifact. No mocks, no test files, no stubs. Empty evidence → FAIL. `--no-validate` is refused and logged.

3. **Dual output.** Every run produces an Opus 4.7 semantic-XML prompt **and** a plan directory. Not one. Both. Atlas writes both.

4. **Skill enrichment.** Probe phase scans `~/.claude/skills/` and project `.claude/skills/`; matching skills inject into the plan's prelude automatically.

5. **Unbounded re-loop on FAIL.** If Hephaestus returns FAIL, route back through Metis with the failure folded into directives; in Temper, reset to Seed (depth 0). No iteration cap on validate re-loops.

6. **Parallelization by default.** Red team spawns fan out as a single parallel batch — three Task invocations in one message. Never sequential.

7. **Category routing, not model picking.** User specifies work-type (`--type ultrabrain|deep|quick`); the harness maps to model. Temper does not lock models.

8. **Dual prompts by model family.** Agents ship Claude-flavored (long, mechanics-driven) and GPT-flavored (short, XML-tagged) prompts. Auto-detected at runtime.

## Temper-specific invariants

### T1. Red team runs at every depth

Unlike Cast (once on a finished plan) and Alloy (once after synthesis), Temper runs the Red-Team Trinity at every depth of the deepen loop. This is the defining property. Without it, Temper degenerates into Cast-with-retry.

### T2. Momus emits a 0-100 score

In Cast and Alloy, Momus emits only a verdict. In Temper, Momus MUST additionally emit `score: <float 0-100>`. The score drives convergence; the verdict drives the gate. Both are required.

### T3. Convergence is deterministic

No LLM decides when to exit the loop. `convergence-check.py` is a pure function over the score history. Three rules (variance / delta / cap). The first rule to fire determines the exit. See [`convergence-rules.md`](./convergence-rules.md) for formal statements.

### T4. Rewrites, not diffs

At depth N ≥ 1, Prometheus-Temper produces a full rewrite — not a patch, not a diff. Each depth owns its plan end-to-end. Rewrites force the planner to re-commit to each decision. Diffs let bad decisions persist invisibly across depths.

### T5. Re-loop resets to Seed

On Hephaestus FAIL, the run routes back to Stage 3 (Metis Enrich) with the failure folded in as a new directive, and the deepen loop restarts from depth 0. It does NOT resume from the prior final depth. Failure reshapes the input; the whole loop learns.

## Refused flags

| Flag | Behavior |
|------|----------|
| `--no-red-team` | Logged and ignored. Red team runs regardless. |
| `--no-validate` | Logged and ignored. Hephaestus runs regardless. |

## Iron Rules (carried from Anneal family)

- No mocks, stubs, test doubles, test files, test frameworks, fake data.
- Evidence-based verdicts only. Cite specific evidence for every PASS/FAIL.
- Build passing ≠ feature working. Compilation is not validation.
- If the real system doesn't work, fix the real system. Never modify the plan to make the verdict PASS.
