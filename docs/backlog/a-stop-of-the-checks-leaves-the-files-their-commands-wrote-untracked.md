---
worth: later
where: skills/lem/scripts/land.py:checks_body
added: 2026-11-19
---
# A stop of the checks leaves the files their commands wrote untracked

A command of the checks writes a file git neither tracks nor ignores (Python's bytecode in a repository with no ignore rule). The run is stopped, the interrupt leaves checks_body from the command loop's finally, and the removal of untracked output after the loop never runs. The next `lem land checks SLUG` or `lem land base SLUG` is refused by need_worktree for a worktree with changes nobody committed. The base commit's cmd_checks raised from its except KeyboardInterrupt before the same removal.

Seen outside the change by review round 1 of task landing-in-the-background (2026-11-19); the base commit has it.
