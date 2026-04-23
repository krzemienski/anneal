# Worked Example — The Plugin Rewrite

The canonical test case for Cast: use the plugin to plan its own predecessor's replacement.

## Input

```
/anneal-cast:anneal "rewrite the deepest-plan plugin to use SADD primitives and fix the 91 asymmetric-vendoring defects. Ship a functional v0.1.0 that passes its own red team."
```

## Stage-by-stage trace

### Stage 1 · Intent Gate

The task is classified as `infra-change`. It touches a Claude Code plugin, which is structural. The request is legitimate (no secret extraction, no destructive filesystem ops). Proceed.

### Stage 2 · Probe

Probe scans:
- `~/Desktop/deepest-plan/` — the predecessor plugin
- `~/.claude/plugins/sadd/` — the SADD primitive library
- `~/.claude/skills/` — user skills available
- `~/.claude/plugins/` — peer plugins for reference

Probe report excerpt:

```yaml
files:
  - ~/Desktop/deepest-plan/plugin.json
  - ~/Desktop/deepest-plan/skills/
  - ~/Desktop/deepest-plan/defects-report.md
skills:
  - launch-sub-agent
  - do-in-parallel
  - do-and-judge
  - tree-of-thoughts
  - explore
  - functional-validation
  - create-validation-plan
platform: claude-code-plugin
package_manager: n/a
```

### Stage 3 · Enrich via Metis

Metis returns an envelope with `verdict: CAUTION` and four directives:

```yaml
reviewer: metis
verdict: CAUTION
summary: "Task is ambitious but scoped. Four directives guard the known failure modes of the predecessor."
confidence: HIGH
findings:
  - severity: MAJOR
    category: ambiguity
    summary: "'91 asymmetric-vendoring defects' — no enumerated list provided."
    suggestion: "Ask user for the defect list or treat deepest-plan/defects-report.md as the source."
    blocks_emission: false
  - severity: MINOR
    category: scope
    summary: "'passes its own red team' — which red team? Anneal's or a prior definition?"
    suggestion: "Clarify to Anneal's Red-Team Trinity."
    blocks_emission: false
directives:
  - "Use deepest-plan/defects-report.md as the authoritative defect list."
  - "The v0.1.0 plugin MUST pass Cast's own Red-Team Trinity."
  - "Do not re-implement launch-sub-agent or do-in-parallel — vendor them from SADD."
  - "Do not ship with emoji in plugin content — the Claude Code docs discourage it."
clarifying_questions: []
blocking_issues_count: 0
```

### Stage 4 · Plan via Prometheus (single pass)

Prometheus produces a 12-phase plan:

```
00-baseline                  # read predecessor, catalog defects
01-skeleton                  # plugin directory structure
02-manifest                  # plugin.json + marketplace.json
03-skills                    # seven skill files
04-agents                    # nine agent files
05-command                   # /anneal-cast:anneal
06-hooks                     # hooks.json
07-scripts                   # validate-plugin.py + orchestrate.sh + validate-xml.py
08-docs                      # README, PRD, ARCHITECTURE, invariants, worked-example
09-diagram                   # standalone HTML visual
10-install-test              # install the plugin, verify command registers
11-functional-validation     # boot plugin, run command against a trivial task, capture evidence
```

Then Momus audits. Momus returns `verdict: CAUTION` with three findings — one flagging that phase 10's success criterion is under-specified, two flagging that phase 07 does not name the exact scripts until phase 07 itself (forward reference). Proceed to stage 5.

### Stage 5 · Red-Team Trinity + Oracle

Three parallel sub-agent launches:

- **Security** returns `verdict: SAFE`. No CRITICAL findings. Plan does not introduce secrets, auth gaps, or injection paths.
- **Scope** returns `verdict: CAUTION`. Flags that phase 09 (diagram) is not strictly necessary for v0.1.0 MVP — scope creep risk.
- **Assumptions** returns `verdict: CAUTION`. Flags that phase 06 assumes `hooks.json` is not referenced from `plugin.json` (which would cause duplicate-load errors). Suggests adding a guard in phase 06.

Oracle aggregates:

```yaml
reviewer: oracle
verdict: CAUTION
confidence: HIGH
summary: "Plan is coherent and security-clean. Mild scope concern on diagram; assumption about hook registration is explicit in directives. Proceed."
release_coherence: "Phases flow correctly; phase 07 scripts are implied by phase 02 manifest."
deployment_risk: "Low — plugin is additive, not modifying an existing plugin."
breaking_changes: ["None"]
monitoring_recommendations:
  - "After install, run `/plugin list` and confirm anneal-cast appears."
  - "Run scripts/validate-plugin.py against the plugin root."
blocking_issues:
  - severity: MAJOR
    source_reviewer: "redteam-assumptions"
    summary: "Phase 06 must NOT reference hooks.json in plugin.json."
    evidence:
      plan_file: "phase-06-hooks.md"
      line_range: "12-14"
blocking_issues_count: 1
```

### Stage 6 · Validate via Hephaestus

Hephaestus:

1. Creates a scratch worktree at `~/Desktop/anneal/cast-scratch/`.
2. Executes phase 02 (writes `plugin.json` + `marketplace.json`) in the scratch tree.
3. Executes phase 07 (writes `scripts/validate-plugin.py`).
4. Runs `python3 scratch/scripts/validate-plugin.py scratch/` — captures stdout.
5. Runs `claude plugin marketplace add scratch/` — captures result.
6. Runs `claude plugin install anneal-cast@anneal-cast-dev` — captures result.
7. Checks that `/anneal-cast:anneal` command is discoverable — captures evidence.

Evidence:
- `evidence/build-log.txt` — 0 errors, plugin files written
- `evidence/validate-plugin-output.txt` — `VALIDATION PASSED`
- `evidence/plugin-install-output.txt` — `anneal-cast installed from anneal-cast-dev`
- `evidence/command-discovery.txt` — `anneal-cast:anneal` listed in `/help`

Verdict: PASS.

### Stage 7 · Emit via Atlas

Rollup:

```yaml
rollup:
  architecture: cast
  run_id: anneal-260422-1440-plugin-rewrite
  overall_verdict: CAUTION
  gate_status:
    metis: CAUTION
    momus: CAUTION
    red_team_trinity: "3/3 PASS"
    oracle: CAUTION
    hephaestus: PASS
  simultaneous_pass: true
  blocking_issues:
    - severity: MAJOR
      source_reviewer: "redteam-assumptions"
      summary: "Phase 06 must NOT reference hooks.json in plugin.json."
  emission_decision: EMIT
  iteration_count: 1
```

Atlas writes to `~/Desktop/anneal-runs/anneal-260422-1440-plugin-rewrite/`:

- `cast-anneal-260422-1440-plugin-rewrite.xml`
- `plan/plan.md`
- `plan/phase-00-baseline.md` through `plan/phase-11-functional-validation.md`
- `rollup.yaml`
- `evidence/` (verbatim copy from Hephaestus)

Atlas prints:

```
Anneal Cast · EMIT
run_id: anneal-260422-1440-plugin-rewrite
architecture: cast
verdict: CAUTION
iteration_count: 1
files:
  - ~/Desktop/anneal-runs/anneal-260422-1440-plugin-rewrite/cast-anneal-260422-1440-plugin-rewrite.xml
  - ~/Desktop/anneal-runs/anneal-260422-1440-plugin-rewrite/plan/plan.md
  - ~/Desktop/anneal-runs/anneal-260422-1440-plugin-rewrite/plan/phase-00-baseline.md
  - ...
next-step:
  $ claude
  > /clear
  > Read ~/Desktop/anneal-runs/anneal-260422-1440-plugin-rewrite/cast-anneal-260422-1440-plugin-rewrite.xml and execute the plan.
```

## Observations

- **Total agent spawns:** 8 (1 Metis + 1 Prometheus + 1 Momus + 3 Red-Team + 1 Oracle + 1 Hephaestus + 1 Atlas). Atlas does not count against the 8 because it is the emitter, but the target profile of ~8 holds.
- **Wall-clock:** 3 min 48 sec measured end-to-end on this task.
- **Iterations:** 1 — no re-loop needed on this task.
- **Blocking issues at emission:** 1 MAJOR, non-blocking (CAUTION-level Oracle verdict is within emission threshold).
- **Creative alternatives explored:** 0 — expected for Cast. A user who wanted alternatives would have run Alloy.

## What Cast would miss

Cast does not explore alternative plan shapes. If the first planner produced a 12-phase plan, nobody examines whether a 6-phase plan would have been better. Alloy would explore that; Cast trades it away for speed.
