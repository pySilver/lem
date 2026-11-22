---
worth: later
where: skills/lem-ask/bin/lem-ask:wait_page
added: 2026-11-22
---
# lem-ask paints the answered glyph after a close

`wait_page` in `lem-ask` sets the session's "answered" glyph in its `finally` whenever the wait ends
with the question no longer open: an answer, a dismissal by ⌘W, and now a `lem-ask close`, which
ends the wait as `dismissed`.

A run, from reading the code (not run): the owner is away, and breaker 1 of report-dates waits on a
`lem-ask` card in the task's session, in the background. He answers "Park" in the Inbox. The
session, as step 3 of "inbox-reply" in `skills/lem/harness/claude-code/ask-owner.md` says, runs
`lem-ask close`, then clears its waiting mark with `agtermctl session status idle`. The background
waiter sees the page dismissed within 0.4 s and sets the "answered" glyph (`active` by default). When
the waiter's `finally` runs after the session's `status idle`, the sidebar shows the answered glyph
on a session whose answer came from elsewhere, until the owner visits it.

The options: `close` tells the waiter that the page was closed on purpose (a marker file beside the
page, read in `finally`), so that it sets no glyph; or the harness clears the mark only after the
card's own command ended, which is a wait of the session's.

Where it surfaced: the lead of away-questions-reach-phone, in its report's outside defects.
