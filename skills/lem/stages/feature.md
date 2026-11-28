# A feature in parts

Read when a stage names this file: an ask that says "as a feature" or "in parts", an ask `part of
NAME: ...`, a task whose record names `part_of` (`lem task show SLUG`), the wake `lem: NAME sync`,
and the landing of a feature or of a part. No other task reads it.

A feature is one task, NAME, whose work goes in parts. Its branch is `feature/NAME`, cut from the
project's base. Each part is an ordinary task whose base is `feature/NAME`: its own checks, its own
review and its own small pull request into that branch. Nothing reaches the base until the end,
and no release flag hides a part. NAME waits `queued` for all of its parts, takes in the base after
each merge to the base (the sync), and at the end goes to the base in one pull request, one squashed
commit, which the owner approves. To throw it away before the end, he drops NAME and deletes one
branch; after the end, he reverts one commit. That is his direction of 2026-11-25
(`docs/rulings/rulings.md`, "The review, the pull request and the merge").

Lem never proposes parts. A task the owner did not ask as a feature stays one task, however large:
a plan of more than seven tasks is two asks (`stages/plan.md`, step 1), its report says so, and he
may then ask the rest as a feature. A feature has no fast track: `lem task split` refuses criteria
of `Size: small`.

## The ask

`/lem new as a feature: <ask>`, or an ask that says "in parts". "Open the task" of `stages/new.md`
as for any ask, with the whole line as he typed it as `--ask`, so that every session of NAME reads
his words. A ticket goes with the feature, never with a part: `lem task open` refuses `--ticket`
with `--part-of`. The feature takes the standard track with an interview, from a ticket too: the
read of step 8 of "The request" with `--track full --then interview --wait interview`, then
`stages/interview.md`, with the steps below in their places.

## The criteria in groups

At step 4 of the interview, write the criteria in one group for each part, in the order the parts
are built, and one group for what only the whole feature meets. The numbers run on across the
groups:

```
## Acceptance criteria

Size: full, because the server and both apps save an item, in three parts.

### save-endpoint: the server saves an item and returns it

1. A saved item comes back from the server: item 17 saved by Ania is in her list.

### ios-save-button: the iOS app saves the item it shows

2. The iOS app saves the item on its screen: a tap on Save adds item 17 to her list.

### android-saved-list: the Android app lists the saved items (independent)

3. The Android app lists her saved items: item 17 is in the list after a refresh.

### The whole feature

4. An item saved on the iOS app shows on the Android app: item 17 shows on both.
```

- A part's heading is `### SLUG: WHAT IT DOES`. The slug follows step 2 of "The request" and is
  free: no task has it. The words are the part's ask.
- Each part waits for the part before it. A heading that ends in `(independent)` waits for none
  and starts at once.
- `### The whole feature` holds at least one criterion. The lead of the end builds its tests.
- A part is one pull request a reviewer reads in one sitting (a guess, not a measurement). A part
  that holds two outcomes is two parts.

At step 5, show each group under its heading. The personas read the whole set once.

At step 6, the page shows each group under its heading, with the order and the parts that start at
once. That page alone takes one more fixed answer, "One pull request". His yes approves the
criteria and the split together:

- **His yes**: step 7, `lem criteria approve NAME --file TASK_DIR/criteria.md` (with `--shown` after
  a change), and then "The split", in the place of `stages/start.md`.
- **"One pull request"**: his yes to the criteria and his no to the parts. Approve them as step 7
  says, split nothing, and go on to `stages/start.md` as for any task. The headings stay, and
  change nothing for a task with no parts.
- **His Yes on the board** is his yes. His No whose note asks for one pull request changes no
  criterion: `lem criteria change NAME --unchanged`, then the page again, where he answers "One
  pull request".

## The split

```bash
lem task split NAME --file TASK_DIR/criteria.md
```

The file is the text he approved, word for word, with its headings. The command cuts
`feature/NAME` from origin's base, pushes it, makes the feature's worktree and one task for each
part, with the part's criteria, the personas' read and his approval copied. NAME is then `queued`
after every part, with its lead next. A refusal names its fix: do it, and run the split again. A
split that was cut off makes only what is missing when it runs again. A `said` in the result is
the line of an origin that did not answer: say it.

1. Write `branch:` and `worktree:` of NAME's `brief.md` again, with `branch` and `worktree` of the
   result: the lead of the end works there.
2. For each slug in `starts`, `open-task-session`: `lem session open PART --why new`. The other
   parts wait for the part before them, and the board's server opens each at its turn.
3. The tick ("The ticks").
4. Say in one line the parts, which start now and which wait. Then write `handoff.md`, with the
   line that NAME is a feature whose end reads this file, and close this session as step 7 of "The
   request" says: `lem session close NAME --why handoff --when-unselected` with
   `run-in-background`.

## A part's session

A part from the split opens with its read and its criteria on its record, approved with the
feature's (`lem criteria approved PART`). It runs no read, no interview and no persona read:

1. Write the lead's `brief.md` of step 6 of "The request", with `branch: TYPE/PART`, TYPE the
   `type` of its shape.
2. Steps 1 to 3 of `stages/start.md`. `lem task worktree PART` cuts the part's branch from origin's
   `feature/NAME`, not from the base. It refuses a part whose feature ended or has no branch on
   origin: tell the owner its `why` in one line, and stop.
3. Say one line: the part, its branch, and that its pull request goes into `feature/NAME`.
4. You are its lead (`stages/start.md`, step 4, the standard track from a complete request).

From there the part is a task as any other: its build, its landing into `feature/NAME`, and its
merge by the merge agent or by the owner as step 7 of `stages/land.md` says. After its merge, the
tick ("The ticks"). The owner may drop a part (`/lem drop PART`). NAME then waits for his "start
NAME now" (`stages/start.md`, "`/lem build`"), as behind any dropped task.

## A part added later

`/lem new part of NAME: <words>`, in any session. "Open the task" of `stages/new.md`, with his
words after the colon as the ask:

```bash
lem task open SLUG --ask "HIS WORDS" --part-of NAME
```

It refuses when NAME is not `queued` with its branch on origin, and when NAME is a part itself:
say its `why`. NAME then waits for this part too. The part's own session takes "The request" as
any task: its read, its interview or the fast track, and his yes to its criteria. Its worktree
starts from `feature/NAME`.

## The sync

`lem: NAME sync`, or a session opened because `sync`: the base moved while NAME waits for its
parts.

```bash
lem task sync NAME
```

It merges origin's base into `feature/NAME` by a merge commit, never a rebase, runs the settings'
checks on the merge, and pushes it.

- *Exit 0*: say its `say` in one line.
- *`conflict`*: `spawn-builder` with the landing's builder brief (`stages/land.md`), the job "the
  repair of a conflict with the base", the feature's worktree, and as its paths the refusal's
  files and its fix: the merge stays in the worktree, and the builder commits it. Then run the
  sync again.
- *`red`*: the same brief, the job "the repair of a failed check", and as its paths the commands
  that failed with their output files. Then run the sync again.
- *`lease`*, *`stopped`* or *`fetch`*: run the sync again, as its fix says.
- After two builders on the same failure, start no third. Tell the owner the refusal's `why` and
  `fix` in one line, mark this session as waiting for him (`mark-waiting`), and wait for his word.

Each other refusal names its fix: do it, and run the sync again. When the sync ran, write
`handoff.md` and close this session as a queued task's session does: `lem session close NAME --why
handoff --when-unselected` with `run-in-background`. NAME stays `queued`.

## The end

When the last part ended, the board's server gives NAME its turn, `lem: NAME queue`. Run `lem task
may-start NAME`, then `lem task move NAME building --line "the end of the feature"`. Never run `lem
task read` for it: a read with no `--after` empties the list of parts that the landing reads.
Behind a dropped part, `may-start` refuses, and NAME waits for his word as step 7 of "The request"
says; his "start NAME now" (`stages/start.md`, "`/lem build`") moves NAME to `building` and keeps
the list. Then you are the lead of the end, as step 4 of `stages/start.md` says for a session whose
phase is the build: its span, then `brief.md`.

- The plan's criteria are his approval, with the headings and the numbers it has. Under a part's
  criterion goes the test line of that part's plan, which `feature/NAME` holds.
- One task: a builder writes the tests of the whole-feature criteria and builds what they show is
  missing. A criterion the build must change takes `lem decisions criterion`, as in every build.

The landing is `stages/land.md`, with these differences:

- `start` refuses `parts-open` while a part has not ended: each part lands, or the owner drops it.
- `base` merges origin's base into the branch, never a rebase. A conflict leaves the merge in the
  worktree, for the builder of a conflict with the base, as in "The sync".
- No polish pass: each part had its own.
- The review: `lem land read NAME` names `prompts/feature-review.md`. Start the review agent with
  the line of step 5 of `stages/land.md`, with `prompts/feature-review.md` in the place of
  `prompts/review.md`.
- The merge is the owner's alone, whatever the settings say: one squashed commit with the report's
  commit subject as `--message`. It refuses while an open pull request has `feature/NAME` as its
  base: tell the owner which one.
- After the merge: the tracker's "land" and the tick, then `clean`, which removes `feature/NAME`
  here and on origin.

## The ticks

When NAME holds a ticket (`ticket` in `lem task show NAME`), its plan of parts is one comment of
Lem's own on that ticket, with a box for each part. `load-skill` the skill `tracker.kind` names,
its "tick", for NAME: for a GitHub issue that is `lem issue tick NAME`. A tick at each of these
places:

- after the split;
- after each part's merge, in the part's session, at step 9 of `stages/land.md`;
- after NAME's own merge, beside the tracker's "land".

A tick writes the comment again from the records. A tick that a stop lost comes back at the next.

## The drop

`/lem drop NAME`: drop it as `stages/correct.md`, "drop", says. Each part that has not ended drops
with it, and each pull request stays open. Say its `say`: it names each open pull request and the
command that deletes the feature's branch on origin, `git push origin --delete feature/NAME`. That
command is the owner's: Lem never deletes the branch. GitHub's docs say that the deletion of a
branch closes its open pull requests; whether that takes in a part's pull request into the branch
is untested (the plan of 2026-11-27, section 5).
