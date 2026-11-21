---
worth: later
where: skills/lem/harness/claude-code/take-screenshot.md
added: 2026-11-21
---
# The one-call screenshot of a board page does not end

`take-screenshot.md` says a desktop picture is one call of headless Chrome with `--headless=new
--screenshot=... URL`. In the task `owner-order-open-defects` (2026-11-21), the builder of task 1
ran that call with Chrome 157 on the board's "Waits for you" page, served by `lem serve` from a
throwaway state folder, and it did not end in 3 minutes. The likely cause is the page's open event
stream, which keeps the load from ending; that is unmeasured. The DevTools driver
`tests/board-cdp.mjs` took the same picture. The harness file names the one call for every page, the
board's among them, which Lem's own agents photograph most.
