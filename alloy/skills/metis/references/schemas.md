# Metis Schemas & Examples

## Input schema

```yaml
task: "<verbatim user task string>"
probe_report:
  project_root: "/abs/path"
  repo_summary: "..."
  enumerated_skills:
    user_skills: [...]    # ~/.claude/skills/*
    project_skills: [...] # .claude/skills/*
  reference_files: [...]
prior_constraints: []     # populated on re-loops from last rollup.blocking_issues
```

## Output schema (per `_shared/plan-reviewer-schema.md`)

```yaml
reviewer: metis
verdict: SAFE | CAUTION | RISKY | BLOCK
summary: "2-3 sentence assessment"
confidence: HIGH | MEDIUM | LOW
findings:
  - severity: CRITICAL | MAJOR | MINOR
    category: ambiguity | scope | security | assumption | coherence | missing-evidence
    reviewer: metis
    summary: "One sentence"
    evidence:
      - plan_file: "<task string or probe reference>"
        line_range: "n/a"
        excerpt: "..."
    suggestion: "Direction, not fix"
    blocks_emission: true | false
directives:
  - "Imperative sentence for the planner."
  - "Another imperative."
clarifying_questions: []   # non-empty ONLY if verdict is BLOCK
blocking_issues_count: <integer>
```

## Example — SAFE verdict

```yaml
reviewer: metis
verdict: SAFE
summary: Task is well-scoped; probe surfaces existing skill coverage; no blocking ambiguity.
confidence: HIGH
findings:
  - severity: MINOR
    category: coherence
    reviewer: metis
    summary: "Task mentions 'fast' without defining threshold."
    evidence:
      - plan_file: "task-string"
        line_range: "n/a"
        excerpt: "...make the cold-start fast..."
    suggestion: "Define fast in the plan (e.g. p95 < 200ms on M1)."
    blocks_emission: false
directives:
  - "The plan must define a measurable threshold for any performance claim."
  - "The plan must reuse `~/.claude/skills/launch-sub-agent` rather than re-implementing agent dispatch."
clarifying_questions: []
blocking_issues_count: 0
```

## Example — BLOCK verdict

```yaml
reviewer: metis
verdict: BLOCK
summary: Task references "the 91 defects" without enumerating which; no planner can proceed without the list.
confidence: HIGH
findings:
  - severity: CRITICAL
    category: ambiguity
    reviewer: metis
    summary: "Task references 91 specific defects by count but does not list them."
    evidence:
      - plan_file: "task-string"
        line_range: "n/a"
        excerpt: "...fix the 91 asymmetric-vendoring defects..."
    suggestion: "List the 91 defects or point to the audit document that enumerates them."
    blocks_emission: true
directives: []
clarifying_questions:
  - "Where is the list of 91 defects? (file path or inline enumeration)"
  - "If the count is approximate, what are the top 10 MUST-fix issues?"
blocking_issues_count: 1
```
