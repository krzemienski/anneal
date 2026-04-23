# Anneal · The Actual Workflow

You asked: "when I go into this directory, what do I actually run?"

This doc is the answer. No theory, just keystrokes.

---

## TL;DR — Two sessions, two commands

```
┌─ Session 1 · PLAN (anneal produces the artifact) ───────────────────────┐
│                                                                          │
│  cd /Users/nick/Desktop/anneal                                          │
│  claude                                                                 │
│                                                                          │
│  > /anneal-temper:anneal "<your task>" --depth 3                        │
│                                                                          │
│  → Writes to ${ANNEAL_RUNS_ROOT:-./.anneal/runs}/{run_id}/                            │
│     ├── temper-{run_id}.xml     (the handoff prompt)                    │
│     └── plan/                   (phase files + plan.md)                 │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘

                                   ↓

┌─ Session 2 · EXECUTE (fresh Claude Code runs the plan) ─────────────────┐
│                                                                          │
│  cd <target project — e.g. /Users/nick/Desktop/blog-series>             │
│  claude                                                                 │
│                                                                          │
│  Paste the entire contents of temper-{run_id}.xml into the chat.        │
│  (Or: cat ${ANNEAL_RUNS_ROOT:-./.anneal/runs}/{run_id}/temper-{run_id}.xml | pbcopy)  │
│                                                                          │
│  → Session 2 executes the plan phase by phase, with functional          │
│     validation between every phase, until done.                         │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

That's the whole workflow. Two sessions. Two commands (plus a paste).

---

## One-time setup (do this once)

```bash
# In any Claude Code session:
/plugin marketplace add /Users/nick/Desktop/anneal
/plugin install anneal-cast@anneal-umbrella-dev
/plugin install anneal-alloy@anneal-umbrella-dev
/plugin install anneal-temper@anneal-umbrella-dev

# Then restart Claude Code.
```

Verify after restart — type `/` and scroll. You should see (plugin prefix is required here because all three plugins register a command named `anneal`):
```
/anneal-cast:anneal
/anneal-alloy:anneal
/anneal-temper:anneal
```
If you install only one of the three, the bare `/anneal` form will also resolve (per Claude Code's optional-prefix rule when there's no collision).

If they're missing → `INSTALL.md § Debug`.

---

## Session 1 detailed — the plan session

### What to run

Pick the architecture that fits your task shape:

```bash
# Linear — fastest, for clear-scope tasks
/anneal-cast:anneal "<task>"

# Tournament — for novel architecture, 5 parallel planners blend
/anneal-alloy:anneal "<task>" --versions 5

# Fixed-point deepen — iterative refinement with variance convergence
/anneal-temper:anneal "<task>" --depth 3
```

Default recommendation for most real work: **`/anneal-temper:anneal ... --depth 3`**. Temper produces the most refined plans because it folds Red Team feedback back into each rewrite.

### What happens during the run

Session 1 runs the 7-stage pipeline:
1. Intent Gate — classifies task shape
2. Probe — scans codebase + enumerates your skills
3. Enrich — Metis flags ambiguity, returns directives
4. Plan — architecture-specific (Cast single-pass, Alloy tournament, Temper deepen loop)
5. Red Team + Oracle — always parallel, always all three adversaries
6. Validate — Hephaestus builds a dry-run, captures evidence
7. Emit — Atlas writes the XML + plan directory

Wall-clock: ~4 min (Cast), ~6 min (Alloy), ~7 min (Temper). You'll see the sub-agents spawn in parallel and report back.

### What you get

At the end, `${ANNEAL_RUNS_ROOT:-./.anneal/runs}/{run_id}/`:

```
anneal-runs/{run_id}/
├── temper-{run_id}.xml       ← THE HANDOFF PROMPT (this is what you paste in Session 2)
└── plan/
    ├── plan.md                ← human-readable plan overview
    ├── phase-00-*.md          ← phase 0 detail
    ├── phase-01-*.md          ← phase 1 detail
    ├── ...                    ← one per phase
    └── fixtures/              ← if any fixtures were generated
```

The `.xml` file contains:
- Full task context (probe report, enrichment directives, user skills)
- The plan itself as structured XML
- Every reviewer's envelope (Metis, Momus, Red-Team Trinity, Oracle)
- Hephaestus's validation evidence
- Iron Rules
- The instruction block at the bottom telling Session 2 what to do

---

## Session 2 detailed — the execute session

### What to run

**Option A — Paste directly into chat** (simplest):
```bash
cd /path/to/target-project
claude

# Then in the session, paste:
cat ${ANNEAL_RUNS_ROOT:-./.anneal/runs}/{run_id}/temper-{run_id}.xml
# (on macOS: | pbcopy and paste into the Claude Code prompt)
```

**Option B — Use `/ck:cook` skill** (ClaudeKit — `~/.claude/skills/cook/SKILL.md`):
```
/ck:cook ${ANNEAL_RUNS_ROOT:-./.anneal/runs}/{run_id}/plan/plan.md --auto
```
`ck:cook` ingests a plan markdown path (NOT the XML file) and drives end-to-end implementation. Per its own docs it supports `--interactive` (default), `--fast`, `--parallel`, `--auto`, `--no-test`, `--tdd`. For anneal plans which already have functional-validation phases baked in, `--auto` is appropriate since the plan itself gates each phase.

**Option C — Headless / non-interactive with `-p`**:
```bash
# Runs once, no interactive session. Good for CI / automation.
claude -p "$(cat ${ANNEAL_RUNS_ROOT:-./.anneal/runs}/{run_id}/temper-{run_id}.xml)"

# For very large XML (>100 KB), stdin-pipe is safer than argv interpolation:
cat ${ANNEAL_RUNS_ROOT:-./.anneal/runs}/{run_id}/temper-{run_id}.xml | claude -p
```

**Recommendation for your question ("run with -p"):** Only use `-p` if you want headless / automated execution. For a real task where you might want to intervene mid-run or inspect intermediate state, use Option A (paste into interactive chat).

### What happens in Session 2

Session 2 reads the XML. The `<instructions>` block at the bottom (query-at-bottom per Opus 4.7 best practice) tells it:
- What the task is
- Which phase to start on
- What success criteria look like
- Which skills to invoke

Claude then works through the plan phase by phase. The per-phase validation criteria (Hephaestus's output) are baked into each phase's success section, so Claude should invoke `functional-validation` between phases. If a phase fails validation, Claude is instructed to re-plan and retry.

**Note:** The XML is a well-structured prompt, not a platform-level self-executor. How well Claude follows it depends on prompt clarity. If a phase stalls or drifts, intervene manually — the "unbounded re-loop" is an instructional target, not a guaranteed behavior.

---

## The specific question — running anneal on the PST task

You said: "basically you should run anneal on that prompt, right? Like basically the chances with a functional validation plan, correct?"

Yes. Exactly that. Here's the exact sequence:

```bash
# Session 1 — PLAN (at /Users/nick/Desktop/anneal or anywhere)
claude
```

```
/anneal-temper:anneal "Deliver the Product Site Template (PST) contract for withagents.dev. Every product (starting with multi-agent-consensus, validationforge, deepest-plan→anneal migration) gets: hero, 3-sentence what-it-does, ≥2 inline usage examples, architecture/flow diagram, how-it-works, feature matrix, install/docs/changelog, links back to brand. Apply the three-tier strategy: Tier 1 apex route /products/{slug}, Tier 2 subdomain rewrite via site/src/proxy.ts, Tier 3 separate Vercel only when isolation demands. Validate via functional-validation + visual-inspection at 375/768/1440 + e2e cross-domain navigation. No mocks, no test files." --depth 3
```

Wait for the run to emit. Copy the run_id from the output. Then:

```bash
# Session 2 — EXECUTE (at /Users/nick/Desktop/blog-series)
cd /Users/nick/Desktop/blog-series
claude

# Paste into the chat:
cat ${ANNEAL_RUNS_ROOT:-./.anneal/runs}/{run_id-from-session-1}/temper-{run_id}.xml
```

Session 2 will build the PST contract. Every phase validates against a real build. When the plan emits SAFE (all gates simultaneously green), you're done — `site/src/lib/products.ts` is updated, product sites render, validation evidence is captured in `e2e-evidence/`.

That IS the dogfood proof. Anneal planning the thing it was built to plan.

---

## Functional validation — yes, always

Every anneal-produced plan includes a `phase-NN-functional-validation.md` as a mandatory late-stage phase. That phase has Hephaestus's criteria:
- Build must produce real output (not "build succeeded" without logs)
- Runtime surface must exist (even pure refactors MUST import the artifact — per Temper's skill-creator round edit)
- Evidence files must be non-empty
- Screenshots must show relevant content, not blank pages
- API responses must include both headers and body
- No mocks, no test files, no stubs

This isn't a flag you pass. It's an Iron Rule baked into every plan anneal emits. Removing it would require editing Momus's `## Iron Rule violations` block (don't).

---

## Cheatsheet for copy-paste

```bash
# Setup (one-time)
/plugin marketplace add /Users/nick/Desktop/anneal
/plugin install anneal-cast@anneal-umbrella-dev
/plugin install anneal-alloy@anneal-umbrella-dev
/plugin install anneal-temper@anneal-umbrella-dev
# restart Claude Code

# Session 1 — plan (any directory)
/anneal-temper:anneal "<your task>" --depth 3

# Session 2 — execute (target project directory)
cat ${ANNEAL_RUNS_ROOT:-./.anneal/runs}/{run_id}/temper-{run_id}.xml | pbcopy
# paste into new Claude Code session
```

Three commands plus a paste. That's anneal.
