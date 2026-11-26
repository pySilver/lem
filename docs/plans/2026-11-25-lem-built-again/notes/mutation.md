# The owner's approval after a skip

`propose_criteria.skipped` uses the first approval by the owner even when it
came before his word to skip the personas' read. The old rule,
`main:src/lem/land.py`'s `read_skipped`, only considers approvals after the
newest word to skip.

`model/criteria/skip.py:skipped` records the word but does not set the existing
`Criteria.skip_at` field. The criteria step owns that writer. Set the moment
there so that the landing can take the first owner approval at or after the
skip, then check that this approval preceded the lead. Prove both sides with
an approval before the skip and one after it, with the lead between them.

## A parked merge on the board

The task model can park an open task whose merger seat failed.
The locked merge and `lem land next` now honor that park. The board's
`model/owner/merging.py:merge_wait` still treats it as a merge it may dispatch.
The owner step owns that look. Suppress fresh dispatch for parked tasks while
the forge's result for a recorded call remains eligible for bookkeeping.
