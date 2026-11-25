task: SLUG · from PHASE · written: YYYY-MM-DDTHH:MMZ

<!--
The handoff of a task's session: what the agent that leaves knows and the next one needs. Three
readers share this form: the fresh agent of the next phase, the summary of a compaction (the
PreCompact hook gives it these five headings) and `lem task resume`. The task's state block is
the truth; this file says how the work stands inside it, and a reader follows the state where this
file is older. Link a plan, a record or a commit by its path or its id, and copy none of their
text. PHASE is shape, build, land or fast, the phase of the session that leaves; the time is UTC.
`lem session handoff SLUG --check` refuses a file without each part, and `lem session next` checks
it before it opens the next session. Remove these comments, and replace each line in capitals.
-->

## Settled

- WHAT IS DECIDED OR DONE, ONE ITEM EACH, WITH ITS PATH, ITS RECORD OR ITS COMMIT.

## Open

- WHAT IS NOT SETTLED YET, ONE ITEM EACH, OR "none".

## Next step

THE ONE STEP THE NEXT AGENT TAKES FIRST.

## Failed

- WHAT WAS TRIED AND DID NOT WORK, AND WHY, ONE ITEM EACH, OR "none".

## Changed files

<!-- Each file this session changed, one line each: its path from the repository root in backticks, a colon, and its status (added, changed, deleted, renamed from OLD, committed in SHA, not committed). "none" when it changed no file. -->

- `PATH/FROM/THE/ROOT`: STATUS
