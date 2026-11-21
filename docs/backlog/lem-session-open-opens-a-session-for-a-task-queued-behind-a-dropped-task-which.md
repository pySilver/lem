---
worth: yes
where: skills/lem/scripts/session.py:queued_behind
added: 2026-11-21
---
# lem session open opens a session for a task queued behind a dropped task, which the board refuses

export-notes-in-order is queued after gift-note-in-export, which is dropped. queued_behind returns None because project.ENDED holds dropped, so /lem status export-notes-in-order runs lem session open export-notes-in-order --why owner and an agent starts, whose lem project may-start refuses until the owner's word; the board's opens_session offers no Open a session, since after_ended needs landed or answered. The same two lines on the base 473cd9d.

Settled, read on 2026-11-22 at f96e87b: `cmd_open` already says the rule in its own refusal ("when
{behind} is dropped it waits for the owner's word, which starts it or drops it"), and the code does
not follow it. The outcome: `lem session open` refuses a task queued behind a dropped task, with
that message, until the owner's "start SLUG now" removes the order, as `lem project may-start` and
the board's `opens_session` already do. `/lem status SLUG` then opens no session for it.

Seen outside the change by review round 2 of task owner-order-open-defects (2026-11-21); the base commit has it.
