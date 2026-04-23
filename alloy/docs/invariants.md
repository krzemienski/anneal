# The Seven Invariants

These apply identically to **Cast**, **Alloy**, and **Temper**. The three architectures differ only in how stage 4 (Plan) generates its output. Every other contract is shared.

An anneal run that violates any invariant is invalid and must not emit. Atlas refuses to serialize runs where an invariant failed.

---

## 1 · Red team always runs

Three parallel adversaries — **Security**, **Scope**, **Assumptions** — run every run. Not a flag. Cannot be disabled. The only way to avoid red team is to not run anneal.

Refused flags (logged and ignored):
- `--no-red-team`

**Why:** Skipping red team makes the plan look stronger than it is. Anneal's entire rationale is "the review is non-negotiable." A flag to disable it would nullify the plugin.

---

## 2 · Validation always runs

Hephaestus builds the real artifact, exercises it, captures evidence. No mocks, no test files, no stubs. Empty evidence → FAIL.

Refused flags:
- `--no-validate`

**Why:** Compilation ≠ validation. Plans that "should work" routinely don't. The only way to know is to build and run.

---

## 3 · Dual output

Every emission produces **two** artifacts:

1. An Opus 4.7 semantic-XML prompt (one file)
2. A plan directory (markdown phase files)

Either artifact alone is insufficient. The XML is for fresh-session dispatch; the plan is for human review and future reference.

---

## 4 · Skill enrichment is automatic

The Probe stage scans:

- `~/.claude/skills/*/SKILL.md` (user skills)
- `<project>/.claude/skills/*/SKILL.md` (project skills)

Matching skills are injected into the plan's prelude. The user does not select skills; Metis consults them and the Synthesizer composites them.

**Why:** Users don't know which skills apply. The plugin does.

---

## 5 · Unbounded re-loop on FAIL

If Hephaestus returns FAIL, the run routes back to planning with the failure added as a new constraint.

- **Cast:** FAIL → Planner (same planner, new constraint)
- **Alloy:** FAIL → Intent Gate (whole tournament re-runs with failure as Metis constraint)
- **Temper:** FAIL → Seed Plan (deepen loop restarts with new seed constraint)

Default soft cap: **3 iterations**. `--loop` flag removes the cap entirely (`max_iterations = 999999`).

The re-loop is not a retry. It is constraint accumulation — each failed iteration adds a new directive to the next.

---

## 6 · Parallelization by default

Wherever two steps are independent, they run in parallel:

- **Red Team Trinity** — three adversaries, always parallel
- **Alloy planners** — N biased variants, always parallel
- **Multi-platform validators** (when Hephaestus sees multiple platforms) — parallel

Sequential execution of independent steps is a bug. The orchestrator enforces parallelism via `xargs -P` or equivalent.

---

## 7 · Category routing, not model picking

Users specify **work category** — `ultrabrain`, `deep`, `quick` — not model. The harness maps category to model. This decouples the user's intent ("hard problem") from the provider's lineup ("opus-4.7 vs sonnet-4.5 vs...").

Refused flags:
- `--model opus`
- `--model sonnet`

Use `--type ultrabrain | deep | quick` instead.

---

## Invariants are not negotiable

Every anneal plugin version 0.1.0+ must satisfy all seven. A plugin that violates any of them is not compliant and must not be published under the `anneal-*` namespace.

When in doubt, ask: "Does this feature weaken one of the seven?" If yes, don't ship it.
