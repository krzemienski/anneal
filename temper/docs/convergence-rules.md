# Convergence Rules · Anneal · Temper

Formal statement of the three rules that drive loop exit, with worked examples.

## Why deterministic convergence

If an LLM decided when the deepen loop exits, "convergence" would be a vibe. Temper instead delegates to `scripts/convergence-check.py` — a pure function over the score history. The loop exits when and only when the script says so.

## Setup

Given a sequence `S = [s_0, s_1, ..., s_k]` of Momus scores at depths 0 through k.
Given `cap` — the hard iteration ceiling (default 3, range 1-5).

## The three rules

### Rule 1 · Variance of top-3 scores

```
top3 = sorted(S, descending)[:3]
if len(S) >= 3 and variance(top3) < 0.3:
    exit(reason="variance")
```

**Semantics:** "The three best scores across all depths we've seen are within a 0.3-variance window." Small variance means the scores are clustered — the plan has converged to its ceiling.

**Why top-3, not last-3:** a rewrite that briefly dips (e.g., added a phase for safety, Momus penalized complexity) shouldn't block convergence if the trajectory was already stable. Top-3 is order-insensitive.

**Threshold 0.3:** variance of 0.3 corresponds to a standard deviation of ~0.55 — tight. If the top-3 scores are `[84.0, 85.0, 85.5]`, variance = 0.39, NOT converged. If they're `[84.5, 85.0, 85.3]`, variance = 0.11, converged.

### Rule 2 · Absolute delta

```
if len(S) >= 2 and abs(S[-1] - S[-2]) < 0.15:
    exit(reason="delta")
```

**Semantics:** "The most recent rewrite moved the score by less than 0.15 points." Diminishing returns.

**Threshold 0.15:** one-seventh of a percentage point. Intentionally tight — we want the loop to keep running unless improvement is genuinely marginal.

**Why absolute, not signed:** a regression (score drops) also means the last depth didn't help. If depth N regresses on depth N-1, the loop should exit and Oracle should make the call.

### Rule 3 · Hard cap

```
if k >= cap:
    exit(reason="cap")
```

**Semantics:** "We've hit the iteration ceiling." No runaway loops.

**Default cap 3, range 1-5:** 3 iterations is enough for most plans to stabilize. Users who want deeper refinement set `--depth 5`. Users who want cheaper runs set `--depth 2` or `--depth 1`.

## Priority order

Multiple rules may fire on the same depth. Priority: **variance > delta > cap**.

- Variance is the cleanest signal — scores have stabilized naturally.
- Delta is the next cleanest — improvement has marginalized.
- Cap is the crudest — we ran out of iterations.

`convergence-check.py` reports the highest-priority triggered rule.

## Worked examples

### Example A · Variance-triggered at depth 2

Scores: `[62.0, 78.0, 85.0, 85.3]` (four depths).
- Top-3: `[85.3, 85.0, 78.0]` → variance = 11.2, NOT < 0.3. Continue.

Let's use a tighter example: `[80.0, 84.9, 85.0, 85.05]`.
- Top-3: `[85.05, 85.0, 84.9]` → variance ≈ 0.0039, < 0.3. **Converged on variance at depth 3.**

### Example B · Delta-triggered at depth 2

Scores: `[80.0, 85.0, 85.05]`.
- Top-3: `[85.05, 85.0, 80.0]` → variance ≈ 5.56, NOT < 0.3.
- Delta: `|85.05 - 85.0| = 0.05`, < 0.15. **Converged on delta at depth 2.**

### Example C · Cap-triggered at depth 3

Scores: `[50.0, 65.0, 78.0, 88.0]`, cap = 3.
- Top-3: `[88.0, 78.0, 65.0]` → variance = 87.56, NOT < 0.3.
- Delta: `|88.0 - 78.0| = 10.0`, NOT < 0.15.
- Depth = 3 ≥ cap = 3. **Converged on cap at depth 3.**

Note: scores are still rising (+10 from prior depth). The loop exits because we ran out of budget, NOT because the plan is done. Oracle will see `reason == cap` and downgrade its verdict accordingly.

### Example D · Continue (no rule fires)

Scores: `[62.0, 78.0]`, cap = 3.
- Top-3: len < 3, rule 1 doesn't apply.
- Delta: `|78.0 - 62.0| = 16.0`, NOT < 0.15.
- Depth = 1 < cap = 3. Do not exit.
- **Continue to depth 2.**

## Interaction with Oracle

Oracle reads the convergence reason and weights its verdict:

| Reason | Oracle behavior |
|--------|-----------------|
| `variance` | Trust the final Momus verdict. High confidence. |
| `delta` | If final score < 70, downgrade one tier. Marginal improvement ≠ good plan. |
| `cap` | If final score < 85, downgrade. We didn't reach a fixed point. |

See `skills/oracle/SKILL.md` § "Convergence-aware synthesis rules" for the full table.

## Configurability

| Parameter | Source | Range | Default |
|-----------|--------|-------|---------|
| `depth_cap` | `--depth N` CLI flag | 1-5 | 3 |
| Variance threshold | architecture constant | — | 0.3 |
| Delta threshold | architecture constant | — | 0.15 |

Variance and delta thresholds are NOT user-configurable. If users want shallower convergence, they set `--depth`. If they want deeper, same. Architecture constants stay constant.

## Implementation reference

`scripts/convergence-check.py` is the authoritative implementation. It is a standalone Python script with zero external dependencies. Run `python3 scripts/convergence-check.py --smoketest` to execute three canonical inputs (variance / delta / cap) and verify the expected behavior.

## Anti-patterns

- Do NOT "hand-tune" variance thresholds per run. The thresholds are architecture constants for a reason — if a user can lower variance to trigger exit sooner, that's a backdoor for "skip the loop."
- Do NOT treat a continuing loop as a failure. `{converged: false}` is a valid, expected state at early depths.
- Do NOT call `convergence-check.py` with stale scores (missing the most recent depth). The script validates `len(scores) == depth + 1`.
