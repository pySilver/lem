---
worth: yes
where: tests/test-lem.sh:doctor
added: 2026-11-16
---
# The doctor tests read the clone they run in

Three checks of `tests/test-lem.sh` fail in a clone that links Lem into itself with
`scripts/setup.py --project .`: "a machine with Claude Code and no lem-builder agent fails the
check", the check of Lem as a plugin, and "with git ... the check passes". The test runs
`doctor.py` from the clone's root with a fake home, and `doctor.py` looks for the builder in the
repository it runs in (`git rev-parse --show-toplevel`, then `.claude/agents/lem-builder.md`)
before the home. The trial's link is there, so the check finds a builder where the test expects
none, and the detail names the clone's file in the place of the fake home's.

Seen on 2026-11-16 at Lem's own onboarding, on `main` at 715d0d3: `3 check(s) failed`, every
other check passed. A task's worktree has no `.claude/` folder, because git ignores it, so the
lookup finds nothing there; the gate of a Lem task should be green on these three, and that is
not run yet.

What it needs: the doctor checks run from a throwaway directory (a repository of their own under
the test's work folder), so the clone's own links do not reach them.
