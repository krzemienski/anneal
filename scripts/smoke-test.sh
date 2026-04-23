#!/usr/bin/env bash
# Smoke test: verify all three anneal plugins are structurally valid.
# Runs each plugin's validate-plugin.py and reports pass/fail.
#
# Usage: bash /Users/nick/Desktop/anneal/scripts/smoke-test.sh

set -u  # fail on unset vars, but continue on individual errors for full report

ROOT="/Users/nick/Desktop/anneal"
PLUGINS=(cast alloy temper)
FAILURES=0

echo "=================================================================="
echo "  Anneal Smoke Test · $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "=================================================================="
echo

for p in "${PLUGINS[@]}"; do
  echo "--- $p ---"
  plugin_dir="$ROOT/$p"

  if [[ ! -d "$plugin_dir" ]]; then
    echo "  FAIL: $plugin_dir does not exist"
    FAILURES=$((FAILURES + 1))
    continue
  fi

  # 1. Manifest present + valid JSON
  manifest="$plugin_dir/.claude-plugin/plugin.json"
  if [[ ! -f "$manifest" ]]; then
    echo "  FAIL: Missing $manifest"
    FAILURES=$((FAILURES + 1))
    continue
  fi

  if ! python3 -c "import json; json.load(open('$manifest'))" 2>/dev/null; then
    echo "  FAIL: Invalid JSON in $manifest"
    FAILURES=$((FAILURES + 1))
    continue
  fi

  name=$(python3 -c "import json; print(json.load(open('$manifest'))['name'])")
  version=$(python3 -c "import json; print(json.load(open('$manifest'))['version'])")
  echo "  Manifest: name=$name version=$version"

  # 1b. Regression guard: plugin.json must NOT contain fields that break --plugin-dir loading.
  # Known-safe top-level set: name, version, description, author, homepage, repository, license, keywords.
  # The fields "skills", "commands", "agents", "requires", "hooks" break --plugin-dir load silently.
  bad_fields=$(python3 -c "
import json, sys
ALLOWED = {'name','version','description','author','homepage','repository','license','keywords'}
m = json.load(open('$manifest'))
extra = [k for k in m.keys() if k not in ALLOWED]
if extra:
    print(','.join(extra))
")
  if [[ -n "$bad_fields" ]]; then
    echo "  FAIL: plugin.json contains non-standard top-level fields that break --plugin-dir: $bad_fields"
    echo "        Allowed set: name, version, description, author, homepage, repository, license, keywords"
    FAILURES=$((FAILURES + 1))
  fi

  # 2. Required directories
  for sub in commands skills agents; do
    if [[ ! -d "$plugin_dir/$sub" ]]; then
      echo "  WARN: $plugin_dir/$sub missing (not required but expected)"
    else
      count=$(find "$plugin_dir/$sub" -type f -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
      echo "  $sub/: $count .md files"
    fi
  done

  # 2b. Agents must declare `model:` in frontmatter (opus|sonnet|haiku)
  if [[ -d "$plugin_dir/agents" ]]; then
    missing_model=0
    for af in "$plugin_dir"/agents/*.md; do
      [[ -f "$af" ]] || continue
      if ! head -20 "$af" | grep -qE "^model:\s*(opus|sonnet|haiku)"; then
        echo "  FAIL: $(basename $af) missing or invalid model: in frontmatter"
        missing_model=$((missing_model + 1))
      fi
    done
    if [[ $missing_model -gt 0 ]]; then
      FAILURES=$((FAILURES + 1))
    fi
  fi

  # 2c. Command body must explicitly prohibit run_in_background: true on Red-Team dispatch.
  # This prevents regression of the "pipeline stops after red-team dispatch" bug discovered
  # during E2E validation on 2026-04-22.
  cmd_file="$plugin_dir/commands/anneal.md"
  if [[ -f "$cmd_file" ]]; then
    if ! grep -qiE "do NOT set .run_in_background: true|do not set .run_in_background" "$cmd_file"; then
      echo "  FAIL: commands/anneal.md missing the 'do NOT set run_in_background: true' dispatch guardrail"
      echo "        This guardrail prevents the pipeline from stopping after red-team dispatch."
      FAILURES=$((FAILURES + 1))
    fi
  fi

  # 2d. No hardcoded absolute user paths in shipped machine-facing JSON.
  # Description strings in marketplace.json are exempt if they use <placeholder> form.
  if grep -rlE '"/(Users|home)/[a-zA-Z0-9_-]+/' "$plugin_dir/.claude-plugin/" 2>/dev/null | grep -v '\.bak$' > /dev/null; then
    echo "  FAIL: .claude-plugin/ contains hardcoded absolute user path(s)"
    grep -rnE '"/(Users|home)/[a-zA-Z0-9_-]+/' "$plugin_dir/.claude-plugin/" 2>/dev/null | grep -v '\.bak$' | head -3 | sed 's/^/    /'
    FAILURES=$((FAILURES + 1))
  fi

  # 3. Per-plugin validator
  validator="$plugin_dir/scripts/validate-plugin.py"
  if [[ ! -f "$validator" ]]; then
    echo "  WARN: No validate-plugin.py in $plugin_dir/scripts/"
  else
    echo "  Running validate-plugin.py..."
    if python3 "$validator" "$plugin_dir" 2>&1 | sed 's/^/    /'; then
      echo "  validate-plugin.py: PASS"
    else
      echo "  validate-plugin.py: FAIL"
      FAILURES=$((FAILURES + 1))
    fi
  fi

  echo
done

echo "=================================================================="
if [[ $FAILURES -eq 0 ]]; then
  echo "  RESULT: ALL PLUGINS PASS"
  exit 0
else
  echo "  RESULT: $FAILURES FAILURE(S)"
  exit 1
fi
