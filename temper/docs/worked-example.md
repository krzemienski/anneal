# Worked Example · The Plugin Rewrite at depth 3

A concrete walkthrough of Temper operating on a real task. The task chosen is the canonical one from the architecture doc: rewriting the `deepest-plan` plugin. This example shows per-depth scores, per-depth red-team findings, convergence behavior, and emission.

## Task

```
/anneal-temper:anneal "rewrite the deepest-plan plugin to use SADD primitives and fix the 91 asymmetric-vendoring defects. ship a functional v0.1.0 that passes its own red team."
```

Flags: none. Default depth cap = 3.

## Stage 1-3 · Intent Gate, Probe, Metis

**Intent Gate:** Task accepted. No unsafe content.

**Probe (explore skill):** Scans project root, finds:
- `plans/260420-1143-full-productization/` — existing plan with 91 documented defects
- `~/.claude/skills/` — enumerates ~40 relevant skills including `launch-sub-agent`, `do-in-parallel`, `functional-validation`
- Recent commits touching `deepest-plan/` show churn around `skills/*/SKILL.md` YAML

**Metis (stage 3):**

```yaml
reviewer: metis
verdict: CAUTION
summary: "Task is clear on the what (rewrite). Silent on: which 91 defects are priority, whether v0.1.0 ships to marketplace or stays local, what 'passes its own red team' means operationally."
confidence: HIGH
findings:
  - severity: MAJOR
    category: ambiguity
    reviewer: metis
    summary: "The phrase 'passes its own red team' lacks an operational definition."
    evidence: []
    suggestion: "Planner must define: red-team PASS = all three adversaries return non-BLOCK verdicts in the same iteration."
    blocks_emission: false
  - severity: MAJOR
    category: scope
    reviewer: metis
    summary: "91 defects is a large surface; task doesn't specify if we address all or a subset."
    evidence: []
    suggestion: "Planner should group defects by category and tackle the top-severity tier first."
    blocks_emission: false
directives:
  - "Define 'passes its own red team' as all three Red Team adversaries returning non-BLOCK verdicts in the same iteration of the deepen loop."
  - "Group the 91 defects by category; plan must address the top-severity category first, with explicit coverage of remaining defects as deferred phases."
  - "Include an explicit phase for 'local install verification' (marketplace add + plugin install + smoke-test invocation). Do NOT assume v0.1.0 ships to a public marketplace."
  - "Functional-validation phase must exercise the emitted XML end-to-end: cat {xml} | claude must launch without parse errors."
clarifying_questions: []
blocking_issues_count: 0
```

## Stage 4 · Deepen Loop

### Depth 0 (Seed)

**Prometheus-Temper at depth 0:**
Writes `plan_0.md` — 11 phases based on Metis directives + probe report. Thesis: "Rewrite deepest-plan via SADD primitives in phased order."

**Red-Team Trinity at depth 0 (parallel):**

```yaml
redteam-security:
  verdict: SAFE
  confidence: HIGH
  findings: []
  blocking_issues_count: 0

redteam-scope:
  verdict: CAUTION
  confidence: HIGH
  findings:
    - severity: MAJOR
      summary: "Phase 04 touches the OMC reference docs — user didn't ask about documentation rewrites."
      blocks_emission: false
    - severity: MINOR
      summary: "Phase 09 proposes a new 'plugin-demo' directory — gold-plating."
      blocks_emission: false
  blocking_issues_count: 0

redteam-assumptions:
  verdict: RISKY
  confidence: HIGH
  findings:
    - severity: MAJOR
      summary: "Phase 06 assumes Claude Code ~1.2+ for plugin hooks support. Not verified."
      failure_mode: "Plugin install silently fails on older Claude Code; user sees nothing."
      blocks_emission: false
    - severity: MAJOR
      summary: "Phase 03 assumes 'pyyaml' is installed for validate-plugin.py. Not verified."
      failure_mode: "validate-plugin.py crashes with ImportError."
      blocks_emission: false
    - severity: MAJOR
      summary: "Phase 07 assumes no existing .anneal/ directory. Not guarded."
      failure_mode: "State file overwritten, prior runs lost."
      blocks_emission: false
    - severity: MINOR
      summary: "Phase 08 assumes bash 4+. Macs default to bash 3.2."
      failure_mode: "associative-array syntax errors."
      blocks_emission: false
  blocking_issues_count: 0
```

**Momus at depth 0:**

```yaml
reviewer: momus
verdict: CAUTION
summary: "Plan covers the 11-phase rewrite with reasonable coverage. Red-Team-Assumptions RISKY caps score at 75. Four unguarded assumptions and two scope creeps are the dominant findings."
confidence: HIGH
score: 62.0
findings:
  - severity: MAJOR
    summary: "Phase 04 (OMC docs) out of scope — remove or justify."
    blocks_emission: true
  - severity: MAJOR
    summary: "No preflight phase guarding the four assumptions flagged by Red-Team."
    blocks_emission: true
  - severity: MAJOR
    summary: "Plan's functional-validation phase doesn't exercise the XML emission end-to-end."
    blocks_emission: true
blocking_issues_count: 3
```

**State:** `scores = [62.0]`, `depth = 0`.

**Convergence check:** `{depth: 0, scores: [62.0], cap: 3}` → `{converged: false, next_depth: 1}`. Continue.

### Depth 1 (First rewrite)

**Prometheus-Temper at depth 1** receives `{prior_plan, prior_momus (blocking_count=3), prior_redteam (scope+assumptions findings), depth_scores=[62.0]}`. Thesis: "Addresses 3 prior blocking Momus issues: removes out-of-scope Phase 04, adds preflight phase for assumptions, extends functional-validation to exercise XML end-to-end."

Writes `plan_1.md` — 12 phases (added preflight, removed OMC-docs, expanded validation).

**Red-Team Trinity at depth 1 (parallel):**

```yaml
redteam-security:
  verdict: SAFE
  findings: []
  blocking_issues_count: 0

redteam-scope:
  verdict: SAFE
  findings:
    - severity: MINOR
      summary: "Phase 09 plugin-demo directory still present."
      resolution_status: persisted
      blocks_emission: false
  blocking_issues_count: 0

redteam-assumptions:
  verdict: CAUTION
  findings:
    - severity: MINOR
      summary: "Phase 06 Claude Code version preflight present but uses 'claude --version | grep 1\\.' — fragile regex."
      resolution_status: persisted (partial)
      blocks_emission: false
  blocking_issues_count: 0
```

**Momus at depth 1:**

```yaml
reviewer: momus
verdict: CAUTION
summary: "Depth-1 rewrite addressed all 3 prior blocking issues. Red-Team all non-BLOCK, 1 CAUTION remaining. Score moves from 62 to 78 — +16, within normal range. Two minor findings remain."
confidence: HIGH
score: 78.0
findings:
  - severity: MINOR
    summary: "Phase 09 plugin-demo directory still scope creep."
    blocks_emission: false
  - severity: MINOR
    summary: "Phase 06 version preflight regex fragile."
    blocks_emission: false
blocking_issues_count: 0
```

**State:** `scores = [62.0, 78.0]`, `depth = 1`.

**Convergence check:** `{depth: 1, scores: [62.0, 78.0], cap: 3}`:
- Top-3: len = 2, rule 1 doesn't apply.
- Delta: `|78.0 - 62.0| = 16.0`, NOT < 0.15.
- Depth 1 < cap 3.
- `{converged: false, next_depth: 2}`. Continue.

### Depth 2 (Second rewrite)

**Prometheus-Temper at depth 2** receives `{prior_plan, prior_momus (2 minor), prior_redteam, depth_scores=[62.0, 78.0]}`. Thesis: "Depth-2 polish: removes phase-09 plugin-demo (scope creep), hardens phase-06 version preflight with proper parsing."

Writes `plan_2.md` — 11 phases (removed plugin-demo; phase-06 now parses version string properly).

**Red-Team Trinity at depth 2 (parallel):**

```yaml
redteam-security:
  verdict: SAFE
  findings: []
  blocking_issues_count: 0

redteam-scope:
  verdict: SAFE
  findings:
    - severity: MINOR
      summary: "Phase 09 plugin-demo removed."
      resolution_status: resolved
      blocks_emission: false
  blocking_issues_count: 0

redteam-assumptions:
  verdict: SAFE
  findings:
    - severity: MINOR
      summary: "Phase 06 version preflight hardened."
      resolution_status: resolved
      blocks_emission: false
  blocking_issues_count: 0
```

**Momus at depth 2:**

```yaml
reviewer: momus
verdict: SAFE
summary: "Depth-2 polish closed both minor findings. All Red-Team SAFE. Score moves from 78 to 85 — +7, normal. Plan is ship-ready."
confidence: HIGH
score: 85.0
findings: []
blocking_issues_count: 0
```

**State:** `scores = [62.0, 78.0, 85.0]`, `depth = 2`.

**Convergence check:** `{depth: 2, scores: [62.0, 78.0, 85.0], cap: 3}`:
- Top-3: `[85.0, 78.0, 62.0]` → variance = 89.56, NOT < 0.3.
- Delta: `|85.0 - 78.0| = 7.0`, NOT < 0.15.
- Depth 2 < cap 3.
- `{converged: false, next_depth: 3}`. Continue.

### Depth 3 (Final rewrite, cap-triggered)

**Prometheus-Temper at depth 3** sees a SAFE plan with no findings. Thesis: "No material changes needed. Plan is stable. Expected score: ~85 (marginal movement)."

Writes `plan_3.md` — 11 phases, cosmetic tightening only.

**Red-Team Trinity at depth 3 (parallel):** All SAFE, no new findings, all prior resolutions stand.

**Momus at depth 3:**

```yaml
reviewer: momus
verdict: SAFE
summary: "Depth-3 rewrite made only cosmetic changes. Score moves from 85 to 85.1 — +0.1, within anti-drift band. Plan is stable."
confidence: HIGH
score: 85.1
findings: []
blocking_issues_count: 0
```

**State:** `scores = [62.0, 78.0, 85.0, 85.1]`, `depth = 3`.

**Convergence check:** `{depth: 3, scores: [62.0, 78.0, 85.0, 85.1], cap: 3}`:
- Top-3: `[85.1, 85.0, 78.0]` → variance ≈ 10.9, NOT < 0.3.
- Delta: `|85.1 - 85.0| = 0.1`, < 0.15. **Delta rule fires.**
- (Cap would have fired too — depth 3 = cap 3 — but delta has higher priority.)
- `{converged: true, reason: "delta", abs_delta: 0.1, ...}`.

**Loop exits. `final_depth = 3`, `final_score = 85.1`, `convergence.reason = "delta"`.**

Note: If Momus at depth 3 had produced, say, 86.5 instead of 85.1, the delta rule would not have fired (`|86.5 - 85.0| = 1.5 > 0.15`), and cap would have fired instead. Same exit, different reason.

## Stage 5 · Oracle

Oracle reads the full depth history and convergence reason.

```yaml
reviewer: oracle
verdict: SAFE
confidence: HIGH
release_coherence: "Phases tell a coherent story: preflight → rewrite → validate → ship. Each phase depends on prior phase state."
deployment_risk: "Low. Plugin installs locally; no marketplace push. Rollback is `rm -rf /path/to/plugin`."
breaking_changes:
  - "Users of deepest-plan v1.0.0 must re-install as anneal-temper; prior state not migrated."
migration_cost: "Low — deepest-plan users had broken state anyway (per the 91 defects)."
blast_radius: "Single plugin; no shared infrastructure."
monitoring_recommendations:
  - "Watch for 'anneal-temper state corruption' reports on first runs."
blocking_issues: []
blocking_issues_count: 0
convergence_assessment: "Delta-triggered at depth 3 with final score 85.1. Score trajectory 62 → 78 → 85 → 85.1 shows healthy convergence: large gains at depths 1-2, marginal at depth 3. Not cap-bounded despite depth==cap because delta fired first."
```

## Stage 6 · Hephaestus

Hephaestus executes the plan's functional-validation phase.

```yaml
reviewer: hephaestus
verdict: PASS
summary: "Plugin installed cleanly. /anneal-temper:anneal registered. Smoke-test run emitted expected state file and XML stub."
confidence: HIGH
build:
  command: "python3 scripts/validate-plugin.py ."
  exit_code: 0
  log_path: "e2e-evidence/hephaestus/build.log"
  log_excerpt: "VALIDATION PASSED"
runtime:
  - action: "Ran /plugin marketplace add /Users/nick/Desktop/anneal/temper"
    evidence_path: "e2e-evidence/hephaestus/step-01-marketplace-add.txt"
    observation: "Exit 0. stdout: 'Marketplace added: anneal-temper-dev'"
  - action: "Ran /plugin install anneal-temper@anneal-temper-dev"
    evidence_path: "e2e-evidence/hephaestus/step-02-install.txt"
    observation: "Exit 0. /anneal-temper:anneal registered."
  - action: "Invoked /anneal-temper:anneal 'smoke test' --depth 1"
    evidence_path: "e2e-evidence/hephaestus/step-03-smoke.txt"
    observation: "Ran at depth 1 with cap=1; converged on cap (as expected for --depth 1). Wrote .anneal/temper-state.json. Emitted stub XML."
findings: []
fail_root_cause: null
blocking_issues_count: 0
```

## Stage 7 · Atlas

Rollup:

```yaml
architecture: temper
run_id: anneal-temper-260422-1540-deepest-plan-rewrite
overall_verdict: SAFE
gate_status:
  metis: CAUTION
  momus: SAFE
  red_team_trinity: "3/3 PASS"
  oracle: SAFE
  hephaestus: PASS
simultaneous_pass: true
blocking_issues: []
emission_decision: EMIT
iteration_count: 0
depth_final: 3
depth_scores: [62.0, 78.0, 85.0, 85.1]
convergence_reason: delta
```

Atlas writes:
- `~/Desktop/anneal-runs/anneal-temper-260422-1540-deepest-plan-rewrite/temper-anneal-temper-260422-1540-deepest-plan-rewrite.xml`
- `~/Desktop/anneal-runs/.../plan/plan.md` + 11 phase files
- `~/Desktop/anneal-runs/.../depth-history.json`
- `~/Desktop/anneal-runs/.../depth-history/depth-{0,1,2,3}-plan.md`

Stdout:

```
Run:          anneal-temper-260422-1540-deepest-plan-rewrite
Architecture: temper
Depth:        3 of 3
Scores:       [62.0, 78.0, 85.0, 85.1]
Convergence:  delta
Verdict:      SAFE
Validate:     PASS
Emitted:      ~/Desktop/anneal-runs/.../temper-anneal-temper-260422-1540-deepest-plan-rewrite.xml
Plan:         ~/Desktop/anneal-runs/.../plan/
History:      ~/Desktop/anneal-runs/.../depth-history.json

Next: open a fresh Claude Code session and run:
  cat ~/Desktop/anneal-runs/.../temper-anneal-temper-260422-1540-deepest-plan-rewrite.xml | claude
```

## Total cost

- Agent spawns: 1 (Metis) + 4×(1 Prometheus + 3 RedTeam + 1 Momus) + 1 (Oracle) + 1 (Hephaestus) + 1 (Atlas) = **24 spawns**.
- Wall-clock: ~7 min (Red Team parallel, sequential planner/Momus/Oracle/Hephaestus/Atlas).
- Matches the architecture contract's "~8 × depth" at depth 3.
