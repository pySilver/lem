# The question card trial

Use a scratch repository, a throwaway HOME and XDG_CONFIG_HOME, and a separate agterm
session. Keep `LEM_SERVE=off` in those shells. Start the rebuilt server explicitly with
`lem serve run --port PORT` on an unused loopback port. Use the same scratch home in the
server and the task's session. Keep the server's PID and address with the evidence.

## Checks

- [ ] A1 The same card in a real agterm overlay and on the board. In the task's session, run
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
  If serving the overlay loses those controls, keep the file overlay and record what failed.
- [ ] A2 Card controls at the Mac and on a phone. Use `lem ask demo design-tokens` and
  `lem ask demo tune` in the scratch session. Exercise single and multiple choices, the
  text and note fields, optional skip, detail and review, back and cancel. On a desktop use
  the number keys, arrows, H/J/K/L, E, Shift-E, /, Tab, Escape, Space, Enter and ?. Change a
  tune control, reset it and replay its preview with the button and R. In a narrow board
  card try a wide table and a long code line. Confirm that the card scrolls inside its
  frame. On the board verify that a note alone leaves the card open, then add a choice and
  submit. Keep a capture of the refusal and the corrected result. Check that the chart draws
  without a network request. Check the runtime's POST and the result on each page.
- [ ] A3 End and replace a task's session while its card still waits. Check that its old
  card leaves the board and that an old page cannot submit. Keep the waits list and the
  answer refusal.

- [ ] A4 The local browser fallback. Run `lem ask q "Keep it?" "Keep it" --browser` in the
  scratch shell. Pick Keep it and check the answer in the command result. Use a spec with a
  button that calls `window.lemAsk.send([1])` and check that the result contains the text
  `[1]`. Reload a question once before answering. Close a second browser question and check
  for the outcome `dismissed`.

- [ ] A5 The sessions step's Stop hook. End a turn while a scratch card still waits. Verify
  the waiting mark stays up if another hook writes a working mark. Repeat with `--no-status`
  on the open and with opposite choices on a later wait. Verify that the latest choice holds.
  Confirm that the hook stops when the question ends. Use the sessions step's agterm
  stand-in for the no-socket and stalled command cases.

Stop the scratch server and close the scratch session. Put the evidence paths beside each
completed check and tick it.
