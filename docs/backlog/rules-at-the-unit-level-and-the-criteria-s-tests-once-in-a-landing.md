---
worth: yes
where: skills/lem/scripts/land.py:cmd_polish
added: 2026-11-21
---
# The rules of nine pure functions at the unit level, and the criteria's tests once in a landing

The task `tests-at-the-unit-level` had the owner's yes to its criteria on 2026-11-20 and a plan of
six tasks, written against `3662a3f`. The redesign of 2026-11-21 changed `land.py` and the landing
blocks under that plan, so the task ended as `dropped` on 2026-11-21 and its wish is this item. Both
halves still hold in the code at `2beb5a5`:

- No file of `tests/unit/` names `type_line`, `ticket_owed`, `braces`, `glob_regex`,
  `investigation_form`, `read_form`, `start_form`, `talk_start_form` or `talk_form` of `project.py`
  (`grep`, 2026-11-21). Their rules are checked through real `lem project` calls in
  `tests/lem-settings.sh`, one process or more for each case.
- A landing on the standard track runs the tests of the criteria two times when the polish pass made
  commits: `cmd_polish` runs `criteria.py red` after the pass, and the checks run it again
  (`criteria_red`), also when the tip is still the commit the pass ended on.

What was approved, in short: each of the nine rules is a unit case, and a shell check of such a rule
goes only when a unit case holds it, with one shell journey kept for each command; the polish pass
keeps its own run and its own message; the checks take that result when their tip is the commit the
pass ended on, and run the tests themselves when the tip moved, when the pass made no commits and on
the fast track; the pull request gives the checks and the seconds of the changed suites, before and
after.

It reaches the topic "A criterion's test is taken as its proof when it is not", so it takes the
careful flow. Its old plan and criteria are in the task directory of `tests-at-the-unit-level` on the
owner's machine, for the next plan to read and not to follow.
