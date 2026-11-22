---
worth: later
where: skills/lem/scripts/land.py:checks
added: 2026-11-22
---
# An ignored __pycache__ left before the checks makes them red

The checks of `merge-leaves-board-lock` (2026-11-22, tip 4b665ab) were red on `bash tests/all.sh`
with `failed: test-gate-panel test-ask-expert lem-command __pycache__`. All four were the same
check, a `__pycache__` folder under `skills/`, and the folder held one file,
`skills/lem/scripts/__pycache__/serve.cpython-315.pyc`, about 2.5 hours older than the run: an
earlier run in the worktree had imported `serve` without `-B`. `.gitignore` hides `__pycache__/`,
so the builder's last check (`git status --short` empty, rule 10 of `agents/lem-builder.md`) did not
see it, and the checks' own clean-up (`removed_untracked`) takes only what git neither tracks nor
ignores and what the run itself wrote. A repair builder found the cause, removed the folder, and
the three suites passed; the landing paid one repair builder and a second run of the checks for a
file of no commit. Which agent left it is not known. Two places could take a fix: the checks could
remove an ignored `__pycache__` under the worktree before the first command, or rule 10 could read
`git status --short --ignored`.
