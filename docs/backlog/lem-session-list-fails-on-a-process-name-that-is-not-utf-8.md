---
worth: later
where: skills/lem/scripts/session.py:process_table
added: 2026-11-23
---
# lem session list fails on a process name that is not UTF-8

`process_table` runs `ps -A -o pid=,ppid=,command=` with `text=True`, which decodes the output as
UTF-8. On 2026-11-23, with Lem 0.3.0, a process on the machine had the byte 0xff in its command line,
and `lem session list` stopped with `UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff`, so
the task's session saw no list at all. One process of the machine, of any owner, is enough. A fix
decodes with `errors="replace"`, so that one bad byte changes one character of one line.

Seen outside the change by the builder of task start-shows-the-started-task (2026-11-23); the base commit has it.
