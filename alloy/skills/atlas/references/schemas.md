# Atlas Schemas & Examples

## Input schema

```yaml
run_id: "anneal-YYYYMMDD-HHMMSS-{slug}"
architecture: "alloy"
task: "<verbatim user task>"
plan_files: ["plan/plan.md", "plan/phase-*.md"]
variants: ["variants/variant-1-*.md", ...]   # Alloy-specific — preserved for debugging
synthesis_provenance: "synthesis-provenance.md"
envelopes:
  metis: {...}
  momus: {...}
  redteam_security: {...}
  redteam_scope: {...}
  redteam_assumptions: {...}
  oracle: {...}
hephaestus_evidence: {...}
output_root: "~/Desktop/anneal-runs/{run_id}/"
```

## Rollup structure

```yaml
rollup:
  architecture: alloy
  run_id: anneal-YYYYMMDD-HHMMSS-{slug}
  overall_verdict: <worst across all reviewers>
  gate_status:
    metis: <verdict>
    momus: <verdict>
    red_team_trinity: "<N/3 PASS>"   # count non-BLOCK
    oracle: <verdict>
    hephaestus: PASS | FAIL
  simultaneous_pass: <bool>
  blocking_issues: [ ... deduped, severity-ordered from all envelopes ... ]
  emission_decision: EMIT | RE_LOOP | ABORT
  iteration_count: <int>
  tournament_stats:
    variant_count: <N>
    biases_participating: [...]
    biases_contributing_to_blend: [...]
    silent_rejections: <int>
    contradictions_resolved: <int>
```

## Decision logic (verbatim from `_shared/plan-reviewer-schema.md`)

- `EMIT` iff `simultaneous_pass == true` AND `overall_verdict in [SAFE, CAUTION]`
- `RE_LOOP` iff `simultaneous_pass == false` AND `iteration_count < max_iterations`
- `ABORT` iff `overall_verdict == BLOCK` AND cause is irreducible (Metis returned `clarifying_questions` the user must answer)

## Alloy `<metadata>` XML additions

Inside the root `<metadata>` element the emitter writes:

```xml
<tournament>
  <variants>N</variants>
  <biases>correctness,minimalist,defensive,performance,ux</biases>
  <silent_rejections>0</silent_rejections>
  <synthesis_provenance_ref>synthesis-provenance.md</synthesis_provenance_ref>
</tournament>
```

## Artifact layout

```
~/Desktop/anneal-runs/{run_id}/
  alloy-{run_id}.xml                     # Opus 4.7 semantic-XML emission
  plan/
    plan.md                              # overview
    phase-00-*.md … phase-NN-*.md        # one per blended phase
    fixtures/                            # optional
  variants/
    variant-1-{bias}.md … variant-N-{bias}.md
  synthesis-provenance.md
  reviews/
    metis-envelope.yaml
    momus-envelope.yaml
    redteam-{security,scope,assumptions}-envelope.yaml
    oracle-envelope.yaml
    hephaestus-evidence/
      step-NN-*.{txt,png,md}
      evidence-inventory.txt
  rollup.yaml
```

## Example summary output

```
Anneal-Alloy run complete.

run_id: anneal-20260422-1452-plugin-rewrite
architecture: alloy (tournament consensus, N=5)
verdict: CAUTION
emission: EMIT

files written:
  ~/Desktop/anneal-runs/anneal-20260422-1452-plugin-rewrite/
    alloy-anneal-20260422-1452-plugin-rewrite.xml
    plan/plan.md
    plan/phase-00-baseline.md through phase-11-ship.md
    variants/ (5 files)
    synthesis-provenance.md
    reviews/ (6 envelopes)
    reviews/hephaestus-evidence/ (23 files, 2.4 MB)
    rollup.yaml

tournament stats:
  variants: 5 (correctness, minimalist, defensive, performance, ux)
  contributing to blend: 4/5 (minimalist contributed 0 phases — flagged by Oracle as MINOR)
  contradictions resolved: 3
  silent rejections: 0

next step:
  Paste into a fresh Claude Code session:
    "Read ~/Desktop/anneal-runs/anneal-20260422-1452-plugin-rewrite/alloy-anneal-20260422-1452-plugin-rewrite.xml
     and execute the plan therein per the <instructions><next_action> block."
```
