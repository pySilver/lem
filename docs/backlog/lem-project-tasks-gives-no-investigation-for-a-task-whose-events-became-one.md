---
worth: later
where: skills/lem/scripts/project.py:read_tasks
added: 2026-11-23
---
# lem project tasks gives no investigation for a task whose events became one summary

An answered task why-slow whose log holds only its task.summary, with investigation {"call": "answer", "line": "the export reads every order twice", "where": "export.py:rows"}, gives {"status": "answered", "investigation": null} in read_tasks, on the base 299afc2f and at the tip: newest_events(root, "investigation") reads investigation events only. So lem issue answer of such a task, with its comment still owed, posts the state's first line in place of the answer's line, and with no where.

Seen outside the change by review round 1 of task an-ended-task-s-records-stay-on-the-machine-for-ever (2026-11-23); the base commit has it.
