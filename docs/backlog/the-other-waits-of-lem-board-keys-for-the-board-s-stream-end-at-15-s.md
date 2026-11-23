---
worth: later
where: tests/lem-board-keys.sh
added: 2026-11-23
---
# The other waits of lem-board-keys for the board's stream end at 15 s

Each `until` of `tests/lem-board-keys.sh` gives its condition 15 s, and some of them wait for the board's
stream to bring a change that a step of the check wrote: on the Tasks view `new-card` and `moved` after
`event.py` writes `keys-new-task` and `cart-total-after-coupon`, and `emptied` after `coupon-has-a-slug`
lands; on "Waits for you" `new-row` and `row-gone` after `event.py` writes `keys-other-wait` and moves the
held task to `building`. Under the load of `bash tests/all.sh`, with all 27 suites at the same time, the
stream brought the new proposal of #44 to "the read after a morph to another text" later than 15 s (the
checks of clean-refuses-a-branch-rebased-after-its-push-and-blames-the-forge, gate 01, 2026-11-23: the
suite ran 275 s and the card still showed 83619bcec85a), and that check now waits with no limit of its
own. These waits have the same 15 s, so the same load can make them red for no fault of the board.

Seen outside the change by the builder of task board-keys-morph-check-survives-load (2026-11-23); the base commit has it.
