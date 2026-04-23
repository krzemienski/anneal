# Anneal · Cast — Product Requirements

**Version:** 0.1.0
**Status:** Design-complete, v0.1.0 shipped
**Author:** Nick Krzemienski
**Date:** 2026-04-22

---

## Problem

Claude Code users routinely ask an agent to "make a plan," get one back, and then watch it fail during execution because the plan silently skipped a security concern, misread the scope, or assumed a file existed that did not. The existing `deepest-plan` plugin ships 91 known asymmetric-vendoring defects and does not enforce adversarial review on the plans it produces.

The fix is not more planning prompts. The fix is a pipeline where the planner is **one** agent among seven, and the other six exist to catch what it missed.

## Proposed solution

Cast is the linear architecture of the Anneal plugin family. It takes a user task and produces two artifacts:

1. A plan directory with markdown phase files
2. An Opus 4.7 semantic-XML prompt encoding the plan, review envelopes, and validation evidence

Cast invokes seven named agents in a fixed order and refuses to emit unless all three gates (Red-Team Trinity, Oracle, Hephaestus) pass in the same iteration.

## Non-goals

- **Not a coder.** Cast does not write code. It writes plans that a downstream fresh Claude Code session executes.
- **Not a test-runner.** Cast does not create test files, mocks, stubs, or unit-test harnesses. Validation is functional — real build, real runtime, real evidence.
- **Not an exploration tool.** Cast runs one planner and does not fan out alternative-plan variations. Users who want that run Alloy.
- **Not a deepen loop.** Cast does not iterate planner passes to convergence. Users who want that run Temper.

## Success criteria

1. **Installable.** `/plugin marketplace add /Users/nick/Desktop/anneal/cast` followed by `/plugin install anneal-cast@anneal-cast-dev` succeeds on a fresh Claude Code session with no manual fix-up.
2. **Self-validating.** `scripts/validate-plugin.py` exits 0 against this plugin's own directory.
3. **Command registers.** `/anneal-cast:anneal <task>` is discoverable via `/help`.
4. **Hook loads.** On session start, the hook prints `Anneal · Cast · v0.1.0 loaded` to the session log.
5. **Agents discover.** `/agents` lists all nine agent files (Metis, Prometheus, Momus, three Red-Team members, Oracle, Hephaestus, Atlas).
6. **Skills register.** All seven skills (metis, prometheus-cast, momus, red-team-trinity, oracle, hephaestus, atlas) are discoverable.

## User stories

### US-1: Fast bug-fix plan

> As a developer with a well-specified bug, I want to type `/anneal-cast:anneal "<bug>"` and get back a reviewed, validated plan in about four minutes — not a raw planner dump.

### US-2: Scoped refactor with safety

> As a developer refactoring authentication, I want the red team to flag any security regression before I hand the plan to an execution session.

### US-3: Functional validation gate

> As a developer with a plan I will execute autonomously, I want Hephaestus to have already built and exercised the artifact, so I know it compiles and runs before my execution session starts.

### US-4: XML prompt handoff

> As a developer running a second Claude Code session to execute the plan, I want an Opus 4.7 semantic-XML prompt I can paste in — context at top, query at bottom.

## Architecture decisions

### AD-1: Single planner pass

Cast runs Prometheus exactly once per plan attempt. No retry within stage 4. On validate FAIL, the re-loop goes back to **Metis**, not to Prometheus — the failure is folded in as a new constraint via Metis's directives.

**Rationale:** Retrying the planner with the same input produces the same plan. The interesting signal lives in the failure. Metis interprets the failure and shapes the next planner call.

### AD-2: Red Team Trinity always parallel

Security, Scope, and Assumptions adversaries always spawn in parallel. Not sequential. Not behind a flag.

**Rationale:** Sequential adversarial review lets earlier reviewers prime later ones. Parallel review preserves the adversarial stance.

### AD-3: Hephaestus is non-negotiable

Every Cast run calls Hephaestus. Even on a pure-refactor task with no runtime surface, Hephaestus still boots the artifact (plugin, CLI, library) and verifies import/load. "Build passes" is never sufficient.

**Rationale:** The `deepest-plan` predecessor shipped 91 defects because it trusted compilation as validation. Cast refuses to.

### AD-4: Atlas owns the only outside-plugin write

No agent except Atlas writes outside the plugin's scoped working directory. Atlas writes to `~/Desktop/anneal-runs/{run_id}/`. This concentrates file-system side effects in one place.

**Rationale:** Audit trail. Every file on disk has exactly one author.

### AD-5: Hook file is JSON, not markdown

Hooks live in `hooks/hooks.json` per the Claude Code plugin spec. The file is auto-loaded — **not** referenced from `plugin.json`'s `hooks` field, which would create a duplicate-load error.

**Rationale:** Follow the plugin format cheatsheet exactly.

## Requirements

### Functional

- FR-1: Provide `/anneal-cast:anneal` slash command
- FR-2: On invocation, read `$1` as the user task
- FR-3: If `$1` empty, prompt the user for a task
- FR-4: Execute stages 1 through 7 in order
- FR-5: At stage 5, fan out Red-Team Trinity in parallel
- FR-6: At stage 7, emit XML + plan directory to `~/Desktop/anneal-runs/{run_id}/`
- FR-7: On validate FAIL, route back to Metis with failure as new constraint
- FR-8: Refuse to emit if `simultaneous_pass` is false or `overall_verdict` is RISKY or BLOCK without explicit user override

### Non-functional

- NFR-1: Installable via the two-step marketplace-add + plugin-install flow
- NFR-2: Pass own `validate-plugin.py` with exit code 0
- NFR-3: All content strictly UTF-8, no BOM, no XML declaration on emitted XML
- NFR-4: All config file paths use `${CLAUDE_PLUGIN_ROOT}`, never hardcoded
- NFR-5: All relative paths in `plugin.json` start with `./`
- NFR-6: No emoji anywhere in shipped content
- NFR-7: All scripts in `scripts/` executable (`chmod +x`)

## Risks and mitigations

| Risk | Severity | Mitigation |
|------|----------|-----------|
| Opus 4.7 XML schema changes | HIGH | `_shared/opus-47-xml-schema.md` lives outside plugin; update path is a single edit |
| Agent auto-discovery fails | HIGH | Each agent ships frontmatter `description:` with trigger keywords; skills include trigger patterns |
| Re-loop runs forever on genuinely unfixable task | MEDIUM | Intent Gate rejects unsafe inputs at stage 1; Metis can return BLOCK with clarifying_questions to force human intervention |
| Hook duplicate-load error | HIGH | `hooks/hooks.json` not referenced in `plugin.json` — auto-load only |
| User runs Cast on task better suited to Alloy | LOW | README documents "best for" and "worst for" per architecture |

## Open questions

- Q1: Should `--fast` actually skip anything, or remain a pure no-op? (Decision: pure no-op, documented in README.)
- Q2: Should Cast ship with a `--loop` flag for unbounded re-loops? (Decision: yes, but it is the default anyway — unbounded is the spec.)
- Q3: Should Atlas compress the emitted directory? (Decision: no; human-inspectable is more important than small.)
