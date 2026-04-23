# Emission Format — Opus 4.7 Semantic XML

Every Atlas emission follows the schema defined in `_shared/opus-47-xml-schema.md` (in the Anneal repo, outside this plugin). This doc is the plugin-local reference and validation target.

## Root envelope

```xml
<anneal_run>
  <metadata>
    <architecture>cast</architecture>
    <run_id>anneal-YYYYMMDD-HHMMSS-{slug}</run_id>
    <timestamp>ISO-8601</timestamp>
    <task>{verbatim user task string}</task>
    <project_root>/absolute/path</project_root>
  </metadata>

  <context>
    <probe_report>{stage 2 output}</probe_report>
    <enrichment_directives>{stage 3 Metis output}</enrichment_directives>
    <user_skills>{enumerated ~/.claude/skills/* and project .claude/skills/*}</user_skills>
    <reference_files>{code refs discovered in probe}</reference_files>
  </context>

  <plan>
    <thesis>{1-paragraph plan summary}</thesis>
    <phases>
      <phase id="00" name="..."> ... </phase>
      <phase id="01" name="..."> ... </phase>
    </phases>
    <iron_rules>{non-negotiable constraints carried over}</iron_rules>
  </plan>

  <review>
    <metis_envelope>...</metis_envelope>
    <momus_envelope>...</momus_envelope>
    <red_team>
      <security>...</security>
      <scope>...</scope>
      <assumptions>...</assumptions>
    </red_team>
    <oracle_envelope>...</oracle_envelope>
    <rollup>
      <overall_verdict>SAFE | CAUTION | RISKY | BLOCK</overall_verdict>
      <simultaneous_pass>true | false</simultaneous_pass>
      <blocking_issues>...</blocking_issues>
      <emission_decision>EMIT | RE_LOOP | ABORT</emission_decision>
    </rollup>
  </review>

  <validation>
    <hephaestus_evidence>
      <build>...</build>
      <runtime>...</runtime>
      <verdict>PASS | FAIL</verdict>
    </hephaestus_evidence>
  </validation>

  <instructions>
    <task>{verbatim task repeated here — query-at-bottom}</task>
    <next_action>...</next_action>
    <success_criteria>...</success_criteria>
  </instructions>

  <thinking_budget>xhigh</thinking_budget>
</anneal_run>
```

## Rules

1. **UTF-8 only**, no BOM, no XML declaration. Claude parses by tag structure.
2. **Tag names are semantic**, not syntactic — `<phase>` not `<div class="phase">`.
3. **Long reference material at top** (`<context>`, `<plan>`, `<review>`, `<validation>`). Actionable query (`<instructions>`) goes last.
4. **No inline HTML.** Plain text inside tags. Line breaks are fine.
5. **Every envelope carries `verdict` + `confidence`** per the plan-reviewer schema.
6. **`<thinking_budget>xhigh</thinking_budget>`** signals the downstream session should engage extended thinking.
7. **Atomic runs.** One `<anneal_run>` per emission. Never concatenate.

## Why this shape

Anthropic's Opus 4.7 research identified a "docs-at-top, query-at-bottom" pattern that yields ~30% better responses for long-context prompts. Atlas puts reference material first and the actionable instruction last to exploit that finding.

The schema is model-family-specific. If you need a prompt for a different family, re-serialize via a different emitter — Atlas only writes Anthropic-flavored XML.

## Validation

Use `scripts/validate-xml.py <path-to-emission.xml>` to check an emitted file against the schema. The validator enforces:

- Encoding (UTF-8, no BOM, no declaration)
- Root element name
- Required children and their order
- `<architecture>` is one of cast / alloy / temper
- `<thinking_budget>` is `xhigh`
- No inline HTML tags anywhere
- Only one `<anneal_run>` per file

Exit 0 on pass. Exit 1 on any violation.

## Filename

```
{architecture}-{run_id}.xml
```

Cast emissions are always `cast-anneal-YYYYMMDD-HHMMSS-{slug}.xml`.

## Emission directory

```
~/Desktop/anneal-runs/{run_id}/
  {architecture}-{run_id}.xml
  plan/
    plan.md
    phase-*.md
    fixtures/
  rollup.yaml
  evidence/
```

## Reading the emission

From a fresh Claude Code session:

```
$ claude
> /clear
> Read ~/Desktop/anneal-runs/{run_id}/cast-{run_id}.xml and execute the plan.
```

The downstream session receives:
- `<context>` — everything the planner saw at stage 2
- `<plan>` — the complete plan markdown, serialized by phase
- `<review>` — every reviewer envelope plus the rollup
- `<validation>` — Hephaestus's captured evidence
- `<instructions>` — the actionable task and success criteria

The session walks the plan, using the context and review envelopes as reference. `<thinking_budget>xhigh</thinking_budget>` tells the harness to allocate extended-thinking budget.
