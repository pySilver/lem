---
worth: later
where: skills/lem/scripts/land.py:small_text
added: 2026-11-20
---
# The fast track's pull request text omits the time without the owner

A fast-track task that ran while the owner was away (`lem project owner away` during its build) gets a pull request with no "It ran without the owner from ..." line: pr_text returns small_text(...) before it calls without_owner(task), and small_text names no span.

Seen outside the change by review round 1 of task away-for-the-whole-machine (2026-11-20); the base commit has it.
