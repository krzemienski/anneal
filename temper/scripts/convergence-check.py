#!/usr/bin/env python3
"""
convergence-check.py — Deterministic convergence checker for the Temper deepen loop.

Reads JSON on stdin with `depth`, `scores`, `cap` fields. Writes JSON decision on stdout.

Exit codes:
  0 — converged; stdout JSON has {"converged": true, "reason": "variance|delta|cap", ...}
  1 — continue; stdout JSON has {"converged": false, "next_depth": <int>}
  2 — invalid input; stderr has a reason

Convergence rules (any one fires):
  1. variance  — variance of top-3 scores < 0.3 (and len(scores) >= 3)
  2. delta     — |scores[-1] - scores[-2]| < 0.15 (and len(scores) >= 2)
  3. cap       — depth >= cap

Multiple rules may fire on the same depth. The first matching rule is reported in
this priority order: variance > delta > cap (because variance is the cleanest
signal, delta the next cleanest, cap the crudest).

Thresholds are architecture constants. Users who want a shallower exit set --depth
on the command line instead of tweaking these.

Run this script directly with `--selftest` to execute the inline smoke tests.
"""

from __future__ import annotations

import json
import math
import sys
from typing import Any


VARIANCE_THRESHOLD = 0.3
DELTA_THRESHOLD = 0.15


def variance(xs: list[float]) -> float:
    """Population variance (not sample). Matches what 'spread of final scores' means."""
    if len(xs) == 0:
        return 0.0
    mean = sum(xs) / len(xs)
    return sum((x - mean) ** 2 for x in xs) / len(xs)


def top_n(xs: list[float], n: int) -> list[float]:
    """Return the top-N values (sorted descending). If len(xs) < n, return all of xs."""
    return sorted(xs, reverse=True)[:n]


def check_convergence(depth: int, scores: list[float], cap: int) -> dict[str, Any]:
    """
    Return a dict describing the convergence decision.

    Priority: variance > delta > cap.

    Continue example (no rule fires yet):

    >>> check_convergence(depth=2, scores=[62.0, 78.0, 85.0], cap=3)
    {'converged': False, 'next_depth': 3}

    Cap-triggered at depth 3 (scores still rising by +10, no variance/delta trigger):

    >>> result = check_convergence(depth=3, scores=[50.0, 65.0, 78.0, 88.0], cap=3)
    >>> result['converged']
    True
    >>> result['reason']
    'cap'

    Delta-triggered (marginal improvement beats cap in priority):

    >>> result = check_convergence(depth=2, scores=[80.0, 85.0, 85.05], cap=5)
    >>> result['converged']
    True
    >>> result['reason']
    'delta'
    >>> round(result['abs_delta'], 4)
    0.05

    Variance-triggered (three very-close top-3 scores):

    >>> result = check_convergence(depth=3, scores=[80.0, 84.9, 85.0, 85.05], cap=5)
    >>> result['converged']
    True
    >>> result['reason']
    'variance'

    Continue example (too few scores for rule 1, delta too large):

    >>> check_convergence(depth=1, scores=[62.0, 78.0], cap=3)
    {'converged': False, 'next_depth': 2}
    """
    if not isinstance(scores, list) or any(not isinstance(s, (int, float)) for s in scores):
        raise ValueError("scores must be a list of numbers")
    if len(scores) != depth + 1:
        raise ValueError(
            f"scores length {len(scores)} does not match depth+1 ({depth + 1})"
        )

    # Rule 1: variance of top-3 < threshold (requires >= 3 scores)
    if len(scores) >= 3:
        top3 = top_n(scores, 3)
        var = variance(top3)
        if var < VARIANCE_THRESHOLD:
            return {
                "converged": True,
                "reason": "variance",
                "variance_top3": round(var, 6),
                "top3": top3,
                "threshold": VARIANCE_THRESHOLD,
            }

    # Rule 2: |delta| across last 2 depths < threshold (requires >= 2 scores)
    if len(scores) >= 2:
        abs_delta = abs(scores[-1] - scores[-2])
        if abs_delta < DELTA_THRESHOLD:
            return {
                "converged": True,
                "reason": "delta",
                "abs_delta": round(abs_delta, 6),
                "last_two": [scores[-2], scores[-1]],
                "threshold": DELTA_THRESHOLD,
            }

    # Rule 3: hit the cap
    if depth >= cap:
        return {
            "converged": True,
            "reason": "cap",
            "depth_reached": depth,
            "cap": cap,
        }

    # Continue
    return {"converged": False, "next_depth": depth + 1}


def run(payload: dict[str, Any]) -> int:
    try:
        depth = int(payload["depth"])
        scores = [float(s) for s in payload["scores"]]
        cap = int(payload["cap"])
    except (KeyError, TypeError, ValueError) as exc:
        print(f"ERROR: invalid input — {exc}", file=sys.stderr)
        print(
            "Expected: {\"depth\": int, \"scores\": [float, ...], \"cap\": int}",
            file=sys.stderr,
        )
        return 2

    if cap < 1 or cap > 5:
        print(f"ERROR: cap out of range (1-5): {cap}", file=sys.stderr)
        return 2
    if depth < 0:
        print(f"ERROR: depth must be >= 0: {depth}", file=sys.stderr)
        return 2

    try:
        decision = check_convergence(depth, scores, cap)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(decision))
    return 0 if decision["converged"] else 1


def selftest() -> int:
    """Execute the inline doctests and return the failure count."""
    import doctest

    results = doctest.testmod(verbose=True)
    return 0 if results.failed == 0 else 1


def smoketest() -> int:
    """Run three canonical inputs and print results. Returns 0 if all behave as expected."""
    cases = [
        {
            "label": "variance-triggered (three tight top-3 scores)",
            "input": {"depth": 3, "scores": [80.0, 84.9, 85.0, 85.05], "cap": 5},
            "expect_converged": True,
            "expect_reason": "variance",
        },
        {
            "label": "delta-triggered (marginal improvement on last step)",
            "input": {"depth": 2, "scores": [80.0, 85.0, 85.05], "cap": 5},
            "expect_converged": True,
            "expect_reason": "delta",
        },
        {
            "label": "cap-triggered (scores still rising, but depth == cap)",
            "input": {"depth": 3, "scores": [50.0, 65.0, 78.0, 88.0], "cap": 3},
            "expect_converged": True,
            "expect_reason": "cap",
        },
        {
            "label": "continue (score history too short, no rule fires)",
            "input": {"depth": 1, "scores": [62.0, 78.0], "cap": 3},
            "expect_converged": False,
            "expect_reason": None,
        },
    ]

    all_ok = True
    for case in cases:
        try:
            decision = check_convergence(
                case["input"]["depth"],
                case["input"]["scores"],
                case["input"]["cap"],
            )
        except ValueError as exc:
            print(f"FAIL  {case['label']}: raised {exc}")
            all_ok = False
            continue

        ok = decision["converged"] == case["expect_converged"]
        if case["expect_reason"] is not None:
            ok = ok and decision.get("reason") == case["expect_reason"]

        marker = "PASS" if ok else "FAIL"
        print(f"{marker}  {case['label']}")
        print(f"       input:  {json.dumps(case['input'])}")
        print(f"       output: {json.dumps(decision)}")
        if not ok:
            all_ok = False

    return 0 if all_ok else 1


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    if "--smoketest" in sys.argv:
        return smoketest()

    raw = sys.stdin.read().strip()
    if not raw:
        print("ERROR: empty stdin; send JSON on stdin", file=sys.stderr)
        return 2

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"ERROR: stdin is not valid JSON — {exc}", file=sys.stderr)
        return 2

    return run(payload)


if __name__ == "__main__":
    sys.exit(main())
