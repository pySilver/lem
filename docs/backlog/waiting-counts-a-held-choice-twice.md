---
worth: later
where: skills/lem/scripts/project.py:cmd_waiting
added: 2026-11-19
---
# The list of what waits counts a held task's choice two times

`stages/build.md` tells a builder that stops at an irreversible choice to write the state `held`
with the line `choice N waits for the owner`, and the choice is also open in
`decisions.jsonl`. `lem project waiting` then lists it two times: `choices` takes it from `lem
decisions pending`, and `held` takes every held task whose line does not start with "the criteria
wait for the owner". So one choice of one task gives `"count": 2`, and the bare `/lem` says two
things wait where the owner has one to answer.

The board's tab "Waits for you" (`waitsOf` in `skills/lem/assets/board.html`) already makes one
row of it: a held task with a choice that waits is the row of that choice. `cmd_waiting` can leave
out of `held` a task that `choices` names. Read in the code on 2026-11-19, in the polish pass of
`feat/status-boards-steady-look`; not run.
