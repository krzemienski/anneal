# Anneal

> Controlled heating, slow cooling, iterative tempering — applied to work plans.

🌐 **Live site:** [anneal.withagents.dev](https://anneal.withagents.dev)

**Runtime status (2026-04-22):** Cast pipeline verified end-to-end in a real Claude Code worker — all 9 Greek-god agents dispatched, artifact written with exact byte match, XML emitted and passes `validate-xml.py`. See [`VERIFICATION-SUMMARY.md`](./VERIFICATION-SUMMARY.md) for the full trace. Alloy and Temper passed load verification; full E2E runs in progress.

**Anneal** is a Claude Code plugin family that converts a vague task into a rigorously-reviewed execution artifact: an XML prompt, a plan directory, and the skill enrichment needed to run it. It replaces the earlier `deepest-plan` prototype (shipped with 91 validator defects due to asymmetric vendoring) with a cleaner core built around three named plan-review archetypes — **Metis**, **Momus**, **Oracle** — and an always-on red team.

The name is literal: the plugin implements simulated annealing against plan-quality scores. Heat (generate candidates), cool (score, prune), temper (red-team critique), repeat until convergence.

Rather than picking one architecture as the default, we ship **three complete, installable plugin variants** — one per architecture — so you can install all three and compare side-by-side on real tasks.

---

## What this directory contains

| Path | What it is |
|------|-----------|
| `README.md` | You are here. |
| `ARCHITECTURE-PROPOSALS.md` | The architecture document (499 lines, 17 sections). Shared invariants, seven-stage spine, agent roster, three proposals. |
| `COMPARISON-PLAYBOOK.md` | How to test Cast / Alloy / Temper head-to-head. Decision rubric. |
| `INSTALL.md` | Install cheatsheet. Umbrella or per-plugin marketplace. |
| `diagrams/anneal-architectures.html` | Shared visual. Three Mermaid flowcharts with zoom/pan, editorial aesthetic. |
| `.claude-plugin/marketplace.json` | Umbrella dev marketplace listing all three plugins. |
| `cast/` | **Plugin · anneal-cast** · Linear single-pour architecture. |
| `alloy/` | **Plugin · anneal-alloy** · Tournament consensus architecture. |
| `temper/` | **Plugin · anneal-temper** · Fixed-point deepen architecture. |
| `_shared/` | Reference docs consumed by all three plugins (Opus 4.7 XML schema, agent prompts, plan-reviewer schema, plugin-format cheatsheet). |
| `scripts/smoke-test.sh` | Cross-plugin validation gate. Runs each plugin's `validate-plugin.py` and reports pass/fail. |
| `scripts/phase-4-review-prompts.md` | Staged reviewer prompts (architect + code-reviewer) for multi-perspective audit. |

Each of the three plugin directories (`cast/`, `alloy/`, `temper/`) is a complete, installable Claude Code plugin:

```
{architecture}/
├── .claude-plugin/plugin.json        # Manifest
├── .claude-plugin/marketplace.json   # Per-plugin dev marketplace
├── README.md                         # Install + usage
├── PRD.md                            # Architecture-specific product requirements
├── ARCHITECTURE.md                   # Implementation detail
├── LICENSE                           # MIT
├── commands/anneal.md                # /anneal-{name}:anneal slash command
├── skills/{7-8 skills}/SKILL.md      # Metis, Prometheus variant, Momus, Red-Team Trinity, Oracle, Hephaestus, Atlas
├── agents/{9 agents}.md              # Agent definitions with model assignments
├── hooks/hooks.json                  # SessionStart: plugin-loaded marker
├── scripts/validate-plugin.py        # Self-validation
├── scripts/orchestrate.sh            # Pipeline implementation
├── diagrams/{name}-architecture.html # Architecture-specific visual
└── docs/                             # Invariants, worked example, emission format
```

---

## Quick start

**Install all three**, restart Claude Code, and all three commands register:

```bash
# Add the umbrella marketplace
/plugin marketplace add /Users/nick/Desktop/anneal

# Install all three
/plugin install anneal-cast@anneal-umbrella-dev
/plugin install anneal-alloy@anneal-umbrella-dev
/plugin install anneal-temper@anneal-umbrella-dev
```

After restart, three slash commands are available:

```
/anneal-cast:anneal <task>         # Linear · ~8 spawns · ~4 min
/anneal-alloy:anneal <task>        # Tournament · ~18 spawns · ~6 min · default --versions 5
/anneal-temper:anneal <task>       # Fixed-point deepen · ~8×depth spawns · ~7 min · default --depth 3
```

Full install options, debugging, uninstall: see [`INSTALL.md`](./INSTALL.md).

---

## The three architectures at a glance

All three satisfy the same eight invariants (red team always, validate always, XML + plan output, skill enrichment, unbounded re-loop, parallelization, category routing, dual-family prompts). They differ only in how stage 4 — **Plan** — works.

| Name | Stage 4 behavior | Cost | Best for |
|------|-----------------|------|----------|
| **Cast** (linear) | One planner, one pass | ~8 spawns | Bug fixes, refactors, clear scope |
| **Alloy** (tournament) | N parallel planners → synthesizer blends | ~18 spawns | Novel architecture, greenfield |
| **Temper** (fixed-point) | Iterative refinement, variance convergence | ~8 × depth | Complex but scoped, iterative |

Each is a complete plugin with its own PRD, architecture doc, skills, agents, orchestration script, HTML diagram, and validation tooling. Install them all; compare.

---

## How to read this repository

**Three reading passes, three time budgets.**

**90-second scan:** open `diagrams/anneal-architectures.html`. Three flowcharts side-by-side. Scroll to comparison matrix.

**Fifteen-minute read:** `ARCHITECTURE-PROPOSALS.md` cover to cover. Positioning section names the lineage (Aider + Ralph + oh-my-openagent). The plan-reviewer output schema is the concrete "flag" format.

**Hands-on compare:** `INSTALL.md` to install all three, then `COMPARISON-PLAYBOOK.md` for the testing framework. Pick one task, run it through all three, measure.

---

## Prior art

- **[oh-my-openagent](https://github.com/code-yeongyu/oh-my-openagent)** — Anneal's Greek-god agent taxonomy (Metis, Momus, Oracle, Prometheus, Hephaestus, Atlas) is directly adapted from oh-my-openagent's system. Verdict tiers (SAFE / CAUTION / RISKY / BLOCK) and the parallel-agent review pattern (with `run_in_background=true`) are borrowed wholesale.
- **[Aider](https://aider.chat/)** — Terminal-first ergonomics, zero-ceremony invocation. Anneal is plan-first rather than edit-first, but shares the "just type and go" philosophy.
- **[Ralph](https://github.com/gheorghe-ciubuc/ralph)** — The unbounded-re-loop discipline. "The boulder never stops." Anneal's stage-7 simultaneous-pass gate trinity is Ralph-shaped.
- **[SADD](https://github.com/Yeachan-Heo/context-engineering-kit)** — The primitive vocabulary (launch-sub-agent, do-in-parallel, do-and-judge, tree-of-thoughts) that Temper in particular composes.
- **[ValidationForge](https://github.com/krzemienski/validationforge)** — Anneal's validation family: `functional-validation`, `create-validation-plan`, `verdict-writer`, `preflight`. Hephaestus is its embodiment.

---

## Status

All three plugin variants are built and structurally valid. The smoke test (`scripts/smoke-test.sh`) gates the umbrella install. The comparison playbook describes how to pick the right architecture for a given task class.

To pick a default for yourself: install all three, run the canonical comparison task (rewriting a real plugin, or whatever is your hardest standing task), and see which emits the cleanest plan at the cost you can afford.
