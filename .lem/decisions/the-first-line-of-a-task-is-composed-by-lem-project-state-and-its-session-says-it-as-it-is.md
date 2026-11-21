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
path with its type line (`opening_line` in `project.py`), prints it as `say` and logs it with the
block's `task.state` event, and the board shows it at the top of the "now" card while that block is
the newest. The forms live in the script, and `stages/new.md` keeps one example. To give the script its
facts, "The request" writes the fast track's criterion and the lead's brief before the task's first
block, and the first block of every path comes before anyone starts. A task of the night gets no
line: the night's report names it.
