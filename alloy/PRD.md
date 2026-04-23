# PRD — anneal-alloy v0.1.0

**Product:** `anneal-alloy` — Tournament Consensus architecture of the Anneal plugin family.
**Version:** 0.1.0
**Author:** Nick Krzemienski
**Date:** 2026-04-22
**Status:** Initial release

---

## 1 · Problem

Single-planner architectures (Cast) succeed when the plan shape is obvious. They fail silently on novel work: the first plan the model produces anchors every subsequent review, and Momus + Red Team can only audit *what was written*, not *what could have been written*.

Worse, single-planner runs hide bias. A planner with a default "correctness" lean produces phased, gate-heavy plans — fine for bug fixes, wrong for UX work where ceremony drowns the signal. There is no mechanism to *surface* the bias, let alone challenge it.

deepest-plan v1.0.0 had consensus-synthesis primitives but used them for *verdicts*, not for *planning*. The single-planner plus multi-validator asymmetry is exactly the 91 vendored-skill defects that triggered the rewrite.

---

## 2 · Goal

Produce a plugin where stage 4 (Plan) runs **N parallel Prometheus variants with distinct biases**, then blends them into one plan via a **Synthesizer** agent distinct from any planner. The blend is what Momus audits, not the individuals.

This forces bias to surface, forces creative tension, and gives the synthesizer genuine material to composite. The first time a defensive plan and a UX plan collide, the result is usually something no single bias would have written.

---

## 3 · Non-goals

- **Not a consensus vote.** The Synthesizer does not "majority rule" — it reads all N plans and composites.
- **Not a retry.** N=5 is tournament, not five-shot-best-of. Every variant runs to completion.
- **Not sequential.** Planners fan out via `xargs -P`. Sequential is wrong.
- **Not unbounded.** N ∈ [2, 7]. Beyond 7 the synthesizer's signal-to-noise collapses.
- **Not model-picking.** Users pick category (`--type ultrabrain`); harness maps to model.

---

## 4 · Users

- **Primary:** A Claude Code user initiating novel or high-stakes work — greenfield features, architecture decisions, production-critical refactors.
- **Secondary:** A CI system invoking `/anneal-alloy:anneal` in non-interactive mode (future — not v0.1.0).

---

## 5 · Acceptance criteria

The plugin is **v0.1.0-shippable** when:

| # | Criterion | Evidence |
|---|-----------|----------|
| 1 | Installs via `/plugin marketplace add && /plugin install anneal-alloy@anneal-alloy-dev` | `/plugin list` shows `anneal-alloy` |
| 2 | `validate-plugin.py` exits 0 on the plugin root | stdout: `VALIDATION PASSED` |
| 3 | `/anneal-alloy:anneal <task>` dispatches 5 parallel Prometheus-Alloy agents | process tree or agent log shows 5 concurrent spawns |
| 4 | `--versions N` changes planner count (range 2–7) | same evidence, N variable |
| 5 | Synthesizer runs once after all N complete | synthesis-provenance.md file produced, cites all N |
| 6 | Momus runs on synthesized plan, not individuals | momus-envelope.yaml cites `plan/` paths not `variants/` paths |
| 7 | Red-Team Trinity runs in parallel after Momus | three envelopes produced within ±3s of each other |
| 8 | Validate FAIL routes to Intent Gate, not Synthesizer | next iteration's Metis envelope includes failure as new constraint |
| 9 | Output is XML + plan directory under `${ANNEAL_RUNS_ROOT:-./.anneal/runs}/{run_id}/` | both files exist, XML follows `opus-47-xml-schema.md` |
| 10 | No test files, no mocks, no stubs written anywhere | `grep -rE '(\.test\.|\.spec\.|mock|stub)' .` returns nothing in plugin source |

---

## 6 · Invariants (non-negotiable)

The seven shared Anneal invariants apply verbatim. See [`docs/invariants.md`](./docs/invariants.md). Alloy adds **no** new invariants — it inherits the contract and varies only stage 4.

---

## 7 · CLI contract

```
/anneal-alloy:anneal <task>                     # N=5 default
/anneal-alloy:anneal <task> --versions 3        # cheaper
/anneal-alloy:anneal <task> --versions 7        # richer
/anneal-alloy:anneal <task> --loop              # unbounded re-loop
/anneal-alloy:anneal <task> --type <category>   # ultrabrain|deep|quick
```

Refused flags (logged and ignored):
- `--no-red-team` — red team is non-negotiable
- `--no-validate` — validation is non-negotiable
- `--versions 1` — that's Cast; use `/anneal-cast:anneal`
- `--versions 8+` — signal-to-noise collapses; refused

---

## 8 · Agent roster

See [`README.md`](./README.md) § The Roster. Eleven agents total:

- 1 Metis
- 1 Prometheus-Alloy spawned N times with different `bias`
- 1 Synthesizer (unique to Alloy)
- 1 Momus
- 3 Red-Team Trinity (parallel)
- 1 Oracle
- 1 Hephaestus
- 1 Atlas

---

## 9 · Biases

### Default five (N=5)

1. **correctness** — exhaustive gate tests, phased rollout
2. **minimalist** — strip ceremony, smallest viable plan
3. **defensive** — every phase has a rollback
4. **performance** — vendor only what's used
5. **ux** — status-line progress, helpful error messages

### Extended two (N=7)

6. **verification** — instrument-before-theorize, debug hooks baked in
7. **migration** — every breaking change has a migration step

### Reduced three (N=3)

correctness + minimalist + defensive. Drops performance (premature for early planning) and ux (specialized). Keeps the three most orthogonal biases.

### Reduced two (N=2)

correctness + minimalist. Minimum viable tournament. Useful primarily for testing Alloy mechanics on trivial tasks.

See [`docs/synthesis-algorithm.md`](./docs/synthesis-algorithm.md) § "Bias Selection" for the routing table.

---

## 10 · Synthesizer contract

The Synthesizer agent is unique to Alloy. Not present in Cast or Temper.

**Input:** N plan variants (markdown) + Metis directives + probe report.
**Output:**
- One blended plan (markdown, same schema as any Prometheus plan)
- `synthesis-provenance.md` — per-phase attribution showing which variant contributed each element

**Hard rules:**

1. The Synthesizer does NOT plan from scratch. It composites.
2. Every phase in the blended plan cites ≥1 source variant.
3. Contradictory elements are resolved in favor of the directive, not a variant — if no directive applies, default to the most conservative variant (defensive > correctness > minimalist).
4. Redundant elements across variants are kept once with a merged attribution.
5. The blended plan must pass the same schema validator as any single-planner plan.

See [`docs/synthesis-algorithm.md`](./docs/synthesis-algorithm.md) for the full algorithm.

---

## 11 · Cost profile

- **Agent spawns per successful run:** 8 + 2N
  - Fixed: Metis, Synthesizer, Momus, Oracle, Hephaestus, Atlas (6) + 3 Red-Team Trinity = 9
  - Variable: 2N (N planners + 1 each for prompt prep, though prep batched so effectively N planners)
  - Rounded convention: **~18 spawns at N=5**
- **Wall-clock:** ~6 min (planners run concurrently)
- **Worst-case with 2 re-loops:** ~18 min

Per-run cost roughly 2.25× Cast. Temper at depth 3 is ~1.3× Alloy. Alloy sits in the middle — breadth without iteration.

---

## 12 · Open questions (tracked, not blocking)

- **Q1:** Should the synthesizer itself run with extended thinking (`thinking_budget: xhigh`)? **Proposed:** Yes by default in v0.1.0. Revisit if latency is a blocker.
- **Q2:** Should N be adaptive (start at 3, expand if Momus score is low)? **Proposed:** No in v0.1.0 — user-controlled only.
- **Q3:** Should individual variant files persist after emit, or be deleted once synthesized? **Proposed:** Persist in `variants/` subdirectory — cheap, useful for debugging bias drift.

---

## 13 · Out of scope for v0.1.0

- CI/non-interactive mode
- Custom bias definitions (users cannot add bias "security-audit" in v0.1.0)
- Marketplace publication (local dev install only)
- Cross-run memory (each invocation is stateless in v0.1.0)

---

## 14 · Dependencies

- Claude Code CLI (`claude`)
- bash 4+
- python3 (plugin validator)
- `xargs -P` (GNU or BSD; BSD `xargs -P` on macOS is sufficient)

No Node.js. No Python packages beyond stdlib (`yaml` for `validate-plugin.py` only).

---

## 15 · Risk register

| Risk | Severity | Mitigation |
|------|----------|------------|
| Synthesizer produces incoherent blend (contradictions not resolved) | High | Hard rule 3 (directive > variant); Momus audits blend; Oracle coherence check |
| N parallel planners exceed harness concurrency | Medium | `xargs -P $(nproc)` caps; documented limit of N ≤ 7 |
| Variant bias drift (planners ignore assigned bias) | Medium | Explicit bias-enforcement clause in `agents/prometheus-alloy.md`; Synthesizer cross-checks |
| Synthesizer chooses wrong conservative default on contradictions | Low | Users can re-loop with `--loop`; conservative default is itself documented |

---

## 16 · Success metric

The plugin is **adopted** when a user runs Alloy instead of Cast for a task *and* ships what Alloy emits. In v0.1.0 we have no telemetry — success is anecdotal. Future versions will track adoption via optional `~/.anneal/telemetry.log` (opt-in).

---

## 17 · Shipping checklist

- [x] `.claude-plugin/plugin.json` valid JSON
- [x] `.claude-plugin/marketplace.json` valid JSON
- [x] 8 skills present with valid YAML frontmatter
- [x] 10 agents present with valid YAML frontmatter
- [x] 1 command present with valid YAML frontmatter
- [x] `scripts/validate-plugin.py` runnable with `python3` stdlib only + `pyyaml`
- [x] `scripts/orchestrate.sh` implements 7-stage pipeline with N parallel planners
- [x] `LICENSE` present (MIT)
- [x] Standalone HTML diagram present
- [x] All docs cross-linked
- [x] `validate-plugin.py` exits 0 on the plugin root
