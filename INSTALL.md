# Anneal · Installation Cheatsheet

Three Claude Code plugins, three architectures, one umbrella marketplace.

## Quick install — all three

```bash
# Add the umbrella dev marketplace (includes all 3)
/plugin marketplace add /Users/nick/Desktop/anneal

# Install all three
/plugin install anneal-cast@anneal-umbrella-dev
/plugin install anneal-alloy@anneal-umbrella-dev
/plugin install anneal-temper@anneal-umbrella-dev

# Restart Claude Code for plugins to register
```

## Quick install — one at a time

Each plugin ships its own dev marketplace (`.claude-plugin/marketplace.json`) so you can install them independently.

### Cast (linear)

```bash
/plugin marketplace add /Users/nick/Desktop/anneal/cast
/plugin install anneal-cast@anneal-cast-dev
```

### Alloy (tournament)

```bash
/plugin marketplace add /Users/nick/Desktop/anneal/alloy
/plugin install anneal-alloy@anneal-alloy-dev
```

### Temper (fixed-point deepen)

```bash
/plugin marketplace add /Users/nick/Desktop/anneal/temper
/plugin install anneal-temper@anneal-temper-dev
```

## Verify install

After restart, all three commands should be available:

```
/anneal-cast:anneal      # linear, single-pour
/anneal-alloy:anneal     # tournament, N parallel planners
/anneal-temper:anneal    # fixed-point deepen, iterative
```

## Head-to-head testing

Same task, three architectures. Compare output quality, cost, wall-clock.

```
/anneal-cast:anneal "rewrite the session-timeout handler to use JWT exp claims"
/anneal-alloy:anneal "rewrite the session-timeout handler to use JWT exp claims" --versions 5
/anneal-temper:anneal "rewrite the session-timeout handler to use JWT exp claims" --depth 3
```

Each run emits to `~/Desktop/anneal-runs/{run_id}/` with:
- `{architecture}-{run_id}.xml` — Opus 4.7 semantic XML prompt
- `plan/plan.md` — executable plan
- `plan/phase-*.md` — per-phase detail files

## Uninstall

```bash
/plugin uninstall anneal-cast@anneal-umbrella-dev
/plugin uninstall anneal-alloy@anneal-umbrella-dev
/plugin uninstall anneal-temper@anneal-umbrella-dev
/plugin marketplace remove anneal-umbrella-dev
```

## Debug

If a plugin fails to load, run with `--debug`:

```bash
claude --debug
```

Look for:
- "Plugin registration: anneal-cast" (should appear)
- Skill discovery logs
- Command registration logs

Common issues:
- **Plugin not loading** → check `/Users/nick/Desktop/anneal/{name}/.claude-plugin/plugin.json` is valid JSON
- **Commands not appearing** → ensure `commands/` is at plugin root, not inside `.claude-plugin/`
- **Hooks not firing** → ensure `hooks/hooks.json` is valid JSON and scripts are `chmod +x`

## Validation

Each plugin ships `scripts/validate-plugin.py`. Run before install:

```bash
python3 /Users/nick/Desktop/anneal/cast/scripts/validate-plugin.py
python3 /Users/nick/Desktop/anneal/alloy/scripts/validate-plugin.py
python3 /Users/nick/Desktop/anneal/temper/scripts/validate-plugin.py
```

Expected output: `VALIDATION PASSED` for each.
