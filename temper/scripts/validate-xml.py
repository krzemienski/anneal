#!/usr/bin/env python3
"""Validate an Anneal emission XML against the Opus 4.7 semantic-XML schema.

Usage:
    python3 scripts/validate-xml.py <emission.xml>

Checks:
  - UTF-8 decoding
  - No XML declaration
  - Root element is <anneal_run>
  - Required top-level children present
  - architecture is 'temper' (this is the temper plugin)
  - <review> includes Temper-specific <depth_history> and <convergence>
  - <thinking_budget> present
  - One <anneal_run> per file

Exits 0 on PASS, 1 on FAIL.
"""
from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path


REQUIRED_TOP_LEVEL = [
    "metadata",
    "context",
    "plan",
    "review",
    "validation",
    "instructions",
    "thinking_budget",
]

REQUIRED_METADATA = ["architecture", "run_id", "timestamp", "task", "project_root"]

REQUIRED_REVIEW = [
    "metis_envelope",
    "depth_history",   # Temper-specific
    "convergence",     # Temper-specific
    "oracle_envelope",
    "rollup",
]


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: validate-xml.py <emission.xml>", file=sys.stderr)
        return 1
    path = Path(sys.argv[1])
    if not path.exists():
        print(f"ERROR: no such file: {path}", file=sys.stderr)
        return 1

    errors: list[str] = []
    warnings: list[str] = []

    try:
        raw = path.read_bytes()
    except OSError as exc:
        print(f"ERROR: cannot read: {exc}", file=sys.stderr)
        return 1

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        errors.append(f"Not valid UTF-8: {exc}")
        text = raw.decode("utf-8", errors="replace")

    if text.lstrip().startswith("<?xml"):
        errors.append("XML declaration present; schema forbids it")

    # Parse
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        errors.append(f"XML parse failed: {exc}")
        print("VALIDATION FAILED")
        for e in errors:
            print(f"  {e}")
        return 1

    if root.tag != "anneal_run":
        errors.append(f"Root element must be <anneal_run>, got <{root.tag}>")

    # Required top-level
    for req in REQUIRED_TOP_LEVEL:
        if root.find(req) is None:
            errors.append(f"Missing top-level <{req}>")

    # Metadata
    md = root.find("metadata")
    if md is not None:
        for req in REQUIRED_METADATA:
            if md.find(req) is None:
                errors.append(f"<metadata> missing <{req}>")
        arch = md.find("architecture")
        if arch is not None and (arch.text or "").strip() != "temper":
            warnings.append(
                f"<architecture> is {arch.text!r}; expected 'temper' in this plugin"
            )

    # Review
    rv = root.find("review")
    if rv is not None:
        for req in REQUIRED_REVIEW:
            if rv.find(req) is None:
                errors.append(f"<review> missing <{req}>")

    # Validation
    val = root.find("validation")
    if val is not None and val.find("hephaestus_evidence") is None:
        errors.append("<validation> missing <hephaestus_evidence>")

    # Instructions
    ins = root.find("instructions")
    if ins is not None:
        for req in ("task", "next_action", "success_criteria"):
            if ins.find(req) is None:
                errors.append(f"<instructions> missing <{req}>")

    # Thinking budget
    tb = root.find("thinking_budget")
    if tb is not None and (tb.text or "").strip() != "xhigh":
        warnings.append(f"<thinking_budget> is {tb.text!r}; expected 'xhigh'")

    print("=" * 60)
    print(f"validate-xml.py — {path}")
    print("=" * 60)
    if warnings:
        print("WARNINGS:")
        for w in warnings:
            print(f"  {w}")
    if errors:
        print("VALIDATION FAILED")
        for e in errors:
            print(f"  {e}")
        return 1
    print("VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
