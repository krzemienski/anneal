# Anneal · Temper

**Fixed-Point Deepen architecture** of the Anneal plugin family. One plan, heated and cooled repeatedly until scores stabilize.

Temper's defining property: **the Red-Team Trinity runs at every depth**. Cast runs red team once. Alloy runs red team once after synthesis. Temper folds adversarial feedback into the very next rewrite.

## Install

```bash
/plugin marketplace add /Users/nick/Desktop/anneal/temper
/plugin install anneal-temper@anneal-temper-dev
```

Verify:

```bash
python3 /Users/nick/Desktop/anneal/temper/scripts/validate-plugin.py /Users/nick/Desktop/anneal/temper
```

## Usage

```bash
# Default: deepen with hard cap 3
/anneal-temper:anneal "rewrite the auth middleware to unify OIDC + legacy JWT"

# Cheaper: cap at depth 2
/anneal-temper:anneal "refactor pagination" --depth 2

# Really melt the rock: cap at depth 5
/anneal-temper:anneal "redesign the event bus" --depth 5

# Explicit --deepen flag (alias for Temper mode)
/anneal-temper:anneal "fix flaky CI jobs" --deepen
```

The `--deepen` flag is an alias for Temper mode (the plugin's native behavior). The `--depth N` flag overrides the default hard cap (range `1-5`).

## What "depth" means

Depth is the iteration count of the deepen loop. At each depth the planner rewrites the prior depth's plan with Momus's 0-100 score and the Red-Team Trinity's findings folded in as input. The loop exits when scores stabilize.

### Convergence rules

Exit the loop when **any one** of these is true:

1. **Variance of top-3 depth scores < 0.3** — scores have stabilized.
2. **|Δ score| < 0.15 across last 2 depths** — marginal improvement, diminishing returns.
3. **depth == hard_cap** — runaway iteration guard (default 3, user-configurable 1-5).

Rule 1 guards against premature stabilization. Rule 2 guards against oscillation. Rule 3 is a hard backstop so no run can spin forever. See [`docs/convergence-rules.md`](./docs/convergence-rules.md) for the formal statement with worked examples.

## The Seven-Stage Spine

Every Temper run follows this order:

```
1. Intent Gate     · reject unsafe inputs
2. Probe           · scan codebase, skills, docs
3. Enrich (Metis)  · catch ambiguity BEFORE planner sees task
4. Plan            · DEEPEN LOOP
                     ├─ Planner (rewrite from prior depth)
                     ├─ Red-Team Trinity (INLINE, every depth)
                     ├─ Momus (score 0-100)
                     └─ Converged? → exit or next depth
5. Oracle          · bird's-eye verdict on final plan
6. Validate        · Hephaestus builds and exercises the artifact
7. Emit / Re-loop  · Atlas writes XML + plan directory OR re-loops on FAIL
```

## Roster

| Agent | Role | When it runs |
|-------|------|--------------|
| **Metis** | Pre-plan consultant | Stage 3 — once |
| **Prometheus-Temper** | Planner (rewrites from prior depth) | Stage 4 — once per depth |
| **Deepen-Loop** | Orchestrator (tracks scores, checks convergence) | Stage 4 — once per run |
| **Red-Team Trinity** | Security · Scope · Assumptions adversaries | Stage 4 — **every depth** |
| **Momus** | Post-plan reviewer (0-100 scorer) | Stage 4 — once per depth |
| **Oracle** | Architecture synthesizer | Stage 5 — once |
| **Hephaestus** | Functional validator | Stage 6 — once |
| **Atlas** | Emitter | Stage 7 — once on EMIT |

## Momus scoring rubric

In Temper, Momus emits both a `verdict` (SAFE/CAUTION/RISKY/BLOCK) and a numeric `score: 0-100`. The score maps back to the verdict band:

| Range | Verdict | Meaning |
|-------|---------|---------|
| 100 | SAFE | Ship it now — no remaining concerns |
| 85-99 | SAFE | All major gaps closed, only minor polish left |
| 70-84 | CAUTION | Non-blocking concerns, plan is implementable |
| 50-69 | RISKY | Significant gaps, human review required |
| 0-49 | BLOCK | Plan is not implementable as written |

Full rubric with anchor descriptions at [`docs/scoring-rubric.md`](./docs/scoring-rubric.md).

## Cost profile

- **Agent spawns per successful run:** ~8 × depth → ~24 at depth 3
- **Wall-clock:** ~7 min at depth 3 (parallel-corrected)
- **Worst-case with one validate re-loop:** ~14 min

Use Temper when:
- The task is well-scoped but complex
- Iteration is the bottleneck, not exploration
- You want every rewrite to genuinely learn from the last

Don't use Temper for:
- Tasks that need breadth — use `anneal-alloy` (N-way tournament)
- Simple bug fixes — use `anneal-cast` (5× cheaper)
- Tasks where a convergence rubric is hard to define

## Invariants (non-negotiable)

1. Red team always runs — **in Temper, at every depth**.
2. Validate always runs. Hephaestus builds and exercises the real artifact.
3. Dual output: Opus 4.7 semantic-XML prompt + plan directory.
4. Skill enrichment auto-scans `~/.claude/skills/` + project `.claude/skills/`.
5. Unbounded re-loop on validate FAIL — routes back to Seed (depth 0) with failure folded into Metis directives.
6. Parallelization by default — Red Team Trinity always spawns in parallel, even inside the loop.
7. Category routing, not model picking — user specifies `--type ultrabrain|deep|quick`, harness maps to model.
8. Dual prompts by model family — Claude-flavored and GPT-flavored prompts auto-detected at runtime.

## Refused flags

- `--no-red-team` — red team is non-negotiable; refused and logged.
- `--no-validate` — validation is non-negotiable; refused and logged.

## Files

```
temper/
├── .claude-plugin/
│   ├── plugin.json
│   └── marketplace.json
├── README.md                   ← this file
├── PRD.md
├── ARCHITECTURE.md
├── LICENSE
├── commands/anneal.md          ← /anneal-temper:anneal
├── skills/
│   ├── metis/
│   ├── prometheus-temper/
│   ├── deepen-loop/            ← orchestrator
│   ├── momus/                  ← with 0-100 scoring
│   ├── red-team-trinity/       ← inline, every depth
│   ├── oracle/
│   ├── hephaestus/
│   └── atlas/
├── agents/
│   ├── metis.md
│   ├── prometheus-temper.md
│   ├── deepen-loop.md          ← orchestrator agent
│   ├── momus.md
│   ├── redteam-security.md
│   ├── redteam-scope.md
│   ├── redteam-assumptions.md
│   ├── oracle.md
│   ├── hephaestus.md
│   └── atlas.md
├── hooks/hooks.json
├── scripts/
│   ├── validate-plugin.py
│   ├── validate-xml.py
│   ├── orchestrate.sh          ← seed → loop{planner,redteam,momus,convergence}
│   └── convergence-check.py    ← runnable variance/delta/cap checker
├── diagrams/temper-architecture.html
└── docs/
    ├── invariants.md
    ├── worked-example.md
    ├── convergence-rules.md
    ├── scoring-rubric.md
    └── emission-format.md
```

## Related plugins

- **anneal-cast** — Linear single-pour. Use for bug fixes and scoped refactors.
- **anneal-alloy** — N-way tournament consensus. Use for novel architecture.
- **anneal-temper** — You are here. Use for complex but scoped tasks where iteration improves the plan.

License: MIT.
