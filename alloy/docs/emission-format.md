# Emission Format — Opus 4.7 Semantic XML

The canonical schema Atlas emits. Based on `_shared/opus-47-xml-schema.md`, with Alloy-specific additions.

Claude Opus 4.7 parses best when long reference material sits at the top of the document and the actionable query sits at the bottom — Anthropic's "docs-at-top, query-at-bottom" finding (~30% quality gain).

---

## Root envelope

```xml
<anneal_run>
  <metadata>
    <architecture>alloy</architecture>
    <run_id>anneal-YYYYMMDD-HHMMSS-{slug}</run_id>
    <timestamp>ISO-8601</timestamp>
    <task>{verbatim user task string}</task>
    <project_root>/absolute/path</project_root>

    <!-- Alloy-specific -->
    <tournament>
      <variants>N</variants>
      <biases>correctness,minimalist,defensive,performance,ux</biases>
      <silent_rejections>0</silent_rejections>
      <synthesis_provenance_ref>synthesis-provenance.md</synthesis_provenance_ref>
    </tournament>
  </metadata>

  <context>
    <probe_report>{stage 2 output — markdown excerpt or full text if <5k tokens}</probe_report>
    <enrichment_directives>
      {stage 3 Metis directives — verbatim YAML}
    </enrichment_directives>
    <user_skills>
      {enumerated ~/.claude/skills/* — list}
    </user_skills>
    <project_skills>
      {enumerated .claude/skills/* — list}
    </project_skills>
    <reference_files>
      {code refs discovered in probe — file paths + 1-line summaries}
    </reference_files>
  </context>

  <plan>
    <thesis>
      {1-paragraph plan summary}
    </thesis>
    <phases>
      <phase id="00" name="baseline">
        <overview>...</overview>
        <files>
          <read>...</read>
          <create>...</create>
          <modify>...</modify>
          <delete>...</delete>
        </files>
        <steps>
          <step n="1">...</step>
          <step n="2">...</step>
          ...
        </steps>
        <success>...</success>
        <risk>...</risk>
        <bias_lens>
          {cites contributing variants and their biases per synthesis-provenance}
        </bias_lens>
      </phase>
      <phase id="01" name="scaffold">...</phase>
      <!-- etc. -->
    </phases>
    <iron_rules>
      <rule>No test files. No mocks. No stubs.</rule>
      <rule>Functional validation phase mandatory.</rule>
      <rule>Evidence before completion.</rule>
    </iron_rules>
  </plan>

  <review>
    <metis_envelope>
      {verbatim YAML envelope from reviews/metis-envelope.yaml}
    </metis_envelope>
    <momus_envelope>
      {verbatim YAML}
    </momus_envelope>
    <red_team>
      <security>{verbatim YAML}</security>
      <scope>{verbatim YAML}</scope>
      <assumptions>{verbatim YAML}</assumptions>
    </red_team>
    <oracle_envelope>
      {verbatim YAML}
    </oracle_envelope>
    <rollup>
      <architecture>alloy</architecture>
      <overall_verdict>SAFE | CAUTION | RISKY | BLOCK</overall_verdict>
      <gate_status>
        <metis>SAFE | CAUTION | RISKY | BLOCK</metis>
        <momus>SAFE | CAUTION | RISKY | BLOCK</momus>
        <red_team_trinity>N/3 PASS</red_team_trinity>
        <oracle>SAFE | CAUTION | RISKY | BLOCK</oracle>
        <hephaestus>PASS | FAIL</hephaestus>
      </gate_status>
      <simultaneous_pass>true | false</simultaneous_pass>
      <blocking_issues>
        {deduped list — each entry cites severity, category, reviewer, summary}
      </blocking_issues>
      <emission_decision>EMIT | RE_LOOP | ABORT</emission_decision>
      <iteration_count>N</iteration_count>

      <!-- Alloy-specific -->
      <tournament_stats>
        <variant_count>N</variant_count>
        <biases_participating>...</biases_participating>
        <biases_contributing_to_blend>...</biases_contributing_to_blend>
        <silent_rejections>0</silent_rejections>
        <contradictions_resolved>N</contradictions_resolved>
      </tournament_stats>
    </rollup>
  </review>

  <validation>
    <hephaestus_evidence>
      <build>
        <command>...</command>
        <output>...</output>
        <exit_code>0</exit_code>
      </build>
      <runtime>
        <step>
          <description>...</description>
          <command>...</command>
          <output>...</output>
          <timestamp>ISO-8601</timestamp>
        </step>
        <!-- more steps -->
      </runtime>
      <evidence_files>
        {list of file paths under reviews/hephaestus-evidence/}
      </evidence_files>
      <verdict>PASS | FAIL</verdict>
    </hephaestus_evidence>
  </validation>

  <instructions>
    <task>{verbatim task — MUST match <metadata><task> byte-for-byte}</task>
    <next_action>
      {what a fresh Claude Code session should do when it reads this XML}
      Example: "Execute the plan in ~/Desktop/anneal-runs/{run_id}/plan/ phase by phase.
      After each phase, re-run scripts/validate-plugin.py and capture evidence."
    </next_action>
    <success_criteria>
      {how the fresh session knows it's done}
      Example: "validate-plugin.py exits 0; /plugin list shows anneal-alloy@0.1.0."
    </success_criteria>
  </instructions>

  <thinking_budget>xhigh</thinking_budget>
</anneal_run>
```

---

## Rules

1. **UTF-8 only.** No BOM. No XML declaration. Claude parses by tag structure.
2. **Tag names are semantic**, not syntactic. `<phase>` not `<div class="phase">`.
3. **Long reference material at top** (`<context>`, `<plan>`, `<review>`, `<validation>`). Actionable query at bottom (`<instructions>`).
4. **No inline HTML.** Plain text inside tags. Line breaks OK.
5. **Every envelope carries `verdict` + `confidence`** per the plan-reviewer schema.
6. **`<thinking_budget>xhigh</thinking_budget>`** signals the downstream session should engage extended thinking.
7. **Atomic runs.** One `<anneal_run>` per emission. Never concatenate multiple runs in a single XML file.
8. **Query-at-bottom invariant.** `<metadata><task>` and `<instructions><task>` must be byte-for-byte identical. `validate-xml.py` enforces this.

## Alloy-specific additions

- **`<metadata><tournament>`** — tournament metadata. Required for Alloy (architecture=alloy).
- **`<review><rollup><tournament_stats>`** — tournament execution stats.
- **`<phase><bias_lens>`** — per-phase bias attribution summary (full detail in `synthesis-provenance.md` reference file).

---

## Emission filename

```
alloy-{run_id}.xml
```

Example: `alloy-anneal-20260422-1452-plugin-rewrite.xml`

---

## Emission location

```
~/Desktop/anneal-runs/{run_id}/
├── alloy-{run_id}.xml                ← this file
├── plan/
│   ├── plan.md                        ← referenced from <plan>
│   └── phase-00-*.md ... phase-NN-*.md
├── variants/                          ← Alloy-specific, preserved from tournament
│   └── variant-{I}-{bias}.md
├── synthesis-provenance.md            ← Alloy-specific, referenced from <metadata><tournament>
├── reviews/
│   ├── metis-envelope.yaml
│   ├── momus-envelope.yaml
│   ├── redteam-*-envelope.yaml
│   ├── oracle-envelope.yaml
│   └── hephaestus-evidence/
└── rollup.yaml                        ← duplicates <review><rollup> for quick diffing
```

---

## Validation

Every emitted XML file must pass `scripts/validate-xml.py`:

```bash
python3 scripts/validate-xml.py ~/Desktop/anneal-runs/{run_id}/alloy-{run_id}.xml
# expected: XML VALIDATION PASSED
```

The validator checks:
- UTF-8 + no BOM + no declaration
- Root is `<anneal_run>`
- All required top-level children present
- `<architecture>alloy</architecture>`
- `<tournament>` present with variants + biases
- `<red_team>` has security, scope, assumptions
- `<thinking_budget>xhigh</thinking_budget>`
- `<metadata><task>` == `<instructions><task>` (query-at-bottom)
