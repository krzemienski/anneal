---
name: red-team-trinity
description: "Three parallel adversarial agents — Security, Scope, Assumptions. In Temper SPECIFICALLY, the Trinity runs at EVERY depth of the deepen loop, not just once at the end. This is Temper's defining property: always-on inline red team. Triggers: invoked once per depth by deepen-loop. Keywords: red-team, adversarial, security, scope, assumptions, inline, every-depth, temper."
license: MIT
---

# Red-Team Trinity — Always-On Adversaries (Every Depth)

Three sibling agents. Always parallel. Always present. Each owns one adversarial angle.

## Temper-specific behavior

**In Cast:** Red Team runs once on a finished plan.
**In Alloy:** Red Team runs once after synthesizer blending.
**In Temper:** Red Team runs at **every depth of the deepen loop**.

This is Temper's defining property. Remove inline red team and Temper degenerates into Cast-with-retry. The reason: rewrites must be adversarially stress-tested before they become the input to the next depth. If red team only saw the final depth, early-depth weaknesses would flow uncontested into later rewrites.

At depth N, Red Team reviews `plan_N` — a full rewrite, not a diff. Each of the three agents runs independently and in parallel.

## Roster

### Red-Team-Security

Finds security failures in the plan. Secrets in plain text, injection paths, auth gaps, data exposure, supply chain, privilege escalation.

See `agents/redteam-security.md` for the full system prompt.

### Red-Team-Scope

Finds scope creep. Phases touching files the user didn't ask about, "while we're here" refactors, features beyond the stated task, gold-plating.

See `agents/redteam-scope.md` for the full system prompt.

### Red-Team-Assumptions

Finds load-bearing assumptions. API versions assumed stable, file paths assumed to exist, dependencies assumed installed, runtime environment assumptions, order-of-execution assumptions without guards, user-action assumptions without checkpoints.

See `agents/redteam-assumptions.md` for the full system prompt.

## Parallelization

The three agents MUST be spawned in a single parallel batch. The orchestrator (deepen-loop) issues three Task calls in one message, not sequentially.

## When to invoke

Stage 4 of every Temper run, **at every depth**, after Prometheus-Temper produces a plan and before Momus scores it. Spawned by deepen-loop.

## Input schema (per agent)

```yaml
depth: <N>
plan_path: "plans/plan_N.md"
plan_content: "<full markdown>"
prior_findings: null | [...]   # findings from depth N-1 of the same adversary
user_task: "<verbatim>"
```

## Output schema (per agent — each returns an envelope)

```yaml
reviewer: redteam-security | redteam-scope | redteam-assumptions
verdict: SAFE | CAUTION | RISKY | BLOCK
summary: "2-3 sentence assessment"
confidence: HIGH | MEDIUM | LOW
findings:
  - severity: CRITICAL | MAJOR | MINOR
    category: security | scope | assumption
    reviewer: redteam-{security|scope|assumptions}
    summary: "One-sentence description"
    evidence:
      - plan_file: "plan_N.md"
        line_range: "..."
        excerpt: "..."
    suggestion: "One-sentence direction"
    blocks_emission: true | false
blocking_issues_count: <integer>
```

## Verdict rules

- **Red-Team-Security:** Any CRITICAL finding → BLOCK. Any MAJOR → RISKY. 2+ MINOR → CAUTION.
- **Red-Team-Scope:** Mild creep → CAUTION. Substantial creep → RISKY. Total scope loss → BLOCK.
- **Red-Team-Assumptions:** >3 unguarded assumptions → RISKY. Any assumption that is load-bearing AND demonstrably false → BLOCK.

## Aggregation (how Red Team Trinity rolls up)

The orchestrator collects three envelopes and reports:
```
red_team_trinity: "3/3 PASS" | "2/3 PASS" | "1/3 PASS" | "0/3 PASS"
```
Where PASS means verdict ∈ {SAFE, CAUTION}. A single BLOCK from any member blocks emission — but Temper does NOT exit the loop on Red Team BLOCK; it folds the BLOCK into Prometheus-Temper's input for the next depth. Only after the deepen loop completes does the final depth's Red Team aggregate become a gate for Oracle.

## Prior-findings awareness (Temper-specific)

When `prior_findings` is non-null (i.e., depth N ≥ 1), each adversary receives the findings from its own prior-depth envelope. The adversary should:

- Explicitly note which prior findings are now resolved (with citation to the new plan).
- Explicitly note which prior findings persist (unchanged or insufficiently addressed).
- Flag any new findings introduced by the rewrite.

This gives the orchestrator a clear signal of whether the rewrite is genuinely progressing.

## Anti-patterns

- Do NOT run the three adversaries sequentially — they MUST be parallel.
- Do NOT share state between the adversaries. They are independent voices.
- Do NOT soften findings because the prior depth had them too. Persistent findings are a red flag, not a reason to downgrade severity.
- Do NOT aggregate the three envelopes inside one adversary. Each returns its own envelope; the orchestrator aggregates.
