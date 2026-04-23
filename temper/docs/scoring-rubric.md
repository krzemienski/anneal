# Momus Scoring Rubric · Anneal · Temper

The 0-100 score Momus emits at every depth. Not a vibe — a rubric with anchors.

## Why a number

In Cast and Alloy, Momus emits a verdict (SAFE/CAUTION/RISKY/BLOCK) and findings. That's enough when the review runs once. In Temper, the review runs at every depth and feeds into a convergence check. Convergence needs a number. The number is the score.

## The rubric

| Score | Band | Verdict | Meaning |
|-------|------|---------|---------|
| 100 | Perfect | SAFE | Ship now. No remaining concerns. |
| 90-99 | Excellent | SAFE | All major gaps closed. Minor polish only. |
| 85-89 | Strong | SAFE | Few minor findings, no majors. |
| 75-84 | Solid | CAUTION | Implementable but has non-blocking concerns. |
| 70-74 | Borderline | CAUTION | Mid-tier. Could go either way. |
| 60-69 | Weak | RISKY | Significant gaps. Human review required. |
| 50-59 | Poor | RISKY | Multiple MAJOR findings. Rewrite likely. |
| 30-49 | Broken | BLOCK | Critical findings, coherence issues. |
| 0-29 | Fundamental | BLOCK | Not implementable as written. |

## Anchor descriptions

### 100 — Perfect

- Zero findings across all categories.
- Red Team Trinity all SAFE (3/3).
- Every phase has success criteria and evidence checkpoints.
- Functional-validation phase is complete and specific.
- No unguarded assumptions.

### 85 — Strong

- 0 CRITICAL findings.
- 0-2 MAJOR findings.
- ≤5 MINOR findings.
- Red Team: 3/3 SAFE, or 2/3 SAFE + 1/3 CAUTION.
- No coherence issues.
- All phases have at least acceptable success criteria.

### 70 — Borderline

- 0 CRITICAL findings.
- 3-5 MAJOR findings, OR 1 Red Team verdict RISKY.
- ≤10 MINOR findings.
- Plan is implementable with human judgment on open issues.
- Non-blocking but needs work before Oracle approves.

### 50 — Poor

- 1 CRITICAL finding that is partially mitigated, OR
- 6+ MAJOR findings, OR
- 2+ Red Team verdicts RISKY.
- Likely to fail Oracle review.
- Rewrite needed.

### 30 — Broken

- Unmitigated CRITICAL finding, OR
- Red Team BLOCK, OR
- Plan missing functional-validation phase.
- Not implementable as written.

### 0 — Fundamental failure

- Plan contradicts the user task.
- Plan cannot be interpreted.
- Multiple unmitigated CRITICAL findings.

## Determinism rules

Momus's score is not a free parameter. It must reflect the underlying data.

### Hard floors (caps based on Red Team)

| Red Team state | Max score |
|----------------|-----------|
| Any BLOCK | 50 |
| Any RISKY | 75 |
| 2+ CAUTION | 85 |
| All SAFE | 100 |

A plan with a Red-Team-Security BLOCK scored at 72 is a validator error. The floor is hard, not soft.

### Anti-drift

If `prior_score` is available (depth N ≥ 1):
- Score movement > +20 points requires a justification sentence in the envelope summary.
- Score movement > -20 points requires a justification sentence.
- Small moves (< 20 in either direction) are self-explanatory.

### Mapping score ↔ verdict

The verdict must be consistent with the score. If score is 88 but verdict is CAUTION, that's a validator error (88 is in the SAFE band). If score is 55 but verdict is SAFE, that's also a validator error.

| Score band | Verdict |
|------------|---------|
| 85-100 | SAFE |
| 70-84 | CAUTION |
| 50-69 | RISKY |
| 0-49 | BLOCK |

## Interaction with convergence

Scores drive `convergence-check.py`:

- Low scores (< 70) at depth 0 → likely to continue (delta likely > 0.15 on next rewrite).
- Rising scores → continue until variance or delta triggers.
- Stable scores in the 85+ band → variance triggers quickly.
- Stuck at cap with score < 85 → Oracle will downgrade.

## Example (depth 0 → 1 → 2)

| Depth | Findings | Red Team | Prior score | New score | Rationale |
|-------|----------|----------|-------------|-----------|-----------|
| 0 | 2 MAJOR, 4 MINOR, 3 blocking | 2/3 CAUTION, 1/3 RISKY | — | 62.0 | RISKY ceiling (75), 3 blocking issues pull to mid-60s. |
| 1 | 1 MAJOR, 3 MINOR, 1 blocking | 3/3 CAUTION | 62.0 | 78.0 | Ceiling lifted to 85 (no RISKY); blocking count dropped from 3 to 1; landed solidly in CAUTION band. +16 movement is within normal range. |
| 2 | 0 MAJOR, 2 MINOR, 0 blocking | 3/3 SAFE | 78.0 | 85.0 | All Red Team SAFE → no ceiling; 0 blocking issues; landed at SAFE threshold. +7 movement is normal, no justification needed. |

Convergence check at depth 2 with scores `[62.0, 78.0, 85.0]`:
- Top-3 variance ≈ 89.6, not < 0.3. Variance rule doesn't fire.
- Delta `|85.0 - 78.0| = 7.0`, not < 0.15. Delta rule doesn't fire.
- Depth 2 < cap 3. Cap rule doesn't fire.
- **Continue to depth 3.**

Depth 3 might deliver a score of 85.2 (marginal gain, all red team still SAFE). Check:
- Top-3: `[85.2, 85.0, 78.0]`, variance ≈ 12.3, not < 0.3.
- Delta `|85.2 - 85.0| = 0.2`, not < 0.15.
- Depth 3 ≥ cap 3. **Cap-triggered.**

So this plan exits at depth 3 with reason=cap, final_score=85.2. Oracle sees reason=cap + score ≥ 85 → does not downgrade. Emits SAFE.

## Anti-patterns

- Do NOT score 85 to force convergence. If the plan isn't at 85, the score isn't 85.
- Do NOT score 95 because "the rewrite looks polished." Polish is not the rubric.
- Do NOT let previous scores anchor new scores. Each score stands on its own evidence.
- Do NOT round scores to integers. Floats are fine (`85.05`, `62.3`).
