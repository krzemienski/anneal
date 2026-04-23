# Hephaestus Protocol & Examples

## Input schema

```yaml
plan_files: ["plan/plan.md", "plan/phase-*.md"]
envelopes:
  metis: "..."
  momus: "..."
  redteam_*: "..."
  oracle: "..."
scratch_worktree: "/tmp/anneal-hephaestus-{run_id}/"   # scratch dir for builds
evidence_dir: "reviews/hephaestus-evidence/"
```

## Output schema

```yaml
reviewer: hephaestus
verdict: PASS | FAIL
build:
  command: "<actual command executed>"
  output: "<actual stdout+stderr, not summarized>"
  exit_code: <int>
runtime:
  - step: "<description>"
    command: "<command>"
    output: "<actual output>"
    screenshot: "<path if UI>"
    timestamp: "<ISO-8601>"
evidence_files:
  - "reviews/hephaestus-evidence/step-01-*.txt"
  - "reviews/hephaestus-evidence/step-02-*.png"
success_criteria_check:
  - criterion: "<from plan>"
    met: true | false
    evidence_cited: "<file>"
failures: []   # populated if verdict is FAIL
```

## Validation protocol

### Step 1 · Set up scratch worktree

- Create `/tmp/anneal-hephaestus-{run_id}/`.
- Copy or git-clone the project into the scratch.
- All subsequent work happens in scratch; the production project stays read-only.

### Step 2 · Execute plan phases in order

For each phase in `plan/phase-NN-*.md`:
- Read "Implementation steps."
- Execute each step verbatim against the scratch worktree.
- Capture stdout + stderr + exit code for every command.
- Write evidence to `reviews/hephaestus-evidence/step-NN-{phase}-{action}.{ext}`.

### Step 3 · Check success criteria

For each phase's "Success criteria":
- Read the criterion verbatim.
- Check the scratch state against it.
- Cite which evidence file proves the criterion (file path + line range if applicable).
- Mark `met: true` only if evidence is non-empty and matches the criterion.

### Step 4 · Aggregate verdict

- PASS iff every success criterion across every phase met.
- FAIL if any criterion not met, or any build step exited non-zero.

## Iron rules (non-negotiable)

1. **No mocks.** Never create mock objects, test doubles, stubs, or fixtures.
2. **No test files.** Never create `*.test.*`, `*.spec.*`, `*_test.*`.
3. **No test frameworks.** Never install jest, pytest, mocha, rspec, etc.
4. **Evidence is real.** Empty files are INVALID. Zero-byte PNGs are INVALID. "Command succeeded" without the log is INVALID.
5. **If the real system does not work, FIX THE REAL SYSTEM.** Never modify the plan to make verdict PASS. Never skip criteria. Never claim PASS without evidence.
6. **Every screenshot describes what you SEE.** Not "screenshot exists" — "screenshot shows the install menu with anneal-alloy listed."
7. **Every build output is quoted verbatim.** Not summarized. The full compile/build log, unless it exceeds 10k lines, in which case the last 200 lines and first 100 lines.

## Alloy-specific addendum

The plan Hephaestus validates is a *synthesized* blend from N variants. A common failure mode: a step that read well in isolation (from one variant) fails in the context of steps from another variant (integration gap).

When FAIL, Hephaestus notes in `failures`:
- Which phase failed.
- Whether the failing step's provenance traces to one variant or the blend.
- If the blend introduced the failure, cite `synthesis-provenance.md` for the contradiction.

This feedback loops back to the Intent Gate (Metis) on re-loop — a blend-integration failure tells Metis the conservative-default resolution rule chose wrong, and the next run's directives need to be more specific. The re-loop does NOT route to Synthesizer: rebiasing the planners with sharper directives is what fixes the root cause; re-blending the same variants would reproduce the same failure.

## Example evidence capture

```
reviews/hephaestus-evidence/
├── step-01-validate-plugin-py-output.txt    # "VALIDATION PASSED"
├── step-02-plugin-list-output.txt           # "anneal-alloy    0.1.0"
├── step-03-anneal-command-exit-code.txt     # "0"
├── step-04-n5-parallel-planner-pids.txt     # 5 distinct PIDs from ps
├── step-05-synthesis-provenance-contents.md # actual provenance output
├── step-06-plan-dir-listing.txt             # ls -la plan/
├── step-07-xml-schema-validation.txt        # xmllint output
└── evidence-inventory.txt                    # every file + byte count
```

## Example verdict (PASS)

```yaml
reviewer: hephaestus
verdict: PASS
build:
  command: "python3 scripts/validate-plugin.py /Users/nick/Desktop/anneal/alloy"
  output: |
    Checked manifest: /Users/nick/Desktop/anneal/alloy/.claude-plugin/plugin.json
    Checked 8 skills, 10 agents, 1 command.
    VALIDATION PASSED
  exit_code: 0
runtime:
  - step: "Install via /plugin marketplace add"
    command: "claude /plugin marketplace add /Users/nick/Desktop/anneal/alloy"
    output: "Marketplace registered: anneal-alloy-dev"
    timestamp: "2026-04-22T14:52:31Z"
  - step: "Install plugin"
    command: "claude /plugin install anneal-alloy@anneal-alloy-dev"
    output: "Plugin installed: anneal-alloy v0.1.0"
    timestamp: "2026-04-22T14:52:45Z"
  - step: "Verify /plugin list shows anneal-alloy"
    command: "claude /plugin list | grep anneal-alloy"
    output: "anneal-alloy    0.1.0    Tournament Consensus..."
    timestamp: "2026-04-22T14:52:58Z"
evidence_files:
  - "reviews/hephaestus-evidence/step-01-validate-plugin-output.txt"
  - "reviews/hephaestus-evidence/step-02-marketplace-add-output.txt"
  - "reviews/hephaestus-evidence/step-03-install-output.txt"
  - "reviews/hephaestus-evidence/step-04-plugin-list-grep.txt"
  - "reviews/hephaestus-evidence/evidence-inventory.txt"
success_criteria_check:
  - criterion: "validate-plugin.py exits 0"
    met: true
    evidence_cited: "step-01-validate-plugin-output.txt"
  - criterion: "anneal-alloy appears in /plugin list"
    met: true
    evidence_cited: "step-04-plugin-list-grep.txt"
failures: []
```
