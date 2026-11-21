---
decided: 2026-11-21
area: The plan, the build and the tests
---

# Two builders of one plan that run at one moment commit only their own paths

`stages/build.md` lets a lead start two builders at one moment when their tasks touch no common
file. Each builder of the owner's ruling ([Each task of a plan gets a fresh builder](../../docs/rulings/each-task-of-a-plan-gets-a-fresh-builder.md))
gets a context of its own, but both work in the task's one worktree, with one index: no builder
gets a worktree of its own (`harness/claude-code.md`, `spawn-builder`). Rules 5 and 10 of
`agents/lem-builder.md` had each one commit its own work and end with an empty `git status
--short`. So builder A could stage its files, builder B could stage its own, and A's plain `git
commit` took both under A's subject; or A's last check saw B's new files and removed them as
leftovers of its own runs. An outside review of 2026-11-21 (Sol, finding 8) named it.

The event log of this repository held 54 `builder.start` events in 15 tasks, and four pairs that
started within one second of each other: away-for-the-whole-machine tasks 3 and 4,
interview-in-a-companion tasks 1 and 5 and tasks 2 and 3, and owner-task-order-stays tasks 1 and
2. In `git log --name-only`, each commit of those pairs (`aea3908` and `3150f38`; `d524811` and
`3839a14`; `b272c59` and `2f1dbd0`; `47ec7fa` beside `9a3a279`, `951a719`, `16bf751`, `de62843`
and `2517230`) holds only files of its own task, by the task sections of their plans. No mixed
commit came of them yet.

The parallel run stays, and it is made safe in the text:

- A builder commits by naming its paths, `git add -- PATHS` and `git commit -m MESSAGE --
  PATHS`, which commits those paths whatever else is staged, and never stages everything.
- When git says that `index.lock` exists, it runs its command again after a few seconds and
  never removes the lock.
- The lead's brief says when another builder runs, with that task's files, and then the
  builder's check of a clean tree is about its own paths; a file of the other task is not its to
  commit or remove. Once both ended, the lead's `git status --short` of the worktree is empty.

The other way, one builder at a time in a plan, gives up the overlap for a risk the four pairs did
not show. A worktree for each builder would need its branch merged back by the lead, which writes
no code. What this does not cover: a test of one builder that runs over the other's half-done
files can fail; the builder's report says so, and the checks before the pull request run the
whole suite over both commits.
