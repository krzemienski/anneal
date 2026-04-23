# Opus 4.7 Semantic XML Output Schema

The canonical schema every Atlas emission must follow. Claude Opus 4.7 reads these tags best when the document places long reference material at the top and the actionable query at the bottom (Anthropic's "docs-at-top, query-at-bottom" finding — ~30% quality gain).

## Root envelope

```xml
<anneal_run>
  <metadata>
    <architecture>cast | alloy | temper</architecture>
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
      <!-- ... -->
    </phases>
    <iron_rules>{non-negotiable constraints carried over}</iron_rules>
  </plan>

  <review>
    <metis_envelope>{pre-plan consult output}</metis_envelope>
    <momus_envelope>{post-plan audit output}</momus_envelope>
    <red_team>
      <security>{envelope}</security>
      <scope>{envelope}</scope>
      <assumptions>{envelope}</assumptions>
    </red_team>
    <oracle_envelope>{bird's-eye verdict}</oracle_envelope>
    <rollup>
      <overall_verdict>SAFE | CAUTION | RISKY | BLOCK</overall_verdict>
      <simultaneous_pass>true | false</simultaneous_pass>
      <blocking_issues>{deduped list}</blocking_issues>
      <emission_decision>EMIT | RE_LOOP | ABORT</emission_decision>
    </rollup>
  </review>

  <validation>
    <hephaestus_evidence>
      <build>{actual build output}</build>
      <runtime>{actual runtime output / screenshots / API responses}</runtime>
      <verdict>PASS | FAIL</verdict>
    </hephaestus_evidence>
  </validation>

  <instructions>
    <task>{verbatim task repeated here — query-at-bottom}</task>
    <next_action>{what a fresh Claude Code session should do when it reads this}</next_action>
    <success_criteria>{how the fresh session knows it's done}</success_criteria>
  </instructions>

  <thinking_budget>xhigh</thinking_budget>
</anneal_run>
```

## Rules

1. **UTF-8 only**, no BOM, no XML declaration (Claude parses by tag structure).
2. **Tag names are semantic**, not syntactic — `<phase>` not `<div class="phase">`.
3. **Long reference material goes at top** (`<context>`, `<plan>`, `<review>`, `<validation>`). Actionable query (`<instructions>`) goes last.
4. **No inline HTML.** Use plain text inside tags. Line breaks OK.
5. **Every envelope carries `verdict` + `confidence`** per the plan-reviewer schema.
6. **`thinking_budget>xhigh`** signals the downstream session should engage extended thinking.
7. **Atomic runs.** One `<anneal_run>` per emission. Never concatenate runs in a single XML file.

## Emission filename

```
{architecture}-{run_id}.xml
```

e.g. `cast-anneal-260422-1440-plugin-rewrite.xml`

Emit to `~/Desktop/anneal-runs/{run_id}/` with a sibling `plan/` directory containing the markdown phase files that `<phases>` references by path.
