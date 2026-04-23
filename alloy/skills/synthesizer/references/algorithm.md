# Synthesizer Algorithm & Schemas

## Input schema

```yaml
variants:
  - path: "variants/variant-1-correctness.md"
    bias: "correctness"
  - path: "variants/variant-2-minimalist.md"
    bias: "minimalist"
  # ... N total
metis_directives: [...]
probe_report: {...}
output_paths:
  plan_dir: "plan/"
  provenance: "synthesis-provenance.md"
```

## Synthesis algorithm

### Step 1 · Phase alignment

For each variant, extract the phase list. Phases across variants overlap semantically but differ in naming/detail. Group phases by semantic equivalence — "set up the plugin scaffolding" and "phase-00-scaffold" are the same phase.

Output: a list of canonical phases, each with a set of contributing variants.

### Step 2 · Per-phase composition

For each canonical phase, for each of the 6 phase sections (Overview, Files, Steps, Success, Risk, Bias Lens), select the strongest version across variants:

| Section | Selection rule |
|---------|---------------|
| Overview | Prefer the **most specific** variant (longest concrete statement of why this phase exists). |
| Files | Prefer the **union** of all variants' file lists — a file that appears in any variant is needed. |
| Steps | Prefer the variant with the **most actionable** numbered steps (concrete commands, file paths, verbs like `run`, `write`, `append`). |
| Success | Prefer the **most citable** criteria — evidence-backed beats vague ("file X contains Y" beats "looks right"). |
| Risk | Prefer the **union** of all variants' risks — risks don't contradict, they compound. |
| Bias Lens | Keep the **attributions** of all contributing variants — this becomes the provenance entry. |

### Step 3 · Contradiction resolution

When two variants prescribe contradictory approaches for the same decision point, resolve in this order:

1. **Directive-match first.** If a Metis directive names the correct approach, use that regardless of variant.
2. **Conservative default.** No matching directive → pick the more conservative option. Priority: `defensive > correctness > migration > verification > ux > performance > minimalist`.
3. **Document the contradiction.** In `synthesis-provenance.md`, log the contradiction, the rule used, and the rejected variant.

### Step 4 · Redundancy collapse

When multiple variants prescribe semantically equivalent steps, merge into one step and attribute to all contributing variants. Equivalent ≠ identical — "run `bash setup.sh`" and "execute setup.sh" are equivalent.

### Step 5 · Coherence pass

Read the blended plan top to bottom. Check:

- Every phase still depends only on earlier phases (no forward references).
- Every "Related code file" mentioned in Steps is listed in Files.
- Every Success criterion is measurable.
- Functional-validation phase is present (Iron Rule).
- No test files, no mocks (Iron Rule).

If coherence fails, adjust minimally (reorder phases, add missing file to list) and log the adjustment in provenance. Never add novel content — if a gap is genuinely missing, flag it in provenance; do not fill it.

### Step 6 · Provenance emission

Write `synthesis-provenance.md` with one section per blended phase. See `§ Provenance format` below.

## Provenance format

```markdown
## phase-00-scaffold

**Contributing variants:** 1 (correctness), 3 (defensive), 5 (ux)

**Section attributions:**
- Overview: variant 3 (defensive) — "chose for explicit rollback framing"
- Files: union of 1, 3, 5
- Steps: variant 1 (correctness) — "most actionable numbered sequence"
- Success: variant 1 (correctness) — "evidence-citable gate test"
- Risk: union of 1, 3
- Bias Lens: merged from 1, 3, 5

**Contradictions resolved:**
- Variant 5 (ux) requested status-line in step 3; variant 1 (correctness) did not.
  Resolution rule: UX directive present in Metis; kept ux variant.

**Rejected elements:**
- Variant 2 (minimalist) omitted the validation checkpoint. Rejected on
  conservative-default rule; validation is non-negotiable per Iron Rules.
```

## Output schema

### `plan/plan.md`

```markdown
# Plan · Alloy Synthesis · {run_id}

**Task:** {verbatim user task}
**Architecture:** alloy (tournament consensus, N={N})
**Biases contributed:** {list}

## Thesis
{blended 1-paragraph summary — drawn from the strongest Thesis across variants}

## Phases
- [phase-00-{slug}](./phase-00-{slug}.md)
- [phase-01-{slug}](./phase-01-{slug}.md)
- ...

## Iron rules
(verbatim from variants — identical across all, picked once)
- No test files. No mocks. No stubs.
- Functional validation phase mandatory.
- Evidence before completion.

## Dependencies
Phase N depends on phase N-1 unless noted otherwise.
```

### `plan/phase-NN-{slug}.md`

Same 6-section schema as variant phases, with composed content.

### `synthesis-provenance.md`

One section per phase, as shown in `§ Provenance format`.

## Failure mode — mutually incoherent variants

If variants are mutually incoherent (e.g. variant 1 → A, variant 2 → B, variant 3 → C, no directive helps, no conservative default applies):

- Pick the option that satisfies the most directives.
- Log it in provenance as "ambiguous resolution."
- Let Momus flag it as MAJOR if it matters.

Do NOT ask the user. The Synthesizer is non-interactive.

## Example provenance excerpt

```markdown
## phase-03-red-team-spawning

**Contributing variants:** 1, 3, 4, 5 (all except minimalist)

**Section attributions:**
- Overview: variant 4 (performance) — "most direct explanation of parallel spawn semantics"
- Files: union (hooks/hooks.json, scripts/orchestrate.sh, agents/redteam-*.md)
- Steps: variant 1 (correctness) — "explicit ordering: spawn, wait, persist envelopes"
- Success: variant 1 (correctness) — "three envelopes under reviews/ within ±3s"
- Risk: union of 1, 3, 4, 5
- Bias Lens: merged

**Contradictions resolved:**
- Variant 3 (defensive) added a rollback for the redteam spawn;
  variant 4 (performance) omitted it.
  Resolution rule: Metis directive "every parallel fan-out must checkpoint"
  → kept defensive variant's rollback.

**Rejected elements:**
- Variant 2 (minimalist) proposed sequential redteam execution.
  Rejected: violates invariant 6 (parallelization by default).
```
