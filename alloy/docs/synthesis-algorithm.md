# Synthesis Algorithm

How the Synthesizer blends N plan variants into one coherent plan. This document is the **normative** reference — the Synthesizer agent prompt and the `synthesizer` skill both implement this algorithm.

---

## Bias selection

The `--versions N` flag selects N ∈ [2, 7]. The orchestrator maps N → bias list:

| N | Biases |
|---|--------|
| 2 | correctness, minimalist |
| 3 | correctness, minimalist, defensive |
| 4 | correctness, minimalist, defensive, performance |
| 5 | correctness, minimalist, defensive, performance, ux |
| 6 | correctness, minimalist, defensive, performance, ux, verification |
| 7 | correctness, minimalist, defensive, performance, ux, verification, migration |

**Why this order:** biases are added in order of *orthogonality to the existing set*. Adding `defensive` to (correctness, minimalist) produces the widest spread. Adding `performance` to (correctness, minimalist, defensive) is next most-orthogonal. And so on.

Adding `security` or `accessibility` biases was considered and rejected for v0.1.0:
- **security** — red-team-security already catches it; an adversarial angle in review is stronger than a friendly angle in planning
- **accessibility** — too domain-specific for the default N

Future versions may allow custom bias sets. v0.1.0 uses the fixed table above.

---

## Algorithm (six steps)

### Step 1 · Phase alignment

For each variant, extract the phase list. Across variants, phases overlap semantically but may differ in naming. Group by **semantic equivalence** using these heuristics:

- Same key verbs in Overview (`scaffold`, `vend`, `install`, `validate`)
- Same Related-Code-Files intersection (if variant A and variant B both mention `.claude-plugin/plugin.json`, they likely share a phase)
- Same position in the dependency chain (phase N-1 in both)

Output of Step 1: a list of **canonical phases**, each annotated with contributing-variant IDs.

### Step 2 · Per-phase composition

For each canonical phase, for each of the 6 phase sections, apply the **Section Selection Table**:

| Section | Rule | Tiebreak |
|---------|------|---------|
| Overview | Most specific variant | longest concrete sentence count |
| Related code files | Union of all variants | — (set union) |
| Implementation steps | Most actionable variant | highest count of (concrete verbs, file paths, commands) |
| Success criteria | Most citable variant | highest count of "file X contains Y" patterns |
| Risk assessment | Union of all variants | — |
| Bias Lens | Merged attributions of all contributors | — |

**Tiebreakers** (when two variants tie on the rule):
- Prefer the variant with the earlier bias in the priority order: `defensive > correctness > migration > verification > ux > performance > minimalist`
- This is the same priority used for contradiction resolution (Step 3), ensuring the most-conservative bias wins ties.

### Step 3 · Contradiction resolution

When two variants prescribe contradictory approaches for the same decision point:

**Rule order:**

1. **Directive-match first.** If a Metis directive names the correct approach, use that regardless of variant.
2. **Conservative default.** No matching directive? Pick the more conservative option using the priority ladder:

   ```
   defensive > correctness > migration > verification > ux > performance > minimalist
   ```

   **Rationale:** under uncertainty, the conservative side is the one that assumes the worst environment. A plan that rolls back cleanly is recoverable; a plan that skipped rollback for perf reasons is not.

3. **Document the contradiction.** In synthesis-provenance.md:
   - Log the contradiction
   - Log the rule used (directive-match or conservative-default)
   - Log the rejected variant

**Example:**

Variant 1 (correctness) says: "Run functional-validation as a gate test in phase-10."
Variant 2 (minimalist) says: "Skip functional-validation — it's not in the user's direct ask."

Resolution:
- Directive match: Metis directive 3 says "plan must include a functional-validation phase with evidence checkpoints."
- Outcome: variant 1 wins via directive match.
- Provenance: "Resolved via directive match — Metis directive 3 mandates validation phase."

### Step 4 · Redundancy collapse

When multiple variants prescribe **semantically equivalent** steps, merge into one step with merged attribution.

Equivalent ≠ identical. "Run `bash setup.sh`" and "execute setup.sh" are equivalent. "Install deps" and "pip install -r requirements.txt" are *not* equivalent (the latter is more specific; keep it).

**Heuristic:** if two steps produce the same filesystem state when executed, they are equivalent.

### Step 5 · Coherence pass

Read the blended plan top to bottom. Check:

| Check | Fix if broken |
|-------|---------------|
| No forward references between phases | Reorder, log adjustment |
| Every file in Steps appears in Files | Add missing to Files list, log |
| Every Success criterion is measurable | Flag as gap in provenance |
| Functional-validation phase present | Flag as Iron Rule violation — route to RE_LOOP |
| No test files, no mocks | Flag as Iron Rule violation — route to RE_LOOP |

**Never add novel content.** If a gap is genuinely missing (a phase needed but absent in all variants), flag it in provenance and let Momus decide. The Synthesizer does not plan.

### Step 6 · Provenance emission

Write `synthesis-provenance.md`. One section per blended phase, format:

```markdown
## phase-NN-{slug}

**Contributing variants:** I (bias), J (bias), ...

**Section attributions:**
- Overview: variant X (bias) — "reason"
- Files: union of I, J, K
- Steps: variant Y (bias) — "reason"
- Success: variant Y (bias) — "reason"
- Risk: union of I, J, K
- Bias Lens: merged from I, J, K

**Contradictions resolved:**
- {description of contradiction}
  Resolution rule: {directive-match | conservative-default}.
  Kept: variant X. Rejected: variant Y.

**Rejected elements:**
- Variant Z proposed {thing}. Rejected: {reason}.
```

**Plus a run-level summary at the top:**

```markdown
# Synthesis provenance — run anneal-YYYYMMDD-HHMMSS-{slug}

**Biases participating:** correctness, minimalist, defensive, performance, ux
**Biases contributing to blend:** correctness, defensive, performance, ux (minimalist 0 phases)
**Contradictions resolved:** 3
**Silent rejections:** 0

**Bias contribution histogram:**
- correctness: 9 phases
- minimalist: 0 phases  ← flagged; bias under-informed
- defensive: 7 phases
- performance: 5 phases
- ux: 6 phases
```

---

## Failure Attribution

When Hephaestus returns FAIL, the failure is attributed to one of three categories. The attribution determines re-loop routing.

### Category A · Variant-induced failure

The failing step traces to a single variant's contribution. Provenance shows only one variant cited for the failing section.

**Route:** Route to **Intent Gate** (not Synthesizer). Add the failure as a new Metis directive. The whole tournament re-runs; the offending bias may produce the same output on retry, but the other biases have a chance to override via directive match.

### Category B · Blend-induced failure

The failing step traces to an interaction between two variants' contributions. The individual contributions were fine; their combination is not.

**Route:** Route to **Intent Gate**. Metis receives a directive: "Phase X has an integration conflict between {bias A} and {bias B}. Prefer {bias A} OR {bias B} explicitly in the next run." This forces contradiction resolution to use directive match instead of conservative default.

### Category C · Missing-phase failure

Hephaestus fails because a step it expected is absent from the plan. All N variants missed a phase.

**Route:** Route to **Intent Gate** with a new Metis directive enumerating the missing step. On the next run, planners see the explicit constraint and can't all miss it again.

**This is why Alloy's re-loop routes to Intent Gate and not to Synthesizer.** The Synthesizer with the same inputs produces the same blend. The only lever that changes the output is the Metis input.

---

## Hard rules summary

1. Never plan from scratch (Synthesizer is not a planner)
2. Never add phases not present in any variant
3. Never silently resolve contradictions
4. Never paraphrase Metis directives
5. Never drop a variant entirely from provenance

---

## Worked example

See [`worked-example.md`](./worked-example.md) for Stage 4 of the plugin rewrite, including a full provenance document.
