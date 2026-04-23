# Anneal · Phase Roadmap

**Date:** 2026-04-22
**Horizon:** Phases 4 through 10 — from review to shipped product
**Thesis:** Anneal is the planning tool for the withagents.dev ecosystem. Its proof is that it uses itself to plan its own product site.

---

## The higher purpose (why the last 4-5 days matter)

The blog series "Agentic Development: 18 Lessons from 23,479 AI Coding Sessions" is one surface of a larger project. The deeper project is an agentic-development **tooling ecosystem** under `withagents.dev` that stays honest about what works. The four pillars so far:

| Pillar | Encoded discipline | Status |
|--------|-------------------|--------|
| Blog series (18 posts) | Lessons from real sessions · evidence-grounded | Published |
| ValidationForge | No mocks, evidence-based verdict tiers | Plugin shipped v0.x |
| Multi-Agent Consensus | Multiple independent perspectives must agree | Plugin shipped v0.2 |
| **Anneal (this)** | Plans must survive red team + functional validation before shipping | Plugin v0.1 built today |

The product-site-architecture plan (`plans/260421-1806-product-site-architecture/DEEPEST-PROMPT.xml`) was supposed to deliver the **Product Site Template (PST)** contract — the schema every product site must satisfy so the ecosystem stays coherent. That attempt failed (91 validator defects, asymmetric vendoring, monolithic XML). The whole motivation for anneal was: **build the tool that could produce that plan correctly.**

Everything since has been circling that one goal. The meta-move is dogfood: anneal must produce its own plan for its own product site. The planning tool that plans itself is the proof.

---

## The full ecosystem graph (current state)

```
withagents.dev (brand + catalog + writing)
├── blog series (18 posts, published)
├── /products/multi-agent-consensus   → Tier 1 catalog entry (done), Tier 2 site pending
├── /products/validationforge         → Tier 1 catalog entry (done), vf.withagents.dev Tier 2 exists
├── /products/deepest-plan            → MISSING — was v1 of anneal, now deprecated
├── /products/anneal                  → MISSING — this is the next deliverable
└── /products/<others>                → future (shannon, ralph, etc per post list)
```

**Gaps to close:**
1. `deepest-plan` / `anneal` missing from `site/src/lib/products.ts` (catalog root)
2. No product site exists for anneal at any tier
3. PST contract still not formally delivered — it's been described in the architecture but never executed end-to-end
4. Consensus product site (`consensus.withagents.dev`) doesn't exist at all

Anneal the plugin is the means. A shipped PST contract + three product sites (anneal, deepest-plan retirement, consensus) is the end.

---

## Phase 4 — Deep Multi-Perspective Review (current, expanded)

Current state: `scripts/phase-4-review-prompts.md` holds two staged prompts (architect + code-reviewer) with test case and grading rubric.

**Expansion — this phase needs more than two reviewers:**

| Reviewer | Model | Scope | Fires after |
|----------|-------|-------|-------------|
| **architect** | opus | Architectural coherence across 3 plugins + invariant audit | Phase 3 QA |
| **code-reviewer** | opus | YAML, prompt-quality, cross-references, scripts | Phase 3 QA |
| **security-reviewer** | opus | STRIDE + OWASP + secret scan across all scripts, hooks, agent prompts | architect+code pass |
| **docs-reviewer** | opus | READMEs, INSTALL, PRDs readable by a fresh dev with zero context | security pass |
| **dogfood-run** | — | Fire `/anneal-cast:anneal` + `/anneal-alloy:anneal` + `/anneal-temper:anneal` against the PST task. Grade per `COMPARISON-PLAYBOOK.md` | docs pass |

**Phase 4 exit criteria (all must green in same round):**
- All four reviewers return SAFE or CAUTION
- Dogfood run produces one or more EMIT verdicts across the three architectures
- The emitted XML + plan directory, handed to a fresh Claude Code session, is consumable without re-prompting

**What this phase unlocks:** Phase 5 — deciding which architecture's output is the PST plan we actually ship.

---

## Phase 5 — The Decisive Dogfood

Run the PST task through all three plugins. Rank their outputs against the original failed DEEPEST-PROMPT.xml. Pick one to execute.

**The task verbatim** (from `scripts/phase-4-review-prompts.md`):
> Deliver the Product Site Template (PST) contract for withagents.dev. Every product (starting with multi-agent-consensus, validationforge, deepest-plan→anneal migration) gets: hero, 3-sentence what-it-does, ≥2 inline usage examples, architecture/flow diagram, how-it-works section, feature matrix, install/docs/changelog, links back to brand. Apply the three-tier strategy (Tier 1 apex, Tier 2 subdomain via proxy.ts, Tier 3 separate Vercel). Validate via functional-validation + visual-inspection at 375/768/1440 + e2e cross-domain navigation. No mocks, no test files.

**Scoring dimensions** (per `COMPARISON-PLAYBOOK.md`):
- Phase coherence (monolithic XML was the original's failure mode)
- Evidence mandate wired into re-loop
- Vendor correctness (symmetric — validation and planning both as skills)
- Red team explicit vs implicit
- Re-loop semantics
- XML output structure

**Phase 5 exit criteria:**
- One architecture's output is selected as the canonical PST plan
- The plan is moved from `~/Desktop/anneal-runs/{run_id}/` to `/Users/nick/Desktop/blog-series/plans/260422-<timestamp>-pst-contract-v2/` (replacing the failed v1)
- The selected architecture becomes the **default** for future anneal invocations (decision locked in `DECISION-LOCKED-v2.md`)

---

## Phase 6 — Execute the PST Plan

Take the chosen plan and actually build. This is the work the original failed plan was supposed to orchestrate.

**What gets built** (per the PST contract):
1. `site/src/lib/products.ts` — add `anneal`, `deepest-plan` (marked deprecated → redirect to anneal), and any other missing entries
2. `site/src/app/products/[slug]/` — ensure Tier 1 apex routes render the full PST sections for every product
3. `site/src/proxy.ts` — confirm Tier 2 subdomain rewrites still work; add `anneal.withagents.dev` if that's the chosen tier
4. Product sites for the three currently-thin/missing:
   - **anneal** — full PST site with all three architecture variants as feature cards
   - **multi-agent-consensus** — upgrade current catalog stub to full PST
   - **consensus.withagents.dev** — new subdomain (if Tier 2 chosen)
5. Tombstone / redirect for deprecated `deepest-plan` product route
6. Evidence captured per plan at `e2e-evidence/` matching phase files

**Phase 6 enforcement:** every phase of the executed plan must pass Hephaestus (functional validator) with cited evidence before the next phase begins. This is the plan executing on itself — the plan was produced BY anneal, now EXECUTED against the plan's own success criteria.

---

## Phase 7 — Anneal Becomes Its Own Product

This is the closing-the-loop phase. Anneal the plugin gets its own product site.

**Tier decision:** Tier 2 subdomain (`anneal.withagents.dev`) is recommended because:
- Three architecture variants have distinct content (Cast / Alloy / Temper each need their own sub-pages)
- Comparison playbook is substantial documentation
- Live demo space (paste a task, pick an architecture, see the generated plan) needs real estate
- Tier 1 apex (`/products/anneal`) stays as the catalog pivot that links to the subdomain

**Site content** (produced by running `/anneal-temper:anneal "build the anneal product site"` on itself):
- Hero: "Controlled heating, slow cooling, iterative tempering — applied to work plans."
- What-it-does (3 sentences): defined
- Usage examples: the three invocations from `INSTALL.md`
- Architecture/flow diagram: reuse `diagrams/anneal-architectures.html` (editorial aesthetic already built)
- How-it-works: 7-stage spine from `ARCHITECTURE-PROPOSALS.md`
- Feature matrix: the comparison table (Cast vs Alloy vs Temper)
- Install: `INSTALL.md` content, tightened
- Docs: link to `ARCHITECTURE-PROPOSALS.md`, `SKILL-OPTIMIZATION-REPORT.md`, `COMPARISON-PLAYBOOK.md`
- Changelog: `v0.1.0 — initial triple-variant build (2026-04-22)`
- Links back: brand home, GitHub repo (when created), blog post about anneal

**Phase 7 enforcement:** the site itself passes Hephaestus validation at 375/768/1440 widths, plus e2e navigation test (products.ts → /products/anneal → anneal.withagents.dev → section links → GitHub). No mocks, no test files.

---

## Phase 8 — Catalog Registration

Register anneal as a first-class product in `site/src/lib/products.ts`.

**Updates:**
1. Add `anneal` product object (slug, title, tagline, tier, subdomain, catalog route)
2. Mark `deepest-plan` as `deprecated: true`, `redirect_to: "anneal"`
3. Ensure the `/products/deepest-plan` route returns 410 Gone (already has GONE_PATHS tombstone support in proxy.ts)
4. Run the catalog-generator / sitemap re-build to propagate

**Phase 8 enforcement:** Functional-validation fetches `/api/products` and confirms anneal appears; fetches `/products/deepest-plan` and confirms 410.

---

## Phase 9 — Blog Post

Anneal gets a blog post in the series. Likely slot: post-19 (series may need to extend beyond the original 18, or this becomes a supplementary essay).

**Post content outline:**
1. The failure — deepest-plan v1, 91 validator defects, asymmetric vendoring diagnosed
2. The redesign pivot — HYBRID A+C (later superseded)
3. The rebrand — naming (anneal from simulated annealing metallurgy)
4. The multi-architecture build — Cast / Alloy / Temper side-by-side
5. The skill-creator discipline — why "audit checklist" isn't enough; what execution-correctness simulation catches
6. The dogfood proof — anneal producing its own product site plan
7. The lesson — if your tool can't plan itself, it's not a tool yet

**Publish target:** `posts/post-19-anneal/post.md` + `site/posts/post-19-anneal/post.md` (mirror).

---

## Phase 10 — Public Release

Open-source publishing.

1. Create `github.com/krzemienski/anneal` repo (monorepo with `cast/`, `alloy/`, `temper/` as plugin directories)
2. Public `marketplace.json` pointing at the three plugins
3. Add to `site/src/lib/products.ts` with GitHub link
4. Announce in blog post (Phase 9) + social channels
5. Add to ValidationForge docs integration guide — cite anneal as a peer planning tool

**Phase 10 exit criteria:**
- `npm view anneal-cast version` or `gh api repos/krzemienski/anneal/releases/latest` returns v0.1.0
- Public install via `/plugin marketplace add krzemienski/anneal` works from a fresh Claude Code install
- First external user installs + runs the canonical invocation without needing Nick to help

---

## The static site in detail

**Tier decision matrix:**

| Option | Cost | Isolation | Discovery | Fit |
|--------|------|-----------|-----------|-----|
| Tier 1 — `/products/anneal` only | Free | None | Part of catalog | For v0.1 launch, probably enough |
| Tier 2 — `anneal.withagents.dev` subdomain | Low | Host-based via proxy.ts | Own subdomain memorable URL | Recommended for v0.2+ when docs expand |
| Tier 3 — separate Vercel project | Medium | Full | Own everything | Only if a live-demo sandbox requires separate auth |

**Recommended path:** Ship Tier 1 in Phase 7. Upgrade to Tier 2 once the docs/examples exceed ~3 distinct sections.

**Content model** (both tiers use the same MDX):
```
anneal-site/
├── page.mdx                  # PST-compliant landing
├── architectures/
│   ├── cast.mdx
│   ├── alloy.mdx
│   └── temper.mdx
├── install.mdx               # from INSTALL.md
├── compare.mdx               # from COMPARISON-PLAYBOOK.md
├── docs/
│   └── architecture.mdx      # from ARCHITECTURE-PROPOSALS.md
└── changelog.mdx
```

---

## The meta-principle (why this shape)

Every plugin in the ecosystem should close its own loop:
- ValidationForge **validates** its own plan file
- Multi-Agent Consensus **reviews** its own release via its own 3-agent gate
- Anneal **plans** its own product site by invoking itself
- Each plugin's product site exists **because** that plugin produced the plan that produced it

If any of these fails the dogfood test, the tool isn't good enough to ship to others.

---

## What's next (immediate, concrete)

Phase 4 is blocked on running the deep reviewers (architect + code + security + docs). The dogfood-run sub-phase is blocked on Phase 4. Everything after Phase 4 depends on which architecture wins the dogfood.

**The single next action:** fire the four Phase 4 reviewers against the current state. That either greenlights the dogfood run, or produces blocking findings that fold into a new iteration via Metis.

If you want, I can expand `scripts/phase-4-review-prompts.md` to include the security + docs reviewer prompts, and a section for the dogfood-run dispatch. Say the word.
