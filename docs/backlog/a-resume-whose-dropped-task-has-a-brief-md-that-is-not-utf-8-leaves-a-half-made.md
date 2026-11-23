---
worth: later
where: skills/lem/scripts/project.py:cmd_resume
added: 2026-11-23
---
# A resume whose dropped task has a brief.md that is not UTF-8 leaves a half-made new task

The decode of brief.md comes after git branch made SLUG-2's branch and after the new folder, its ask.txt and the carried files were written, so the SettingsError stops the resume with a folder SLUG-2 and a branch left behind; the base reads it with text_of(directory / "brief.md") at the same place.

Seen outside the change by review round 1 of task an-ended-task-s-records-stay-on-the-machine-for-ever (2026-11-23); the base commit has it.
