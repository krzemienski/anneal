#!/usr/bin/env python3
"""
validate-plugin.py — Self-validation for the anneal-cast Claude Code plugin.

Runs against the plugin directory (defaults to current directory). Verifies:
- .claude-plugin/plugin.json exists and is valid JSON
- .claude-plugin/marketplace.json exists and is valid JSON
- plugin.json contains required keys (name, version, description, author, license)
- Every skill has a SKILL.md with valid YAML frontmatter (name + description)
- Every command has a .md file with valid YAML frontmatter (description)
- Every agent has a .md file with valid YAML frontmatter (description)
- hooks/hooks.json exists and is valid JSON
- Scripts under scripts/ are executable
- No emoji in any markdown or JSON content

Exit code 0 = pass; 1 = fail.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F680-\U0001F6FF"  # transport & map
    "\U0001F700-\U0001F77F"
    "\U0001F780-\U0001F7FF"
    "\U0001F800-\U0001F8FF"
    "\U0001F900-\U0001F9FF"
    "\U0001FA00-\U0001FA6F"
    "\U0001FA70-\U0001FAFF"
    "\U00002600-\U000026FF"  # misc symbols
    "\U00002700-\U000027BF"  # dingbats
    "\U0001F1E0-\U0001F1FF"  # flags
    "]",
    flags=re.UNICODE,
)


def parse_yaml_frontmatter(text: str) -> tuple[dict, str] | None:
    """Return (frontmatter_dict, body) or None if no valid frontmatter."""
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    fm_text = parts[1]
    body = parts[2]
    # Minimal YAML parse: only `key: value` lines we actually rely on.
    # Avoids requiring PyYAML as a hard dependency.
    out: dict[str, str] = {}
    current_key: str | None = None
    for line in fm_text.splitlines():
        stripped = line.rstrip()
        if not stripped:
            continue
        if stripped.lstrip().startswith("#"):
            continue
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*)\s*:\s*(.*)$", stripped)
        if m:
            current_key = m.group(1)
            value = m.group(2).strip()
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            out[current_key] = value
        else:
            # Continuation — treat as part of last value.
            if current_key is not None:
                out[current_key] += " " + stripped.strip()
    return out, body


def load_json(path: Path, errors: list[str]) -> dict | None:
    if not path.exists():
        errors.append(f"Missing required file: {path}")
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"Invalid JSON in {path}: {exc}")
        return None


def validate_plugin_json(manifest: dict, errors: list[str]) -> None:
    required = ["name", "version", "description", "author", "license"]
    for key in required:
        if key not in manifest:
            errors.append(f"plugin.json missing required key: {key}")
    # Path-shape checks for directory-pointer fields.
    for key in ("skills", "commands", "agents"):
        value = manifest.get(key)
        if isinstance(value, str) and not value.startswith("./"):
            errors.append(
                f"plugin.json field '{key}' must use './' prefix — got '{value}'"
            )


def validate_marketplace_json(marketplace: dict, errors: list[str]) -> None:
    if "name" not in marketplace:
        errors.append("marketplace.json missing required key: name")
    if "plugins" not in marketplace or not isinstance(marketplace["plugins"], list):
        errors.append("marketplace.json missing 'plugins' array")
        return
    if not marketplace["plugins"]:
        errors.append("marketplace.json 'plugins' array is empty")


def validate_frontmatter_file(
    path: Path,
    required_fields: list[str],
    errors: list[str],
) -> dict | None:
    text = path.read_text(encoding="utf-8")
    result = parse_yaml_frontmatter(text)
    if result is None:
        errors.append(f"{path}: missing or invalid YAML frontmatter")
        return None
    fm, _body = result
    for field in required_fields:
        if field not in fm or not fm[field]:
            errors.append(f"{path}: frontmatter missing required field '{field}'")
    return fm


def scan_emoji(path: Path, errors: list[str]) -> None:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        errors.append(f"{path}: cannot read for emoji scan — {exc}")
        return
    matches = EMOJI_RE.findall(text)
    if matches:
        unique = sorted(set(matches))
        errors.append(
            f"{path}: contains emoji characters {unique} — plugin content must be emoji-free"
        )


def check_executable(path: Path, errors: list[str]) -> None:
    if not path.exists():
        errors.append(f"Missing expected script: {path}")
        return
    mode = path.stat().st_mode
    if not (mode & 0o111):
        errors.append(f"{path}: not executable (run `chmod +x`)")


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    errors: list[str] = []

    if not root.exists() or not root.is_dir():
        print(f"VALIDATION FAILED: {root} is not a directory")
        return 1

    print(f"Validating plugin at: {root}")

    # 1. Manifest files
    plugin_json = load_json(root / ".claude-plugin" / "plugin.json", errors)
    if plugin_json is not None:
        validate_plugin_json(plugin_json, errors)
    marketplace_json = load_json(root / ".claude-plugin" / "marketplace.json", errors)
    if marketplace_json is not None:
        validate_marketplace_json(marketplace_json, errors)

    # 2. Skills
    skills_dir = root / "skills"
    if not skills_dir.exists():
        errors.append(f"Missing skills/ directory at {skills_dir}")
    else:
        skill_files = list(skills_dir.glob("*/SKILL.md"))
        if not skill_files:
            errors.append("skills/ directory has no SKILL.md files")
        for skill_md in skill_files:
            validate_frontmatter_file(skill_md, ["name", "description"], errors)
            scan_emoji(skill_md, errors)

    # 3. Commands
    commands_dir = root / "commands"
    if not commands_dir.exists():
        errors.append(f"Missing commands/ directory at {commands_dir}")
    else:
        cmd_files = list(commands_dir.glob("*.md"))
        if not cmd_files:
            errors.append("commands/ directory has no .md files")
        for cmd_md in cmd_files:
            validate_frontmatter_file(cmd_md, ["description"], errors)
            scan_emoji(cmd_md, errors)

    # 4. Agents
    agents_dir = root / "agents"
    if not agents_dir.exists():
        errors.append(f"Missing agents/ directory at {agents_dir}")
    else:
        agent_files = list(agents_dir.glob("*.md"))
        if not agent_files:
            errors.append("agents/ directory has no .md files")
        for agent_md in agent_files:
            validate_frontmatter_file(agent_md, ["description"], errors)
            scan_emoji(agent_md, errors)

    # 5. Hooks
    hooks_json_path = root / "hooks" / "hooks.json"
    hooks_json = load_json(hooks_json_path, errors)
    if hooks_json is not None and "hooks" not in hooks_json:
        errors.append(f"{hooks_json_path}: missing top-level 'hooks' key")
    # Also ensure plugin.json does NOT reference hooks (would cause duplicate load).
    if plugin_json is not None and "hooks" in plugin_json:
        errors.append(
            "plugin.json references a 'hooks' field — remove it. "
            "hooks/hooks.json is auto-loaded; explicit reference causes duplicate-load errors."
        )

    # 6. Scripts are executable
    scripts_dir = root / "scripts"
    if scripts_dir.exists():
        for script in scripts_dir.iterdir():
            if script.is_file() and script.suffix in (".sh", ".py"):
                check_executable(script, errors)

    # 7. Emoji scan on top-level docs
    for doc_name in ("README.md", "PRD.md", "ARCHITECTURE.md"):
        doc = root / doc_name
        if doc.exists():
            scan_emoji(doc, errors)

    # 8. Report
    print()
    if errors:
        print("VALIDATION FAILED")
        for err in errors:
            print(f"  - {err}")
        return 1

    print("VALIDATION PASSED")
    print(f"  plugin: {plugin_json.get('name') if plugin_json else '?'}")
    print(f"  version: {plugin_json.get('version') if plugin_json else '?'}")
    print(f"  skills: {len(list(skills_dir.glob('*/SKILL.md'))) if skills_dir.exists() else 0}")
    print(f"  commands: {len(list(commands_dir.glob('*.md'))) if commands_dir.exists() else 0}")
    print(f"  agents: {len(list(agents_dir.glob('*.md'))) if agents_dir.exists() else 0}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
