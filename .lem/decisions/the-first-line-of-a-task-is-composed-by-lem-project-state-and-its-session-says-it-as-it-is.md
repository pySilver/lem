---
decided: 2026-11-21
area: A task's session, and whether he is there
---

# The first line of a task is composed by `lem project state`, and its session says it as it is

The first line is where the owner corrects Lem's read of a request: the type, the criterion or the
outcome in his words, the branch, the track with its steps, what he must do, and a careful topic
first. In three of four real tasks of 2026-11-21 (lem-trial and lem-scratch) the session's first
words were "The builder runs now. I wait for its reply." or "The scout reads the code now.", the
last on 0.1.4, after `prompts/session.md` had been changed to make that line its first words. A
stronger sentence did not work; what sessions do reliably is run a command and say its `say`.

So `lem project state` composes the line from the task's files for the block that names the task's
path with its type line (`opening_line` in `project.py`), and from three lines of a queued block,
`the owner's order: "HIS WORDS"`, `then: PATH` and `the one open task that fits his words`, which
`state` refuses in another form. The hold of an order that names no task (`the order waits for the
owner`) names no path: the first block after the owner's answer that names one gets the line, with
the hold's type line. `state` prints the line as `say` and logs it with the
block's `task.state` event, and the board shows it at the top of the "now" card while that block is
the newest. The forms live in the script, and `stages/new.md` keeps one example. To give the script its
facts, "The request" writes the fast track's criterion and the lead's brief before the task's first
block, and the first block of every path comes before anyone starts. A task of the night gets no
line: the night's report names it.

The session where the owner typed the request says the line too, with the task named and in its
commands (`lem session wait SLUG --first-line`, the `then` of `lem session open SLUG --why new`),
because the task's session did not say it in a real task on 0.1.5 (lem-trial, 2026-11-21), and a
session on the fast track takes no focus, so he is not in it.
