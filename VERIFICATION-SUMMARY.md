# Verification Summary

**Date:** 2026-04-22 (updated 19:25 after runtime-defect discovery and fix)
**Trigger:** User directive to close the confidence loop through actual behavior, not static structure.

---

## ⚠️ CRITICAL UPDATE — runtime defect found AND fixed

An earlier version of this doc claimed "install-ready" based on static validation only. Subsequent runtime testing via a real Claude Code worker session launched with `claude --plugin-dir <path>` proved that **all three plugins silently failed to load their slash commands and agents** — the worker reported "no /anneal commands found" despite `validate-plugin.py` passing.

**Root cause:** `plugin.json` contained non-standard top-level fields (`skills: "./skills/"`, `commands: "./commands/"`, `agents: "./agents/"`, `requires: {…}`) that broke `--plugin-dir` loading. Known-working plugins (claude-session-driver, superpowers) declare only: `name`, `version`, `description`, `author`, `homepage`, `repository`, `license`, `keywords`.

**Fix applied:** All three `plugin.json` manifests stripped down to the safe set. Re-verified by spawning three separate workers (`--plugin-dir <plugin>`) — each confirmed `/anneal-{cast,alloy,temper}:anneal` is now visible.

**Regression guard added:** `scripts/smoke-test.sh` now flags any non-standard top-level plugin.json field with: "FAIL: plugin.json contains non-standard top-level fields that break --plugin-dir: <fields>". Tested in both directions — PASS on current state, FAIL on restored-bad state.

### Runtime evidence captured

| Plugin | Worker session | Response to "is /anneal-{variant}:anneal available?" |
|---|---|---|
| Cast | `0f0da246-97ea-4556-960b-3f9725ec65c7` | **Yes** |
| Alloy | `0c69ee35-81ce-4d11-8b51-b4c714bf1bf2` | **Yes.** |
| Temper | `f561071f-879e-4176-b950-24c24b7b52e8` | **Yes.** |

Evidence method: `claude-session-driver` — real Claude Code sessions launched in tmux, prompt sent via `send-prompt.sh`, response read via `converse.sh`. No mocks. No sub-agent summaries. Actual worker output.

### End-to-end Cast pipeline: NOW VERIFIED PASS

Executed `/anneal-cast:anneal "Write one line 'hello world' to /tmp/anneal-probe/readme.txt"` in a real Claude Code worker session (session `34b661e6…`). Full transcript captured.

**Stage evidence (all 9 Greek-god agents dispatched and returned):**
- `23:36:08` Metis dispatched → SAFE (4 findings, 13 directives)
- `23:37:21` Prometheus-Cast dispatched → plan written
- `23:41:06` Momus dispatched → SAFE (1 finding)
- `23:42:47` Red-Team Security → PASS
- `23:44:26` Red-Team Scope → PASS
- `23:45:44` Red-Team Assumptions → RISKY (1 finding)
- `23:48:02` Oracle dispatched → CAUTION (aggregate verdict)
- `23:49:08` Hephaestus dispatched → artifact built + 5 evidence files
- `23:53:44` Atlas dispatched → XML + plan directory emitted
- `00:01:29` stop event — 27 min wall clock

**Artifacts produced (all personally verified with `cat` / `wc` / `ls`):**
- `/tmp/anneal-probe/readme.txt` — "hello world" + newline, exactly 12 bytes ✓
- `~/Desktop/anneal-runs/cast-smoke-260422-1936/cast-cast-smoke-260422-1936.xml` — 239 lines of Opus 4.7 semantic-XML ✓
- `~/Desktop/anneal-runs/cast-smoke-260422-1936/rollup.yaml` — `simultaneous_pass: true`, per-reviewer verdicts recorded ✓
- `~/Desktop/anneal-runs/cast-smoke-260422-1936/plan/plan.md` + `phase-01-write-hello-world.md` ✓
- `~/Desktop/anneal-runs/cast-smoke-260422-1936/evidence/` — Hephaestus build log, xxd dump, ls, read capture, artifact copy ✓

**Second round-trip also succeeded** (`~/Desktop/anneal-runs/cast-260422-1950-hello-world-probe/`) — the pipeline is repeatable, not a one-off.

### Dispatch-semantics fix applied mid-session

The first Cast E2E run stopped after dispatching Red-Team Trinity because the command body's "parallel" language caused Claude to use `run_in_background: true` (fire-and-forget). Root cause identified, fixed in all 3 command bodies: "parallelism comes from batching Task calls in one message, NOT from the background flag". Explicit "Do NOT set run_in_background: true" guidance added. Second run completed all 9 stages.

### What is still untested

- Alloy E2E (same architecture, same dispatch fix) — running next
- Temper E2E with `--depth 2` (adds convergence loop beyond Cast's structure) — running after Alloy

---

What was verified, what was fixed, and what still needs a longer-running interactive test.

---

## Method

Four parallel sub-agents ran in the background:

1. **plugin-validator** against Cast — full structural + contract validation
2. **plugin-validator** against Alloy — includes tournament contract check
3. **plugin-validator** against Temper — includes convergence checker selftests
4. **Workflow verification research agent** — answered 8 specific questions against official Claude Code docs at `~/.claude/plugins/cache/superpowers-marketplace/superpowers-developing-for-claude-code/0.3.1/skills/working-with-claude-code/references/`

Reports: `/tmp/anneal-validation/{cast,alloy,temper}-validation-report.md` + `workflow-verification-report.md`.

---

## Results

### Plugin validation (all PASS — zero CRITICAL)

| Plugin | CRITICAL | MAJOR | MINOR | Contract fidelity |
|--------|---------|-------|-------|-------------------|
| Cast   | 0 | 5 (all resolved) | 6 | PASS — single Prometheus, no tournament, no deepen |
| Alloy  | 0 | 2 (all resolved) | 6 | PASS — N parallel planners, Synthesizer cannot plan cold, FAIL → Metis |
| Temper | 0 | 0 | 4 (all non-blocking) | PASS — Red-Team every depth, `convergence-check.py` 12/12 selftests pass, `score: 0-100` rubric honored |

### Workflow verification (claims vs Claude Code docs)

| Claim | Status |
|-------|--------|
| `/anneal-cast:anneal` namespace form | VERIFIED — `slash-commands.md:213-254` |
| Command body is a prompt, not a shell script | VERIFIED — `slash-commands.md:33-35` |
| Sub-agent dispatch via Task tool | VERIFIED — `sub-agents.md:235-242` |
| Skills are model-invoked (autonomous) | VERIFIED — `skills.md:16` |
| `/ck:cook <plan.md>` compatible with anneal | VERIFIED — `~/.claude/skills/cook/SKILL.md:62-69` |
| `/plugin marketplace add <dir>` form | VERIFIED — `plugins.md:90-98` |
| Restart-required after install | VERIFIED — `plugins.md:104` |
| "XML is self-executing" | OVERSTATED — FIXED |
| `--fork-session` flag for headless | UNDOCUMENTED in cli-reference.md — REPLACED with stdin pipe |
| "Invoke the metis skill" | MISLEADING — FIXED (skills are autonomous, agents are dispatched) |

---

## Fixes applied

### `_shared/` MAJOR across all 3 plugins

`_shared/opus-47-xml-schema.md`, `agent-prompts-core.md`, `plan-reviewer-schema.md`, `plugin-format-cheatsheet.md` now vendored into **each plugin's root** at `{cast,alloy,temper}/_shared/`. References like `_shared/opus-47-xml-schema.md` now resolve correctly when the plugin is installed anywhere.

### Hardcoded `/Users/nick/…` in all 3 marketplace.json

Replaced with `<path-to-anneal-{variant}-plugin>` placeholder. Users installing from a fork or clone no longer get install instructions pointing at a nonexistent directory.

### WORKFLOW.md — 3 edits

| Line area | Change |
|-----------|--------|
| ~57 | Added note that `/anneal` bare form works when only one variant is installed (per Claude Code's optional-prefix rule) |
| ~150 | Replaced `claude --fork-session -p "$(cat … .xml)"` with `cat … .xml | claude -p` — stdin pipe is safer for large prompts, fork-session flag is undocumented |
| ~164 | Softened "XML is self-executing" — now describes XML as a well-structured prompt whose effectiveness depends on Claude following embedded instructions |

### CLAUDE.md — 3 edits

| Line area | Change |
|-----------|--------|
| ~34 | XML description now clarifies "strong prompt, not self-executing program" |
| ~67 | Agent/skill dispatch surface separated: agents via Task tool (deterministic), skills autonomous / model-invoked |
| ~108 | Added guardrail: don't remove "Always use the Task tool to spawn agents" directive — that's the line that converts orchestration prose into real dispatches |

### Smoke test (post-fix)

```
bash /Users/nick/Desktop/anneal/scripts/smoke-test.sh
  → RESULT: ALL PLUGINS PASS
```

All three `validate-plugin.py` self-validators exit 0.

---

## What I am now confident about

- **Install will work** — `/plugin marketplace add /Users/nick/Desktop/anneal` → `/plugin install anneal-{cast,alloy,temper}@anneal-umbrella-dev` (verified against `plugins.md:90-104`)
- **Commands will appear** — as `/anneal-cast:anneal`, `/anneal-alloy:anneal`, `/anneal-temper:anneal` (prefix needed because three plugins collide)
- **Command body will execute** — Claude reads it as a prompt, the explicit "Always use the Task tool" line drives sub-agent dispatch
- **Agents will spawn in parallel** — Red-Team Trinity fans out in a single message with 3 Task calls
- **`_shared/` references will resolve** — now vendored in each plugin root
- **`/ck:cook <plan.md> --auto`** option is valid — the ClaudeKit cook skill accepts the plan.md path produced by anneal
- **Convergence math is correct** — Temper's `convergence-check.py` passes 12/12 doctests + 4/4 smoketests
- **Contract fidelity holds** — each plugin honors its specific invariants (Cast linear, Alloy tournament, Temper deepen)

## What still requires an interactive test from the user

These were not testable via static analysis:

1. **Whether the XML actually drives phase-by-phase execution without user intervention.** Official docs do not describe a self-execution primitive. The XML is a prompt; its phase-loop behavior is emergent from prompt quality. Reality-check only by pasting a real temper XML into a fresh session and observing.

2. **argv size ceiling for `claude -p "$(cat file.xml)"`.** macOS `ARG_MAX` varies; Claude Code's own limit is undocumented. A 50 KB anneal XML should be fine; anything above 100 KB use stdin pipe.

3. **Whether the `skills/metis/SKILL.md` ever autonomously activates during a Temper run** (given that `agents/metis.md` is also dispatched via Task). Docs do not cover nested agent+skill interactions.

4. **End-to-end run against the PST task** — the dogfood test described in `PHASE-ROADMAP.md`. This is the ultimate validation: anneal plans its own product-site contract, a fresh session executes the plan, the plan passes functional-validation.

---

## Next steps (user-facing)

```bash
# One-time setup
/plugin marketplace add /Users/nick/Desktop/anneal
/plugin install anneal-cast@anneal-umbrella-dev
/plugin install anneal-alloy@anneal-umbrella-dev
/plugin install anneal-temper@anneal-umbrella-dev
# → restart Claude Code

# Plan session
/anneal-temper:anneal "<your task>" --depth 3

# Execute session (in target project)
cat ~/Desktop/anneal-runs/{run_id}/temper-{run_id}.xml   # paste into fresh Claude Code session
# or
/ck:cook ~/Desktop/anneal-runs/{run_id}/plan/plan.md --auto
```

All three paths are documented in `WORKFLOW.md` (Options A/B/C).

---

## Report files

- `/tmp/anneal-validation/cast-validation-report.md` — N/A (agent returned inline; summary above)
- `/tmp/anneal-validation/alloy-validation-report.md` — 188 lines
- `/tmp/anneal-validation/temper-validation-report.md` — 298 lines
- `/tmp/anneal-validation/workflow-verification-report.md` — 283 lines
