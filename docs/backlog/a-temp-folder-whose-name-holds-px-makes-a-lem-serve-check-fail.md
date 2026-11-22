---
worth: soon
where: tests/lem-serve.sh:594
added: 2026-11-22
---
# A temp folder whose name holds PX makes a check of lem-serve fail

The check "lem board opens the server's address as a page companion" asserts `! grep -q "PX\|overlay open\|session close" <<<"$kept_calls"`, to show that the board leaves the companion of another repository (session `PX`) alone. Each recorded call ends with `--socket $WORK/agterm.sock`, and `tests/lib.sh` makes `$WORK` with `mktemp -d`, so a random suffix with `PX` in it (`tmp.i5PXEuX2vx` in the gate run of task merge-without-review-rerun, `gate/01.log`, 2026-11-22) matches the socket path and fails the check on any commit. The check should match the id as its own word (`--target PX`), not the two letters anywhere in the call.

Seen in the checks of task merge-without-review-rerun, which does not change `tests/lem-serve.sh`, `tests/lib.sh` or `board.py`; the same suite passed on the branch and on an export of main after it.
