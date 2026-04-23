---
name: red-team-trinity
description: "Always-on adversarial trio for anneal-cast. Spawns three parallel sub-agents — redteam-security, redteam-scope, redteam-assumptions — that read the finished plan independently and return three envelopes. The skill does NOT synthesize; oracle does that. Triggers: invoke at stage 5 of every /anneal-cast:anneal run; always parallel, always all three, never skipped. Do NOT collapse into one combined red-team agent, do NOT launch sequentially (kills independence), and do NOT synthesize here (oracle owns synthesis at stage 5 close-out)."
license: MIT
---

# Red-Team Trinity — Always-On Adversaries

## Purpose

The adversarial gate. Three perspectives, three independent agents, three envelopes, one parallel launch.

Each member owns one angle:
- **Security** — what fails under hostile input or access
- **Scope** — where the plan creeps beyond the stated task
- **Assumptions** — what load-bearing beliefs the plan bakes in

The trio runs in parallel so that no member primes another. Their envelopes are independent.

## When to invoke

- Stage 5 of every anneal run
- Always. Non-negotiable. No flag disables this.
- Always parallel. Sequential invocation invalidates the independence guarantee.

## Input schema

```yaml
plan_dir: /path/to/staging/plan/
task: "<verbatim user task>"
metis_envelope: { ... }
momus_envelope: { ... }
```

## Output schema

Three envelopes, one per member:

```yaml
- reviewer: redteam-security
  verdict: SAFE | CAUTION | RISKY | BLOCK
  summary: "..."
  confidence: HIGH | MEDIUM | LOW
  findings: [ ... ]
  blocking_issues_count: <int>

- reviewer: redteam-scope
  ...

- reviewer: redteam-assumptions
  ...
```

## Dispatch pattern

The skill orchestrates three sub-agent launches:

1. Launch `redteam-security` agent. Input: plan + task.
2. Launch `redteam-scope` agent. Input: plan + task + Metis directives.
3. Launch `redteam-assumptions` agent. Input: plan + task + probe report.

Use the `launch-sub-agent` primitive when present (see `docs/worked-example.md` for the expected vendoring); otherwise dispatch via the Task tool with three parallel calls. All three launches MUST be issued in the same tool-call batch — serial launches invalidate the independence guarantee.

Wait for all three to complete before returning. Partial output is not accepted.

## Per-member focus

### redteam-security

Look for:
- Secrets in plain text (env vars, config, logs)
- Injection paths (SQL, shell, XML, command)
- Auth/authz gaps (missing checks, broken roles)
- Data exposure (over-broad reads/writes, unbounded output)
- Supply chain (unpinned dependencies, unvendored code from untrusted sources)
- Privilege escalation (plan creates path to more access than declared)

Verdict BLOCK on any CRITICAL finding.

### redteam-scope

Look for:
- Phases that touch files the user did not ask about
- "While we're here" refactors
- Features added beyond the stated task
- Infrastructure changes (hooks, CI, config) not implied by the task
- Gold-plating (polish without stated requirement)

Verdict CAUTION for mild creep, RISKY for substantial, BLOCK for total scope loss.

### redteam-assumptions

Look for:
- API versions the plan assumes are stable
- File paths the plan assumes exist
- Dependencies the plan assumes are installed
- Runtime environment assumptions (OS, shell, language versions)
- Order-of-execution assumptions with no guard
- User-action assumptions ("user will..." without checkpoint)

For every assumption found, cite phase + line and state what fails if the assumption is wrong.

Verdict RISKY if >3 unguarded assumptions, BLOCK if any load-bearing assumption is demonstrably false.

## Rules

1. Never skip a member. All three run on every plan.
2. Never run sequentially. Parallel launch is the independence guarantee.
3. Never synthesize here. This skill returns three envelopes; Oracle reads them together at stage 5 close-out.
4. Refused flags: `--no-red-team`, `--skip-security`, etc. are logged and ignored.

## Anti-patterns

- Collapsing the trio into a single "red-team" agent with three prompts (loses independence).
- Running one member, finding nothing, and skipping the others.
- Waiting for one member to finish before launching the next.

## Agent binding

This skill spawns three agents:
- `redteam-security` (`agents/redteam-security.md`) · model=sonnet
- `redteam-scope` (`agents/redteam-scope.md`) · model=sonnet
- `redteam-assumptions` (`agents/redteam-assumptions.md`) · model=sonnet

Sonnet is the correct tier — adversarial review is pattern-matching, not architectural reasoning.
