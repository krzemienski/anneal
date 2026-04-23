# Anneal · Cast

**Linear single-pour plan-review plugin for Claude Code.**

One planner. One red team. One oracle. One validate. Emit.

Cast is the fastest of the three Anneal architectures. Use it when the spec is clear, the task is scoped, and you want a rigorously-reviewed plan in about four minutes.

---

## What Cast does

Given a task, Cast runs a seven-stage pipeline:

1. **Intent Gate** — classify task shape, reject unsafe inputs
2. **Probe** — scan the codebase, enumerate skills, read existing docs
3. **Enrich** — Metis flags ambiguity and emits planner directives
4. **Plan** — Prometheus writes a single markdown plan (one pass)
5. **Review** — Momus audits, Red-Team Trinity fans out (security / scope / assumptions), Oracle synthesizes
6. **Validate** — Hephaestus builds and exercises the real artifact, captures evidence
7. **Emit** — Atlas writes an Opus 4.7 semantic-XML prompt plus a plan directory

On validate FAIL the re-loop routes the failure back to Metis as a new constraint — not a fresh restart, a constrained retry.

---

## Install

From a fresh Claude Code session:

```
/plugin marketplace add /Users/nick/Desktop/anneal/cast
/plugin install anneal-cast@anneal-cast-dev
```

Verify installation:

```
/plugin list
```

You should see `anneal-cast 0.1.0` listed.

---

## Usage

```
/anneal-cast:anneal <task>
```

Examples:

```
/anneal-cast:anneal "fix the pagination bug in src/feed/list.ts where page=0 returns duplicates"
/anneal-cast:anneal "refactor the auth middleware so every route reads the same session-resolver"
/anneal-cast:anneal --fast "rename the InternalUser type to AuthenticatedUser across the monorepo"
```

The `--fast` flag is a no-op; Cast is already the fast path. It exists for CLI symmetry with Alloy and Temper.

---

## Output

Every successful run writes to `${ANNEAL_RUNS_ROOT:-./.anneal/runs}/{run_id}/`:

```
anneal-runs/
  cast-anneal-260422-1440-{slug}/
    cast-{run_id}.xml        ← Opus 4.7 semantic-XML prompt
    plan/
      plan.md                ← overview + phase index
      phase-00-*.md          ← phase files
      phase-01-*.md
      ...
      fixtures/              ← (optional) generated fixtures
    rollup.yaml              ← reviewer envelopes aggregated
    evidence/                ← Hephaestus captured evidence
```

The XML file is designed to be pasted into a **fresh** Claude Code session — the session reads the prompt, walks the plan, and executes against the captured review and validation context.

---

## The Roster

Seven named agents, Greek etymology signalling when each runs.

| Agent | Role | Stage |
|-------|------|-------|
| **Metis** | Pre-plan consultant · catches ambiguity | 3 |
| **Prometheus** | Planner · writes the plan | 4 |
| **Momus** | Post-plan reviewer · ruthless audit | 4 close-out |
| **Red-Team Trinity** | Security · Scope · Assumptions | 5 |
| **Oracle** | Synthesizer · bird's-eye verdict | 5 close-out |
| **Hephaestus** | Functional validator · builds + exercises | 6 |
| **Atlas** | Emitter · XML + plan directory | 7 |

---

## Cost profile

| Metric | Value |
|--------|-------|
| Agent spawns per successful run | ~8 |
| Wall-clock per run | ~4 minutes |
| Worst-case with 3 re-loops | ~12 minutes |

---

## Invariants

All Anneal architectures share these eight invariants. Cast enforces them at the command level.

1. Red team always runs. Three parallel adversaries. Cannot be disabled.
2. Validation always runs. No mocks, no test files, no stubs.
3. Dual output — XML prompt AND plan directory.
4. Skill enrichment on — probe scans `~/.claude/skills/` and project skills.
5. Unbounded re-loop on FAIL — back to Metis with failure as new constraint.
6. Parallelization by default — Red Team fans out.
7. Category routing, not model picking.
8. Dual prompts by model family (shipped in agent definitions).

See `docs/invariants.md` for the full description.

---

## Project docs

- `PRD.md` — product requirements
- `ARCHITECTURE.md` — one-page architecture of Cast
- `docs/invariants.md` — the eight invariants
- `docs/worked-example.md` — walking the plugin rewrite through Cast
- `docs/emission-format.md` — Opus 4.7 XML schema
- `diagrams/cast-architecture.html` — standalone visual

---

## Relationship to the Anneal family

Cast is one of three Anneal architectures. All three satisfy the same invariants; they differ only at stage 4.

| Architecture | Plan strategy | When to use |
|--------------|---------------|-------------|
| **Cast** (this plugin) | Single planner call | Bug fixes, scoped refactors |
| **Alloy** | N parallel planners + synthesizer | Novel architecture, greenfield |
| **Temper** | Fixed-point deepen loop | Well-scoped complex tasks |

Install the other two as sibling plugins when you need them.

---

## License

MIT. See `LICENSE`.
