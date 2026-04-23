# Worked Example — Plugin Rewrite with N=5

The canonical test case: use Alloy to plan the rewrite of `deepest-plan v1.0.0` into this very plugin.

**User input:**

```
/anneal-alloy:anneal "rewrite the deepest-plan plugin to use SADD primitives and fix the 91 asymmetric-vendoring defects. ship a functional v0.1.0 that passes its own red team."
```

No `--versions` → defaults to **N=5**.

---

## Stage 1 · Intent Gate

- Task shape: `code + plan + infrastructure`
- Not destructive (no `rm -rf`, no credentials cited)
- State: `~/Desktop/anneal-runs/anneal-20260422-1452-rewrite-the-deepest-plan-plugi/state.json` initialized

**Elapsed:** ~2s

---

## Stage 2 · Probe

Probe enumerates user skills and project skills:

```
~/.claude/skills/
  launch-sub-agent, do-in-parallel, do-and-judge, tree-of-thoughts,
  create-validation-plan, functional-validation, ...

.claude/skills/ (in blog-series project)
  (no project-specific skills relevant to this task)
```

Reference files surfaced:
- `~/Desktop/anneal/ARCHITECTURE-PROPOSALS.md`
- `~/Desktop/anneal/_shared/*.md`
- `site/src/app/products/deepest-plan/` (the existing catalog entry being deprecated)

**Elapsed:** ~20s

---

## Stage 3 · Enrich (Metis)

Metis reads task + probe. Output envelope:

```yaml
reviewer: metis
verdict: CAUTION
summary: |
  Task references "the 91 defects" without enumerating. Probe surfaces SADD
  primitives (launch-sub-agent, do-in-parallel, do-and-judge) that should be
  reused. Iron Rules apply: no test files, no mocks.
confidence: HIGH
findings:
  - severity: MAJOR
    category: ambiguity
    reviewer: metis
    summary: "Task cites '91 defects' count without listing them."
    evidence:
      - plan_file: "task-string"
        line_range: "n/a"
        excerpt: "fix the 91 asymmetric-vendoring defects"
    suggestion: "Planner should either reference the audit doc or treat as rough count."
    blocks_emission: false
directives:
  - "The plan must reuse SADD primitives (launch-sub-agent, do-in-parallel, do-and-judge) rather than re-implement agent dispatch."
  - "The plan must not create test files, mocks, or stubs (Iron Rule)."
  - "The plan must include a functional-validation phase with evidence checkpoints."
  - "The plan must ship a plugin that passes its own red-team on first full run."
  - "The plan must deprecate deepest-plan v1.0.0 via tombstones, not deletions."
clarifying_questions: []
blocking_issues_count: 0
```

**Elapsed:** ~25s (opus)

---

## Stage 4 · Plan — the Tournament

### Step 4.1 · Bias selection (N=5)
correctness, minimalist, defensive, performance, ux

### Step 4.2 · Parallel fan-out

5 Prometheus-Alloy agents spawn concurrently via `xargs -P 5`. Each receives:
- Same task string
- Same Metis directives (verbatim)
- Same probe report
- Different bias

**Variant 1 · correctness (opus)**
- 14 phases, every phase has a measurable gate test
- Validation phase has 8 checkpoints
- Slow but airtight

**Variant 2 · minimalist (opus)**
- 7 phases
- No rollback clauses; no preflight
- Violates Metis directive 3 silently (validation phase is 1 step)
- Flagged by Synthesizer as under-weighted

**Variant 3 · defensive (opus)**
- 12 phases, every phase has rollback
- State file writes at each phase boundary
- Assumes hostile environment

**Variant 4 · performance (opus)**
- 9 phases
- Parallel where possible (red team, validators)
- Vendors only the 6 core SADD primitives
- Rejects tree-of-thoughts (unused)

**Variant 5 · ux (opus)**
- 10 phases with status-line signals
- Every failure path names the next action
- "What the user sees" column in each phase

**Elapsed (longest variant wins):** ~90s

### Step 4.3 · Synthesizer (opus)

Synthesizer reads all 5 variants. Composition:

| Canonical phase | Contributing variants | Notes |
|----------------|----------------------|-------|
| phase-00-baseline | 1, 3, 5 | Correctness's gate test + Defensive's state-file + UX's status line |
| phase-01-scaffold | All 5 | Union of file lists; Correctness's steps; Defensive's rollback |
| phase-02-manifest | 1, 3, 4 | Perf's deps list (tighter) + Correctness's schema check |
| phase-03-skill-vending | 1, 3, 4 | Perf wins — only the 6 primitives actually used |
| phase-04-agent-roster | All 5 | 10 agents; model assignments from Correctness |
| phase-05-command | 1, 3, 5 | UX's arg-hint + Correctness's phase-by-phase spec |
| phase-06-orchestrator | 3, 4 | Defensive's xargs -P fallback (BSD) + Perf's parallel contract |
| phase-07-hooks | 1, 3 | Minimal — only SessionStart |
| phase-08-docs | 1, 5 | UX's skimmable structure + Correctness's cross-refs |
| phase-09-diagram | 5 | UX only — visual is a UX concern |
| phase-10-validate | 1, 3 | Correctness's checkpoints + Defensive's per-gate rollback |
| phase-11-ship | 1, 3, 5 | Correctness's gate + Defensive's tombstones + UX's summary |

**Contradictions resolved:**

1. Variant 2 (minimalist) omitted functional-validation phase. Rejected — violates Metis directive 3 AND Iron Rule. Logged in provenance under "Rejected elements."
2. Variant 4 (perf) used `nproc` without fallback. Variant 3 (defensive) used `$(sysctl -n hw.ncpu 2>/dev/null || nproc)`. Resolution: Metis directive "plan runs on macOS default shell" → kept defensive.
3. Variant 1 (correctness) required Oracle to re-read variant files post-synthesis. Variant 4 (perf) said Oracle reads only the blend. Resolution: Spec in `ARCHITECTURE-PROPOSALS.md` says Oracle reads envelopes + blend, not variants → kept perf's interpretation.

Synthesizer writes `plan/plan.md` + 12 phase files + `synthesis-provenance.md`.

**Elapsed:** ~60s (opus)

### Step 4.4 · Momus (opus)

Momus audits the blend:

```yaml
reviewer: momus
verdict: CAUTION
summary: |
  Plan is coherent. Provenance is clean — 3 contradictions all traced to
  directive match. Phase 06 integration between Defensive rollback and Perf
  parallel has a subtle ordering dependency that could race.
confidence: HIGH
findings:
  - severity: MAJOR
    category: coherence
    reviewer: momus
    summary: "Phase 06 rollback triggers on any subshell exit; parallel planners have independent subshells."
    evidence:
      - plan_file: "plan/phase-06-orchestrator.md"
        line_range: "34-45"
        excerpt: "trap 'rollback' EXIT"
    suggestion: "Scope the trap to the parent shell, not each xargs child."
    blocks_emission: false
  - severity: MINOR
    category: missing-evidence
    reviewer: momus
    summary: "Phase 10 validation doesn't specify the evidence-quality heuristic (byte-count threshold)."
    evidence:
      - plan_file: "plan/phase-10-validate.md"
        line_range: "22"
        excerpt: "evidence is non-empty"
    suggestion: "Define 'non-empty' as >0 bytes AND parseable JSON/YAML/text."
    blocks_emission: false
blocking_issues_count: 0
```

**Elapsed:** ~30s (opus)

---

## Stage 5 · Review (parallel)

Three Red-Team agents spawn concurrently. Each reads the blend + prior envelopes.

### Red-Team-Security (sonnet) — **SAFE**
- No secrets in plan text
- Shell interpolation in phase-06 is quoted
- Dep versions are pinned via plugin.json requires block
- Findings: 0 CRITICAL, 0 MAJOR, 1 MINOR (suggestion to redact absolute paths from emitted XML)

### Red-Team-Scope (sonnet) — **CAUTION**
- Plan adds a `hooks/hooks.json` with SessionStart. User didn't mention hooks.
- Justified by defensive variant's state-file pattern; conservative default kept it.
- 1 MAJOR finding, non-blocking.

### Red-Team-Assumptions (sonnet) — **CAUTION**
- Assumes `xargs -P` supports concurrency on BSD (verified — macOS `xargs -P 5` is supported)
- Assumes `claude` CLI dispatches agents via the harness (true — plugin contract)
- 2 MINOR, 1 MAJOR finding — assumption about python3 stdlib `yaml` import. **Correction:** pyyaml is not stdlib. Plan must note the pip install step, OR pivot validate-plugin.py to stdlib-only. Flagged MAJOR.

**Elapsed (max of three):** ~40s

### Oracle (opus) — **CAUTION**

Oracle reads all prior envelopes + synthesis-provenance.md.

```yaml
reviewer: oracle
verdict: CAUTION
summary: |
  Plan is coherent; tournament showed genuine synthesis value (all 5 variants
  contributed phases, no bias collapse). Three prior CAUTION verdicts
  compound but none are deploy-blocking. Biggest risk: pyyaml dep not pinned
  in the validate-plugin.py shebang logic.
confidence: HIGH
release_coherence: |
  Plan tells one story. Phases 00-06 build the plugin; 07-10 docs + validate;
  11 ships. Synthesis provenance cites all 5 biases; minimalist contributed
  only 2 phases but was not silently rejected.
deployment_risk: |
  pyyaml is not stdlib. Plan needs either a pip install note or a pivot to
  manual YAML frontmatter parsing. Mitigation: plan v0.1.0 assumes pyyaml is
  installed (macOS has it via homebrew claude installation).
breaking_changes:
  - "deepest-plan v1.0.0 users must migrate via docs/migration.md (planned phase-11)"
  - "Removes 5 skills: judge-with-debate, do-in-steps, multi-agent-patterns,
     full-functional-audit, visual-inspection"
monitoring_recommendations:
  - "Watch synthesis-provenance.md for bias-collapse patterns in future Alloy runs"
  - "Track first-run Hephaestus evidence: plugins that FAIL validation on
     install are a regression indicator"
findings: [ ... deduped 3 MAJOR, 3 MINOR ... ]
blocking_issues_count: 0
```

**Elapsed:** ~45s (opus)

---

## Stage 6 · Validate (Hephaestus)

Since Oracle returned CAUTION (not BLOCK), Hephaestus runs.

1. Copies plugin to `/tmp/anneal-hephaestus-anneal-20260422-1452.../`
2. Executes plan phases in order:
   - `python3 scripts/validate-plugin.py` → exit 0, "VALIDATION PASSED"
   - `claude /plugin marketplace add .` → "Marketplace registered: anneal-alloy-dev"
   - `claude /plugin install anneal-alloy@anneal-alloy-dev` → "Plugin installed: 0.1.0"
   - `claude /plugin list | grep anneal-alloy` → match
3. Success criteria across all phases: 12/12 met.

Verdict: **PASS**

Evidence:
- 23 files under `reviews/hephaestus-evidence/`
- 2.4 MB total
- Every file >0 bytes
- `evidence-inventory.txt` lists all files + byte counts

**Elapsed:** ~3 min (longest stage — real builds + installs)

---

## Stage 7 · Emit (Atlas)

Atlas computes rollup:

```yaml
rollup:
  architecture: alloy
  run_id: anneal-20260422-1452-rewrite-the-deepest-plan-plugi
  overall_verdict: CAUTION
  gate_status:
    metis: CAUTION
    momus: CAUTION
    red_team_trinity: "3/3 PASS"    # all non-BLOCK
    oracle: CAUTION
    hephaestus: PASS
  simultaneous_pass: true
  blocking_issues: []
  emission_decision: EMIT
  iteration_count: 1
  tournament_stats:
    variant_count: 5
    biases_participating: [correctness, minimalist, defensive, performance, ux]
    biases_contributing_to_blend: [correctness, minimalist, defensive, performance, ux]
    silent_rejections: 0
    contradictions_resolved: 3
```

`simultaneous_pass: true` AND `overall_verdict: CAUTION` → **EMIT**.

Atlas writes:
- `~/Desktop/anneal-runs/{run_id}/alloy-{run_id}.xml`
- `~/Desktop/anneal-runs/{run_id}/plan/plan.md` + 12 phase files
- `~/Desktop/anneal-runs/{run_id}/variants/` (5 files preserved)
- `~/Desktop/anneal-runs/{run_id}/synthesis-provenance.md`
- `~/Desktop/anneal-runs/{run_id}/reviews/` (6 envelopes + evidence)
- `~/Desktop/anneal-runs/{run_id}/rollup.yaml`

Prints next-step command:
```
Paste into a fresh Claude Code session:
"Read ~/Desktop/anneal-runs/anneal-20260422-1452-rewrite-the-deepest-plan-plugi/alloy-*.xml
 and execute the plan therein per the <instructions><next_action> block."
```

**Elapsed:** ~15s (sonnet)

---

## Total cost

| Stage | Agents | Wall-clock |
|-------|--------|-----------|
| 1 · Intent Gate | 0 | 2s |
| 2 · Probe | 1 | 20s |
| 3 · Metis | 1 | 25s |
| 4 · Tournament | 5 + 1 + 1 = 7 | 180s |
| 5 · Red Team + Oracle | 3 + 1 = 4 | 85s |
| 6 · Hephaestus | 1 | 180s |
| 7 · Atlas | 1 | 15s |
| **Total** | **15 agent spawns** | **~8.5 min** |

(The published "~18 spawns at N=5" figure in the architecture doc counts bias-specific prompt prep as separate spawns — in practice the harness batches prep with the planner call, yielding 15 here.)

---

## What would have happened in Cast

- ~8 agent spawns, ~4 min
- Single planner would have produced Variant 1 (correctness-dominant) output
- No synthesis → the Defensive rollback pattern + UX status-line + Perf dep-pruning would all have been absent
- Same gate outcomes, less breadth

## What would have happened in Temper

- Depth cap 3 → likely converged at depth 2
- ~24 agent spawns, ~7 min
- Each iteration genuinely improved on the prior
- Red Team runs every depth — more paranoid
- Less breadth than Alloy (one line of thought, refined)

## Verdict

Alloy was the right choice for this task because:
1. The plan shape was not obvious (no existing template)
2. All 5 biases contributed — genuine synthesis
3. The single Defensive rollback the Synthesizer picked up from variant 3 caught a race condition that Cast would have missed

Cost: ~2× Cast. Benefit: 1 MAJOR defect caught pre-validation. Worth it.
