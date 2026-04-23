#!/usr/bin/env python3
"""
validate-xml.py — Validate Atlas emissions against the Opus 4.7 semantic-XML schema.

Usage:
    validate-xml.py <path-to-emission.xml>

Rules enforced (from _shared/opus-47-xml-schema.md):
- UTF-8 encoded, no BOM.
- No `<?xml version=?>` declaration.
- Root element is <anneal_run>.
- Required children in order: metadata, context, plan, review, validation, instructions, thinking_budget.
- <metadata> contains architecture, run_id, timestamp, task, project_root.
- <metadata><architecture> is one of: cast, alloy, temper.
- <thinking_budget> text is 'xhigh'.
- No inline HTML tags (div, span, img, etc.).
- One <anneal_run> per file.

Exit 0 on pass, 1 on any violation.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from xml.etree import ElementTree


DISALLOWED_HTML_TAGS = {
    "div", "span", "img", "br", "hr", "table", "tr", "td", "th",
    "a", "p", "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "li",
    "button", "input", "form", "label", "select", "option",
}

REQUIRED_ROOT_CHILDREN = [
    "metadata",
    "context",
    "plan",
    "review",
    "validation",
    "instructions",
    "thinking_budget",
]

REQUIRED_METADATA_CHILDREN = [
    "architecture",
    "run_id",
    "timestamp",
    "task",
    "project_root",
]

VALID_ARCHITECTURES = {"cast", "alloy", "temper"}


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: validate-xml.py <path-to-emission.xml>", file=sys.stderr)
        return 1

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"VALIDATION FAILED: file not found: {path}", file=sys.stderr)
        return 1

    errors: list[str] = []

    # 1. Encoding and declaration checks (raw bytes)
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        errors.append("File has BOM — schema forbids it")
    text = raw.decode("utf-8", errors="replace")
    stripped = text.lstrip()
    if stripped.startswith("<?xml"):
        errors.append("File has <?xml ...?> declaration — schema forbids it")

    # 2. XML parse
    try:
        root = ElementTree.fromstring(text)
    except ElementTree.ParseError as exc:
        errors.append(f"XML parse error: {exc}")
        print_report(errors)
        return 1

    # 3. Root element
    if root.tag != "anneal_run":
        errors.append(
            f"Root element must be <anneal_run>, got <{root.tag}>"
        )

    # 4. Required children in order
    actual_children = [child.tag for child in root]
    for required in REQUIRED_ROOT_CHILDREN:
        if required not in actual_children:
            errors.append(f"Missing required root child: <{required}>")

    # 5. metadata contents
    metadata = root.find("metadata")
    if metadata is not None:
        for required in REQUIRED_METADATA_CHILDREN:
            if metadata.find(required) is None:
                errors.append(f"<metadata> missing required child: <{required}>")
        arch_el = metadata.find("architecture")
        if arch_el is not None and arch_el.text:
            arch = arch_el.text.strip()
            if arch not in VALID_ARCHITECTURES:
                errors.append(
                    f"<architecture> value '{arch}' not in "
                    f"{sorted(VALID_ARCHITECTURES)}"
                )

    # 6. thinking_budget value
    tb = root.find("thinking_budget")
    if tb is not None and (tb.text or "").strip() != "xhigh":
        errors.append(
            f"<thinking_budget> must be 'xhigh', got '{(tb.text or '').strip()}'"
        )

    # 7. Disallowed HTML tags anywhere in the tree
    for el in root.iter():
        if el.tag in DISALLOWED_HTML_TAGS:
            errors.append(
                f"Disallowed HTML tag <{el.tag}> found — schema is plain-text only"
            )

    # 8. Ensure only one <anneal_run>. ElementTree gives us one root by default,
    # but check the raw text for multiple occurrences (naive but effective).
    opens = len(re.findall(r"<anneal_run(\s|>)", text))
    if opens > 1:
        errors.append(
            f"Found {opens} <anneal_run> elements — schema allows only one per file"
        )

    print_report(errors)
    return 1 if errors else 0


def print_report(errors: list[str]) -> None:
    if errors:
        print("XML VALIDATION FAILED")
        for err in errors:
            print(f"  - {err}")
    else:
        print("XML VALIDATION PASSED")


if __name__ == "__main__":
    sys.exit(main())
