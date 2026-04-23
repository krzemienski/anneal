# Phase 4 — Multi-Perspective Review Prompts

Staged prompts for the two review agents that run after Phase 3 QA passes. Fire these in parallel.

---

## PRIOR WORK CONTEXT (read before dispatch)

Reviewers must start from the current optimized baseline, not the initial build. Before firing the architect and code-reviewer prompts, ensure each agent has these references:

### Reports already written (under `/Users/nick/Desktop/anneal/`)
- `ARCHITECTURE-PROPOSALS.md` (499 lines) — shared architecture spec. 8 invariants + 7-stage spine + 7 named agents. Source of truth for architectural contract.
- `FINAL-REPORT.md` — original build report. Lists 31 / 35 / 36 files per plugin, all validators exit 0, umbrella smoke-test PASS.
- `SKILL-OPTIMIZATION-REPORT.md` — skill-creator eval round results. 115/115 test inputs pass across 23 skills. Enumerates every SKILL.md edit with input#, failure reason, and fix.
- `COMPARISON-PLAYBOOK.md` — how to test head-to-head. Metrics, decision rubric.
- `INSTALL.md` — umbrella + per-plugin install instructions.
- `_shared/` — 4 reference docs (Opus 4.7 XML schema, agent prompts, plan-reviewer schema, plugin format cheatsheet). The agent prompts in `agents/*.md` derive from here.

### Evidence already captured
- `/tmp/anneal-skill-eval/test-inputs.md` (8 KB, 35 Cast inputs)
- `/tmp/anneal-skill-eval/temper-test-inputs.md` (175 lines, 25 Temper inputs)
- Alloy test inputs documented inline in its sub-agent report (see SKILL-OPTIMIZATION-REPORT.md § Alloy)

### What's already passing (before Phase 4 even runs)
- `bash /Users/nick/Desktop/anneal/scripts/smoke-test.sh` → `RESULT: ALL PLUGINS PASS`
- Per-plugin `scripts/validate-plugin.py` → exit 0 on all three
- `temper/scripts/convergence-check.py --selftest` → 12/12 passed
- All 23 SKILL.md bodies ≤200 lines
- All frontmatter YAML parses clean

### Edits already made during the skill-creator round (what reviewers will see in the files)
| Plugin | Skill | Change |
|--------|-------|--------|
| cast | metis | Added `## Verdict selection` block with 4 concrete BLOCK triggers |
| cast | momus | Added `## Iron Rule violations` block — 5 auto-CRITICAL categories |
| cast | oracle | Changed `source_reviewer: str` → `source_reviewers: [...]` array schema |
| alloy | red-team-trinity | Added anti-pattern forbidding peer-envelope reads (orthogonality preservation) |
| temper | metis | Broadened slop-risk from "skills/tools" → "skills/tools/libraries" + `probe_report.libs_installed` check |
| temper | prometheus-temper | Strengthened Rule 2: CRITICAL findings MUST be resolved in current depth, no deferrals |
| temper | hephaestus | New runtime-surface rule: pure refactors MUST import/load the artifact |
| temper | momus | Deduplicated inline rubric (references `docs/scoring-rubric.md`) |
| temper | oracle | Tightened convergence-aware synthesis cross-refs |
| temper | atlas | 201 → 138 lines via progressive disclosure to `references/xml-template.md` |

**Implication for Phase 4:** The architect and code-reviewer agents should START at SAFE or CAUTION baseline and have a high bar for finding BLOCKING issues — the structural audit has been done. Their value-add is catching architectural drift between plugins and verifying the skill-creator edits haven't introduced new contradictions.

---

## THE CONCRETE TEST CASE

The original failed monolith attempt lives at:

**`/Users/nick/Desktop/blog-series/plans/260421-1806-product-site-architecture/`**

- `DEEPEST-PROMPT.xml` (842 lines) — the monolithic prompt that was produced but had structural defects
- `e2e-evidence/` — validation evidence captured during the failed run
- `research/` — context research agents produced
- `reports/` — downstream verdicts

That plan attempted to deliver the Product Site Template (PST) contract for `withagents.dev`. It is the canonical "this wasn't correctly created" artifact.

**The proof of anneal:** run the original task through all three architectures and verify each produces a correct version — one that actually validates, one whose phases compose coherently, one whose XML-and-plan outputs are both consumable by a fresh Claude Code session without re-prompting.

### Canonical invocation for the test

The original task, restated for anneal:

> Deliver the Product Site Template (PST) contract for withagents.dev. Every product (starting with `multi-agent-consensus`, `validationforge`, and `deepest-plan`) gets: hero, 3-sentence what-it-does, ≥2 inline usage examples, architecture/flow diagram, how-it-works section, feature matrix, install/docs/changelog, links back to brand. Apply the three-tier strategy: Tier 1 apex route at `/products/{slug}`, Tier 2 subdomain rewrite via `site/src/proxy.ts`, Tier 3 separate Vercel project only when isolation demands. Validate via functional-validation + visual-inspection at 375/768/1440 + e2e cross-domain navigation. No mocks, no test files.

Run it three ways:

```
/anneal-cast:anneal   "<task above>"
/anneal-alloy:anneal  "<task above>" --versions 5
/anneal-temper:anneal "<task above>" --depth 3
```

### Grading rubric vs original DEEPEST-PROMPT.xml

Each architecture's output must beat the original on these dimensions:

| Dimension | Original (failed) | Anneal must achieve |
|-----------|-------------------|---------------------|
| Phase coherence | Monolithic XML, no phase separation | Plan directory with one `phase-XX-*.md` per phase, consumable independently |
| Evidence mandate | Declared but not wired into re-loop | Every gate's PASS cites an evidence file; FAIL routes back through Metis with the evidence gap as new constraint |
| Vendor correctness | Asymmetric (validation vendored as skills, planning collapsed to prose) | All review skills vendored consistently; no inline prose-as-skill |
| Red team | Implicit in mock_detection_preamble | Explicit Red-Team Trinity (Security/Scope/Assumptions) running in parallel, producing envelope per `plan-reviewer-schema.md` |
| Re-loop semantics | Not specified | Unbounded simultaneous-pass gate trinity — CI+review+validate must all green in same iteration |
| XML output | One monolithic `<deepest_plan>` | Opus 4.7 semantic XML per `_shared/opus-47-xml-schema.md` — docs-at-top, query-at-bottom, `<thinking_budget>xhigh</thinking_budget>` |

Architect review prompt (below) must include these dimensions as explicit grading criteria when comparing anneal's output against the original failed attempt.

---

## Architect review

**Agent:** `oh-my-claudecode:architect` (read-only)
**Model:** opus
**Scope:** Architectural coherence across all three plugins.

```
You are reviewing three Claude Code plugins that share architecture: Cast (linear), Alloy (tournament), Temper (fixed-point deepen). All three are in /Users/nick/Desktop/anneal/{cast,alloy,temper}/.

Source of truth: /Users/nick/Desktop/anneal/ARCHITECTURE-PROPOSALS.md (499 lines, 17 sections). This doc defines 8 invariants that ALL three plugins must satisfy, plus architecture-specific behavior for stage 4 (Plan).

YOUR JOB: confirm or refute — does each plugin's implementation actually honor the architecture contract?

Read these files per plugin:
- {plugin}/.claude-plugin/plugin.json (manifest)
- {plugin}/PRD.md (product requirements)
- {plugin}/ARCHITECTURE.md (implementation summary)
- {plugin}/commands/anneal.md (CLI contract)
- {plugin}/agents/prometheus-*.md (planner agent — architecture varies here)
- {plugin}/skills/*/SKILL.md (all skills)

For each plugin, answer:

1. INVARIANT AUDIT — for each of the 8 invariants, cite the specific file+line that implements it. Missing citations = FAIL the invariant.
2. ARCHITECTURE-SPECIFIC CONTRACT:
   - Cast: does stage 4 really run one planner, one pass?
   - Alloy: does stage 4 really spawn N parallel planners + a distinct synthesizer?
   - Temper: does stage 4 really run the deepen loop with red team inline every depth, and does convergence use the variance rule?
3. COHERENCE — do the three plugins feel like siblings or do they contradict each other in ways that would confuse a user?

Return structured verdict:
- overall_verdict: SAFE | CAUTION | RISKY | BLOCK (same tiers the plugins themselves use)
- per_plugin:
    cast: {verdict, invariants_honored: [list], invariants_violated: [list], contract_match: true|false}
    alloy: {...}
    temper: {...}
- coherence_across_plugins: {assessment, examples of drift if any}
- blocking_issues: []

Do NOT edit files. Read-only review.
```

## Code reviewer

**Agent:** `oh-my-claudecode:code-reviewer` (read-only)
**Model:** opus
**Scope:** Markdown quality, skill frontmatter, command ergonomics.

```
You are reviewing the markdown-based content of three Claude Code plugins at /Users/nick/Desktop/anneal/{cast,alloy,temper}/.

For Claude Code plugins, "code quality" means:
- YAML frontmatter in SKILL.md files is valid and complete (name, description required; description must contain trigger keywords for discovery)
- Command files (commands/*.md) have valid frontmatter (description required, argument-hint optional)
- Agent files (agents/*.md) have valid frontmatter (description required, model optional)
- Prompt bodies are clear, directive, and free of AI-slop patterns (emoji overuse, "I'll help you...", excessive hedging)
- Cross-references between skills/agents use consistent names
- Python/bash scripts are syntactically valid and handle errors

Per plugin, audit:
1. YAML frontmatter — run yaml.safe_load on every frontmatter block. Report parse failures.
2. Trigger keywords — each skill's description must include explicit triggers. Report skills without them.
3. Prompt quality — skill/agent prompts should be imperative, specific, and include concrete examples where helpful. Flag any that are vague or bureaucratic.
4. Cross-reference integrity — does the command file reference skills that exist? Do agents reference other agents by correct name?
5. Script quality — validate-plugin.py, orchestrate.sh, convergence-check.py (temper only). Are they valid? Do they handle edge cases?
6. Consistency — the three plugins share most structure. Are common elements (Metis, Momus, Oracle, Hephaestus, Atlas) implemented consistently across plugins, or has drift crept in?

Return structured verdict:
- overall_verdict: SAFE | CAUTION | RISKY | BLOCK
- per_plugin:
    cast: {yaml_parse_ok, trigger_keywords_present, prompt_quality_score /10, xref_integrity, script_quality, findings: []}
    alloy: {...}
    temper: {...}
- consistency_across_plugins: {assessment, drift_examples: []}
- blocking_issues: []

Do NOT edit files. Read-only review.
```

## Dispatch

When Phase 3 QA passes, fire both prompts in parallel:

```python
# Pseudocode for the Phase 4 dispatch
Agent(subagent_type="oh-my-claudecode:architect", prompt=architect_prompt, run_in_background=True)
Agent(subagent_type="oh-my-claudecode:code-reviewer", prompt=reviewer_prompt, run_in_background=True)
```

Wait for both to complete. Aggregate their verdicts per the plan-reviewer-schema rollup rules: worst verdict wins. If either returns BLOCK, fix and re-review. If both SAFE or CAUTION, proceed to Phase 5.

## Acceptance criteria for Phase 4

- architect returns verdict SAFE or CAUTION
- code-reviewer returns verdict SAFE or CAUTION
- No plugin has invariants_violated
- All three plugins honor their architecture-specific contract
- Blocking issues count = 0 across both reviewers

Failure → fix and re-run. Unbounded loop until all three gates green (architect + code-reviewer + the earlier QA). Matches the "simultaneous pass" discipline the plugins themselves implement.
