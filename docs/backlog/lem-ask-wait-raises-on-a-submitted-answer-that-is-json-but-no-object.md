---
worth: yes
where: src/lem/ask.py:wait_page
added: 2026-11-24
---
# lem-ask wait raises on a submitted answer that is JSON but no object

`wait_page` takes a submitted value that is not JSON as the text of one answer, but one that is
JSON and no object reaches `ans["pageID"] = page_id` and raises `TypeError`: the agent gets a
traceback and no answer. The page's buttons send an object; `window.lemAsk.send(v)` in
`skills/lem-ask/runtime/ask.js` sends what a spec's own script gives. Run at c674b18d with `ctl`
stood in by a `submitted` reply: `[1]`, `42` and `"text"` raise, an object and `not json` exit 0.
Such a value should be taken as text that is not JSON is.

Seen by a Python style worker on 2026-11-24, which typed the function and left the case.
