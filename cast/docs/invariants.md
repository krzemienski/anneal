# The Eight Invariants

Every Anneal architecture — Cast, Alloy, Temper — satisfies the same eight invariants. They differ only in how stage 4 (Plan) is generated. The invariants are load-bearing: remove any one and the plugin stops being Anneal.

---

## 1. Red team always runs

Three parallel adversaries — Security, Scope, Assumptions. Not a flag. Cannot be disabled.

Refused flags:
- `--no-red-team` — logged and ignored
- `--skip-security` — logged and ignored

Rationale: the `deepest-plan` predecessor shipped 91 defects because its review was optional. Red team is the non-negotiable floor.

## 2. Validation always runs

Hephaestus builds and exercises the real artifact. No mocks, no test files, no stubs. Empty evidence equals FAIL.

Refused flags:
- `--no-validate` — logged and ignored

Rationale: compilation is not validation. "Build passed" is a necessary but insufficient signal.

## 3. Dual output

Every run produces both:
- an Opus 4.7 semantic-XML prompt (for the downstream execution session)
- a plan directory with markdown phase files (for human review)

Not one or the other. Both.

Rationale: the XML is the machine handoff; the plan directory is the human audit trail.

## 4. Skill enrichment

Probe phase scans `~/.claude/skills/` and the project's `.claude/skills/`. Matching skills are listed in the plan's `## Skill enrichment` section. The downstream execution session auto-invokes them.

Rationale: skills carry project-specific context the planner lacks. A plan that ignores available skills is leaving leverage on the table.

## 5. Unbounded re-loop on FAIL

If validate FAILs, route back to the plan stage with the failure as a new constraint. No iteration cap.

In Cast, the re-loop routes through Metis (not directly to Prometheus) — the failure is folded as a new directive.

Rationale: retrying the same planner with the same input produces the same plan. The interesting signal lives in the failure. Metis interprets it.

## 6. Parallelization by default

Red team, validators, and (in Alloy) planners fan out as concurrent agents.

In Cast, the only parallel stage is Red-Team Trinity at stage 5.

Rationale: sequential adversarial review lets earlier reviewers prime later ones. Parallel preserves independence.

## 7. Category routing, not model picking

User specifies work-type via `--type <category>` (`ultrabrain`, `deep`, `quick`). The harness maps the category to a model tier. Cast does not expose `--model opus` directly.

Rationale: model names churn; work-type categories do not. Insulate users from Anthropic model-version drift.

## 8. Dual prompts by model family

Every agent ships Claude-flavored prompts (long, mechanics-driven) AND GPT-flavored prompts (short, XML-tagged). Auto-detected at runtime.

In the Cast v0.1.0 release, all agents ship Claude-flavored prompts only. GPT-flavored prompts are a declared v0.2.0 deliverable.

Rationale: the same task produces different quality when prompted for Claude versus GPT. Don't force one prompt shape onto a model family it wasn't written for.

---

## How Cast enforces them

| Invariant | Enforcement point in Cast |
|-----------|---------------------------|
| 1. Red team always runs | `red-team-trinity` skill dispatches three agents at stage 5, non-optional |
| 2. Validation always runs | `hephaestus` skill runs at stage 6, non-optional |
| 3. Dual output | `atlas` skill emits both XML and plan directory |
| 4. Skill enrichment | Probe stage enumerates skills; `prometheus-cast` lists them in plan.md |
| 5. Unbounded re-loop | Orchestration layer routes FAIL → Metis → new iteration |
| 6. Parallelization | Red-Team Trinity is the parallel stage |
| 7. Category routing | `--type` flag maps to model tier (v0.2.0 scope) |
| 8. Dual prompts | Claude-flavored in v0.1.0; GPT-flavored planned for v0.2.0 |

## Invariant violations

If any invariant is broken, the plugin is no longer Anneal. Forks are welcome, but they should rename themselves. The invariants are the identity of the family.
