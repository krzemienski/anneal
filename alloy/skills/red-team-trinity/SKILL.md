---
name: red-team-trinity
description: "Three always-on adversaries — Security, Scope, Assumptions — that audit the synthesized anneal-alloy plan from three orthogonal angles. Spawned in parallel, never sequentially; blind to each other's findings until Oracle synthesizes. Returns one envelope per adversary at reviews/redteam-{security,scope,assumptions}-envelope.yaml. Non-negotiable — not a flag. The only way to skip red team is to not run anneal. Triggers: invoke at stage 5 of every anneal-alloy run, immediately after the Momus envelope is persisted; all three members spawn concurrently."
license: MIT
---

# Red-Team Trinity — Always-On Adversaries

## Purpose

Three adversarial reviewers auditing the same synthesized plan from three orthogonal angles — parallel, never sequential — so no adversary anchors on another's findings.

## When to invoke

- Stage 5 of every anneal-alloy run, immediately after Momus's envelope is persisted.
- All three members spawn simultaneously via `xargs -P` or equivalent parallel launcher.
- The orchestrator waits for all three envelopes before invoking Oracle.

## When NOT to use

- Do not invoke sequentially. Parallel spawn is a load-bearing invariant; sequential execution destroys orthogonality.
- Do not invoke individual adversaries separately. Trinity is atomic — all three or none.
- Do not invoke outside stage 5. Red team audits the blended plan, not variants, not raw tasks.
- Do not invoke on RISKY or BLOCK from Momus — loop back to planning first.

## The three adversaries

Each attacks only its assigned angle. Full attack-surface catalogs, verdict rules, and Alloy-specific notes: `references/adversaries.md`.

- **Red-Team-Security** — secrets in plain text, injection paths, authz gaps, data exposure, supply chain, privilege escalation. BLOCK on any CRITICAL or any secret in plan text.
- **Red-Team-Scope** — files the user did not mention, "while we're here" refactors, unrequested infra, gold-plating. CAUTION on mild creep, RISKY on 2-3 phase creep, BLOCK on total scope loss. On Alloy, check `synthesis-provenance.md` — creep can enter through one variant and survive synthesis.
- **Red-Team-Assumptions** — API version assumptions, missing path guards, dependency version assumptions, runtime-env assumptions, order-of-execution assumptions, user-action assumptions. RISKY on >3 unguarded, BLOCK if any assumption is demonstrably false. On Alloy, an assumption reinforced across variants is a stronger signal, not weaker.

## Hard rules (all three)

1. Run in parallel. No adversary sees another's output during execution.
2. Never coordinate. Each is blind to the others' findings until Oracle synthesizes.
3. Cite evidence on every finding — `plan_file`, `line_range`, `excerpt`.
4. Never fix. Only flag.
5. BLOCK is absolute. If any adversary returns BLOCK, Oracle sees it; Oracle cannot overturn BLOCK, only accept or escalate.

## Anti-patterns

- Never return SAFE as a default "nothing obviously wrong" verdict. If you could not find anything, confidence is MEDIUM or LOW, not HIGH.
- Never attack outside your assigned angle. Security does not do scope. Scope does not do security. Overlap is Oracle's job.
- Never flag the same issue across multiple adversaries. If Security flagged a secret, Scope does not re-flag it as "new infrastructure the user did not ask for." Stay in lane.
- Never refuse to return an envelope. Even a SAFE verdict with zero findings is a valid envelope.
- Never anchor on Momus's envelope. Red-team reads Momus for context only; the adversarial attack is fresh.
- Never read peer red-team envelopes even if they appear in input. The input schema lists only `metis_envelope` and `momus_envelope`; any `redteam-*-envelope.yaml` in the working directory was written by a peer and must be ignored until Oracle synthesizes. Reading a peer envelope collapses orthogonality.

## Why parallel is load-bearing

Sequential red team lets later adversaries anchor on earlier findings. Parallel keeps the three angles orthogonal. This is the oh-my-openagent pre-publish-review pattern — three layers running in parallel for the same reason.

## References

- `references/adversaries.md` — full input/output schemas, attack surfaces, verdict rules, Alloy-specific notes for Scope and Assumptions, and a full example envelope.
- `_shared/plan-reviewer-schema.md` — envelope and rollup definitions.
- `_shared/agent-prompts-core.md § Red-Team Trinity` — base system prompts for each adversary.
- Sibling skills: `momus` (audits the blend first), `oracle` (synthesizes all red-team envelopes).
