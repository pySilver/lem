---
worth: yes
where: src/lem/project.py:resumed_slug
added: 2026-11-24
---
# A blank resumed-from file makes the resume of a task loop for ever

`resumed_slug` follows `resumed-from.txt` from task to task while the file exists, and takes
`.strip() or first` as the next slug. A file that is blank leaves `first` as it was, so the loop
never ends; two tasks that name each other do the same. `cmd_resume` and `open_resumed` call it.
The function should refuse a blank link and a slug it met before, with the file's path and the fix.

Read by the outside read of 2026-11-24 (`docs/plans/2026-11-24-lem-as-an-app/astra-read.md`); not
run.
