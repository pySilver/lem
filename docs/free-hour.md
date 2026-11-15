# The free hour and Lem

An agent's free hour is a scheduled session with nobody at the terminal. It may improve Lem. The
owner's ruling is short: the free hour may edit Lem's skills on a branch of the clone, and it never
pushes; the owner or a session merges. This page is how.

## Why a branch in a worktree, and never the main checkout

A setup links Lem from the main checkout of this clone (`scripts/setup.py`). So a file edited
there is the file the next session reads, in every repository that uses Lem, the moment it is
saved: before any test ran and before anybody read it. A branch alone does not help either,
because a checkout of that branch in the main checkout swaps the running Lem for all of them.

So the work happens in a worktree of the clone:

```bash
python3 skills/lem/scripts/project.py worktree-dir free-hour-2026-11-15   # prints the path, in a folder git ignores
git worktree add -b free-hour/2026-11-15 PATH main
```

Everything after that is inside `PATH`.

## The rules of the hour

- **One change, with what showed the need.** A session that went wrong, a measurement, a
  correction that came back: name it in the commit message, with its date. A change nobody needed
  is not made (`AGENTS.md`, "Opinionated and small").
- **The rules of a change here hold** (`AGENTS.md`): a number carries its source and date, a
  stage names a capability and never a tool, a change to a script comes with its test.
- **Run the checks** in the worktree before the commit: the four commands under "Checks" in
  `AGENTS.md`.
- **Commit on the branch, and stop there.** Never push. Never merge. Never check out another
  branch in the main checkout, and never commit, stash or reset there.
- **The owner's rulings are not the hour's to change.** Neither is `agents/lem-builder.md`'s
  model, or a default in the settings template: those are choices of the owner's. A doubt about
  one is a line in the hour's own notes for him.
- **Leave the worktree.** The session that merges removes it.

## What waits, and who merges

```bash
git branch --list 'free-hour/*' --no-merged main
```

lists the branches that wait. A session that takes one reads its diff, runs the checks, has it
reviewed like any other part of Lem, and merges it or says why not. The owner may do the same.
A branch nobody took is not lost and not live.
