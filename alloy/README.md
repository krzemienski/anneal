# anneal-alloy

> Tournament Consensus architecture of the Anneal plugin family.

**N parallel planner biases compete. A synthesizer blends their best material into one plan.** Then Momus audits the blend, Red-Team Trinity attacks it from three angles, Oracle renders a bird's-eye verdict, and Hephaestus builds the artifact for real before Atlas writes the XML prompt + plan directory.

Always-on red team. Always-on functional validation. No mocks. No test files. No stubs.

---

## Install

```bash
/plugin marketplace add /Users/nick/Desktop/anneal/alloy
/plugin install anneal-alloy@anneal-alloy-dev
```

Then confirm registration:

```bash
/plugin list
```

You should see `anneal-alloy` present.

---

## Usage

```bash
# Default — N=5 parallel planner biases
/anneal-alloy:anneal "rewrite the deepest-plan plugin to use SADD primitives"

# Cheaper — 3 biases
/anneal-alloy:anneal "add a status-line progress ticker" --versions 3

# Richer — 7 biases for high-stakes work
/anneal-alloy:anneal "port the ios streaming bridge to macOS" --versions 7
```

`--versions N` must be in range **2–7**. Below 2 there is no tournament; above 7 the synthesizer's signal-to-noise collapses. Default is **N=5**.

---

## Why Alloy

Three architectures satisfy the same invariants. They differ only in *how* stage 4 (Plan) generates its output.

| Architecture | Stage-4 shape | Best for |
|-------------|---------------|----------|
| **Cast** | One planner, one shot | Bug fixes, scoped refactors, clear specs |
| **Alloy** | N parallel biased planners → synthesizer | Novel architecture, greenfield, high-stakes |
| **Temper** | One plan, iteratively deepened | Well-scoped but complex, convergence-friendly |

Alloy wins when the *plan shape isn't obvious*. Blending a defensive plan with a UX plan often produces something neither bias would have written alone.

Cost profile: ~8 + 2N agent spawns per successful run (≈18 at N=5). ~6 min wall-clock. 5× Cast's planner cost — but the synthesizer is where the creative leaps happen.

---

## The Five Default Biases (N=5)

Every Prometheus variant in the tournament receives the same Metis directives and the same probe report — but a different lens:

| Bias | What it optimizes for |
|------|---|
| **correctness** | Exhaustive gate tests, phased rollout, every success criterion measurable |
| **minimalist** | Smallest viable plan, strip ceremony, YAGNI to the bone |
| **defensive** | Every phase has a rollback, checkpoint before risk, fail-safe defaults |
| **performance** | Vendor only what the plan actually uses, prune speculative infra |
| **ux** | Status-line progress, helpful error messages, friendly failure paths |

When `--versions 3`: correctness + minimalist + defensive.
When `--versions 7`: all five plus **verification** (instrument-before-theorize) and **migration** (every breaking change has a migration step).

See `docs/synthesis-algorithm.md` for how the Synthesizer decides which elements to keep.

---

## The Seven Invariants (shared across Cast / Alloy / Temper)

1. **Red team always runs.** Security · Scope · Assumptions in parallel. Not a flag.
2. **Validation always runs.** Hephaestus builds and exercises the real artifact. No mocks.
3. **Dual output.** Every run produces an Opus 4.7 semantic-XML prompt *and* a plan directory.
4. **Skill enrichment.** Probe scans `~/.claude/skills/` and project `.claude/skills/`; matching skills inject automatically.
5. **Unbounded re-loop on FAIL.** Failure is folded into the next run's constraints, not counted.
6. **Parallelization by default.** Planners, red team, and validators fan out as background agents.
7. **Category routing, not model picking.** Harness maps `ultrabrain`/`deep`/`quick` to models.

See [`docs/invariants.md`](./docs/invariants.md) for the full text.

---

## The Roster

| Agent | Role | Model | When |
|-------|------|-------|------|
| **Metis** | Pre-plan consultant | opus | Stage 3 (Enrich) |
| **Prometheus-Alloy** | Biased planner (runs N times) | opus | Stage 4 — N parallel instances |
| **Synthesizer** | Plan-blender (unique to Alloy) | opus | Stage 4 close-out — one call reading N plans |
| **Momus** | Post-plan reviewer | opus | Stage 4 — audits the blend, not the individuals |
| **Red-Team-Security** | Adversary | sonnet | Stage 5 (parallel) |
| **Red-Team-Scope** | Adversary | sonnet | Stage 5 (parallel) |
| **Red-Team-Assumptions** | Adversary | sonnet | Stage 5 (parallel) |
| **Oracle** | Architecture synthesizer | opus | Stage 5 close-out |
| **Hephaestus** | Functional validator | sonnet | Stage 6 |
| **Atlas** | Emitter | sonnet | Stage 7 |

---

## Re-loop on FAIL

On validate FAIL, Alloy routes back to **Intent Gate** — not to the synthesizer. A failed synthesis suggests the *bias mix* was wrong. The re-loop folds the failure as a new constraint into Metis's directives, and the whole tournament runs again. See `docs/synthesis-algorithm.md` § "Failure Attribution".

---

## Outputs

```
${ANNEAL_RUNS_ROOT:-./.anneal/runs}/{run_id}/
├── alloy-{run_id}.xml              # Opus 4.7 semantic-XML prompt
├── plan/
│   ├── plan.md                     # Overview
│   ├── phase-00-*.md               # Phase detail files
│   ├── ...
│   └── phase-NN-*.md
├── variants/
│   ├── variant-1-correctness.md    # Raw planner output, bias 1
│   ├── variant-2-minimalist.md
│   ├── ...
│   └── variant-N-*.md
├── synthesis-provenance.md          # Which variant contributed what
└── reviews/
    ├── metis-envelope.yaml
    ├── momus-envelope.yaml
    ├── redteam-security-envelope.yaml
    ├── redteam-scope-envelope.yaml
    ├── redteam-assumptions-envelope.yaml
    ├── oracle-envelope.yaml
    ├── hephaestus-evidence/
    └── rollup.yaml
```

---

## Files

- [`PRD.md`](./PRD.md) — Product requirements for Alloy specifically
- [`ARCHITECTURE.md`](./ARCHITECTURE.md) — One-page Alloy architecture
- [`docs/invariants.md`](./docs/invariants.md) — The seven shared invariants
- [`docs/worked-example.md`](./docs/worked-example.md) — Plugin rewrite walkthrough with N=5
- [`docs/synthesis-algorithm.md`](./docs/synthesis-algorithm.md) — How the Synthesizer blends
- [`docs/emission-format.md`](./docs/emission-format.md) — Opus 4.7 XML schema
- [`diagrams/alloy-architecture.html`](./diagrams/alloy-architecture.html) — Standalone visual

---

## License

MIT. See [`LICENSE`](./LICENSE).
