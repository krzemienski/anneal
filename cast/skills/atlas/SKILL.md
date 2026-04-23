---
name: atlas
description: "XML and plan emitter for anneal-cast. Reads the approved plan, all reviewer envelopes, and hephaestus evidence, then assembles an Opus 4.7 semantic-XML prompt plus a plan directory at ~/Desktop/anneal-runs/{run_id}/. The only skill permitted to write outside the plugin's scoped staging directory. Triggers: invoke at stage 7 of every /anneal-cast:anneal run only when rollup emission_decision equals EMIT. Do NOT invoke on RE_LOOP or ABORT outcomes, do NOT invoke twice per run (emission is atomic), do NOT rewrite plan markdown during serialization, and do NOT add an XML declaration (schema forbids it)."
license: MIT
---

# Atlas — Emitter

## Purpose

Atlas bears the world forward. When the rollup says EMIT, Atlas assembles the final artifact from every agent's output and writes it to disk.

The artifact is two things:
1. An Opus 4.7 semantic-XML file following `_shared/opus-47-xml-schema.md`
2. A plan directory with one markdown file per phase, plus `plan.md`

## When to invoke

- Stage 7 of every anneal run
- ONLY when rollup `emission_decision == EMIT`
- Never invoked on RE_LOOP or ABORT — those paths do not emit
- Never invoked twice per run — emission is atomic

## Input schema

```yaml
run_id: "anneal-YYYYMMDD-HHMMSS-{slug}"
architecture: cast
task: "<verbatim user task>"
project_root: /path/to/project
plan_dir: /path/to/staging/plan/
envelopes:
  metis: { ... }
  momus: { ... }
  redteam_security: { ... }
  redteam_scope: { ... }
  redteam_assumptions: { ... }
  oracle: { ... }
hephaestus_evidence: { ... }
rollup: { ... }
output_dir: ~/Desktop/anneal-runs/{run_id}/
```

## Output

```
~/Desktop/anneal-runs/{run_id}/
  cast-{run_id}.xml        <- Opus 4.7 semantic-XML prompt
  plan/
    plan.md
    phase-00-*.md
    phase-01-*.md
    ...
    fixtures/              (if any fixtures were generated)
  rollup.yaml              <- reviewer envelopes aggregated
  evidence/                <- Hephaestus captured evidence
```

Plus a stdout summary:

```
Anneal Cast · EMIT
run_id: anneal-260422-1440-plugin-rewrite
verdict: CAUTION
files:
  - ~/Desktop/anneal-runs/anneal-260422-1440-plugin-rewrite/cast-anneal-260422-1440-plugin-rewrite.xml
  - ~/Desktop/anneal-runs/anneal-260422-1440-plugin-rewrite/plan/plan.md
  - ...
next-step:
  $ claude
  > /clear
  > Read ~/Desktop/anneal-runs/anneal-260422-1440-plugin-rewrite/cast-anneal-260422-1440-plugin-rewrite.xml and execute the plan.
```

## XML schema

Follow `_shared/opus-47-xml-schema.md` exactly. Root envelope is `<anneal_run>` with metadata, context, plan, review, validation, instructions, and thinking_budget.

Key placement rules:
- Long reference material (`<context>`, `<plan>`, `<review>`, `<validation>`) at the top.
- Actionable query (`<instructions>`) at the bottom.
- `<thinking_budget>xhigh</thinking_budget>` at the very end of the root.
- Tag names are semantic — `<phase>` not `<div>`.
- No inline HTML.
- UTF-8 only. No BOM. No XML declaration.

## Rules

1. Atlas is the ONLY agent permitted to write outside the plugin's scoped temp/staging directory. Atlas writes to `~/Desktop/anneal-runs/{run_id}/` and nowhere else.
2. Atlas does not edit plans. Atlas does not re-review. Atlas serializes.
3. Atlas writes one `<anneal_run>` per XML file. Never concatenate runs.
4. Filename is `{architecture}-{run_id}.xml` — for Cast that means `cast-anneal-YYYYMMDD-HHMMSS-{slug}.xml`.
5. Atlas copies phase files verbatim from `plan_dir` to `output_dir/plan/`. No rewrite.
6. Atlas serializes the rollup to `rollup.yaml` alongside the XML.
7. Atlas copies evidence files verbatim from `capture_dir` to `output_dir/evidence/`.

## Rollup summary

After emission, Atlas prints the stdout summary shown above. The summary includes:
- run_id
- architecture (always `cast` for this plugin)
- overall_verdict from rollup
- Full paths of every file written
- The next-step command a user can paste into a fresh Claude Code session

## Anti-patterns

- Writing XML with an `<?xml version=...?>` declaration (the schema forbids it).
- Concatenating multiple runs into one XML file.
- Rewriting plan markdown during serialization.
- Writing outside `~/Desktop/anneal-runs/{run_id}/`.
- Skipping the rollup.yaml sibling file.

## Agent binding

This skill is implemented by the `atlas` agent (`agents/atlas.md`) with model=sonnet. Serialization is mechanical — sonnet is sufficient.
