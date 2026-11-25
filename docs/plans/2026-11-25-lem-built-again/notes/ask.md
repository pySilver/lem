# The question card's seams

## For the join

The owned worktree's local stand-in is `board/ask/{ends,form,keys,overlay_read,receipts,saved,shape,updates}.py`.
The CLI and board both use it. The import-linter configuration permits their shared layer,
but the design in part 2 names one crossing only. Move these eight shared modules into
`app/asking/` at the join and update the imports in this step and its tests. Keep HTTP routes,
request checks and responses in `board/ask/`. The overlay adapter can move to
`adapters/terminal_agterm` when its port has typed operations for open, result and close.

The task's card key starts with `card:` and ends with the page id, as the views expect. It
puts the question, HTML digest and first end in `task.json`. The same write appends the
card's journal line. The HTML and the metadata live in `cards/PAGE/`. The answer's full
wire value is an immutable file there, keyed by the answer's exact timestamp. Publish it
before the task cites it. An uncited attempt is an unused artifact.

## For the owner model and board views

The card metadata holds the exact agterm session id. The POST route checks the latest
session that the task opened, the terminal's list and the overlay result before it takes an
answer. `model/owner/held.py:card_rows` can still show an earlier session's card when a later
session of the task is live. Give the card's `Question` its session id and
`model/owner/looks.Session` the live session id. Fill the latter from
`app/owner/sessions.py:session_of` and compare them in `card_rows`. The current card id and
the board's page path stay the same. The stale row belongs to trial A3. Also render a
`closed` or `dismissed` card as a closed card in `views/panel/card.py`.

## For sessions

The Stop hook can use the pending overlay's file in `TMPDIR/lem-ask/`. File names with
`.no-status.html` give the opening command's choice. If `PAGEID.wait.html` is present,
its contents (`status` or `no-status`) give the more recent choice. The hook remains in
`hooks/stop.py` and uses the standard library only. The CLI tests prove that the wait word
follows the latest call. The hook itself remains a stub on this base.

The sessions ledger already moved four `AskStopHook` rows to `ask`. Returning them in a
second move forms a cycle. Their fates name A5 until the join removes their original move.
