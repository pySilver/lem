# review

Review after the landing is a promise that is easy to break: after about 28 hours of this flow in
one repository, the queue held 48 items and 43 were still open (convertiser-server, 2026-11-14). So the queue has rules that keep it honest.

Lem's stage. `python3 SKILL_DIR/scripts/review_queue.py list` prints the open items, the `high`
ones first.

1. **Every `high` item is reviewed on the day it lands.** A session that lands a `high` item
   starts its review before it starts another task.
2. **`normal` items are taken oldest first** with what the day leaves. An item nobody read in
   seven days is closed by `review_queue.py expire` as `not reviewed`, and the status and the next
   report say how many: an unread item is a fact the owner sees, never a silent backlog.
3. **One review is one round of the project's review tool** over the item's landed range, with the
   project's own lenses and profile (`project.py path review`; with revmux, that directory is its
   `--config-dir`). The project's `AGENTS.md` names the profile for a `high` item and for a
   `normal` one. A finding is confirmed against the code before it counts.
   The round and the confirming run in a context of their own, since both read the diff: give the
   item to a fresh agent through `spawn-builder`, told to change nothing. It writes
   `reviews/ID.md` in the folder `project.py state-dir` prints: each finding with its file, its
   symbol, why, and `major` or `minor`, and whether the code confirms it or not, with the lines
   that show it. Its reply is that path. One round at a time: the review tool starts several
   agents of its own.
4. **A confirmed finding becomes a task**: `/lem new` with the finding as the ask, for a major
   one at once, for minor ones as one task per item reviewed. A finding the project decides
   against is recorded where its review tool keeps rejected findings, so no later round raises it
   again.
5. **Close the item**: `review_queue.py close ID` with the outcome: `clean`, `fixed in <slug>` or
   `rejected`.

A project that releases says in its `AGENTS.md` what a release waits for; the usual rule is no
open `high` item on the range it ships.
