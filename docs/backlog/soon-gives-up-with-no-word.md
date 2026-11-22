---
worth: later
where: tests/lib.sh:soon
added: 2026-11-22
---
# soon gives up with no word

`soon` in `tests/lib.sh`, which many `lem-*` blocks use to wait for a state, tries its command 150
times, 0.2 s apart, and after about 30 s returns 0 with nothing printed (`[ "$tries" -gt 0 ] || return
0`). A check that waited for a server's file or line that never came then fails one step later, on an
assertion that does not say what it waited for, or passes on a state it did not mean to test. Seen
by the lead of `merge-leaves-board-lock` (2026-11-22), whose checks of a held merge wait with their own
`until_for` and fail with a line that names the wait. A fix that makes `soon` fail changes every
block that relies on its silent end, so each caller needs a read first.
