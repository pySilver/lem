---
worth: later
where: skills/lem/scripts/serve.py:Notes.put
added: 2026-11-22
---
# The note of a merge that waits over an hour expires, and its result is never shown

Read in the code, not run: Notes.put drops every note older than NOTE_SECONDS (3600 s), the note of a merge that still runs included. When a merge waits longer than that and any act of the board puts a note, the merge's note is gone; at its end Notes.change finds no token and does nothing, so the page of the merge never shows Merged or the refusal.

Seen outside the change by review round 1 of task merge-leaves-board-lock (2026-11-22); the base commit has it.
