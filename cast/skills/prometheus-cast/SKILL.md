---
name: prometheus-cast
description: "Cast-flavored planner. Writes a complete markdown plan in a single pass — no retry, no tournament, no deepen loop. Consumes Metis directives and the probe report; emits phase files plus plan.md. Triggers: invoke at stage 4 of every /anneal-cast:anneal run exactly once per iteration. Do NOT invoke outside stage 4, do NOT invoke twice without a full re-loop through Metis, and do NOT use this skill for Alloy tournament planning or Temper deepen-loop planning — those are separate plugins."
license: MIT
---

# Prometheus · Cast — Planner

## Purpose

Write the plan. One pass. One markdown directory. No alternatives explored.

Cast's flavor of Prometheus differs from the Alloy and Temper variants:
- **Cast:** one call, one plan, no feedback loop inside stage 4
- Alloy: N parallel calls, each with a different bias, feeding a synthesizer
- Temper: one call per depth, each rewriting the prior iteration with feedback baked in

This skill is the Cast flavor.

## When to invoke

- Stage 4 of every Cast run, exactly once per iteration
- Never invoked outside stage 4
- Never invoked twice without a full re-loop (which routes through Metis first)

## Input schema

```yaml
task: "<verbatim user task>"
task_classification: bug-fix | scoped-refactor | infra-change | new-feature | documentation
metis_directives:
  - "imperative sentence 1"
  - "imperative sentence 2"
probe_report:
  files: [ ... ]
  skills: [ ... ]
  docs: [ ... ]
  platform: <detected>
  package_manager: <detected>
output_dir: /path/to/staging/plan/
```

## Output schema

Markdown files written to `output_dir`:

```
plan/
  plan.md                          <- overview, phase index, dependencies, 80 lines max
  phase-00-<kebab-name>.md         <- setup / preflight phase
  phase-01-<kebab-name>.md
  ...
  phase-NN-functional-validation.md  <- mandatory final phase
```

Each phase file:

```markdown
# Phase <NN> — <name>

## Overview
Why this phase exists. 3-5 sentences.

## Related code files

### Read
- path/to/file.ts

### Create
- path/to/new-file.ts

### Modify
- path/to/existing-file.ts

### Delete
- path/to/obsolete-file.ts

## Implementation steps
1. Specific numbered step.
2. Specific numbered step.
...

## Success criteria
- [ ] Concrete, measurable, evidenced outcome 1
- [ ] Concrete, measurable, evidenced outcome 2

## Risk assessment
- Risk: description. Mitigation: description.
```

## Rules

1. Every Cast plan MUST include a functional-validation phase. It is the last phase. It has evidence checkpoints describing what Hephaestus must capture.
2. Cast plans MUST NOT include "write unit tests," "add test coverage," or any test-framework step. Validation is functional, not synthetic.
3. Every Metis directive must appear in the plan as a respected constraint. If a directive conflicts with user goals, surface the conflict as a note in `plan.md` — do not silently resolve.
4. Phase count is as many as needed — usually 5 to 12. Never pad to hit a number.
5. `plan.md` stays under 80 lines. The phase files carry the detail.
6. No emoji in any plan file.
7. Use relative paths from the repo root consistently.

## Skill enrichment

If the probe report enumerated user skills that match the task domain, add a `## Skill enrichment` section at the top of `plan.md`:

```markdown
## Skill enrichment

The following skills from ~/.claude/skills/ apply to this plan:
- skill-name — why it applies
- another-skill — why it applies
```

The downstream execution session reads this and auto-invokes matching skills.

## Example output (excerpt)

```markdown
# Plan · Fix pagination bug in src/feed/list.ts

## Thesis
page=0 currently returns duplicate rows because the cursor resets without checking bounds. Fix by guarding the cursor reset and adding a regression guard in the route handler.

## Phase index
- 00 — reproduce-the-bug
- 01 — isolate-root-cause
- 02 — implement-guard
- 03 — add-route-assertion
- 04 — functional-validation
```

## Anti-patterns

- Writing code instead of plan.
- Over-specifying implementation detail (the plan is for a downstream session; leave room).
- Under-specifying success criteria (Hephaestus needs to check them).
- Skipping the validation phase.

## Agent binding

This skill is implemented by the `prometheus-cast` agent (`agents/prometheus-cast.md`) with model=opus.
