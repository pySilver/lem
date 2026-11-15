---
worth: yes
where: scripts/setup.py
added: 2026-11-15
---
# Lem does not build Lem yet

Every part of Lem so far was built by one session that wrote the code itself and had Codex
review it by hand. The owner agreed on 2026-11-15 that Lem's own repository should use Lem,
after his `/lem init` run in a scratch repository and before a real project.

What it needs, and what the owner has not ruled on:

- **The settings.** A `.lem/project.toml` here: the base branch `main`; the gate, which is the
  four commands under "Checks" in `AGENTS.md`; the careful paths, where a defect costs most
  (`skills/lem/scripts/*`, `scripts/*`, `agents/*`); who lands; the reviewer.
- **How this clone links Lem to itself.** `scripts/setup.py --project .` links the clone's own
  skills into its own `.claude`, so only sessions in this repository see them.
- **One hazard to state where a reader meets it.** A setup links Lem from this clone's main
  checkout. A build in a task's worktree leaves the running Lem alone, but a landing changes the
  running Lem at that moment, for every repository that links to this clone, and for the landing
  itself: `land.py` and the stage text it follows are among the files that change under it. A
  landing here should end before the next step reads a stage file again, or the land script
  should run from a copy.

Recommendation: write the settings with the owner in a `/lem init` run in this repository, with
`land = "owner"` at first, so that the first landings of Lem by Lem are his to make.

The owner asked "its cool to use Lem for lem development. Will it be possible?" on 2026-11-15, in
the session that started Lem, and agreed to the order above.
