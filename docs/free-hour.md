# The free hour and Lem

This page is for a session that maintains Lem, in the repository of Lem. It is not for a user of
Lem.

An agent's free hour is a scheduled session with nobody at the terminal. Here it is the night's:
the scheduled `/lem night` of this repository takes it, and the scheduled `/lem retro` takes none
(`AGENTS.md`). The owner's ruling is short: the free hour searches and proposes, and makes no
branch. What it finds reaches him only as a backlog item that the reviewer passed. This page is
how. A session of another repository never edits Lem (`skills/lem/stages/learn.md`).

## Why the hour makes no branch

Every repository installs Lem as a plugin from `main` of this repository, and an update of the
plugin takes the commit there when the manifest's `version` changed. A commit on `main` that changes
the version reaches every project at its next update, before anybody else read it. A session that loads this clone with
`claude --plugin-dir` reads the files of the main checkout as they are saved. So a change in the
main checkout changes the running Lem of that session too.

A branch of the hour would come to a merge with no reviewer's read and no yes of the owner before
it. What Lem finds about itself reaches a project only through the agreed paths
(`docs/rulings/rulings.md`, "A project that uses Lem gets Lem's improvements only through the agreed
paths"). So the hour writes one thing: its proposals, into the night's file of the day,
`.lem/state/night/DATE.json`, which git ignores.

## The rules of the hour

- **One proposal for each finding, with what showed the need.** A session that went wrong, a
  measurement, a correction that came back, a check that failed by chance: the proposal names its
  place, its reason and its source with the date. A change nobody needed is not proposed
  (`docs/rulings/rulings.md`, "Opinionated and small").
- **Search with what reads.** The state folder (the tasks' records, the event log, the naps'
  waking notes), the files of the clone, and the checks: `bash tests/all.sh`, the one command under
  "Checks" in `AGENTS.md`, which runs every suite. `git status --short` of the main checkout shows
  the same after the hour as before it.
- **A proposal keeps the rules of a change here** (`AGENTS.md`, "Rules for a change here"): a
  number carries its source and date, a stage names a capability and never a tool, a change to a
  script comes with its test.
- **Write each proposal through the command `skills/lem/stages/night.md` names**, never the file
  by hand.
- **Change no file that git tracks, make no branch and no worktree, and never push.** Never check
  out another branch in the main checkout, and never commit, stash or reset there.
- **The owner's rulings are not the hour's to change** (`AGENTS.md`, "The owner's rulings").
- **This page adds its own limit**: a proposal leaves alone the choices of the maintaining session
  that `docs/rulings/rulings.md` lists as open to the owner, the builder agent's model and effort,
  and the defaults of the settings template. Those are not rulings. They are choices a person
  should see being made, and the hour runs with nobody there. A doubt about one is a proposal that
  names the doubt for the owner and proposes no change of it.

## What waits, and who decides

In the morning, after the retro, a fresh reviewer reads the night's proposals with the retro's
against the backlog bar (`skills/lem/stages/learn.md`, "retro"). A proposal it refutes stays in the
retro's file with its reason. It writes those that pass as backlog items in `.lem/state/backlog/`,
one for each area. The board's "Backlog" view shows each one as undecided, with "Start a task" and
"Drop". A task the owner starts from one lands as any task of Lem does, through its pull request.
