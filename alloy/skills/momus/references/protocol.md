# Momus Protocol & Examples

## Input schema

```yaml
plan_files:
  - "plan/plan.md"
  - "plan/phase-00-scaffold.md"
  - "plan/phase-01-...md"
  # ... all blended phase files
provenance: "synthesis-provenance.md"
metis_directives: [...]
```

## Output schema (per `_shared/plan-reviewer-schema.md`)

```yaml
reviewer: momus
verdict: SAFE | CAUTION | RISKY | BLOCK
summary: "2-3 sentence direct assessment — not diplomatic"
confidence: HIGH | MEDIUM | LOW
findings:
  - severity: CRITICAL | MAJOR | MINOR
    category: ambiguity | scope | security | assumption | coherence | missing-evidence
    reviewer: momus
    summary: "One-sentence description"
    evidence:
      - plan_file: "plan/phase-03-synth.md"
        line_range: "45-58"
        excerpt: "...actual text..."
    suggestion: "Direction, not fix"
    blocks_emission: true | false
blocking_issues_count: <integer>
```

## Audit protocol

For every phase in the plan, ask:

1. **What's missing?** An implementer would need X and X is absent. (category: missing-evidence)
2. **What's ambiguous?** Two readers would interpret this differently. (category: ambiguity)
3. **What's assumed?** An assumption is baked in that has not been validated. (category: assumption)
4. **What fails off happy-path?** The plan assumes success at every step with no fallback. (category: coherence)
5. **What leaks scope?** This phase touches something the task did not ask about. (category: scope)
6. **What exposes the system?** Secrets, injection, unbounded output, privilege escalation. (category: security)

Every phase MUST have at least one finding unless the plan is genuinely pristine (rare — expect zero-finding phases <10% of real runs).

## Alloy-specific addendum

Momus reads the synthesized plan PLUS provenance, giving unique visibility into synthesis-quality issues.

### Check 1 · Attribution sanity

For each phase in the plan:
- Does the provenance entry cite ≥1 variant?
- Does the cited variant's bias explain the chosen approach? (e.g. Overview citing `defensive` → does Overview actually reflect a defensive lens?)
- Are contradictions documented or silently resolved?

If a phase's provenance shows "contributed nothing" from all but one variant, flag as MAJOR category=coherence — that is not a tournament, that is a single planner with N-1 wasted spawns.

### Check 2 · Bias collapse

If the blended plan is ~100% from one variant, the tournament had no synthesis value. Flag as MAJOR category=coherence. Diagnostic for bias-drift in Prometheus-Alloy.

### Check 3 · Contradiction persistence

Every contradiction logged in `synthesis-provenance.md § Contradictions resolved` should either:
- Trace to a Metis directive (good), OR
- Have triggered the conservative default (documented), OR
- Be flagged by Momus as MAJOR if silently resolved.

### Check 4 · Phase count reasonableness

The Synthesizer cannot add novel phases. If the output has <3 phases (all variants under-scoped) or >20 phases (variants over-scoped + Synthesizer failed to collapse redundancy), flag MAJOR.

## Verdict decision table

| Conditions | Verdict |
|-----------|---------|
| Zero findings; every phase pristine; attribution clean | SAFE |
| 1-3 MINOR findings; no CRITICAL | SAFE |
| 1+ MAJOR finding, no CRITICAL, ≤3 MAJOR total | CAUTION |
| 4+ MAJOR findings OR 1-2 MAJOR that touch Iron Rules | RISKY |
| Any CRITICAL finding | BLOCK |
| Any finding with `blocks_emission: true` | BLOCK |

## Example envelope

```yaml
reviewer: momus
verdict: CAUTION
summary: Plan is coherent and the synthesis traces. Two assumptions are load-bearing and unguarded. One phase collapses to a single variant with 3 other variants rejected silently.
confidence: HIGH
findings:
  - severity: MAJOR
    category: coherence
    reviewer: momus
    summary: "Phase 05 Synthesizer step cites only variant 1; provenance shows 4 other variants rejected with no explanation."
    evidence:
      - plan_file: "synthesis-provenance.md"
        line_range: "34-41"
        excerpt: "Contributing variants: 1. Rejected elements: (none documented)"
    suggestion: "Either document why 2-5 contributed nothing, or re-run the Synthesizer — silent rejection breaks the tournament rationale."
    blocks_emission: false
  - severity: MAJOR
    category: assumption
    reviewer: momus
    summary: "Phase 03 assumes xargs -P is GNU; on macOS BSD xargs has different semantics."
    evidence:
      - plan_file: "plan/phase-03-parallel-planners.md"
        line_range: "22"
        excerpt: "xargs -P $(nproc)"
    suggestion: "Use sysctl -n hw.ncpu as fallback; BSD xargs -P is supported on macOS."
    blocks_emission: false
blocking_issues_count: 0
```
