# Anneal — Architecture Proposals

**Date:** 2026-04-22
**Replaces:** `deepest-plan` v1.0.0 (deprecated — 91 asymmetric-vendoring defects)
**Visual companion:** [`diagrams/anneal-architectures.html`](./diagrams/anneal-architectures.html)
**Inspired by:** [oh-my-openagent](https://github.com/code-yeongyu/oh-my-openagent) — Greek-god agent taxonomy, parallel fan-out reviews, unbounded verify loops, verdict tiers.

---

## The Thesis

Anneal converts a vague task into a rigorously-reviewed execution artifact — an XML prompt, a plan directory, and the skill enrichment needed to run it — through controlled heating (exploration), slow cooling (convergence), and iterative tempering (red-team adversarial review). The metaphor is not ornamental: the plugin literally implements simulated annealing against plan-quality scores.

Three architectures are proposed. All three satisfy the same eight invariants. They differ only in *how the plan itself is generated* at stage 4 of the pipeline.

---

## Positioning · Anneal ≈ Aider + Ralph + Red Team

Anneal is not a new category. It sits at the intersection of three proven patterns, taking the strongest idea from each and refusing the weakest.

| Reference | What anneal borrows | What anneal refuses |
|-----------|---------------------|---------------------|
| **[Aider](https://aider.chat/)** | Terminal-first invocation. Zero ceremony. The user types `/anneal "do X"` and the plan comes back. No forms, no wizards, no YAML config for the happy path. Aider-style git-awareness: every emit includes a commit template. | Aider's file-by-file chat mode. Anneal is plan-first, not edit-first — it produces the plan and the XML prompt that a *different* session executes. |
| **[Ralph](https://github.com/gheorghe-ciubuc/ralph)** (OMC's persistence loop) | The "doesn't stop until done" discipline. Unbounded re-loop on validate FAIL. Session continuity via a state file (`.anneal/state.json`) so interrupted runs resume. "The boulder never stops." | Ralph's linear re-entry. Anneal's re-loop is not a retry — it folds the failure into the next plan's input as a new constraint, closer to Temper's deepen loop than Ralph's iteration counter. |
| **[oh-my-openagent](https://github.com/code-yeongyu/oh-my-openagent)** | The Greek-god agent taxonomy (Metis · Momus · Oracle · Prometheus · Hephaestus · Atlas). Verdict tiers SAFE / CAUTION / RISKY / BLOCK. 16-agent parallel review pattern. Category routing (`ultrabrain`, `deep`, `quick`) over model-picking. | Their model-lock-in framing — anneal doesn't ship provider-specific fallback chains; it trusts the Claude Code harness to route. |

**The one-sentence positioning:**
> Anneal is Aider's ergonomics, Ralph's persistence, and oh-my-openagent's multi-agent review — wrapped around a simulated-annealing core that makes the red team non-negotiable.

### Consensus agreement · Ralph-style

The "consensus agreement" pattern Ralph uses — iterate until all gates pass *simultaneously* — is Anneal's stage-7 discipline. The three gates:

1. **Red-Team Trinity PASS** — all three adversarial agents return non-BLOCK verdicts
2. **Oracle PASS** — bird's-eye verdict is SAFE or CAUTION (never RISKY or BLOCK without user override)
3. **Hephaestus PASS** — real artifact builds, runs, and produces cited evidence

All three must be green in the *same iteration*. If a fix for gate 2 breaks gate 3, you don't ship — you re-loop. This is structurally identical to oh-my-openagent's work-with-pr skill where CI + review-work + Cubic must all pass in the same push.

---

## Invariants (apply to all three proposals)

1. **Red team always runs.** Three parallel adversaries (Security · Scope · Assumptions). Not a flag. Cannot be disabled.
2. **Validation always runs.** Hephaestus builds and exercises the real artifact. No mocks, no test files, no stubs. Empty evidence → FAIL.
3. **Dual output.** Every run produces an Opus 4.7 semantic-XML prompt **and** a plan directory. Not one. Both.
4. **Skill enrichment.** Probe phase scans `~/.claude/skills/` and project `.claude/skills/`; matching skills inject into the plan's prelude automatically.
5. **Unbounded re-loop on FAIL.** If validate FAILs, route back to the plan stage with the failure as a new constraint. No iteration cap.
6. **Parallelization by default.** Red team, validators, and (in Alloy) planners fan out as background agents.
7. **Category routing, not model picking.** User specifies work-type (`ultrabrain`, `deep`, `quick`). Harness maps to model.
8. **Dual prompts by model family.** Every agent ships Claude-flavored (long, mechanics-driven) and GPT-flavored (short, XML-tagged) prompts. Auto-detected at runtime.

---

## The Seven-Stage Spine

Every anneal run follows this order. Only stage 4 varies.

| # | Stage | Purpose | Agents |
|---|-------|---------|--------|
| 1 | Intent Gate | Classify task shape; reject unsafe inputs | — |
| 2 | Probe | Scan codebase, enumerate skills, read existing docs | Explore |
| 3 | Enrich | Detect ambiguity · flag slop · build directives | **Metis** |
| 4 | **Plan** (varies) | Generate the plan | **Prometheus** (1, N, or N × depth) |
| 5 | Red Team + Oracle | Adversarial audit + bird's-eye verdict | **Red-Team Trinity** (3) + **Oracle** |
| 6 | Validate | Build and exercise the real artifact | **Hephaestus** |
| 7 | Emit / Re-loop | Write XML + plan, or loop back on FAIL | **Atlas** |

---

## The Roster

Seven named agents. Each has a Greek etymology that signals when they run.

| Agent | Role | Etymology | When it runs |
|-------|------|-----------|--------------|
| **Metis** | Pre-plan consultant | Goddess of wisdom / prudence | Stage 3 — catches ambiguity before the planner sees the task |
| **Prometheus** | Planner | Titan of forethought | Stage 4 — writes the actual plan (1, N, or N × depth copies) |
| **Momus** | Post-plan reviewer | God of satire / mockery | End of stage 4 — ruthless audit of the finished plan |
| **Red-Team Trinity** | Always-on adversaries | Security · Scope · Assumptions | Stage 5 — three parallel agents, never sequential |
| **Oracle** | Architecture synthesizer | Delphic seer | End of stage 5 — bird's-eye verdict SAFE/CAUTION/RISKY/BLOCK |
| **Hephaestus** | Functional validator | Craftsman of the gods | Stage 6 — builds and exercises the real artifact |
| **Atlas** | Emitter | Bearer of the world | Stage 7 — assembles XML prompt + plan directory |

Metis and Momus are directly borrowed from oh-my-openagent. Oracle is a simplification of their architecture consultant. Hephaestus is re-purposed — in oh-my-openagent it is the deep worker; here it is the functional validator, reflecting its craftsman etymology.

---

## Verdict Tiers

Every reviewer agent returns one of four verdicts. These are the agent-communication currency:

- **SAFE** — No blocking issues. Proceed.
- **CAUTION** — Non-blocking concerns noted. Proceed with awareness.
- **RISKY** — Significant issues but not fatal. Human judgment required before emit.
- **BLOCK** — Critical issues. Do not emit. Route back to planner.

A run can emit with verdict SAFE or CAUTION. RISKY forces a re-loop unless the user explicitly overrides. BLOCK is absolute.

---

## Plan-Reviewer Output Schema · The Flag Format

Metis, Momus, Red-Team Trinity members, and Oracle all emit findings in the same structured format. This is the canonical "flag" the user asked for: a machine-readable issue record the re-loop can parse and fold back into the next plan.

### Per-finding record

```yaml
- severity: CRITICAL | MAJOR | MINOR
  category: ambiguity | scope | security | assumption | coherence | missing-evidence
  reviewer: metis | momus | redteam-security | redteam-scope | redteam-assumptions | oracle
  summary: "One-sentence description of the issue."
  evidence:
    - plan_file: "phase-04-vendor-skills.md"
      line_range: "45-58"
      excerpt: "...the actual text that triggered the flag..."
  suggestion: "One-sentence remediation. Not a fix, but a direction."
  blocks_emission: true | false
```

### Reviewer verdict envelope

Each reviewer returns:

```yaml
reviewer: momus
verdict: SAFE | CAUTION | RISKY | BLOCK
summary: "2-3 sentence bird's-eye assessment."
confidence: HIGH | MEDIUM | LOW
findings: [ ... list of per-finding records ... ]
blocking_issues_count: <integer>
```

### Rollup at stage 7

Atlas aggregates all reviewer envelopes into a single rollup before emission:

```yaml
rollup:
  overall_verdict: SAFE | CAUTION | RISKY | BLOCK
  gate_status:
    red_team_trinity: 3/3 PASS | 2/3 PASS | ...
    oracle: SAFE | CAUTION | RISKY | BLOCK
    hephaestus: PASS | FAIL
  simultaneous_pass: true | false    # all three gates green in this iteration
  blocking_issues: [ ... deduped, severity-ordered ... ]
  emission_decision: EMIT | RE_LOOP | ABORT
```

A run emits only when `simultaneous_pass: true` and `overall_verdict` is SAFE or CAUTION.

### Why this schema

The user asked for "a plan reviewer that can flag issues." The flag format above is the concrete contract. Every reviewer fills the same record shape, so the re-loop has a deterministic input — it reads the rollup, extracts all CRITICAL and MAJOR findings, and folds them into the next plan's constraints section. No LLM has to "interpret the review" — the data is already structured.

This is the pattern oh-my-openagent uses in its pre-publish-review skill (layer-1 ultrabrain + layer-2 review-work + layer-3 oracle synthesis all emit verdicts in the same envelope). Anneal adapts it for plan-review instead of release-review.

---

## Proposal A — Cast (Linear)

> Single-pour. One planner. One red team. One oracle. One validate. Emit.

### Pipeline

```
Intent Gate → Probe → Enrich (Metis) → Planner → Momus → Red-Team Trinity → Oracle → Validate → Emit
                                                                                               │
                                                                                  [FAIL ──────┘]
                                                                                               ↓
                                                                                         back to Planner
```

### Cost profile
- **Agent spawns per successful run:** ~8
- **Wall-clock:** ~4 min (parallel-corrected)
- **Worst-case with re-loops:** ~12 min (3 re-loops)

### Best for
- Bug fixes
- Scoped refactors
- Tasks where the spec is already clear
- Situations where speed matters more than plan breadth

### Worst for
- Novel architecture
- Greenfield features
- Tasks that benefit from alternative-interpretation exploration

### CLI
```
/anneal <task> --fast       # explicit
/anneal <task>              # implicit default
```

### Key tradeoff
Cast does not explore alternative plan shapes. If the first planner misses a creative approach, nobody else will find it. Mitigation: Momus and Red-Team still audit the single plan rigorously. Validation still exercises the real artifact. The re-loop still routes FAILs back to planning.

---

## Proposal B — Alloy (Tournament Consensus)

> N parallel planners compete. A synthesizer blends their best material into one plan.

### Pipeline

```
Intent Gate → Probe → Enrich (Metis)
                         │
        ┌────────────────┼────────────────┐
        ↓     ↓     ↓    ↓    ↓           │
     Planner1 ... PlannerN     (parallel, different biases)
        │     │     │    │
        └─────┴──┬──┴────┘
                 ↓
            Synthesizer
                 ↓
               Momus
                 ↓
      Red-Team Trinity (parallel)
                 ↓
              Oracle
                 ↓
            Validate
                 ↓
           [FAIL → back to Intent Gate]
                 ↓
               Emit
```

### Planner biases (when N=5 default)
1. **Correctness-biased** — exhaustive gate tests, phased rollout
2. **Minimalist-biased** — strip ceremony, smallest viable plan
3. **Defensive-biased** — every phase has a rollback
4. **Performance-biased** — vendor only what's used
5. **UX-biased** — status-line progress, helpful error messages

### Cost profile
- **Agent spawns per successful run:** ~8 + 2N → ~18 when N=5
- **Wall-clock:** ~6 min (planners run concurrently)
- **Worst-case with re-loops:** ~18 min

### Best for
- Novel architecture
- Greenfield features
- High-stakes refactors
- Tasks where you'd want a second, third, fourth opinion

### Worst for
- Simple tasks (overkill — Cast is 5× cheaper)
- Tight deadlines where 6 min matters

### CLI
```
/anneal <task> --versions 5     # default N=5
/anneal <task> --versions 3     # cheaper
/anneal <task> --versions 7     # richer blend
```

### Key tradeoff
Alloy is the most expensive. 5× planner cost. But the synthesizer is where creative leaps happen — blending a defensive plan with a UX plan often produces something neither would have written alone. Worth it when the plan shape isn't obvious.

---

## Proposal C — Temper (Fixed-Point Deepen)

> One plan, heated and cooled repeatedly until scores stabilize.

### Pipeline

```
Intent Gate → Probe → Enrich (Metis) → Seed Plan (Prometheus)
                                              │
                                              ↓
                     ┌────────────────────────┐
                     │   DEEPEN LOOP          │
                     │                        │
                     │   Planner (rewrite)    │
                     │        ↓               │
                     │   Red-Team Trinity     │ (inline, every depth)
                     │        ↓               │
                     │   Momus (score 0-100)  │
                     │        ↓               │
                     │   Converged?           │
                     │   └── No → next depth  │
                     │   └── Yes → exit       │
                     └────────────────────────┘
                                │
                                ↓
                             Oracle
                                ↓
                            Validate
                                ↓
                       [FAIL → Seed Plan]
                                ↓
                              Emit
```

### Convergence rules

Exit the deepen loop when **any one** of these is true:

1. **Variance of top-3 depth scores < 0.3** (scores have stabilized)
2. **|Δ score| < 0.15 across last 2 depths** (marginal improvement)
3. **depth == 3** (hard cap; no runaway iteration)

### Cost profile
- **Agent spawns per successful run:** ~8 × depth (depth 1–3)
- **Wall-clock:** ~7 min at depth 3
- **Worst-case with re-loops:** ~21 min

### Best for
- Well-scoped but complex tasks
- Cases where iteration is the bottleneck, not exploration
- The plugin rewrite itself (the canonical test case)

### Worst for
- Tasks needing breadth (Temper refines one line of thought, not many)
- Tasks where convergence rubric is hard to define

### CLI
```
/anneal <task> --deepen             # default depth cap 3
/anneal <task> --deepen --depth 2   # cheaper
/anneal <task> --deepen --depth 5   # really melt the rock
```

### Key tradeoff
Temper's red team runs *every iteration*. Genuinely always-on inside the loop. Unlike Cast (red team runs once) and Alloy (red team runs once after synthesis), Temper folds adversarial feedback into the very next rewrite. The cost of this is depth-linear; the benefit is that each iteration genuinely learns from the prior.

---

## Combined: Ultra (`--ultra`)

> Alloy then Temper the winner.

The combined form runs Alloy (N-way tournament, default 5) and then Temper on the synthesizer's output. Maximum cost, maximum quality. Use for truly high-stakes plans.

```
/anneal <task> --ultra
```

- **Agent spawns:** ~18 (Alloy) + ~16 (Temper depth 2 on winner) → ~34
- **Wall-clock:** ~10 min
- **Best for:** Mission-critical architecture decisions where neither breadth nor depth alone is sufficient.

---

## CLI Contract (complete)

| Command | Architecture | Notes |
|---------|-------------|-------|
| `/anneal <task>` | Cast (default) | Smart mode, fast path |
| `/anneal <task> --fast` | Cast | Explicit fast mode |
| `/anneal <task> --versions N` | Alloy | N parallel planners (default 3, range 2–7) |
| `/anneal <task> --deepen` | Temper | Fixed-point deepen, depth cap 3 |
| `/anneal <task> --depth N` | — | Override depth cap for Temper (1–5) |
| `/anneal <task> --ultra` | Alloy → Temper | Maximum quality |
| `/anneal <task> --loop` | — | Unbounded re-loop (no hard cap on retries) |
| `/anneal <task> --type <cat>` | — | Category routing: `ultrabrain`, `deep`, `quick` |
| `/anneal consolidate <dir>` | — | Synthesize existing plans in a directory |
| `/anneal red-team <plan>` | — | Run Red-Team Trinity on an existing plan |
| `/anneal validate <plan>` | — | Run Hephaestus on an existing plan |

Refused flags (logged and ignored):
- `--no-red-team` — red team is non-negotiable
- `--no-validate` — validation is non-negotiable

---

## Worked Example: The Plugin Rewrite

**User input:**
```
/anneal "rewrite the deepest-plan plugin to use SADD primitives and fix the 91 asymmetric-vendoring defects. ship a functional v0.1.0 that passes its own red team."
```

### Cast would
1. Metis flags 4 clarifying questions ("which 91 defects?").
2. Prometheus writes a single 12-phase plan.
3. Momus finds 6 gaps; plan revised.
4. Red-Team Trinity: Security clean. Scope flags "Phase 11 too broad." Assumptions flags "Opus 4.7 XML spec not stable."
5. Oracle: **CAUTION**.
6. Hephaestus dry-runs — plugin boots, command registers.
7. Atlas emits.

**Outcome:** ~8 spawns, ~4 min, solid plan but no alternatives explored.

### Alloy would
1. Metis directives distributed to 5 planners.
2. Five planners run in parallel — P1 correctness, P2 minimalist, P3 defensive, P4 perf, P5 UX.
3. Synthesizer takes P1's phased structure + P3's rollback discipline + P5's status-line. Rejects P2 as under-scoped, P4 as premature optimization.
4. Momus finds 2 integration gaps between P1+P3 rollback semantics; fixed.
5. Red-Team + Oracle: **SAFE**.
6. Validate + emit.

**Outcome:** ~18 spawns, ~6 min, richer plan than any single planner would produce.

### Temper would
1. Metis + Seed planner produce v1. Momus score: 62. Red Team: 5 issues.
2. Depth 1: Planner rewrites v1 with feedback → v2. Score: 78. Issues: 2.
3. Depth 2: Planner rewrites v2 → v3. Score: 85. Issues: 0. Variance(top-3) = 0.18 → converged.
4. Oracle: **SAFE**.
5. Validate + emit.

**Outcome:** ~24 spawns, ~7 min, most refined plan. Each iteration genuinely improved on the prior.

---

## Comparison Matrix

| Dimension | Cast | Alloy | Temper |
|-----------|------|-------|--------|
| Agent spawns per run | ~8 | ~8 + 2N | ~8 × depth |
| Wall-clock | Fastest (~4 min) | Medium (~6 min) | Longest (~7 min) |
| Plan-quality ceiling | Good | Highest | Highest (different path) |
| Exploration of alternatives | None | High | Low |
| Learning across iterations | None | None | High |
| Red team runs | Once | Once | Every depth |
| Best for | Bug fixes · refactors | Novel architecture | Complex but scoped |
| Worst for | Creative tasks | Simple tasks | Tasks needing breadth |
| Default CLI | `--fast` or bare | `--versions N` | `--deepen` |

---

## Skill Inventory — Re-Examined

Anneal vendors these skills into its plugin directory. Each was re-evaluated against the new architecture; retained or cut.

### Vendored — core infrastructure (retained)

| Skill | Source | Purpose |
|-------|--------|---------|
| `launch-sub-agent` | SADD 1.3.3 | Primitive for spawning background agents |
| `do-in-parallel` | SADD 1.3.3 | Primitive for fan-out (Red Team, Alloy planners) |
| `do-and-judge` | SADD 1.3.3 | Primitive for the plan-review sandwich pattern |
| `tree-of-thoughts` | SADD 1.3.3 | Only used by Temper; lazy-loaded |
| `explore` | OMC 4.13.1 | Stage 2 Probe agent |
| `create-agent-skills` | Anneal custom | Emits plan files with correct schema |

### Vendored — validation family (retained)

| Skill | Source | Purpose |
|-------|--------|---------|
| `functional-validation` | VF | Hephaestus's core skill |
| `create-validation-plan` | VF | Plan-phase validation criteria |
| `verdict-writer` | VF | Writes PASS/FAIL with evidence |
| `preflight` | VF | Stage 2 Probe co-skill |

### Vendored — reviewer agents (new, borrowed from oh-my-openagent)

| Skill | Source | Purpose |
|-------|--------|---------|
| `metis-consult` | Anneal (adapted from oh-my-openagent/Metis) | Pre-plan ambiguity detection |
| `momus-review` | Anneal (adapted from oh-my-openagent/Momus) | Post-plan ruthless audit |
| `oracle-synthesize` | Anneal (adapted from oh-my-openagent/Oracle) | Bird's-eye verdict + synthesis |

### Cut from v1 (`deepest-plan`)

| Skill | Why cut |
|-------|---------|
| `judge-with-debate` | Redundant with Momus + Red Team |
| `do-in-steps` | Complexity not worth it; Cast/Alloy/Temper cover sequential needs |
| `multi-agent-patterns` | Reference-only; not runnable |
| `full-functional-audit` | Too heavy; Hephaestus covers it |
| `visual-inspection` | Optional only (gated by task type) |

### Declared companions (not vendored)

| Skill | Why not vendored |
|-------|------------------|
| `visual-explainer` | Optional; user invokes via `/visual-explainer:generate-web-diagram` if they want architecture diagrams |
| `context7` | Optional; lazy-loaded by Metis when docs lookup needed |
| `sequential-analysis` | Reference-only rule; not a runnable skill |

---

## Decision Gate

Which architecture should anneal default to for the bare `/anneal <task>` invocation?

All three remain available as flags. The default choice shapes what "one run" feels like to the user.

- **Cast** — bare `/anneal <task>` runs Cast. `--versions N` and `--deepen` opt into Alloy and Temper.
- **Alloy** — bare `/anneal <task>` runs Alloy with N=3. `--fast` opts into Cast. `--deepen` opts into Temper.
- **Temper** — bare `/anneal <task>` runs Temper with depth cap 2. `--fast` opts into Cast. `--versions N` opts into Alloy.

The user picks one by name. Anneal is shipped with that proposal as the bare default.

---

## Next Step

After the user picks the default architecture, I will:

1. Create `~/Desktop/anneal/AUTONOMOUS-BUILD-PROMPT.xml` — the Opus 4.7 semantic-XML prompt encoding the locked architecture, the invariants, the vendored skills, and the sub-agent dispatch instructions.
2. Populate `~/Desktop/anneal/plan/` with supporting phase files (`phase-00-baseline.md` through `phase-11-ship.md`) and fixtures.
3. Deliver a single command the user can paste into a fresh Claude Code session: the session will read the XML prompt and autonomously build the entire plugin against the locked architecture, using sub-agents, functional validation, and re-looping until the plugin passes its own red team.
