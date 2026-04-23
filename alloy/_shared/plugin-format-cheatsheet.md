# Claude Code Plugin Format — Cheatsheet

For the three anneal plugins. Every plugin needs this structure.

## Directory layout

```
{plugin-name}/
├── .claude-plugin/
│   ├── plugin.json           # Manifest (required)
│   └── marketplace.json      # Marketplace listing (optional but recommended)
├── commands/
│   └── *.md                  # Slash commands. Filename becomes /{plugin-name}:{cmd}
├── skills/
│   └── {skill-name}/
│       └── SKILL.md          # Skill definition with YAML frontmatter
├── agents/
│   └── *.md                  # Agent definitions with YAML frontmatter
├── hooks/                    # Optional — lifecycle hooks
├── scripts/                  # Optional — support scripts
├── diagrams/                 # Optional — visual docs
├── docs/                     # Optional — extended docs
├── README.md
├── PRD.md
├── ARCHITECTURE.md
└── LICENSE                   # MIT recommended
```

## plugin.json

```json
{
  "name": "anneal-cast",
  "version": "0.1.0",
  "description": "Linear single-pour architecture of the Anneal plugin family.",
  "author": {
    "name": "Nick Krzemienski",
    "email": "nick@krzemienski.com"
  },
  "homepage": "https://github.com/krzemienski/anneal",
  "repository": "https://github.com/krzemienski/anneal",
  "license": "MIT",
  "keywords": ["plan", "review", "multi-agent", "annealing", "claude-code", "plugin"],
  "requires": {
    "external_tools": ["claude", "bash"],
    "notes": "claude CLI for agent dispatch; bash 4+ for scripts"
  },
  "skills": "./skills/",
  "commands": "./commands/",
  "agents": "./agents/"
}
```

Field notes:
- `name`: kebab-case. Claude Code uses this as the slash-command namespace (`/anneal-cast:...`).
- `version`: semver.
- `skills` / `commands` / `agents`: directory paths relative to plugin root.

## marketplace.json

Only if publishing. Describes the marketplace-visible metadata.

```json
{
  "name": "anneal-cast",
  "displayName": "Anneal · Cast",
  "description": "Linear single-pour plan-review plugin",
  "longDescription": "...",
  "categories": ["planning", "review", "multi-agent"],
  "icon": "./assets/icon.png",
  "screenshots": ["./diagrams/cast-architecture.html"]
}
```

## Hook file format — IMPORTANT

Hooks go in a **single JSON file** at `hooks/hooks.json`. NOT markdown. NOT individual files per hook.

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/format-code.sh"
          }
        ]
      }
    ],
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/init.sh"
          }
        ]
      }
    ]
  }
}
```

**⚠ DO NOT** reference `hooks/hooks.json` in `plugin.json`'s `hooks` field — Claude Code auto-loads it, and an explicit reference creates "Duplicate hooks file detected" errors.

**Hook events available:** `PreToolUse`, `PostToolUse`, `UserPromptSubmit`, `Notification`, `Stop`, `SubagentStop`, `SessionStart`, `SessionEnd`, `PreCompact`.

**Always use `${CLAUDE_PLUGIN_ROOT}`** in command paths — never hardcoded paths.

## Command file format

`commands/anneal.md`:

```markdown
---
description: Run the Cast architecture against a task and emit XML + plan.
argument-hint: "<task description>"
---

# /anneal-cast:anneal

You are invoking the Cast architecture — single-pour linear plan generation with always-on red team and functional validation.

## Flow

1. Intent Gate ...
2. Probe via Explore ...
3. Enrich via Metis ...
4. Plan via Prometheus (one call) ...
5. Review via Momus + Red-Team Trinity + Oracle (parallel) ...
6. Validate via Hephaestus ...
7. Emit via Atlas — XML + plan directory ...

## Input

The user's task is passed as `$1`. If empty, prompt for it.

## Invariants (non-negotiable)

- Red team always runs.
- Validate always runs.
- Output is XML + plan directory.
- Skill enrichment is always on.
- Re-loop on FAIL is unbounded.

## Execution

... (detailed prompt instructions)
```

## Skill file format

`skills/metis/SKILL.md`:

```markdown
---
name: metis
description: "Pre-plan consultant. Reads the user's task and the probe report and flags ambiguity, unstated requirements, and slop-risk patterns. Returns directives for the planner. Triggers: invoked at stage 3 of every anneal run."
license: MIT
---

# Metis — Pre-Plan Consultant

{body — purpose, when to invoke, input schema, output schema, example, anti-patterns}
```

Skill frontmatter rules:
- `name`: kebab-case, matches directory name
- `description`: required. Include explicit trigger keywords in the description so the skill auto-discovers.
- `license`: optional but recommended

## Agent file format

`agents/oracle.md`:

```markdown
---
name: oracle
description: Architecture synthesizer. Reads all reviewer envelopes and emits a bird's-eye verdict (SAFE/CAUTION/RISKY/BLOCK).
model: opus
---

{system prompt — typically copy from _shared/agent-prompts-core.md + architecture addenda}
```

Agent frontmatter rules:
- `name`: kebab-case
- `description`: used for sub-agent auto-discovery
- `model`: `opus` | `sonnet` | `haiku` | omit to inherit

## Validation

Every plugin ships `scripts/validate-plugin.py`:

```python
#!/usr/bin/env python3
"""Validate a Claude Code plugin's manifest, skills, commands, agents."""
import json, sys, os, re, yaml
from pathlib import Path

def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    errors = []

    # Manifest
    manifest = root / ".claude-plugin" / "plugin.json"
    if not manifest.exists():
        errors.append(f"Missing {manifest}")
    else:
        try:
            json.loads(manifest.read_text())
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON in {manifest}: {e}")

    # Skills
    for skill_md in (root / "skills").glob("*/SKILL.md"):
        content = skill_md.read_text()
        if not content.startswith("---"):
            errors.append(f"{skill_md}: no YAML frontmatter")
            continue
        try:
            _, fm, _ = content.split("---", 2)
            yaml.safe_load(fm)
        except Exception as e:
            errors.append(f"{skill_md}: frontmatter parse failed — {e}")

    # Commands
    for cmd_md in (root / "commands").glob("*.md"):
        content = cmd_md.read_text()
        if not content.startswith("---"):
            errors.append(f"{cmd_md}: no YAML frontmatter")

    # Report
    if errors:
        print("VALIDATION FAILED")
        for e in errors: print(" ", e)
        sys.exit(1)
    else:
        print("VALIDATION PASSED")

if __name__ == "__main__":
    main()
```
