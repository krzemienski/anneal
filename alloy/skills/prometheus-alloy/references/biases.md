# Prometheus-Alloy Bias Catalog

Every variant reads the SAME Metis directives and the SAME probe report. The `bias` parameter shapes *which tradeoffs the planner takes*.

Valid values: `correctness | minimalist | defensive | performance | ux | verification | migration`.

- N ∈ [2,5] uses the first 5 biases.
- N = 6 adds `verification`.
- N = 7 adds `migration`.

## Output markdown template

```markdown
# Variant {I} · Bias: {bias}

## Thesis
{1-paragraph plan summary from this bias's perspective}

## Phases

### phase-00-{slug}
- **Overview:** why this phase exists (bias-specific framing)
- **Related code files:** read / create / modify / delete
- **Implementation steps:** numbered, specific
- **Success criteria:** measurable (no "looks good" vibes)
- **Risk assessment:** what fails if this phase is wrong
- **Bias lens:** how {bias} shaped this phase (e.g. "added rollback checkpoint because defensive")

### phase-01-{slug}
...

## Iron rules inherited
- No test files. No mocks. No stubs.
- Functional validation phase mandatory.
- Evidence before completion.

## Bias disclosure
This plan was written under `{bias}` bias. Elements I prioritized:
- ...
- ...
Elements I deliberately under-weighted:
- ...
- ...
```

## The 7 bias lenses

### `correctness`
- Every phase ends with a measurable gate test.
- Phased rollout: no phase depends on a future phase succeeding.
- Success criteria are evidence-citable (not "checked" but "file X exists AND contains Y").
- Validation phase has ≥3 checkpoints, not 1.

### `minimalist`
- Strip every non-essential phase.
- No "while we're here" polish.
- Success criteria cite only the user's stated requirements, not implied best practices.
- No preflight unless a directive mandates it.
- Target: shortest plan that still satisfies directives.

### `defensive`
- Every phase has an explicit rollback section.
- Checkpoint before every destructive operation.
- Failure modes enumerated per phase, not per plan.
- State file writes (`.anneal/state.json`) at phase transitions.
- Assumes hostile environment (disk full, network flaky, tool missing).

### `performance`
- Vendor only what the plan's implementation steps actually USE.
- No speculative infra ("we might need a cache layer").
- Parallelize wherever ordering allows.
- Prefer bash pipelines over multi-step orchestration when functionally equivalent.
- Minimize hot-path allocations — name the hot path explicitly.

### `ux`
- Every phase has a status-line progress signal (e.g. `[3/12] Synthesizing...`).
- Error messages name the next action, not just the symptom.
- First-failure guidance: most likely failure per phase + the fix.
- Output is skimmable (headers, bullets, code blocks — never prose-walls).
- "What the user sees" column in each phase.

### `verification` (N=6 or 7 only)
- Instrument-before-theorize: every hypothesis has a print/log/capture step.
- Phases include explicit debug hooks that can be removed post-validation.
- Evidence paths named upfront (`.debug/<issue-id>/...`).
- No more than 10 minutes of theoretical reasoning before instrumentation.

### `migration` (N=7 only)
- Every breaking change has an explicit migration step.
- Tombstones / 410 Gone for removed paths.
- Compatibility shims where removal-cost > shim-cost.
- "Users on v0.x must do X to upgrade" documented per breaking change.

## Phase-count guardrails

- Minimum 3 phases per variant (fewer = under-scoped).
- Maximum 20 phases per variant (more = the Synthesizer cannot consume it in one pass).
- Every phase has all 6 sections (Overview, Files, Steps, Success, Risk, Bias Lens). Missing sections = plan incomplete.
