#!/usr/bin/env python3
"""
Execution-correctness contract evaluator for the 8 Temper skills.

Each skill has 5 synthetic input scenarios. The evaluator reads each SKILL.md
and verifies its spec contains the rules, schema fields, and anti-patterns
that would force a correct behavioral output for each synthetic input.

This is a spec-conformance evaluator, not mocking. The real system being
validated is the skill specification itself — we are asking "does this spec
contain the machinery to handle input X correctly?"

Run:  python3 contract_eval.py <skills-dir>
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def load_skill(skills_dir: Path, name: str) -> str:
    return (skills_dir / name / "SKILL.md").read_text(encoding="utf-8")


def has(text: str, *needles: str, ci: bool = True) -> bool:
    hay = text.lower() if ci else text
    return all((n.lower() if ci else n) in hay for n in needles)


def any_of(text: str, *needles: str, ci: bool = True) -> bool:
    hay = text.lower() if ci else text
    return any((n.lower() if ci else n) in hay for n in needles)


def regex(text: str, pattern: str, flags=re.IGNORECASE | re.DOTALL) -> bool:
    return re.search(pattern, text, flags) is not None


CASES: dict[str, list[dict]] = {
    "deepen-loop": [
        {
            "name": "seed-depth-0-continue",
            "synthetic_input": {"depth": 0, "scores": [62.0], "cap": 3},
            "expected": "continue; no rule fires at depth 0 with 1 score and cap=3",
            "checks": [
                ("mentions-convergence-check-py", lambda s: has(s, "convergence-check.py")),
                ("no-vibe-convergence", lambda s: any_of(s, "never synthesize", "feels done", "use the script")),
                ("exit-code-1-continue", lambda s: any_of(s, "continue to next depth", "exit 1", "`1`")),
                ("handles-depth-0-seed", lambda s: regex(s, r"depth\s*=?\s*0") and any_of(s, "seed")),
                ("state-persistence", lambda s: any_of(s, "state file", "temper-state.json", "write state")),
            ],
        },
        {
            "name": "variance-converged",
            "synthetic_input": {"depth": 3, "scores": [80.0, 84.9, 85.0, 85.05], "cap": 5},
            "expected": "converged; reason=variance; emit final envelope",
            "checks": [
                ("variance-handled", lambda s: has(s, "variance")),
                ("calls-the-script", lambda s: has(s, "convergence-check.py")),
                ("exit-0-converged", lambda s: any_of(s, "exit 0", "`0`", "converged")),
                ("output-depth-history", lambda s: has(s, "depth_history")),
                ("output-final-depth", lambda s: any_of(s, "final_depth")),
            ],
        },
        {
            "name": "cap-hit",
            "synthetic_input": {"depth": 3, "scores": [50.0, 65.0, 78.0, 88.0], "cap": 3},
            "expected": "exit on cap; reason=cap",
            "checks": [
                ("cap-handled", lambda s: any_of(s, "cap ", "cap-triggered", "depth_cap", "cap)")),
                ("no-skip-depths", lambda s: any_of(s, "never skip", "never synthesize", "use the script")),
                ("convergence-reason-emitted", lambda s: has(s, "reason")),
            ],
        },
        {
            "name": "redteam-block-not-loop-exit",
            "synthetic_input": {"depth": 1, "scores": [62.0, 78.0], "cap": 3, "redteam_block": True},
            "expected": "Red Team BLOCK does not exit loop; folds into next depth",
            "checks": [
                ("parallel-fan-out", lambda s: any_of(s, "parallel", "single batch", "one message", "fan out")),
                ("prometheus-before-redteam", lambda s: any_of(s, "prometheus-temper runs before", "prometheus.*before.*red team", "freshly-written")),
                ("redteam-before-momus", lambda s: any_of(s, "momus runs after", "after red team", "after red-team")),
            ],
        },
        {
            "name": "convergence-check-exit-2",
            "synthetic_input": {"depth": -1, "scores": [], "cap": 3},
            "expected": "exit 2 invalid; retry once then abort",
            "checks": [
                ("exit-2-invalid", lambda s: any_of(s, "exit 2", "`2`", "invalid input")),
                ("retry-then-abort", lambda s: any_of(s, "retry once", "abort")),
            ],
        },
    ],

    "prometheus-temper": [
        {
            "name": "depth-0-cold-start",
            "synthetic_input": {"depth": 0, "metis_directives": ["..."]},
            "expected": "seed plan; no prior plan bundle",
            "checks": [
                ("depth-0-branch", lambda s: regex(s, r"depth\s*0") and any_of(s, "seed", "cold")),
                ("includes-functional-validation", lambda s: has(s, "functional-validation")),
                ("metis-directive-aware", lambda s: any_of(s, "metis_directives", "metis directives")),
            ],
        },
        {
            "name": "depth-1-folds-feedback",
            "synthetic_input": {"depth": 1, "prior_momus_score": 62, "blocking_issues_count": 3},
            "expected": "rewrite (not diff); address all blocking issues + CRITICAL red team findings",
            "checks": [
                ("address-every-blocking", lambda s: any_of(s, "address every blocking", "must explicitly address", "address every critical")),
                ("full-rewrite-no-diff", lambda s: any_of(s, "never diff", "full rewrite", "not a diff", "end-to-end")),
                ("address-critical-redteam", lambda s: any_of(s, "every critical red team", "critical red team", "critical red-team")),
            ],
        },
        {
            "name": "depth-2-score-trajectory-awareness",
            "synthetic_input": {"depth": 2, "score_history": [62.0, 78.0]},
            "expected": "aware of trajectory; annotate if score may drop",
            "checks": [
                ("trajectory-concept", lambda s: any_of(s, "score trajectory", "depth_score_history", "trajectory")),
                ("annotate-score-drop", lambda s: any_of(s, "score may drop", "annotate", "score might")),
                ("convergence-awareness", lambda s: any_of(s, "convergence", "delta")),
            ],
        },
        {
            "name": "metis-contradicts-user-goal",
            "synthetic_input": {"contradiction": True},
            "expected": "surface contradiction; do not silently resolve",
            "checks": [
                ("surface-contradiction", lambda s: any_of(s, "contradict", "surface")),
                ("no-silent-resolve", lambda s: any_of(s, "do not silently", "silently resolve")),
            ],
        },
        {
            "name": "output-schema-sections",
            "synthetic_input": {"emit": "plan"},
            "expected": "Thesis + Phases with success criteria + risk + functional-validation",
            "checks": [
                ("has-thesis-section", lambda s: has(s, "thesis")),
                ("has-phases-section", lambda s: any_of(s, "phases", "phase 00")),
                ("has-success-criteria", lambda s: has(s, "success criteria")),
                ("has-risk-assessment", lambda s: has(s, "risk assessment")),
                ("functional-validation-phase", lambda s: has(s, "functional-validation")),
                ("iron-rule-no-mocks", lambda s: any_of(s, "no mocks", "never write tests", "iron rule")),
            ],
        },
    ],

    "momus": [
        {
            "name": "high-quality-plan-scored-strong",
            "synthetic_input": {"critical": 0, "major": 1, "redteam": "3/3 SAFE"},
            "expected": "score ~85; verdict SAFE",
            "checks": [
                ("rubric-band-85", lambda s: any_of(s, "85-100", "85+", "strong")),
                ("rubric-file-referenced", lambda s: has(s, "scoring-rubric")),
                ("has-score-field", lambda s: regex(s, r"score\s*:\s*[<\[]")),
                ("safe-verdict-mapped", lambda s: has(s, "safe")),
            ],
        },
        {
            "name": "redteam-block-hard-floor",
            "synthetic_input": {"redteam_block": True},
            "expected": "score capped at 50; verdict BLOCK",
            "checks": [
                ("hard-floor-50", lambda s: any_of(s, "max score 50", "hard floor")),
                ("block-verdict", lambda s: has(s, "block")),
                ("polish-is-not-rubric", lambda s: any_of(s, "polish is not", "polished")),
            ],
        },
        {
            "name": "anti-drift-large-jump",
            "synthetic_input": {"prior_score": 62, "new_score": 88},
            "expected": "20+ point move requires justification sentence",
            "checks": [
                ("anti-drift-mentioned", lambda s: any_of(s, "anti-drift", "anti drift")),
                ("threshold-20", lambda s: regex(s, r"20\s*point")),
                ("justification-required", lambda s: any_of(s, "justification", "justify")),
            ],
        },
        {
            "name": "score-verdict-mapping",
            "synthetic_input": {"score": 88, "verdict_proposed": "CAUTION"},
            "expected": "88 -> SAFE; mismatch is validator error",
            "checks": [
                ("mapping-rule", lambda s: any_of(s, "score ↔ verdict", "verdict", "must be consistent", "scoring-rubric")),
                ("safe-band-anchor", lambda s: any_of(s, "85-100", "scoring-rubric")),
            ],
        },
        {
            "name": "finding-schema-complete",
            "synthetic_input": {"finding": "one"},
            "expected": "finding has severity, category, reviewer, summary, evidence, suggestion, blocks_emission",
            "checks": [
                ("finding-severity", lambda s: has(s, "severity")),
                ("finding-category", lambda s: has(s, "category")),
                ("finding-reviewer", lambda s: has(s, "reviewer")),
                ("finding-evidence", lambda s: has(s, "evidence")),
                ("finding-suggestion", lambda s: has(s, "suggestion")),
                ("finding-blocks-emission", lambda s: has(s, "blocks_emission")),
                ("one-finding-per-phase", lambda s: any_of(s, "finding per phase", "at least one finding")),
            ],
        },
    ],

    "red-team-trinity": [
        {
            "name": "depth-0-parallel-fan-out",
            "synthetic_input": {"depth": 0},
            "expected": "3 Task calls in single batch",
            "checks": [
                ("parallel-required", lambda s: any_of(s, "parallel", "single batch", "one message")),
                ("three-agents-listed", lambda s: has(s, "security") and has(s, "scope") and has(s, "assumptions")),
                ("must-rule", lambda s: has(s, "must")),
            ],
        },
        {
            "name": "every-depth-invariant",
            "synthetic_input": {"depth": 2},
            "expected": "runs at every depth of the loop",
            "checks": [
                ("every-depth", lambda s: any_of(s, "every depth", "always present", "always-on", "always on")),
                ("defining-property", lambda s: any_of(s, "defining property", "temper's")),
                ("contrast-cast-alloy", lambda s: any_of(s, "cast", "alloy")),
            ],
        },
        {
            "name": "prior-findings-awareness",
            "synthetic_input": {"depth": 1, "prior_findings": ["..."]},
            "expected": "note resolved/persistent/new",
            "checks": [
                ("resolved-persistent-new", lambda s: any_of(s, "resolved") and any_of(s, "persist", "persistent") and any_of(s, "new finding", "new ones", "newly")),
                ("prior-findings-input", lambda s: has(s, "prior_findings")),
                ("no-soften", lambda s: any_of(s, "do not soften", "not a reason to downgrade")),
            ],
        },
        {
            "name": "redteam-block-not-loop-exit",
            "synthetic_input": {"security_block": True},
            "expected": "BLOCK blocks emission but does not exit loop",
            "checks": [
                ("block-blocks-emission", lambda s: any_of(s, "blocks emission")),
                ("not-loop-exit", lambda s: any_of(s, "does not exit", "does NOT exit", "folds")),
            ],
        },
        {
            "name": "three-envelopes-orchestrator-aggregates",
            "synthetic_input": {"depth": 1},
            "expected": "each adversary returns own envelope; orchestrator rolls up",
            "checks": [
                ("roll-up-format", lambda s: any_of(s, "3/3", "2/3", "aggregate")),
                ("independent-voices", lambda s: any_of(s, "independent", "do not share state")),
                ("do-not-aggregate-inside", lambda s: any_of(s, "do not aggregate", "each returns its own")),
            ],
        },
    ],

    "oracle": [
        {
            "name": "variance-converged-safe",
            "synthetic_input": {"reason": "variance", "final_score": 85.0},
            "expected": "trust final Momus, SAFE, HIGH confidence",
            "checks": [
                ("variance-trust", lambda s: any_of(s, "trust the final", "high confidence")),
                ("variance-reason", lambda s: has(s, "variance")),
            ],
        },
        {
            "name": "cap-downgrade",
            "synthetic_input": {"reason": "cap", "final_score": 68.0},
            "expected": "downgrade because cap with score < 85",
            "checks": [
                ("cap-reason", lambda s: has(s, "cap")),
                ("downgrade", lambda s: has(s, "downgrade")),
                ("cap-threshold-85", lambda s: any_of(s, "< 85", "score < 85")),
            ],
        },
        {
            "name": "delta-downgrade",
            "synthetic_input": {"reason": "delta", "final_score": 64.0},
            "expected": "delta with score < 70 -> downgrade one tier",
            "checks": [
                ("delta-reason", lambda s: has(s, "delta")),
                ("downgrade-rule", lambda s: has(s, "downgrade")),
                ("delta-threshold-70", lambda s: any_of(s, "< 70", "score < 70")),
            ],
        },
        {
            "name": "missing-functional-validation-block",
            "synthetic_input": {"has_validation_phase": False},
            "expected": "Oracle emits BLOCK if plan lacks functional-validation phase",
            "checks": [
                ("functional-validation", lambda s: has(s, "functional-validation")),
                ("missing-triggers-block", lambda s: any_of(s, "lacks", "missing")),
                ("block-verdict", lambda s: has(s, "block")),
            ],
        },
        {
            "name": "output-schema-full",
            "synthetic_input": {"synthesize": True},
            "expected": "output has release_coherence, deployment_risk, breaking_changes, migration_cost, blast_radius, monitoring_recommendations",
            "checks": [
                ("release-coherence", lambda s: has(s, "release_coherence")),
                ("deployment-risk", lambda s: has(s, "deployment_risk")),
                ("breaking-changes", lambda s: has(s, "breaking_changes")),
                ("migration-cost", lambda s: has(s, "migration_cost")),
                ("blast-radius", lambda s: has(s, "blast_radius")),
                ("monitoring-recs", lambda s: has(s, "monitoring_recommendations")),
                ("final-gate-before-hephaestus", lambda s: any_of(s, "final gate", "last gate", "before hephaestus")),
            ],
        },
    ],

    "hephaestus": [
        {
            "name": "iron-no-mocks",
            "synthetic_input": {"plan_says": "write unit tests"},
            "expected": "refuse to write tests/mocks; fix real system only",
            "checks": [
                ("no-mocks-rule", lambda s: any_of(s, "no mocks", "NO mocks")),
                ("never-write-tests", lambda s: any_of(s, "never write tests")),
                ("iron-rule-label", lambda s: any_of(s, "iron rule")),
            ],
        },
        {
            "name": "empty-evidence-invalid",
            "synthetic_input": {"build_exit": 0, "screenshot_bytes": 0},
            "expected": "FAIL: empty file is invalid evidence; build success alone insufficient",
            "checks": [
                ("empty-file-invalid", lambda s: any_of(s, "empty", "0 bytes", ">0 bytes")),
                ("invalid-evidence", lambda s: any_of(s, "invalid")),
                ("build-not-sufficient", lambda s: any_of(s, "summaries are not evidence", "build succeeded", "not evidence")),
            ],
        },
        {
            "name": "fail-reloops-via-metis",
            "synthetic_input": {"verdict": "FAIL"},
            "expected": "fail_root_cause emitted; orchestrator re-loops via Metis",
            "checks": [
                ("fail-root-cause-field", lambda s: has(s, "fail_root_cause")),
                ("metis-reloop", lambda s: has(s, "metis")),
                ("depth-reset", lambda s: any_of(s, "depth = 0", "reset", "validate_attempts")),
            ],
        },
        {
            "name": "never-modify-plan-to-pass",
            "synthetic_input": {"observed": "no button", "criterion": "button appears"},
            "expected": "FAIL; never rewrite criterion",
            "checks": [
                ("never-modify-plan", lambda s: any_of(s, "never modify the plan")),
                ("no-rewrite-to-fit", lambda s: any_of(s, "do not rewrite", "make verdict pass", "make the verdict pass")),
            ],
        },
        {
            "name": "evidence-schema",
            "synthetic_input": {"step": 1},
            "expected": "evidence at e2e-evidence/hephaestus/step-NN-*.{png,json,txt}",
            "checks": [
                ("hephaestus-dir", lambda s: has(s, "e2e-evidence/hephaestus")),
                ("step-NN-pattern", lambda s: regex(s, r"step-\d+|step-\{NN|step-NN")),
                ("what-was-seen", lambda s: any_of(s, "what was seen", "what is seen", "Login form visible")),
                ("inventory", lambda s: has(s, "evidence-inventory")),
            ],
        },
    ],

    "metis": [
        {
            "name": "ambiguous-task-block",
            "synthetic_input": {"user_task": "add user authentication"},
            "expected": "BLOCK verdict; populated clarifying_questions <=3",
            "checks": [
                ("block-verdict", lambda s: has(s, "block")),
                ("clarifying-questions-field", lambda s: has(s, "clarifying_questions")),
                ("max-3", lambda s: any_of(s, "maximum 3", "max.*3", "3 questions")),
                ("one-sentence", lambda s: any_of(s, "one sentence")),
            ],
        },
        {
            "name": "directives-imperative-only",
            "synthetic_input": {"draft_directive": "Consider using JWT"},
            "expected": "REJECT soft; directives must be imperative",
            "checks": [
                ("imperative-required", lambda s: any_of(s, "imperative")),
                ("not-suggestions", lambda s: any_of(s, "not suggestions", "not a suggestion", "They are not suggestions")),
                ("bad-directive-example", lambda s: any_of(s, "consider using", "would be nice", "probably")),
            ],
        },
        {
            "name": "validate-reloop-context",
            "synthetic_input": {"validate_fail_context": {"fail_root_cause": "Redis not running"}},
            "expected": "emit directive referencing failure root cause",
            "checks": [
                ("validate-fail-context-field", lambda s: has(s, "validate_fail_context")),
                ("directive-references-failure", lambda s: any_of(s, "at least one directive", "referencing the failure")),
                ("preflight-or-dep-check", lambda s: any_of(s, "preflight", "dependency check")),
                ("no-downgrade-on-reloop", lambda s: any_of(s, "do not downgrade", "do NOT downgrade", "new signal")),
            ],
        },
        {
            "name": "slop-risk-patterns",
            "synthetic_input": {"task": "refactor everything"},
            "expected": "flag slop-risk categories",
            "checks": [
                ("scope-creep", lambda s: has(s, "scope creep")),
                ("over-engineering", lambda s: has(s, "over-engineering")),
                ("hallucinated", lambda s: has(s, "hallucinated")),
                ("re-implementation", lambda s: has(s, "re-implementation")),
                ("deployment-ambiguity", lambda s: has(s, "deployment ambiguity")),
            ],
        },
        {
            "name": "never-plan-only-surface",
            "synthetic_input": {"role": "consult"},
            "expected": "Metis does not plan; only surfaces directives",
            "checks": [
                ("never-plan", lambda s: any_of(s, "never plan", "does not plan")),
                ("only-surface", lambda s: any_of(s, "surface")),
                ("directives-output", lambda s: has(s, "directives")),
            ],
        },
    ],

    "atlas": [
        {
            "name": "emit-gate-conditions",
            "synthetic_input": {"simultaneous_pass": False, "hephaestus": "PASS"},
            "expected": "Atlas NOT invoked when any EMIT condition false",
            "checks": [
                ("simultaneous-pass-gate", lambda s: has(s, "simultaneous_pass")),
                ("hephaestus-pass-gate", lambda s: has(s, "hephaestus.verdict")),
                ("safe-caution-only", lambda s: any_of(s, "safe, caution", "{safe, caution}", "safe|caution")),
                ("not-invoked-if-false", lambda s: any_of(s, "not invoked", "do not emit")),
            ],
        },
        {
            "name": "three-output-artifacts",
            "synthetic_input": {"run_id": "xyz"},
            "expected": "XML + plan/ + depth-history.json",
            "checks": [
                ("xml-output", lambda s: any_of(s, ".xml", "semantic-xml", "xml file")),
                ("plan-directory", lambda s: any_of(s, "plan directory", "plan/")),
                ("depth-history-json", lambda s: has(s, "depth-history.json")),
            ],
        },
        {
            "name": "atlas-serializes-only",
            "synthetic_input": {"plan": "text"},
            "expected": "Atlas does not edit / not review / not re-run",
            "checks": [
                ("does-not-edit", lambda s: any_of(s, "does not edit")),
                ("does-not-review", lambda s: any_of(s, "does not re-review", "not re-review")),
                ("only-agent-writes-outside", lambda s: any_of(s, "only agent permitted", "only .* permitted to write")),
            ],
        },
        {
            "name": "xml-validator-gate-before-write",
            "synthetic_input": {"xml": "<anneal_run>..."},
            "expected": "run validate-xml.py; if fails, do not emit",
            "checks": [
                ("validate-xml-script", lambda s: any_of(s, "validate-xml", "validate-xml.py")),
                ("do-not-emit-on-fail", lambda s: any_of(s, "do not emit", "surface the error")),
            ],
        },
        {
            "name": "xml-temper-additions",
            "synthetic_input": {"depth_history": "..."},
            "expected": "XML contains <depth_history>, <convergence>, <iteration_count>",
            "checks": [
                ("depth-history-tag", lambda s: has(s, "depth_history")),
                ("convergence-tag", lambda s: has(s, "convergence")),
                ("iteration-count-tag", lambda s: any_of(s, "iteration_count", "validate_attempts")),
                ("template-reference", lambda s: any_of(s, "xml-template.md", "references/xml-template")),
            ],
        },
    ],
}


def evaluate(skills_dir: Path) -> dict:
    results = {}
    for name, cases in CASES.items():
        text = load_skill(skills_dir, name)
        skill_out = []
        for c in cases:
            check_results = []
            for label, fn in c["checks"]:
                try:
                    ok = fn(text)
                except Exception:
                    ok = False
                check_results.append({"label": label, "passed": ok})
            all_pass = all(r["passed"] for r in check_results)
            skill_out.append({
                "name": c["name"],
                "synthetic_input": c["synthetic_input"],
                "expected": c["expected"],
                "passed": all_pass,
                "checks": check_results,
                "fail_labels": [r["label"] for r in check_results if not r["passed"]],
            })
        results[name] = skill_out
    return results


def report(results: dict) -> tuple[int, int]:
    total = 0
    passed_total = 0
    print(f"{'Skill':<22} {'Case':<44} {'Verdict':<8} Checks")
    print("-" * 92)
    for skill, cases in results.items():
        n_pass = sum(1 for c in cases if c["passed"])
        for c in cases:
            total += 1
            verdict = "PASS" if c["passed"] else "FAIL"
            if c["passed"]:
                passed_total += 1
            ratio = f"{sum(1 for k in c['checks'] if k['passed'])}/{len(c['checks'])}"
            print(f"{skill:<22} {c['name']:<44} {verdict:<8} {ratio}")
            if c["fail_labels"]:
                print(f"  missing: {', '.join(c['fail_labels'])}")
        print(f"  [{skill}] {n_pass}/{len(cases)}")
    print("-" * 92)
    print(f"TOTAL PASS: {passed_total}/{total}")
    return passed_total, total


def main() -> int:
    skills_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/Users/nick/Desktop/anneal/temper/skills")
    results = evaluate(skills_dir)
    passed, total = report(results)
    out = skills_dir.parent / "skills-workspace" / "latest_results.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2))
    print(f"\nResults JSON: {out}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
