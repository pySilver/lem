<!-- lem: old form -->
# A bug and a question

A bug is investigated before anyone writes a criterion: "typically the root-cause-investigation is
needed to unerstand what triggers the bug that we aim to correct" (the owner, 2026-11-16). A
question is the same work with a question in place of the bug, and its answer is the whole
task.

1. **May it start, the worktree and the state.** `lem project may-start SLUG`, and the worktree
   on the task's branch, as steps 1 and 2 of `stages/start.md` say. A task queued `after:`
   another starts its investigator when its turn comes, not a lead: its `queued` block carries
   the line `investigation: bug` or `investigation: question`, and `lem project tasks` gives
   either no `investigation` yet or one whose `call` is `not-reproduced`, which waits for the
   second investigator. Then write the state:

   ```bash
   lem project state SLUG building "an investigator reproduces the bug and finds its cause" "investigation: bug" "type: fix, because WHY"
   ```

   with `an investigator finds the answer`, `investigation: question` and the line `type:
   question, because WHY` for a question, and the `careful:` line of step 1 of "The request" when
   it found a topic in reach. The board draws a block with an `investigation:` line as the
   investigation. When this is the task's first block, the call prints `say`: say it as it is
   before step 2, as step 8 of "The request" (`stages/new.md`) says.
2. **Start the investigator**, a fresh builder (`spawn-builder`) with the brief

   ```
   Read `skills/lem/prompts/investigator.md` in the folder that `lem version` prints as `root`, and follow it; when `lem version` fails, stop and say that `lem` is not on the PATH, with `lem doctor` as the check.
   request: TASK_DIRECTORY/ask.txt
   type: fix or question
   worktree: the path `lem project worktree-dir SLUG` prints
   branch: the branch of step 2 of "The request"
   task directory: TASK_DIRECTORY
   ```

   Log its start as it starts, `lem project log SLUG investigation.start
   type=fix` (or `type=question`); the record of step 3 is its end. Then wait: its reply wakes
   you, and the first line of step 1 told him already. No investigation has been timed yet.
3. **Read its report.** Its reply is the path of `investigation.md` in the task directory. When
   its agent refused it the write, its reply is the whole report: write it into that file word
   for word, with one line at the top that says who copied it and why. The report is knowledge of
   the code for the criteria, as the scout's is; you still read no diff and write no code. Then
   write what it found, which the board shows and the landing reads:

   ```bash
   lem project log SLUG investigation type=fix call=CALL "line=ONE LINE" where=PATH:SYMBOL reproduced:=true|false
   ```

   `call` is the report's: `small` (the fast track), `full` (the standard track), `not-a-bug` or `not-reproduced` for a fix, and
   `answer` for a question (`type=question`), which has no `reproduced`. `line` is the cause, the
   answer, or what was tried, in one line. `where` is the cause's place, which a plain cause has.
   When you take another call than the report's (a one-rule fix whose cause is in reach of a
   topic never takes the fast track), log yours and tell the owner why in one line.
4. **The path**, from the call:
   - *small*: the fast track, with its one criterion the rule that removes the cause, in his
     words made exact, and with nothing careful: read the cause, its place and how far the report
     says it reaches against each topic, as step 1 of "The request" reads an ask. The
     reproducing test is the criterion's test: the fast track's builder names it under the
     criterion. Tell him in one line the criterion and the track, in the first line's words
     ("Fast track: one builder, the checks, one read, then the pull request."), and go on with
     "The fast track" (`stages/new.md`).
   - *full*: the standard track with an interview and no scout, whose interview starts from the cause
     ("the total adds the refund as a payment, in `billing/invoice.py:total`; should the refund
     lower the total, or stand as a line of its own?"). Write the state `held` with the line `the
     interview waits for the owner` first: the investigator's place is free again. Then write the
     lead's `brief.md` as step 6 of "The request" says, and take `stages/interview.md` here: it
     reads `investigation.md` as the scout's report.
   - *not a bug*: tell him what the code does in his case and why, as one run (`SKILL.md`, "What
     the owner has to understand is told as one run"), with where each step was read. Write the
     state `answered` with that in one line, the ticket's "answer" (below), and `lem land clean
     SLUG`: the worktree goes, and a
     branch with commits of its own stays, the reproducing test among them, with how to delete it;
     a branch with none, which the base holds whole, goes.
   - *not reproduced*: tell him each try in one line, and ask him for one more fact: the record,
     the input, the time, what he saw. Write the state `held` with the line `the investigation
     waits for one more fact`. Write his answer into `task.md`, add one line to the brief,
     `tried before:` with the report's tries, and start a fresh investigator from step 1.
   - *answer*, for a question: show him the answer as the report gives it, with where each
     part was read. Write the state `answered` with the answer in one line, the ticket's "answer"
     (below), and `lem land clean SLUG`.
   `lem project state SLUG answered "THE ANSWER"` refuses a task with no `investigation.md` or no
   record whose call is `not-a-bug` or `answer`. For an answered task that came from a ticket, the tracker
   comments the answer on the ticket right after that state, before `lem land clean`, so that a
   worktree the cleanup refuses does not stop the comment (`load-skill` the skill `tracker.kind`
   names, its "answer"). It removes an assignee it added at the start and changes no status: tell
   the owner which status the ticket has now (an issue stays open). A task that goes on keeps the report in its directory, and
   its pull request names the cause in one line, from the record. A task that ended here closes
   its session last, as `prompts/session.md` says under "The end".
5. **A task from the report.** He can start one with `/lem new` and the report's path, as he can
   with a backlog item: the new task's ask is his words, and the report its written context. The
   report stays in the answered task's directory until nothing of the task happened for
   `state.keep_days` days; then `lem project prune` removes it with every file but the task's small
   record. A task from the report starts within that time; after it, it starts from the answer's
   line on the board (the newest `investigation` of `lem project tasks`) and his words, with no
   report. Copy the report into the new task's directory as `investigation.md`, name it in its
   `task.md`, and take its path in step 4 of "The request": when the report and his words settle
   what is wanted, that is the standard track from a complete request, and when they ask for one
   plain change, the fast track. The answered task's branch may hold a test the new task can take.
