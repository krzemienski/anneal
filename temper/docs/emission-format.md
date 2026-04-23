# Emission Format · Anneal · Temper

The XML Atlas writes at stage 7, plus the companion plan directory and depth-history log.

## File layout

```
${ANNEAL_RUNS_ROOT:-./.anneal/runs}/{run_id}/
├── temper-{run_id}.xml           # Opus 4.7 semantic-XML
├── plan/
│   ├── plan.md                   # Top-level plan overview (< 80 lines)
│   ├── phase-00-*.md             # Phase detail files
│   ├── phase-01-*.md
│   ├── ...
│   └── phase-NN-functional-validation.md
├── depth-history.json            # Temper-specific: per-depth scores, envelopes
└── depth-history/
    ├── depth-0-plan.md           # Per-depth plan snapshots
    ├── depth-1-plan.md
    └── depth-2-plan.md
```

## The XML

Follows `_shared/opus-47-xml-schema.md` with Temper-specific extensions in `<review>`.

```xml
<anneal_run>
  <metadata>
    <architecture>temper</architecture>
    <run_id>anneal-temper-YYYYMMDD-HHMMSS-{slug}</run_id>
    <timestamp>2026-04-22T14:44:00Z</timestamp>
    <task>{verbatim user task}</task>
    <project_root>/absolute/path</project_root>
  </metadata>

  <context>
    <probe_report>{stage 2 output, plain text or YAML-like}</probe_report>
    <enrichment_directives>{Metis directives, one per line}</enrichment_directives>
    <user_skills>{enumerated ~/.claude/skills/* and project .claude/skills/*}</user_skills>
    <reference_files>{code refs discovered in probe}</reference_files>
  </context>

  <plan>
    <thesis>{final plan thesis paragraph, from plan_N.md}</thesis>
    <phases>
      <phase id="00" name="baseline">...</phase>
      <phase id="01" name="...">...</phase>
      ...
      <phase id="NN" name="functional-validation">...</phase>
    </phases>
    <iron_rules>{non-negotiable constraints — no mocks, evidence-based, etc.}</iron_rules>
  </plan>

  <review>
    <metis_envelope>{YAML-serialized envelope}</metis_envelope>

    <!-- Temper-specific -->
    <depth_history>
      <depth n="0">
        <score>62.0</score>
        <momus_envelope>{YAML envelope}</momus_envelope>
        <redteam_envelopes>
          <security>{YAML envelope}</security>
          <scope>{YAML envelope}</scope>
          <assumptions>{YAML envelope}</assumptions>
        </redteam_envelopes>
      </depth>
      <depth n="1">
        <score>78.0</score>
        <momus_envelope>{...}</momus_envelope>
        <redteam_envelopes>
          <security>{...}</security>
          <scope>{...}</scope>
          <assumptions>{...}</assumptions>
        </redteam_envelopes>
      </depth>
      <depth n="2">
        <score>85.0</score>
        <momus_envelope>{...}</momus_envelope>
        <redteam_envelopes>
          <security>{...}</security>
          <scope>{...}</scope>
          <assumptions>{...}</assumptions>
        </redteam_envelopes>
      </depth>
    </depth_history>

    <convergence>
      <reason>variance</reason>
      <variance_top3>0.18</variance_top3>
      <abs_delta>7.0</abs_delta>
      <depth_reached>2</depth_reached>
    </convergence>
    <!-- End Temper-specific -->

    <oracle_envelope>{YAML envelope}</oracle_envelope>

    <rollup>
      <architecture>temper</architecture>
      <overall_verdict>SAFE</overall_verdict>
      <gate_status>
        <metis>SAFE</metis>
        <momus>SAFE</momus>
        <red_team_trinity>3/3 PASS</red_team_trinity>
        <oracle>SAFE</oracle>
        <hephaestus>PASS</hephaestus>
      </gate_status>
      <simultaneous_pass>true</simultaneous_pass>
      <blocking_issues></blocking_issues>
      <emission_decision>EMIT</emission_decision>
      <iteration_count>0</iteration_count>
    </rollup>
  </review>

  <validation>
    <hephaestus_evidence>
      <build>
        <command>python3 scripts/validate-plugin.py .</command>
        <exit_code>0</exit_code>
        <log_excerpt>VALIDATION PASSED</log_excerpt>
      </build>
      <runtime>
        <step n="01">
          <action>Ran /plugin marketplace add ...</action>
          <observation>Exit 0. Marketplace registered.</observation>
          <evidence_path>e2e-evidence/hephaestus/step-01-marketplace-add.txt</evidence_path>
        </step>
        ...
      </runtime>
      <verdict>PASS</verdict>
    </hephaestus_evidence>
  </validation>

  <instructions>
    <task>{verbatim task repeated — query-at-bottom}</task>
    <next_action>Read this entire XML, construct the plan from the plan/ directory, execute each phase sequentially, and exit when the functional-validation phase reports PASS.</next_action>
    <success_criteria>Every phase's success_criteria met. Functional-validation evidence non-empty. Oracle-level concerns addressed.</success_criteria>
  </instructions>

  <thinking_budget>xhigh</thinking_budget>
</anneal_run>
```

## The plan directory

### `plan.md` (top-level, < 80 lines)

```markdown
# Plan · {task-slug}

**Run:** {run_id}
**Architecture:** temper
**Depth:** {final_depth} of {depth_cap}
**Convergence:** {reason}
**Final score:** {final_score}
**Verdict:** {overall_verdict}
**Validate:** PASS

## Thesis
{One paragraph}

## Phases
- [Phase 00 · baseline](./phase-00-baseline.md)
- [Phase 01 · ...](./phase-01-...md)
- ...
- [Phase NN · functional-validation](./phase-NN-functional-validation.md)

## Iron Rules
- Red team runs every depth.
- No mocks, stubs, test doubles, test files.
- Evidence-based verdicts only.
- Compilation is not validation.
- Fix the real system, not the plan.

## Depth history
| Depth | Score | Verdict | Blocking issues |
|-------|-------|---------|-----------------|
| 0 | 62.0 | CAUTION | 3 |
| 1 | 78.0 | CAUTION | 1 |
| 2 | 85.0 | SAFE | 0 |
```

### Per-phase files

Each phase file follows the standard structure:

```markdown
# Phase 00 · {name}

## Overview
Why this phase exists.

## Related code files
- Read: [...]
- Create: [...]
- Modify: [...]
- Delete: [...]

## Implementation steps
1. Step one.
2. Step two.
3. ...

## Success criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Risk assessment
What could go wrong, and the mitigation.
```

## The depth-history log

### `depth-history.json`

```json
{
  "run_id": "anneal-temper-YYYYMMDD-HHMMSS-{slug}",
  "architecture": "temper",
  "depth_scores": [62.0, 78.0, 85.0],
  "depth_cap": 3,
  "convergence": {
    "reason": "variance",
    "variance_top3": 0.18,
    "abs_delta": 7.0,
    "depth_reached": 2
  },
  "depth_details": [
    {
      "depth": 0,
      "plan_path": "depth-history/depth-0-plan.md",
      "score": 62.0,
      "momus_envelope": {...},
      "redteam_envelopes": {
        "security": {...},
        "scope": {...},
        "assumptions": {...}
      }
    },
    {
      "depth": 1,
      "plan_path": "depth-history/depth-1-plan.md",
      "score": 78.0,
      ...
    },
    {
      "depth": 2,
      "plan_path": "depth-history/depth-2-plan.md",
      "score": 85.0,
      ...
    }
  ]
}
```

### `depth-history/depth-N-plan.md`

Snapshot of `plan_N.md` for each N. These are the full rewrites from each depth. Kept verbatim; no post-processing.

## Why transparency wins

The depth history is not a debug artifact — it's part of the emission. Downstream sessions reading the XML can see how the plan evolved, which rewrites addressed which findings, and why convergence fired where it did.

This is a deliberate design choice. Hiding the history would save a few KB of disk. Surfacing it costs the user nothing and provides:
- Auditability (why did we ship this plan?)
- Debugging (where did a weak phase come from?)
- Learning (which kinds of issues does Temper resolve quickly vs slowly?)

## File sizes

Typical Temper emission at depth 3:
- `temper-{run_id}.xml`: 20-50 KB
- `plan/plan.md`: 2-4 KB
- `plan/phase-*.md`: 3-8 KB each × 8-12 phases → 30-100 KB
- `depth-history.json`: 10-30 KB
- `depth-history/depth-N-plan.md`: 20-60 KB each × 3 depths → 60-180 KB

Total: ~150-400 KB per run. Well under any filesystem or IDE limit.
