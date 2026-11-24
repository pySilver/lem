---
worth: yes
where: src/lem/board_model.py:Reader.read_log
added: 2026-11-24
---
# The board names the wrong line of the event log after a blank line

`Reader.read_log` numbers a bad line from `len(self.events) + len(self.log_bad)` and skips blank
lines, so a blank line before it makes the number one too small. With a blank line, a good event
and then a line that is no JSON on line 3 of the file, the board says "line 2 is no event with a
time", and the owner repairs the wrong line. `self.log_lines` already counts the lines of the
file.

Seen by the outside read of 2026-11-24 (`docs/plans/2026-11-24-lem-as-an-app/astra-read.md`), which
ran the reader on such a log.
