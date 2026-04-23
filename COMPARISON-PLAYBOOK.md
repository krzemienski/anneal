# Anneal Comparison Playbook

How to test Cast, Alloy, and Temper against the same task and decide which architecture fits which class of work.

## Pre-flight

Before starting, verify all three plugins installed and loaded:

```bash
claude --debug 2>&1 | grep -E "anneal-(cast|alloy|temper)"
```

Expected: three lines, one per plugin, all registered.

## The canonical comparison task

Pick a task that stresses plan quality. Recommended starting point — the plugin rewrite itself:

```
rewrite the deepest-plan plugin to use SADD primitives and fix the 91 asymmetric-vendoring defects. ship a functional v0.1.0 that passes its own red team.
```

Run it against all three, one after another:

```
/anneal-cast:anneal "rewrite the deepest-plan plugin to use SADD primitives and fix the 91 asymmetric-vendoring defects. ship a functional v0.1.0 that passes its own red team."

/anneal-alloy:anneal "rewrite the deepest-plan plugin to use SADD primitives and fix the 91 asymmetric-vendoring defects. ship a functional v0.1.0 that passes its own red team." --versions 5

/anneal-temper:anneal "rewrite the deepest-plan plugin to use SADD primitives and fix the 91 asymmetric-vendoring defects. ship a functional v0.1.0 that passes its own red team." --depth 3
```

Each run writes to `~/Desktop/anneal-runs/{run_id}/`.

## What to measure

### 1. Plan quality (subjective)

Read the three `plan/plan.md` outputs side-by-side. Judge:
- Coverage — does every invariant get a phase?
- Specificity — are success criteria measurable?
- Risk — are failure modes named and mitigated?
- Coherence — do phases compose into a single shippable story?

### 2. Agent spawn count (objective)

Every run's `rollup.yaml` records `iteration_count` plus per-gate status. Cost scales with spawns:

- **Cast** — expect ~8 spawns
- **Alloy** — expect ~18 spawns (8 + 2N when N=5)
- **Temper** — expect ~8 × actual-depth (8 to 24)

If a run needs re-loops, spawns multiply by iteration count. Track the re-loop count — that's a quality signal (first plan was weak if multiple re-loops needed).

### 3. Wall-clock (objective)

Start-to-EMIT timing from the rollup. Typical expectations:

- **Cast** — ~4 min (no parallelism within stage 4)
- **Alloy** — ~6 min (N planners parallel, but synthesizer is sequential tail)
- **Temper** — ~7 min at depth 3

### 4. Red-Team findings (objective)

Each run's `review/red_team/*` envelopes enumerate findings. More findings on Cast ≠ worse — it may mean Cast's planner naturally explored less, so red team found gaps the richer architectures avoided.

Compare:
- **Severity distribution** — ratio of CRITICAL : MAJOR : MINOR
- **Category distribution** — security vs scope vs assumptions (which angle finds the most?)
- **Blocking issues** — which architecture produces plans that need the fewest re-loops?

### 5. XML prompt quality

The downstream consumer is a fresh Claude Code session pasting the XML. Quality proxy:
- File size — smaller is not better, but bloat is a signal
- `<context>` richness — does probe output include the right files?
- `<iron_rules>` clarity — are they specific or generic?
- `<instructions>/<next_action>` — is it actionable with zero ambiguity?

## Decision rubric

Use this grid to pick the right architecture for a new task:

| Task shape | Pick |
|-----------|------|
| Bug fix, clear repro, single file | **Cast** |
| Refactor across 3-5 files, pattern obvious | **Cast** |
| New feature, pattern unclear, multiple viable approaches | **Alloy** |
| Greenfield architecture, no precedent in codebase | **Alloy** |
| Complex but well-scoped, iterative improvement opportunity | **Temper** |
| Mission-critical plan that must land first try | **`--ultra`** (Alloy → Temper the winner; requires separate orchestration) |

## Red flags during testing

- **Cast fires ≥3 re-loops** — task is likely under-scoped. Re-run on Alloy.
- **Alloy's synthesizer picks only 1 plan** — task was actually clear; Cast would have been cheaper.
- **Temper hits depth cap 3 without converging** — variance never settled, task is too novel for iterative refinement. Re-run on Alloy.
- **Any architecture returns BLOCK on Metis** — task has unresolvable ambiguity. Answer the clarifying_questions and re-run.

## Reporting

After each comparison, save a summary to `~/Desktop/anneal-runs/comparison-YYYYMMDD.md`:

```markdown
# Comparison · {task-one-line} · {date}

| Metric | Cast | Alloy | Temper |
|--------|------|-------|--------|
| Overall verdict | SAFE | SAFE | SAFE |
| Agent spawns | 8 | 18 | 24 |
| Wall-clock | 4m12s | 6m41s | 7m55s |
| Re-loops | 0 | 0 | 0 |
| CRITICAL findings | 0 | 0 | 0 |
| MAJOR findings | 2 | 1 | 0 |
| Plan phases | 9 | 11 | 13 |

## Subjective plan-quality notes

- Cast: {what it nailed, what it missed}
- Alloy: {same}
- Temper: {same}

## Decision

For tasks like this I would use: {pick}
Reason: {one sentence}
```

Iterate across multiple task shapes to build intuition. Three architectures over ten tasks produces a decision rubric you can trust.
