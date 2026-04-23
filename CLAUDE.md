# CLAUDE.md — Anneal Workspace

Read this FIRST when a Claude Code session opens at `/Users/nick/Desktop/anneal/`. This is the bootstrap context.

---

## What this directory is

**Anneal is a Claude Code plugin family that turns a vague task into a rigorously-reviewed execution artifact** — an Opus 4.7 semantic-XML prompt plus a plan directory — that a fresh Claude Code session can paste and autonomously execute.

Three plugin variants, three architectures, all sharing 8 invariants. Pick by task shape:

| Command | Architecture | When to pick |
|---------|-------------|--------------|
| `/anneal-cast:anneal <task>` | Linear single-pour | Clear scope, bug fixes, refactors. Fastest. |
| `/anneal-alloy:anneal <task> --versions 5` | Tournament consensus | Novel architecture, greenfield. N parallel planners blend. |
| `/anneal-temper:anneal <task> --depth 3` | Fixed-point deepen | Complex but scoped. Iterates until variance converges. |

All three: always red-team, always validate, always emit XML+plan, always enrich from user skills, always re-loop on FAIL.

## What anneal can do (concrete)

Paste this string after install and watch:

```
/anneal-temper:anneal "Deliver the Product Site Template contract for withagents.dev. Every product gets: hero, 3-sentence what-it-does, ≥2 inline usage examples, architecture diagram, how-it-works, feature matrix, install/docs/changelog, links back to brand. Three-tier strategy (Tier 1 apex, Tier 2 subdomain rewrite, Tier 3 separate Vercel). Validate via functional-validation + visual-inspection at 375/768/1440 + e2e cross-domain navigation. No mocks, no test files." --depth 3
```

Output lands at `${ANNEAL_RUNS_ROOT:-./.anneal/runs}/{run_id}/` with:
- `temper-{run_id}.xml` — the handoff prompt
- `plan/plan.md` + `plan/phase-NN-*.md` — executable phases
- Every phase has cited evidence criteria, no mocks, no test files

The XML file, pasted into a fresh Claude Code session (or piped via `cat temper-{run_id}.xml | claude -p` for headless runs), is a well-structured prompt that tells Claude exactly what to build and how to prove it works. Effectiveness depends on Claude following the embedded instructions — treat the XML as a strong prompt, not a self-executing program.

## Directory layout

```
anneal/
├── CLAUDE.md                      ← you are here
├── README.md                      ← product orientation
├── INSTALL.md                     ← install cheatsheet (umbrella + per-plugin)
├── COMPARISON-PLAYBOOK.md         ← how to test all 3 head-to-head
├── ARCHITECTURE-PROPOSALS.md      ← full 499-line architecture spec
├── FINAL-REPORT.md                ← build report with validator evidence
├── SKILL-OPTIMIZATION-REPORT.md   ← skill-creator round (115/115 inputs pass)
├── PHASE-ROADMAP.md               ← phases 4-10 (current → shipped product)
├── .claude-plugin/marketplace.json ← umbrella dev marketplace
├── _shared/                       ← reference docs consumed by plugins
│   ├── opus-47-xml-schema.md
│   ├── agent-prompts-core.md
│   ├── plan-reviewer-schema.md
│   └── plugin-format-cheatsheet.md
├── diagrams/anneal-architectures.html  ← editorial aesthetic visual
├── scripts/
│   ├── smoke-test.sh              ← cross-plugin validation gate
│   └── phase-4-review-prompts.md  ← staged review prompts + test case
├── cast/                          ← Plugin · anneal-cast · 31 files
├── alloy/                         ← Plugin · anneal-alloy · 35 files
└── temper/                        ← Plugin · anneal-temper · 36 files
```

Each plugin dir is self-contained with: `.claude-plugin/plugin.json`, `commands/anneal.md`, `skills/{7-8 skills}/SKILL.md`, `agents/{9-10 agents}.md`, `hooks/hooks.json`, `scripts/validate-plugin.py` + orchestrator, `diagrams/{name}-architecture.html`, `docs/` (invariants · worked-example · emission-format · plus temper's convergence-rules and scoring-rubric).

## Agent roster (shared across all 3 plugins)

Seven named Greek-god **agents** (dispatched explicitly via the Task tool from the `/anneal-*:anneal` command body). Each agent role also ships a companion **skill** (`skills/{name}/SKILL.md`) that Claude may autonomously pick up as context — but skills are model-invoked, never called by name. Only the agents are deterministic. Each has a single job:

| Agent | Etymology | Role | Stage |
|-------|-----------|------|-------|
| **Metis** | Wisdom, prudence | Pre-plan consultant — ambiguity and slop-risk detector | 3 · Enrich |
| **Prometheus** | Forethought | The planner. Cast: one call. Alloy: N biased. Temper: iterative. | 4 · Plan |
| **Momus** | Satire, mockery | Post-plan ruthless auditor | 4 · close-out |
| **Red-Team Trinity** | (Security · Scope · Assumptions) | Three parallel adversaries | 5 · always |
| **Oracle** | Delphic seer | Bird's-eye synthesis · SAFE/CAUTION/RISKY/BLOCK | 5 · close-out |
| **Hephaestus** | Craftsman | Functional validator · no mocks, real artifacts | 6 · Validate |
| **Atlas** | Bearer of the world | Emits XML + plan directory | 7 · Emit |

The three plugin variants only differ in stage 4. Everything else is identical.

## Quick verification (run this to confirm the workspace is healthy)

```bash
bash /Users/nick/Desktop/anneal/scripts/smoke-test.sh
```

Expected final line: `RESULT: ALL PLUGINS PASS`

Current state (as of 2026-04-22): three plugins built + optimized (115/115 test inputs pass across 23 skills), all validators exit 0, no known blocking issues.

## What to do when a user asks you to...

| User request | You should |
|-------------|-----------|
| "Install anneal" | Read `INSTALL.md`, run the umbrella install commands, tell user to restart Claude Code |
| "What can anneal do?" | Cite the 3 architecture table above + the concrete example string in § What anneal can do |
| "How do I pick between Cast, Alloy, Temper?" | Point at `COMPARISON-PLAYBOOK.md` decision rubric |
| "Review / audit the plugins" | Dispatch the prompts in `scripts/phase-4-review-prompts.md` (architect + code-reviewer at minimum) |
| "Run anneal against a task" | User needs the plugins installed first. After install, paste `/anneal-{cast\|alloy\|temper}:anneal "<task>"` |
| "Why does anneal exist?" | Read § Higher purpose in `PHASE-ROADMAP.md` — it's the planning tool for the withagents.dev ecosystem, replaces failed deepest-plan v1 |
| "What's next?" | `PHASE-ROADMAP.md` — Phase 4 dogfood, then Phase 5 decisive run against the PST task, then Phases 6-10 |

## What NOT to do

- Don't edit `_shared/` files — those are reference docs consumed by sub-agents. Changes propagate unpredictably.
- Don't edit `{plugin}/agents/*.md` or `{plugin}/skills/*/SKILL.md` without running that plugin's `scripts/validate-plugin.py` after.
- Don't modify `temper/scripts/convergence-check.py` — it has 12/12 selftests that must stay passing.
- Don't create mock files, test files, or stubs in any plugin. The Iron Rule is enforced by the plugins' own Momus skill.
- Don't remove the "Always use the Task tool to spawn agents" directive from any plugin's `commands/anneal.md`. That one line is what converts the natural-language orchestration into deterministic sub-agent dispatches. Without it, Claude may read the orchestration as suggestion and skip agent spawns.
- Don't mark tasks complete without real command output / file content as evidence.

## The thesis

Anneal IS the planning tool for the `withagents.dev` agentic-development ecosystem. The proof loop: anneal produces its own product-site plan. The plan produces anneal's product site. The product site demos anneal by showing anneal running against itself.

If any step of that loop fails, anneal isn't good enough to ship to others. That's the dogfood test.

For the full picture: read `PHASE-ROADMAP.md`. For architecture detail: `ARCHITECTURE-PROPOSALS.md`. For install: `INSTALL.md`. For validation: `scripts/smoke-test.sh`.

## Recent work log (summary)

- 2026-04-21 — diagnosed deepest-plan v1 failure (91 defects, asymmetric vendoring)
- 2026-04-22 AM — designed 3 architectures · Cast (linear), Alloy (tournament), Temper (fixed-point deepen)
- 2026-04-22 PM — built all three plugins in parallel (31 + 35 + 36 files)
- 2026-04-22 PM — skill-creator eval round across 23 skills (115/115 pass rate)
- 2026-04-22 evening — documented PHASE-ROADMAP through Phase 10 (public release)

Next: Phase 4 deep reviews, then the decisive dogfood run against the PST task.
