---
worth: later
where: skills/lem/scripts/session.py:queued_behind
added: 2026-11-21
---
# lem session open opens a session for a task queued behind a dropped task, which the board refuses

export-notes-in-order is queued after gift-note-in-export, which is dropped. queued_behind returns None because project.ENDED holds dropped, so /lem status export-notes-in-order runs lem session open export-notes-in-order --why owner and an agent starts, whose lem project may-start refuses until the owner's word; the board's opens_session offers no Open a session, since after_ended needs landed or answered. The same two lines on the base 473cd9d.

Seen outside the change by review round 2 of task owner-order-open-defects (2026-11-21); the base commit has it.
