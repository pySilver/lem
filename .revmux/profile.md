# Lem: what a reviewer here reads first

A draft written at Lem's onboarding on 2026-11-16. revmux copies this file into every round.

## What the project is

Lem is a set of Claude Code skills that carries one unit of work in a repository from an ask to a
pull request that says green or not green. Most of the repository is instructions to agents
(`skills/*/SKILL.md`, `skills/lem/stages/*.md`, `skills/lem/prompts/*.md`) and standard-library
Python scripts that keep a task's state and do its landing (`skills/lem/scripts/*.py`). This
repository is also the Lem that runs: a change that reaches `main` changes every session that uses
it.

## Read first

- `AGENTS.md`: the rules of a change here and one sentence for each of the owner's rulings, whose
  full text is in `docs/rulings/`. A finding that asks for what a ruling forbids is wrong; a change
  that bends a ruling is a must-fix.
- `.lem/profile.md`: the same project as the personas read it.
- For a script: its test file in `tests/` (a change to a script comes with its test).
- For a stage file: `skills/lem/SKILL.md`, which holds what is true in every stage.

## What counts as a defect here

- A sentence in a skill file that an agent would follow into a wrong act, or that two stage files
  say differently.
- A number with no source and date; a tool's name in a stage file (it belongs in
  `skills/lem/harness/claude-code.md` or a part of it in `claude-code/`).
- A script that falls back without a word, or refuses with no fix in its message.
- Documentation that describes a past state.

## Findings rejected here

None yet.
