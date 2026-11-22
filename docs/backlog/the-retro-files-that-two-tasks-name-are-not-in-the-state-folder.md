---
worth: later
where: skills/lem/stages/learn.md
added: 2026-11-22
---
# The retro files that two tasks name are not in the state folder

`skills/lem/stages/learn.md` has the retro write its moves and removals into
`retros/YYYY-MM-DD.json` in the folder `lem project state-dir` prints, and `lem project waiting`
lists each file there (`RETROS` in `skills/lem/scripts/project.py`). The docstring of
`project.py` says that `lem project prune` keeps the retros.

When the task moved-base-merge-agent-call opened on 2026-11-22, `.lem/state/retros/` of this
repository was an empty folder, though its ask names `.lem/state/retros/2026-11-22.json`, and two
tasks of 2026-11-21 name `.lem/state/retros/2026-11-21.json`. The folder's change time was
2026-11-22 09:55. Either something removed the files after the retros wrote them, or the retro
wrote them to another folder (another checkout's state folder, or its own scratch). Nothing of
this task looked for which.

Seen by the lead of moved-base-merge-agent-call (2026-11-22), outside its change.
