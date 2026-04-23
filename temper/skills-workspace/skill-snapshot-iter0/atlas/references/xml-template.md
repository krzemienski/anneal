# Atlas · Opus 4.7 XML Emission Template (Temper)

The canonical XML body Atlas writes to `${ANNEAL_RUNS_ROOT:-./.anneal/runs}/{run_id}/temper-{run_id}.xml`.
Schema source: `_shared/opus-47-xml-schema.md`. This file adds Temper-specific additions (`<depth_history>`, `<convergence>`).

## Full template

```xml
<anneal_run>
  <metadata>
    <architecture>temper</architecture>
    <run_id>anneal-temper-YYYYMMDD-HHMMSS-{slug}</run_id>
    <timestamp>ISO-8601</timestamp>
    <task>{verbatim user task}</task>
    <project_root>/absolute/path</project_root>
  </metadata>

  <context>
    <probe_report>{stage 2 output}</probe_report>
    <enrichment_directives>{Metis directives}</enrichment_directives>
    <user_skills>{enumerated skills}</user_skills>
    <reference_files>{code refs from probe}</reference_files>
  </context>

  <plan>
    <thesis>{final plan thesis paragraph}</thesis>
    <phases>
      <phase id="00" name="...">...</phase>
      <phase id="01" name="...">...</phase>
      <!-- ... -->
    </phases>
    <iron_rules>{non-negotiable constraints carried over}</iron_rules>
  </plan>

  <review>
    <metis_envelope>{yaml or json-serialized envelope}</metis_envelope>

    <!-- Temper-specific: depth history -->
    <depth_history>
      <depth n="0">
        <score>62.0</score>
        <momus_envelope>{...}</momus_envelope>
        <redteam_envelopes>
          <security>{...}</security>
          <scope>{...}</scope>
          <assumptions>{...}</assumptions>
        </redteam_envelopes>
      </depth>
      <depth n="1">...</depth>
      <depth n="2">...</depth>
    </depth_history>

    <convergence>
      <reason>variance | delta | cap</reason>
      <variance_top3>0.18</variance_top3>
      <abs_delta>7.0</abs_delta>
      <depth_reached>2</depth_reached>
    </convergence>

    <oracle_envelope>{...}</oracle_envelope>

    <rollup>
      <overall_verdict>SAFE | CAUTION</overall_verdict>
      <simultaneous_pass>true</simultaneous_pass>
      <blocking_issues>{deduped list or empty}</blocking_issues>
      <emission_decision>EMIT</emission_decision>
      <iteration_count>{validate_attempts}</iteration_count>
    </rollup>
  </review>

  <validation>
    <hephaestus_evidence>
      <build>{actual build output}</build>
      <runtime>{actual screenshots / API / CLI}</runtime>
      <verdict>PASS</verdict>
    </hephaestus_evidence>
  </validation>

  <instructions>
    <task>{verbatim task repeated — query-at-bottom}</task>
    <next_action>{what a fresh Claude Code session should do}</next_action>
    <success_criteria>{how the fresh session knows it's done}</success_criteria>
  </instructions>

  <thinking_budget>xhigh</thinking_budget>
</anneal_run>
```

## Rules

1. UTF-8 only, no BOM, no XML declaration.
2. Tag names are semantic, not syntactic.
3. Long reference material at top (`<context>`, `<plan>`, `<review>`, `<validation>`). Actionable query (`<instructions>`) at the bottom.
4. `<thinking_budget>xhigh</thinking_budget>` at the end of the root envelope.
5. One `<anneal_run>` per file. Never concatenate runs.
6. No `<thinking>` tags — this is a prompt, not a transcript.

## Temper-specific additions vs. Cast/Alloy schema

- `<depth_history>` — one `<depth>` block per loop iteration with score + envelopes.
- `<convergence>` — single block with reason (variance/delta/cap) and measured values.
- `<rollup><iteration_count>` — validate_attempts counter for re-loop tracking.

## Sibling artifacts Atlas writes alongside the XML

- `plan/plan.md` + `plan/phase-NN-*.md` — plan directory.
- `depth-history.json` — machine-readable per-depth snapshot (see SKILL.md § "Depth history log").
- `depth-history/depth-N-plan.md` — per-depth plan snapshots.
