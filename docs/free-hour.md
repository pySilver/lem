# The free hour and Lem

This page is for a session that maintains Lem, in the repository of Lem. It is not for a user of
Lem.

An agent's free hour is a scheduled session with nobody at the terminal. Here it is the night's:
the scheduled `/lem night` of this repository takes it, and the scheduled `/lem retro` takes none
(`AGENTS.md`). The owner's ruling is short: the free hour searches and proposes, and makes no
branch. What it finds reaches him only as a backlog item that the reviewer passed. This page is
how. A session of another repository never edits Lem (`skills/lem/stages/learn.md`).

## Why the hour makes no branch

Every repository installs Lem as a plugin from the newest release tag of this repository: the
`lem` entry of `.claude-plugin/marketplace.json` names it as its `ref`, and an update takes it when
the `version` changed. A commit on `main` reaches no project until a release is cut from it, and a
release is one push of a commit and its tag, on the owner's word (`AGENTS.md`, "A release"). The
hour makes none. A session that loads this clone with
`claude --plugin-dir` reads the files of the main checkout as they are saved. So a change of a
branch in the main checkout changes the running Lem of that session too.

A branch of the hour would come to a merge with no reviewer's read and no yes of the owner before
it. What Lem finds about itself reaches a project only through the agreed paths
(`docs/rulings/rulings.md`, "A project that uses Lem gets Lem's improvements only through the agreed
paths"). So the hour writes one thing: its proposals, into the night's file of the day,
`.lem/state/night/DATE.json`, which git ignores.

## The rules of the hour

- **One proposal for each finding, with what showed the need.** A session that went wrong, a
  measurement, a correction that came back, a check that failed by chance: the proposal names its
  place, its reason and its source with the date. A change nobody needed is not proposed
  (`docs/rulings/rulings.md`, "Opinionated").
- **Search with what reads.** Read the tasks' records and journals, the naps' waking notes, and
  the files of the clone. Run `.venv/bin/python -I -B tests --level full` for the checks.
  `git status --short` of the main checkout shows the same after the hour as before it.
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
against the backlog bar (`skills/lem/stages/learn.md`, "retro"). A proposal it refutes stays with its reason
in the file that holds it: a night's proposal in the night's file, `.lem/state/night/DATE.json`,
and as an item of its own in `.lem/state/backlog/`, `worth: no` with that reason. The board shows
these items under "Decided against". The **Backlog** key excludes them. The reviewer writes the
proposals that pass as backlog items there, one for each area. The view shows each one as undecided,
with "Start a task" and "Drop". A task the owner starts from one lands as any task of Lem does,
through its pull request.
