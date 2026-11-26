# Mutation of the landing model

The lists below name the remaining `# pragma: no mutate` lines under
`src/lem/model/landing/`. Each line has an unreachable fallback or a
mutation that preserves the result for the landing's inputs.

| File and line | Reason |
| --- | --- |
| `bar_lines.py:93` | Git writes both file headers before the first hunk. The new header replaces the initial hunk list. |
| `bar_lines.py:94` | Git writes the old path header before the new path header, including on deletion. The initial path is unused. |
| `bar_marks.py:148` | The changed separator preserves equality of the normalized word lists. The caller uses the text as an equality key. |
| `checks_red.py:234` | The runner sets `ok` exactly when no test has a problem. The `or` and `and` give the same answer on its records. |
| `filing_asks.py:78` | The place builder returns one place for each finding. The `zip` length check always succeeds. |
| `filing_plan.py:85` | The item writer supplies a heading that the item reader parses. The fallback cannot occur in a filing plan. |
| `merge_call.py:43` | The merge decision required a check run before it built the call. The fallback base is unused. |
| `merge_call.py:46` | A safe base call requires a reason in `merge_said.base_call_of`. The fallback text is unused. |
| `merge_call.py:56` | The merge decision required an open pull request. The branch for an absent pull request is unused. |
| `merge_call.py:69` | The merge decision required a subject for a squash. The fallback text is unused. |
| `merge_evidence.py:32` | The hold rule gives the same result for each destination other than `dropped`, including the generated changes to `open`. |
| `merge_standing.py:55` | The template has one opening parenthesis. The split direction and any positive limit give the same prefix. |
| `merge_standing.py:60` | The careful-reason argument can be an empty tuple or `None`. Both add zero reasons. |
| `merge_standing.py:120` | A kept refusal requires a proposal in the landing. The fallback for an absent landing is unused. |
| `mergeread.py:92` | Each unusable reply has a nonempty reason. The fallback text is unused. |
| `phases.py:63–65` | Proposal evidence is always due in the preparing phase. Each line of the final wait is unreachable in that phase. |
| `propose.py:131` | The checks gate requires a worktree tip before it admits a proposal. The fallback text is unused. |
| `propose_lines.py:75` | The first entry is fresh. Its own line gives the depth before the next entry can use it. |
| `propose_lines.py:84` | An open entry uses a false flag. `None` has the same truth value. |
| `reconcile_queue.py:57` | Bookkeeping for an open request without an intent requires a queue acceptance. Its tip supplies the text. |
| `reconcile_queue.py:71` | A queued call keeps its proposal. Old queue records without an actor use the proposal's actor. |
| `review.py:93` | The start and checks supply the worktree tip before the review runs. The fallback text is unused. |

## A parked merge on the board

The task model can park an open task whose merger seat failed.
The locked merge and `lem land next` now honor that park. The board's
`model/owner/merging.py:merge_wait` still treats it as a merge it may dispatch.
The owner step owns that look. Suppress fresh dispatch for parked tasks while
the forge's result for a recorded call remains eligible for bookkeeping.
