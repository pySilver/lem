---
worth: later
where: skills/lem/scripts/criteria.py:stop
added: 2026-11-19
---
# The stop of the criteria's check can kill a serial wrapper before its own cleanup ends its command

A criterion's test runs under checks.serial through project.py serial, and the command ignores SIGTERM. On a stop, stop sends the wrapper's process group a term, waits 3 s, and sends a kill. The wrapper's own cleanup (project.py, cmd_serial) also waits 3 s before it kills its command, so the wrapper can die first and leave the command running. Read in the code, not run.

Seen outside the change by review round 1 of task landing-in-the-background (2026-11-19); the base commit has it.
