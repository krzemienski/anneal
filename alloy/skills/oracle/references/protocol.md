# Oracle Protocol & Examples

## Input schema

```yaml
plan_files: ["plan/plan.md", "plan/phase-*.md"]
envelopes:
  metis: "reviews/metis-envelope.yaml"
  momus: "reviews/momus-envelope.yaml"
  redteam_security: "reviews/redteam-security-envelope.yaml"
  redteam_scope: "reviews/redteam-scope-envelope.yaml"
  redteam_assumptions: "reviews/redteam-assumptions-envelope.yaml"
synthesis_provenance: "synthesis-provenance.md"   # Alloy-specific context
```

## Output schema

```yaml
reviewer: oracle
verdict: SAFE | CAUTION | RISKY | BLOCK
summary: "2-3 sentence bird's-eye assessment"
confidence: HIGH | MEDIUM | LOW
release_coherence: |
  multi-line assessment of whether the plan tells a coherent story
deployment_risk: |
  specific concerns about what breaks if we ship tomorrow
breaking_changes:
  - "Enumerated breaking change 1"
  - "..."
  # OR: ["None"]
monitoring_recommendations:
  - "Watch metric X after deploy"
  - "..."
findings: [...]    # deduped across all prior reviewers, severity-ordered
blocking_issues_count: <integer>
```

## Synthesis protocol

### Step 1 · Aggregate findings

Read all five prior envelopes. Dedupe findings that describe the same issue from different angles. A single issue may surface in Momus (ambiguity) and Red-Team-Assumptions (unguarded assumption) — collapse to one finding in Oracle's output with both reviewers cited.

### Step 2 · Compute overall verdict

Overall verdict is the **worst** verdict across all reviewers. Oracle can escalate:

- Momus CAUTION + 2+ Red-Team CAUTION → Oracle may return RISKY (synergy of concerns).
- Metis SAFE but Momus + Red-Team together produced 4+ MAJOR findings → RISKY.
- Oracle **cannot downgrade** any reviewer's verdict. BLOCK stays BLOCK.

### Step 3 · Release coherence

Ask:
- Does the plan tell one coherent story, or does it read like 5 separate variants stapled together?
- Does synthesis-provenance show genuine composition, or a single-variant win with N-1 wasted spawns?
- Are the Iron Rules inherited consistently across phases?

For Alloy specifically, coherence failure often traces to Synthesizer drift. If provenance shows silent contradictions, Oracle notes this in `release_coherence`.

### Step 4 · Deployment risk

Ask:
- What breaks if we ship this tomorrow, as-is?
- Which phase has the largest blast radius?
- What's the cost of migration for existing users?
- What is the rollback path?

Enumerate concerns. Cite specific phase + line when possible.

### Step 5 · Breaking changes

List every breaking change. `"None"` is valid if the plan genuinely breaks nothing. Otherwise exhaustive.

### Step 6 · Monitoring recommendations

After ship, what should be watched? E.g. "monitor error rate on /api/plan for 24h" or "watch for `synthesis-provenance.md` files where all phases cite one variant — indicates bias drift."

## Alloy-specific checks

Oracle has unique visibility into tournament integrity. Two checks only possible at Oracle's stage:

### Check A · Tournament value

Compute the fraction of phases where the synthesized output differs meaningfully from any single variant. If <30%, the tournament added no synthesis value. Flag as MAJOR category=coherence.

### Check B · Bias coverage

For each of the N biases that participated, count phases where that bias contributed (per provenance). If any bias contributed to zero phases, that is either an under-informed variant (fix via re-loop with stronger directives) or a bias with no relevant input (flag as MINOR — diagnostic only).

## Verdict decision table

| Conditions | Verdict |
|-----------|---------|
| Zero blocking issues; all prior SAFE; coherence HIGH | SAFE |
| Prior worst is CAUTION; no CRITICAL; 1-3 MAJOR total | CAUTION |
| Prior worst is RISKY OR 4+ MAJOR total | RISKY |
| Any prior BLOCK OR any CRITICAL unresolved | BLOCK |

## Example envelope

```yaml
reviewer: oracle
verdict: CAUTION
summary: |
  Plan is coherent; red team raised 2 MAJOR findings. Tournament value is solid
  (60% of phases show genuine blend). One bias contributed to zero phases —
  diagnostic but not blocking.
confidence: HIGH
release_coherence: |
  The synthesized plan reads as one coherent artifact. Phase ordering follows
  dependency chain. Iron Rules consistently applied. Synthesis provenance
  documents all 3 contradictions resolved via conservative default + directive
  match.
deployment_risk: |
  Phase 04 assumes xargs -P GNU semantics; BSD semantics differ on macOS.
  Mitigated by fallback to sysctl -n hw.ncpu. No other deploy-blocking risks.
  Blast radius: Synthesizer failure would cause Stage 4 to produce empty plan.
breaking_changes:
  - "Replaces deepest-plan v1.0.0 — users must migrate via docs/migration.md"
  - "Removes judge-with-debate skill (redundant with Momus + Red Team)"
monitoring_recommendations:
  - "Watch synthesis-provenance.md for bias-collapse (one variant contributes >80%)"
  - "Track N-parallel planner completion variance — >30% variance suggests bias drift"
findings:
  - severity: MAJOR
    category: assumption
    reviewer: oracle
    summary: "Phase 04 xargs -P semantics"
    evidence:
      - plan_file: "plan/phase-04-intent-gate.md"
        line_range: "22"
        excerpt: "xargs -P $(nproc)"
    suggestion: "Use sysctl -n hw.ncpu fallback."
    blocks_emission: false
  - severity: MINOR
    category: coherence
    reviewer: oracle
    summary: "ux bias contributed zero phases in this blend."
    evidence:
      - plan_file: "synthesis-provenance.md"
        line_range: "varies"
        excerpt: "ux not cited in any phase"
    suggestion: "Either the task had no UX dimension, or the ux planner drifted. Not blocking."
    blocks_emission: false
blocking_issues_count: 0
```
