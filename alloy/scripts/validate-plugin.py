#!/usr/bin/env python3
"""Validate the anneal-alloy Claude Code plugin.

Checks:
  - .claude-plugin/plugin.json exists and is valid JSON with required fields
  - .claude-plugin/marketplace.json exists and is valid JSON
  - commands/*.md have YAML frontmatter with `description`
  - skills/*/SKILL.md have YAML frontmatter with `name` + `description`
  - agents/*.md have YAML frontmatter with `name` + `description`
  - hooks/hooks.json (if present) is valid JSON with `hooks` top-level key
  - scripts/*.sh are executable
  - Required agent set for Alloy: metis, prometheus-alloy, synthesizer, momus,
    redteam-{security,scope,assumptions}, oracle, hephaestus, atlas
  - Required skill set for Alloy: metis, prometheus-alloy, synthesizer, momus,
    red-team-trinity, oracle, hephaestus, atlas

Exits 0 on pass, 1 on any error. Prints "VALIDATION PASSED" or "VALIDATION FAILED".
"""
import json
import sys
import os
from pathlib import Path

try:
    import yaml
except ImportError:
    print("VALIDATION FAILED: pyyaml not installed. Run: python3 -m pip install pyyaml", file=sys.stderr)
    sys.exit(1)


REQUIRED_AGENTS = {
    "metis",
    "prometheus-alloy",
    "synthesizer",
    "momus",
    "redteam-security",
    "redteam-scope",
    "redteam-assumptions",
    "oracle",
    "hephaestus",
    "atlas",
}

REQUIRED_SKILLS = {
    "metis",
    "prometheus-alloy",
    "synthesizer",
    "momus",
    "red-team-trinity",
    "oracle",
    "hephaestus",
    "atlas",
}

REQUIRED_COMMANDS = {"anneal"}


def parse_frontmatter(content: str):
    """Parse YAML frontmatter from a markdown file. Returns (frontmatter_dict, body) or (None, None)."""
    if not content.startswith("---"):
        return None, None
    parts = content.split("---", 2)
    if len(parts) < 3:
        return None, None
    try:
        fm = yaml.safe_load(parts[1])
        return fm, parts[2]
    except yaml.YAMLError:
        return None, None


def validate(root: Path):
    errors = []
    warnings = []

    # --- Manifest ---
    manifest_path = root / ".claude-plugin" / "plugin.json"
    if not manifest_path.exists():
        errors.append(f"Missing manifest: {manifest_path}")
    else:
        try:
            manifest = json.loads(manifest_path.read_text())
            for required_field in ("name", "version", "description"):
                if required_field not in manifest:
                    errors.append(f"{manifest_path}: missing required field '{required_field}'")
            if manifest.get("name") != "anneal-alloy":
                errors.append(f"{manifest_path}: name must be 'anneal-alloy', got '{manifest.get('name')}'")
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON in {manifest_path}: {e}")

    # --- Marketplace ---
    marketplace_path = root / ".claude-plugin" / "marketplace.json"
    if not marketplace_path.exists():
        warnings.append(f"Missing marketplace listing: {marketplace_path} (optional but recommended)")
    else:
        try:
            marketplace = json.loads(marketplace_path.read_text())
            if "name" not in marketplace or "plugins" not in marketplace:
                errors.append(f"{marketplace_path}: must have 'name' and 'plugins' fields")
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON in {marketplace_path}: {e}")

    # --- Commands ---
    commands_dir = root / "commands"
    found_commands = set()
    if commands_dir.exists():
        for cmd_md in sorted(commands_dir.glob("*.md")):
            content = cmd_md.read_text()
            fm, _ = parse_frontmatter(content)
            if fm is None:
                errors.append(f"{cmd_md}: no YAML frontmatter or parse failed")
                continue
            if "description" not in fm:
                errors.append(f"{cmd_md}: frontmatter missing 'description'")
            found_commands.add(cmd_md.stem)

    missing_commands = REQUIRED_COMMANDS - found_commands
    if missing_commands:
        errors.append(f"Missing required commands: {sorted(missing_commands)}")

    # --- Skills ---
    skills_dir = root / "skills"
    found_skills = set()
    if skills_dir.exists():
        for skill_md in sorted(skills_dir.glob("*/SKILL.md")):
            content = skill_md.read_text()
            fm, _ = parse_frontmatter(content)
            if fm is None:
                errors.append(f"{skill_md}: no YAML frontmatter or parse failed")
                continue
            if "name" not in fm or "description" not in fm:
                errors.append(f"{skill_md}: frontmatter missing 'name' or 'description'")
                continue
            dir_name = skill_md.parent.name
            if fm["name"] != dir_name:
                errors.append(f"{skill_md}: name '{fm['name']}' does not match directory '{dir_name}'")
            found_skills.add(dir_name)

    missing_skills = REQUIRED_SKILLS - found_skills
    if missing_skills:
        errors.append(f"Missing required skills: {sorted(missing_skills)}")

    # --- Agents ---
    agents_dir = root / "agents"
    found_agents = set()
    if agents_dir.exists():
        for agent_md in sorted(agents_dir.glob("*.md")):
            content = agent_md.read_text()
            fm, _ = parse_frontmatter(content)
            if fm is None:
                errors.append(f"{agent_md}: no YAML frontmatter or parse failed")
                continue
            if "name" not in fm or "description" not in fm:
                errors.append(f"{agent_md}: frontmatter missing 'name' or 'description'")
                continue
            if fm["name"] != agent_md.stem:
                errors.append(f"{agent_md}: name '{fm['name']}' does not match filename '{agent_md.stem}'")
            # Model field is optional but recommended
            if "model" not in fm:
                warnings.append(f"{agent_md}: no 'model' field (will inherit from harness)")
            found_agents.add(agent_md.stem)

    missing_agents = REQUIRED_AGENTS - found_agents
    if missing_agents:
        errors.append(f"Missing required agents: {sorted(missing_agents)}")

    # --- Hooks ---
    hooks_path = root / "hooks" / "hooks.json"
    if hooks_path.exists():
        try:
            hooks_data = json.loads(hooks_path.read_text())
            if "hooks" not in hooks_data:
                errors.append(f"{hooks_path}: missing top-level 'hooks' key")
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON in {hooks_path}: {e}")

    # --- Scripts ---
    scripts_dir = root / "scripts"
    if scripts_dir.exists():
        for sh in scripts_dir.glob("*.sh"):
            if not os.access(sh, os.X_OK):
                warnings.append(f"{sh}: not executable (will chmod +x on install)")

    # --- Report ---
    print("=" * 64)
    print(f"Validating plugin at: {root}")
    print("=" * 64)
    print(f"Commands found: {sorted(found_commands)}")
    print(f"Skills found:   {sorted(found_skills)}")
    print(f"Agents found:   {sorted(found_agents)}")
    print("-" * 64)

    if warnings:
        print(f"Warnings ({len(warnings)}):")
        for w in warnings:
            print(f"  - {w}")
        print()

    if errors:
        print(f"Errors ({len(errors)}):")
        for e in errors:
            print(f"  - {e}")
        print()
        print("VALIDATION FAILED")
        return 1

    print("VALIDATION PASSED")
    return 0


def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    if not root.exists():
        print(f"VALIDATION FAILED: path does not exist: {root}", file=sys.stderr)
        return 1
    return validate(root)


if __name__ == "__main__":
    sys.exit(main())
