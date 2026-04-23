# Plan-Reviewer Output Schema

Every reviewer agent (Metis, Momus, Red-Team Trinity members, Oracle) returns envelopes in this format. Atlas aggregates them into a rollup at stage 7.

## Per-finding record

```yaml
- severity: CRITICAL | MAJOR | MINOR
  category: ambiguity | scope | security | assumption | coherence | missing-evidence
  reviewer: metis | momus | redteam-security | redteam-scope | redteam-assumptions | oracle
  summary: "One-sentence description"
  evidence:
    - plan_file: "phase-04-vendor-skills.md"
      line_range: "45-58"
      excerpt: "...actual text..."
  suggestion: "One-sentence direction, not a fix"
  blocks_emission: true | false
```

## Reviewer envelope

```yaml
reviewer: metis
verdict: SAFE | CAUTION | RISKY | BLOCK
summary: "2-3 sentence assessment"
confidence: HIGH | MEDIUM | LOW
findings: [ ... per-finding records ... ]
blocking_issues_count: <integer>
# Momus-only additional field:
score: 0-100   # only in Temper architecture
# Metis-only additional field:
directives: ["imperative sentence 1", "imperative sentence 2", ...]
clarifying_questions: []  # populated only if verdict is BLOCK
```

## Rollup (Atlas stage 7)

```yaml
rollup:
  architecture: cast | alloy | temper
  run_id: anneal-YYYYMMDD-HHMMSS-{slug}
  overall_verdict: SAFE | CAUTION | RISKY | BLOCK
  gate_status:
    metis: SAFE | CAUTION | RISKY | BLOCK
    momus: SAFE | CAUTION | RISKY | BLOCK
    red_team_trinity: "N/3 PASS"
    oracle: SAFE | CAUTION | RISKY | BLOCK
    hephaestus: PASS | FAIL
  simultaneous_pass: true | false
  blocking_issues: [ ... deduped, severity-ordered ... ]
  emission_decision: EMIT | RE_LOOP | ABORT
  iteration_count: <integer>
```

## Decision logic

- `EMIT` iff `simultaneous_pass == true` AND `overall_verdict in [SAFE, CAUTION]`
- `RE_LOOP` iff `simultaneous_pass == false` AND `iteration_count < max_iterations`
- `ABORT` iff `overall_verdict == BLOCK` AND cause is irreducible (Metis returned clarifying_questions that user must answer)

## Severity escalation rules

- Any finding with `severity: CRITICAL` → reviewer verdict is at least RISKY.
- Any finding with `blocks_emission: true` → reviewer verdict is BLOCK.
- 3+ MAJOR findings in one envelope → reviewer verdict at least CAUTION.
- Metis-specific: if `clarifying_questions` non-empty → verdict must be BLOCK.

## Overall-verdict aggregation

The rollup's `overall_verdict` is the **worst** verdict across all reviewers. If any reviewer returned BLOCK, overall is BLOCK regardless of other verdicts.
