#!/usr/bin/env python3
"""Validate a Claude Code plugin's manifest, skills, commands, agents, hooks.

Usage:
    python3 scripts/validate-plugin.py .
    python3 scripts/validate-plugin.py /Users/nick/Desktop/anneal/temper

Exits 0 on VALIDATION PASSED, 1 on VALIDATION FAILED.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path


def _load_yaml_frontmatter(text: str) -> tuple[dict | None, str | None]:
    """Parse YAML frontmatter without importing PyYAML. Returns (mapping, error)."""
    if not text.startswith("---\n") and not text.startswith("---\r\n"):
        return None, "no YAML frontmatter (must start with '---')"
    # Find the closing fence
    lines = text.splitlines()
    if lines[0] != "---":
        return None, "opening fence not exactly '---'"
    end_idx = None
    for i, line in enumerate(lines[1:], start=1):
        if line == "---":
            end_idx = i
            break
    if end_idx is None:
        return None, "no closing '---' fence for frontmatter"

    fm_lines = lines[1:end_idx]
    mapping: dict = {}
    current_key = None
    current_value_buf: list[str] = []
    for raw in fm_lines:
        # Strip trailing whitespace but keep inner
        line = raw.rstrip()
        if not line.strip():
            continue
        # Top-level key: value or key:
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*)\s*:\s*(.*)$", line)
        if m:
            if current_key is not None and current_value_buf:
                mapping[current_key] = "\n".join(current_value_buf).strip()
                current_value_buf = []
            current_key = m.group(1)
            rest = m.group(2)
            if rest == "":
                # Multiline value follows; accumulate
                mapping[current_key] = ""
                current_value_buf = []
            else:
                mapping[current_key] = _unquote(rest)
                current_key = None
        else:
            # Continuation line (for multiline descriptions, etc.)
            if current_key is not None:
                current_value_buf.append(line.strip())
    if current_key is not None and current_value_buf:
        mapping[current_key] = "\n".join(current_value_buf).strip()
    return mapping, None


def _unquote(s: str) -> str:
    s = s.strip()
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        return s[1:-1]
    return s


def _check_manifest(root: Path, errors: list[str]) -> None:
    manifest_path = root / ".claude-plugin" / "plugin.json"
    if not manifest_path.exists():
        errors.append(f"Missing manifest: {manifest_path}")
        return
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"Invalid JSON in {manifest_path}: {exc}")
        return
    for key in ("name", "version", "description"):
        if key not in data:
            errors.append(f"{manifest_path}: missing required field '{key}'")
    name = data.get("name", "")
    if not re.match(r"^[a-z][a-z0-9\-]*$", name):
        errors.append(f"{manifest_path}: 'name' must be kebab-case (got {name!r})")
    version = data.get("version", "")
    if not re.match(r"^\d+\.\d+\.\d+", version):
        errors.append(f"{manifest_path}: 'version' must be semver (got {version!r})")


def _check_marketplace(root: Path, errors: list[str]) -> None:
    mp_path = root / ".claude-plugin" / "marketplace.json"
    if not mp_path.exists():
        # Optional — skip
        return
    try:
        data = json.loads(mp_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"Invalid JSON in {mp_path}: {exc}")
        return
    for key in ("name", "plugins"):
        if key not in data:
            errors.append(f"{mp_path}: missing required field '{key}'")
    if "plugins" in data and not isinstance(data["plugins"], list):
        errors.append(f"{mp_path}: 'plugins' must be an array")


def _check_skills(root: Path, errors: list[str], warnings: list[str]) -> int:
    skills_root = root / "skills"
    if not skills_root.is_dir():
        warnings.append(f"No skills/ directory at {skills_root}")
        return 0
    count = 0
    for skill_md in sorted(skills_root.glob("*/SKILL.md")):
        count += 1
        text = skill_md.read_text(encoding="utf-8")
        fm, err = _load_yaml_frontmatter(text)
        if err:
            errors.append(f"{skill_md}: {err}")
            continue
        if fm is None or not isinstance(fm, dict):
            errors.append(f"{skill_md}: frontmatter did not parse to a mapping")
            continue
        for key in ("name", "description"):
            if key not in fm or not fm.get(key):
                errors.append(f"{skill_md}: frontmatter missing '{key}'")
        # Ensure name matches directory name
        expected_name = skill_md.parent.name
        if fm.get("name") and fm.get("name") != expected_name:
            errors.append(
                f"{skill_md}: frontmatter name '{fm.get('name')}' does not match "
                f"directory '{expected_name}'"
            )
    return count


def _check_commands(root: Path, errors: list[str], warnings: list[str]) -> int:
    cmd_root = root / "commands"
    if not cmd_root.is_dir():
        warnings.append(f"No commands/ directory at {cmd_root}")
        return 0
    count = 0
    for cmd_md in sorted(cmd_root.glob("*.md")):
        count += 1
        text = cmd_md.read_text(encoding="utf-8")
        fm, err = _load_yaml_frontmatter(text)
        if err:
            errors.append(f"{cmd_md}: {err}")
            continue
        if fm is None:
            errors.append(f"{cmd_md}: frontmatter did not parse")
            continue
        if not fm.get("description"):
            errors.append(f"{cmd_md}: frontmatter missing 'description'")
    return count


def _check_agents(root: Path, errors: list[str], warnings: list[str]) -> int:
    agents_root = root / "agents"
    if not agents_root.is_dir():
        warnings.append(f"No agents/ directory at {agents_root}")
        return 0
    count = 0
    for agent_md in sorted(agents_root.glob("*.md")):
        count += 1
        text = agent_md.read_text(encoding="utf-8")
        fm, err = _load_yaml_frontmatter(text)
        if err:
            errors.append(f"{agent_md}: {err}")
            continue
        if fm is None:
            errors.append(f"{agent_md}: frontmatter did not parse")
            continue
        for key in ("name", "description"):
            if not fm.get(key):
                errors.append(f"{agent_md}: frontmatter missing '{key}'")
        model = fm.get("model")
        if model and model not in ("opus", "sonnet", "haiku"):
            warnings.append(
                f"{agent_md}: 'model' = {model!r} not in [opus, sonnet, haiku]"
            )
    return count


def _check_hooks(root: Path, errors: list[str], warnings: list[str]) -> None:
    hooks_json = root / "hooks" / "hooks.json"
    if not hooks_json.exists():
        # Hooks are optional
        return
    try:
        data = json.loads(hooks_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"Invalid JSON in {hooks_json}: {exc}")
        return
    if "hooks" not in data:
        errors.append(f"{hooks_json}: missing top-level 'hooks' key")
        return
    if not isinstance(data["hooks"], dict):
        errors.append(f"{hooks_json}: 'hooks' must be an object")
        return


def _check_scripts_executable(root: Path, warnings: list[str]) -> None:
    scripts_root = root / "scripts"
    if not scripts_root.is_dir():
        return
    for script in scripts_root.iterdir():
        if script.suffix in (".py", ".sh") and script.is_file():
            if not os.access(script, os.X_OK):
                warnings.append(
                    f"{script}: not executable (chmod +x recommended for hooks)"
                )


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    if not root.is_dir():
        print(f"ERROR: not a directory: {root}", file=sys.stderr)
        return 1

    errors: list[str] = []
    warnings: list[str] = []

    _check_manifest(root, errors)
    _check_marketplace(root, errors)
    n_skills = _check_skills(root, errors, warnings)
    n_commands = _check_commands(root, errors, warnings)
    n_agents = _check_agents(root, errors, warnings)
    _check_hooks(root, errors, warnings)
    _check_scripts_executable(root, warnings)

    # Required files
    for required in ("README.md", "LICENSE"):
        if not (root / required).exists():
            errors.append(f"Missing {root / required}")

    print("=" * 60)
    print(f"validate-plugin.py — {root}")
    print("=" * 60)
    print(f"Skills:   {n_skills}")
    print(f"Commands: {n_commands}")
    print(f"Agents:   {n_agents}")
    print()

    if warnings:
        print("WARNINGS:")
        for w in warnings:
            print(f"  {w}")
        print()

    if errors:
        print("VALIDATION FAILED")
        for e in errors:
            print(f"  {e}")
        return 1

    print("VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
