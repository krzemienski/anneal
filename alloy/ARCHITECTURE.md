# Architecture — anneal-alloy

> One page. Tournament Consensus. N biased planners, one synthesized plan.

```
┌─────────────┐
│ Intent Gate │  Stage 1 — classify task, reject unsafe
└──────┬──────┘
       ↓
┌─────────────┐
│   Probe     │  Stage 2 — scan repo, enumerate skills (~/.claude/skills/*, .claude/skills/*)
└──────┬──────┘
       ↓
┌─────────────┐
│   Metis     │  Stage 3 — pre-plan directives + slop-risk flags (opus)
└──────┬──────┘
       ↓
┌─────────────────────────────────────────────────┐
│  STAGE 4 — PLAN (Tournament)                    │
│                                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│  │Prometheus│ │Prometheus│ │Prometheus│  ...    │
│  │  bias=1  │ │  bias=2  │ │  bias=N  │        │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘        │
│       │ parallel (xargs -P)     │               │
│       └──────┬──────────────────┘               │
│              ↓                                   │
│        ┌──────────┐                              │
│        │Synthesizer│  reads N plans, composites  │
│        └────┬──────┘                              │
└─────────────┼───────────────────────────────────┘
              ↓
       ┌──────────┐
       │  Momus   │   audits the BLEND, not individuals (opus)
       └────┬─────┘
            ↓
┌──────────────────────────────────────────┐
│  STAGE 5 — REVIEW (parallel)             │
│                                          │
│  ┌───────┐ ┌───────┐ ┌───────┐          │
│  │Security│ │ Scope │ │Assump.│          │
│  └───┬───┘ └───┬───┘ └───┬───┘          │
│      └────┬────┴─────────┘               │
│           ↓                              │
│       ┌────────┐                         │
│       │ Oracle │  bird's-eye (opus)      │
│       └────┬───┘                         │
└────────────┼─────────────────────────────┘
             ↓
       ┌───────────┐
       │Hephaestus │  Stage 6 — build + run + evidence
       └────┬──────┘
            │
   PASS ────┴──── FAIL
    ↓              │
┌───────┐          │
│ Atlas │ Stage 7  │ re-loop to Intent Gate
│ EMIT  │          │ (not to Synthesizer — failed synthesis
└───┬───┘          │  suggests bias mix was wrong)
    ↓              ↓
 XML + plan/   constraints += {FAIL}
               → back to Stage 1
```

## Why route back to Intent Gate on FAIL

In **Cast** the failure routes back to the single planner — there's nowhere else for it to go.

In **Temper** the failure routes back to the seed planner of the deepen loop — the convergence machinery is still intact.

In **Alloy** a validation failure is a signal that the *blend itself* didn't survive contact with reality. That's not a bug in any one variant — it means the bias mix was wrong, or the Synthesizer's contradiction resolution was wrong, or Metis's directives missed a key constraint. Re-running the Synthesizer on the same variants would produce the same blend. Re-running individual variants doesn't help either — they already gave their best shot.

The only useful lever is **regenerate the whole tournament with the failure as a new Metis constraint.** This is why FAIL → Intent Gate in Alloy specifically.

## What makes this Tournament Consensus

Three properties:

1. **Parallel competition, not sequential retry.** All N variants run to completion. None is discarded for being "worse" — the Synthesizer may take one phase from the variant that scored lowest overall if that phase was the strongest on a particular axis.

2. **Synthesizer ≠ planner.** The Synthesizer cannot write code, cannot add phases beyond what the variants produced, cannot invent novel structure. Its job is composition. This is load-bearing — a Synthesizer that falls back to planning defeats the entire tournament rationale.

3. **Momus audits the blend.** Not the individuals. This means Momus reviews once, not N times. The blended plan is the artifact that passes gates.

## Cost model

```
8 fixed agents (Metis, Synthesizer, Momus, Oracle, Hephaestus, Atlas + 3 Red-Team Trinity)
+ N Prometheus-Alloy spawns
= 8 + 2N when counting bias-specific prompt prep as separate spawns

Rounded: ~18 at N=5.
```

Wall-clock is dominated by the slowest planner in the tournament + synthesizer sequential step + Red-Team max. ~6 min typical.

## File ownership

See [`PRD.md`](./PRD.md) § 10 "Synthesizer contract" and `docs/synthesis-algorithm.md` for full synthesis rules. See [`docs/invariants.md`](./docs/invariants.md) for the seven rules that bind all three anneal architectures identically.

## The load-bearing invariant, restated

**Alloy is Cast's ergonomics × N planners × 1 Synthesizer.** The stage-4 substitution is the *entire* architectural delta. Stages 1-3 and 5-7 are bit-identical to Cast. If a change to Cast's Stage 5 helps, it helps Alloy. If a Synthesizer bug drops a critical phase, Momus catches it at Stage 4 close-out and the run routes to RE_LOOP.
