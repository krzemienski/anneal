#!/usr/bin/env python3
"""Validate an anneal-alloy emitted XML file against the Opus 4.7 semantic-XML schema.

Checks:
  - File is UTF-8 decodable with no BOM
  - File has no XML declaration (<?xml ...?>)
  - Root element is <anneal_run>
  - Required top-level children: metadata, context, plan, review, validation, instructions, thinking_budget
  - <metadata> contains architecture=alloy, run_id, task, project_root
  - <metadata> contains <tournament> with variants + biases (Alloy-specific)
  - <review> contains metis_envelope, momus_envelope, red_team, oracle_envelope, rollup
  - <red_team> contains security, scope, assumptions
  - <thinking_budget> is 'xhigh'
  - <instructions> contains task repeated verbatim (query-at-bottom)

Exits 0 on pass, 1 on any error. Prints "XML VALIDATION PASSED" or "XML VALIDATION FAILED".
"""
import sys
from pathlib import Path

try:
    import xml.etree.ElementTree as ET
except ImportError:
    print("XML VALIDATION FAILED: xml.etree.ElementTree not available", file=sys.stderr)
    sys.exit(1)


REQUIRED_TOP_CHILDREN = {
    "metadata", "context", "plan", "review",
    "validation", "instructions", "thinking_budget",
}

REQUIRED_METADATA_CHILDREN = {
    "architecture", "run_id", "timestamp", "task", "project_root", "tournament",
}

REQUIRED_TOURNAMENT_CHILDREN = {
    "variants", "biases",
}

REQUIRED_REVIEW_CHILDREN = {
    "metis_envelope", "momus_envelope", "red_team", "oracle_envelope", "rollup",
}

REQUIRED_REDTEAM_CHILDREN = {"security", "scope", "assumptions"}


def validate(xml_path: Path):
    errors = []

    if not xml_path.exists():
        return [f"File does not exist: {xml_path}"]

    raw_bytes = xml_path.read_bytes()
    if raw_bytes.startswith(b"\xef\xbb\xbf"):
        errors.append("File has UTF-8 BOM — schema requires no BOM.")
        raw_bytes = raw_bytes[3:]

    try:
        text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as e:
        return [f"File is not valid UTF-8: {e}"]

    stripped = text.lstrip()
    if stripped.startswith("<?xml"):
        errors.append("File starts with XML declaration — schema forbids it.")

    try:
        root = ET.fromstring(text)
    except ET.ParseError as e:
        return [f"XML parse error: {e}"]

    if root.tag != "anneal_run":
        errors.append(f"Root element must be <anneal_run>, got <{root.tag}>.")

    present_children = {child.tag for child in root}
    missing = REQUIRED_TOP_CHILDREN - present_children
    if missing:
        errors.append(f"Missing required top-level children: {sorted(missing)}")

    # metadata checks
    metadata = root.find("metadata")
    if metadata is not None:
        present_meta = {c.tag for c in metadata}
        missing_meta = REQUIRED_METADATA_CHILDREN - present_meta
        if missing_meta:
            errors.append(f"<metadata> missing required children: {sorted(missing_meta)}")
        arch = metadata.find("architecture")
        if arch is not None and (arch.text or "").strip() != "alloy":
            errors.append(f"<architecture> must be 'alloy', got '{arch.text}'")
        tournament = metadata.find("tournament")
        if tournament is not None:
            present_tour = {c.tag for c in tournament}
            missing_tour = REQUIRED_TOURNAMENT_CHILDREN - present_tour
            if missing_tour:
                errors.append(f"<tournament> missing: {sorted(missing_tour)}")

    # review checks
    review = root.find("review")
    if review is not None:
        present_rev = {c.tag for c in review}
        missing_rev = REQUIRED_REVIEW_CHILDREN - present_rev
        if missing_rev:
            errors.append(f"<review> missing: {sorted(missing_rev)}")
        redteam = review.find("red_team")
        if redteam is not None:
            present_rt = {c.tag for c in redteam}
            missing_rt = REQUIRED_REDTEAM_CHILDREN - present_rt
            if missing_rt:
                errors.append(f"<red_team> missing: {sorted(missing_rt)}")

    # thinking budget
    tb = root.find("thinking_budget")
    if tb is not None and (tb.text or "").strip() != "xhigh":
        errors.append(f"<thinking_budget> must be 'xhigh', got '{tb.text}'")

    # instructions check — task must appear at top AND bottom (query-at-bottom)
    metadata_task = root.find("metadata/task")
    instructions_task = root.find("instructions/task")
    if metadata_task is not None and instructions_task is not None:
        top_text = (metadata_task.text or "").strip()
        bot_text = (instructions_task.text or "").strip()
        if top_text and bot_text and top_text != bot_text:
            errors.append("<metadata><task> and <instructions><task> must match verbatim (query-at-bottom).")

    return errors


def main():
    if len(sys.argv) < 2:
        print("Usage: validate-xml.py <path-to-xml>", file=sys.stderr)
        return 1
    xml_path = Path(sys.argv[1]).resolve()

    print("=" * 64)
    print(f"Validating XML: {xml_path}")
    print("=" * 64)

    errors = validate(xml_path)

    if errors:
        print(f"Errors ({len(errors)}):")
        for e in errors:
            print(f"  - {e}")
        print()
        print("XML VALIDATION FAILED")
        return 1

    print("XML VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
