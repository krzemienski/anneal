# Red-Team Trinity Adversary Detail

## Input schema (each adversary)

```yaml
plan_files:
  - "plan/plan.md"
  - "plan/phase-*.md"
metis_envelope: "reviews/metis-envelope.yaml"
momus_envelope: "reviews/momus-envelope.yaml"
output_path: "reviews/redteam-{role}-envelope.yaml"
role: "security" | "scope" | "assumptions"
```

## Output schema (per adversary, per `_shared/plan-reviewer-schema.md`)

```yaml
reviewer: redteam-security | redteam-scope | redteam-assumptions
verdict: SAFE | CAUTION | RISKY | BLOCK
summary: "2-3 sentence assessment from this angle"
confidence: HIGH | MEDIUM | LOW
findings: [...]
blocking_issues_count: <integer>
```

## Red-Team-Security

**Attack surface:**
- Secrets in plain text (env vars, config files, logs, example snippets).
- Injection paths (SQL, shell, XML, command, path traversal).
- Auth / authz gaps (missing checks, broken roles, over-broad reads).
- Data exposure (unbounded output, logging PII, no redaction).
- Supply chain (unpinned deps, vendored code from untrusted sources).
- Privilege escalation (plan creates a path to more access than declared).

**Verdict rules:**
- Any CRITICAL finding → BLOCK.
- Secrets in plan text → BLOCK, always.
- 2+ MAJOR findings → RISKY.
- 1 MAJOR → CAUTION.

## Red-Team-Scope

**Attack surface:**
- Phases that touch files the user did not mention.
- "While we're here" refactors outside stated scope.
- Features added beyond the stated task.
- Infrastructure changes (hooks, CI, config) not implied by the task.
- Gold-plating — polish without stated requirement.
- Architectural changes when a local fix would suffice.

**Alloy-specific note.** Because the plan is blended from N biased variants, scope creep can enter through any one variant and survive synthesis. Check `synthesis-provenance.md` — if a phase traces to only the `ux` variant and introduces status-line infra the user did not ask for, that is scope creep even if the variant's bias "justified" it.

**Verdict rules:**
- Mild creep (1 phase, justified by tangential directive) → CAUTION.
- Substantial creep (2-3 phases, not justified by directive) → RISKY.
- Total scope loss (plan rewrites unrelated systems) → BLOCK.

## Red-Team-Assumptions

**Attack surface:**
- API versions assumed stable ("Opus 4.7 XML spec," "xargs -P behavior").
- File paths assumed to exist without a guard.
- Dependencies assumed installed (bash 4+, python3, specific CLI versions).
- Runtime environment (OS, shell, node/bun/python versions).
- Order-of-execution assumptions with no guard.
- User-action assumptions ("user will run X after this").

**Alloy-specific note.** Synthesis can amplify assumptions — a phase that survives the blend because 3 variants all assumed `xargs -P` GNU semantics is a **stronger** signal than 1 variant making the assumption, not a weaker one. Cite the provenance when the assumption is reinforced across variants.

**Verdict rules:**
- >3 unguarded load-bearing assumptions → RISKY.
- Any assumption demonstrably false (e.g. plan assumes file X exists when probe confirmed absence) → BLOCK.
- 1-3 assumptions, well-scoped → CAUTION.

## Why parallel is load-bearing

Sequential red team lets later adversaries anchor on earlier findings. Parallel prevents that. Every adversary sees the plan fresh, with no prior-finding influence, ensuring the three angles remain orthogonal.

This is the oh-my-openagent pattern — the pre-publish-review skill runs three layers parallel for the same reason.

## Example: Red-Team-Security envelope

```yaml
reviewer: redteam-security
verdict: CAUTION
summary: "No secrets leaked. Shell commands in phase 04 are unquoted — injection risk if user task contains shell metachars. Dep versions pinned."
confidence: HIGH
findings:
  - severity: MAJOR
    category: security
    reviewer: redteam-security
    summary: "Phase 04 interpolates $1 directly into bash eval."
    evidence:
      - plan_file: "plan/phase-04-intent-gate.md"
        line_range: "15-18"
        excerpt: 'bash -c "echo $1"'
    suggestion: "Quote the argument and use printf %s or $@ addressing."
    blocks_emission: false
blocking_issues_count: 0
```
