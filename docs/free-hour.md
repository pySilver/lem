# The free hour and Lem

An agent's free hour is a scheduled session with nobody at the terminal. It may improve Lem. The
owner's ruling is short: the free hour may edit Lem's skills on a branch of the clone, and it never
pushes; the owner or a session merges. This page is how.

## Why a branch in a worktree, and never the main checkout

A setup links Lem from the main checkout of this clone (`scripts/setup.py`). So a file edited
there is the file the next session reads, in every repository that uses Lem, the moment it is
saved: before any test ran and before anybody read it. A branch alone does not help either,
because a checkout of that branch in the main checkout swaps the running Lem for all of them.

So the work happens in a worktree of the clone, on a branch named after the run:

```bash
stamp=$(date -u +%Y-%m-%d-%H%M)
where=$(python3 skills/lem/scripts/project.py worktree-dir "free-hour-$stamp")
git worktree add -b "free-hour/$stamp" "$where" main
```

The second line prints where the worktree goes and makes the folder that holds it,
`.lem/worktrees/`, with an ignore file in it. That folder and that file are the one thing the
hour writes in the main checkout: no session reads them, and git does not show them. An agent
whose shell refuses a variable writes the three values out. Everything after that is inside the
worktree.

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
- **The owner's rulings are not the hour's to change** (`AGENTS.md`, "The owner's rulings").
- **This page adds its own limit**: the hour also leaves alone the designs `AGENTS.md` lists as
  open to the owner, the builder agent's model and effort, and the defaults of the settings
  template. Those are not rulings. They are choices a person should see being made, and the hour
  runs with nobody there. A doubt about one is a line in the hour's own notes for the owner.
- **Leave the worktree.** The session that merges removes it.

## What waits, and who merges

```bash
git branch --list 'free-hour/*' --no-merged main
```

lists the branches that wait. A session that takes one reads its diff, runs the checks, has it
reviewed like any other part of Lem, and merges it or says why not. The owner may do the same.
A branch nobody took is not lost and not live.
