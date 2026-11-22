---
worth: later
where: skills/lem/scripts/lem_board_model.py:settle
added: 2026-11-22
---
# The board finds the owner's skip of the read by its time and by its place

In `settle`, `read_in` counts the owner's word to skip the personas' read when its time is at or
after the newest block's (`d.ts >= last["ts"]`), and `approvable` follows from it. `turn_of` counts
the same word only when it comes after the newest block in the log. The two disagree when a held
block is written again in the same second as the word, after it. A log of `gift-note` with the held
block at 09:00:00, `interview.start` at 09:01, `interview.end` at 09:05, `read.skip.asked` at 09:06,
the owner's skip decision at 09:07:00 and the held block again at 09:07:00 gives `turn` `asks` and
the card's line "the interview waits for you", while `now_head` says "The criteria wait for your
yes" (run at `823c147` with the helpers of `tests/unit/test_board_model.py`). A fix reads both by
the log's order, which needs the order of a decision in `Decision` and the approvals' floor by
order too.
