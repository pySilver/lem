---
worth: later
where: skills/lem/scripts/lem_board_model.py:Reader.read_log
added: 2026-11-22
---
# The board names a bad line of the log one too low after a blank line

`Reader.read_log` reads the event log on from where its last read stopped, and names each line
that is no event with a time in the status bar ("line N"). The first read counts every line,
blank ones too. A later read starts its count at `len(self.events) + len(self.log_bad)`, which
leaves out the blank lines read before. Run on 2026-11-22 at the branch of
`old-task-events-summarized`: a log of one event, a blank line and one event, read once; then the
line `not json` appended and read again. The status bar says "events.jsonl: line 3 is no event
with a time", and the bad line is line 4.

The reader now counts every whole line it read in `self.log_lines` (the count of the stream's
`log_version`), so the fix is to start the count there: `number = self.log_lines` before the loop.
It needs a case in `tests/unit/test_board_model.py` beside the reader's other cases; the polish
pass of that task could not add it, as that file held the task's criteria.
