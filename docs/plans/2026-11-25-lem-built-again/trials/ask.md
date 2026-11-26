# The question card trial

Use the [run order](run.md) and the [scratch checkout](real.md#scratch-checkout). Use one
trial home and a separate agterm session for the task and the server. Keep `LEM_SERVE=off`.
Run `lem task open ask-cards --ask 'Check the question card.'` in the scratch checkout.
Open it with `lem session open ask-cards --why owner` in the scratch agterm pane. Start the
board as in the real sheet and keep its PID and address. For a phone, also use R6's door setup
and cleanup in this folder. Use the owner's phone and Mac for A1, A2 and A5. The orchestrator
can drive A3 and A4 in the trial profile.

Use headless Chrome with its own profile and keychain for the local browser cases. Start it
on a free DevTools port `CDP`, outside 4536 and 4537, and keep the port on loopback.

```sh
"$T/step" a-chrome -- "$CHROME" --headless --use-mock-keychain --user-data-dir="$T/chrome" --remote-debugging-address=127.0.0.1 --remote-debugging-port="$CDP" about:blank &
```

Use the trial DevTools client at `http://127.0.0.1:$CDP/json/list` to navigate, press a key,
inspect the actual POST and save the screenshot, as in the plugin's `take-screenshot.md`.
For A4 write the two-line executable `T/bin/trial-browser` below, with `T` expanded in the path.
Set its mode to `700`. The launcher records the URL for the headless browser you started.

```sh
#!/bin/sh
printf '%s\n' "$1" > 'T/tmp/browser-url'
```

Start each A4 request through `T/step` with `/usr/bin/env BROWSER="$T/bin/trial-browser %s"` before
`lem ask`. Open the URL from `T/tmp/browser-url` in the headless browser. Clear this file before
starting another request. Keep it private. Stop Chrome by the PID of `a-chrome` at cleanup.

## Checks

- [x] A1 The same card in a real agterm overlay and on the board. In the task's session, run
  `lem ask q "What goes in the empty cell?" "Keep it empty" "Write a dash" --no-wait`.
  Check the page id, focus and sidebar mark. Open the card from Waits for you. In the overlay,
  pick Keep it empty. Run `lem ask wait PAGEID`. Check that the result says `answered` and
  `from: session`. Try to submit Write a dash in the board tab that still holds the page.
  Check that the board says which answer took effect. Ask the same question again. In the board
  card, pick Write a dash with the note "For the export". Run `lem ask wait PAGEID`. Check
  `from: board`, the option, the note, the device and listener. Check that this wait closes
  its own overlay and the row leaves Waits for you. Keep the command results and the task
  record. Try the card's HTTP address with `agtermctl session overlay open --url URL --js` in
  the scratch session. Check whether the same result arrives with the needed overlay controls.

  Mac part passed on 2026-11-26 at 12:19 on the tag `v0.99.0`, with the board on port 65351 and the
  stand-in `r-bin/agtermctl` for every pane Lem opened; the phone part runs in R6. Page
  `D762B576`, sidebar `blocked`, the session not selected; `from: session`; the board then said
  "Keep it empty was taken in the session at 12:15", and a stale page's submit got 409 "Keep it
  empty was recorded in the session" once the wait had read it (before that, "submitted the card in
  the session"). Board answer `8F08BF50`: `from: board`, `o2`, the note, `device: computer`,
  `via: local`; the wait closed its overlay and Waits for you is empty. The pick in the overlay was
  sent with `agtermctl session overlay submit` and the page's own value: an agent cannot click in
  an agterm overlay. The served card (`overlay open --url ... --js`) loads, but agterm gives a URL
  page no bridge, so it answers over HTTP like a browser tab (`from: board`) and stays open after
  the answer: the file overlay stays. Evidence in `/private/tmp/lem-trial-r1/evidence/`: `a1-*`, `a-task`, `a-session-open.txt`,
  `a-board-server2.json`, `a-socket-link-note.txt`, `r-agterm-calls.jsonl`.
- [x] A2 Card controls at the Mac and on a phone. Use `lem ask demo design-tokens` and
  `lem ask demo tune` in the scratch session. Exercise single and multiple choices, the
  text and note fields, optional skip, detail and review, back and cancel. On a desktop use
  the number keys, arrows, H/J/K/L, E, Shift-E, /, Tab, Escape, Space, Enter and ?. Change a
  tune control, reset it and replay its preview with the button and R. In a narrow board
  card try a wide table and a long code line. Confirm that the card scrolls inside its
  frame. On the board verify that a note alone leaves the card open, then add a choice and
  submit. Keep a capture of the refusal and the corrected result. Check that the chart draws
  without a network request. Check the runtime's POST and the result on each page.

  Mac part passed on 2026-11-26 at 12:26; the phone part runs in R6. Both demos opened and closed in
  the scratch overlay (`lem ask close`); their keys, tune change, reset, replay (button and R) and
  POSTs ran in headless Chrome through the browser fallback, since an agent cannot press keys in an
  agterm overlay. Every listed key worked; H and L move only on a grid. The narrow board card (618
  px): the code line scrolls in its own box (5448 of 582 px), the 14-column table wraps, the page
  does not scroll sideways; the chart is an inline SVG with no request. A note alone: 422 "The board
  takes a choice with a note", card open; with CSV: 200, `from: board`. Optional skip: `selected:
  []`. Evidence in `/private/tmp/lem-trial-r1/evidence/`: `a2-*`.
- [ ] A3 End and replace a task's session while its card still waits. Check that its old
  card leaves the board and that an old page cannot submit. From the scratch pane run
  `lem session close ask-cards --why owner`, then `lem session open ask-cards --why owner`.
  Keep the waits list, both session identifiers and the old answer refusal.

  Failed on 2026-11-26 at 12:30. The close removed the card from Waits for you and an old page
  got 409; after the open (`89B73C2B` replaced by `650CAEA1`) the old card was back in `lem waiting`
  and on the board, still refused 409, and `lem ask close` said `gone`. Lem's: `card_rows` in
  `src/lem/model/owner/held.py` lists every open card while any session is live, not only the live
  session's. Evidence in `/private/tmp/lem-trial-r1/evidence/`: `a3-*`.

- [ ] A4 The local browser fallback. Run `lem ask q "Keep it?" "Keep it" --browser` in the
  scratch shell. Pick Keep it and check the answer in the command result. Use a spec with a
  button that calls `window.lemAsk.send([1])` and check that the result contains the text
  `[1]`. Reload a question once before answering. Close a second browser question with the page cancel action, or navigate to `about:blank`
  to exercise the page unload. Check for `dismissed`. Keep the request, POST result and raw
  command output.

  Failed on 2026-11-26 at 12:31: a reload before the answer ends the question as `dismissed`, twice
  (`a4-keep`, `a4-keep2` with `location.reload()`), in headless Chrome 159. The beacon of the old
  page reached the server after the new page's GET, so the GET did not clear it (`RELOAD_GRACE` in
  `src/lem/cli/ask/browser.py`, `do_GET` in `browser_http.py`). Keep it with no reload (`a4-keep3`),
  `[1]` (`a4-send`) and `about:blank` to `dismissed` (`a4-blank`) passed. Evidence in `/private/tmp/lem-trial-r1/evidence/`:
  `a4-*`.

- [ ] A5 The sessions step's Stop hook. End a turn while a scratch card still waits. Verify
  the waiting mark stays up if another hook writes a working mark. Repeat with `--no-status`
  on the open and with opposite choices on a later wait. Verify that the latest choice holds.
  Confirm that the hook stops when the question ends. Use the sessions step's agterm
  stand-in for the no-socket and stalled command cases.

  Failed on 2026-11-26 at 12:32: after another hook's `active`, a turn's end left the mark `active`
  with the card open. The tag's Stop hook says nothing (`src/lem/hooks/stop.py`: "until then the
  hook gives a turn's end no word"), though the plan keeps the Stop hook's mark. `--no-status` left
  the mark alone. The rest waits for the hook; the phone part runs in R6. Evidence in `/private/tmp/lem-trial-r1/evidence/`:
  `a5-*`.

Stop the scratch server and close the scratch session. Put the evidence paths beside each
completed check and tick it.
