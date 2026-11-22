---
worth: later
where: skills/lem/scripts/lem_state.py:load_start
added: 2026-11-22
---
# a hand-written start = nan passes the check and the gate never opens

with [load] start = nan in machine.toml, load_start() returns nan on the base and on the tip, 1.0 < nan is False, so wait_for_load waits for ever and logs that the checks start below nan; lem project load --start nan is refused, only the file read lets it through

Seen outside the change by review round 1 of task load-gate-default-forty (2026-11-22); the base commit has it.
