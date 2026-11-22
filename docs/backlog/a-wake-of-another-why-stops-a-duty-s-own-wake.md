---
worth: later
where: skills/lem/scripts/serve.py:duties
added: 2026-11-22
---
# A wake of another why stops a duty's own wake

`duties` in `serve.py` wakes a task's session for `merged`, `refused` and `queue` only when no
`session.wake` came after the event that makes the duty due, and it counts every wake there,
whatever its `why`: `any(w["order"] > since for w in t.wakes)`. Only the `conflict` duty looks at
the `why` of each wake (`w.get("why") in ("conflict", None)`).

A run, from reading the code (not run): the task report-dates is `open`, and the merge agent's merge
is refused on the tip Lem proposed last. Before the server's next look, a `lem session wake
report-dates --why owner` (his act on the board) or `--why inbox` (a thing of the task went to the
owner's Inbox while he is away) lands in the log. The `refused` duty then finds a wake after the
refusal and never sends `lem: report-dates refused`.

The session reads the files at any wake (`prompts/session.md`, "A wake-up"), so it may still see the
refusal; whether it acts on it depends on the stage the other word sent it to. Today the Inbox's
watcher sends no `inbox` wake for a refused merge (it goes as a note) or for a landed task (it has
no row of "Waits for you"), so the case needs an `owner` wake in the same seconds.

The options: count only the wakes of the duty's own `why`, as the `conflict` duty does; or keep the
rule and write in the docstring that any wake makes the session read the files.

Where it surfaced: the lead of away-questions-reach-phone, in its report's outside defects.
