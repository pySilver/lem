---
worth: later
where: skills/lem/scripts/project.py:cmd_waiting
added: 2026-11-19
---
# The list of what waits has no group for a plan the owner reads

`stages/plan.md` has a lead stop with the state `planned` and the line `the owner reads the
plan`. That plan waits for the owner: the board counts it (`forOwner`, and a row "Read the plan"
in its tab "Waits for you"). `lem project waiting` has no group for it. Its groups are `choices`,
`criteria`, `held`, `pull_requests` and `retros`, so the bare `/lem` does not name the plan, and
`count` is one lower than the board's tab.

A group `plans` for each `planned` task whose state line names the owner would make the two agree.
Read in the code on 2026-11-19, in the polish pass of `feat/status-boards-steady-look`; not run.
