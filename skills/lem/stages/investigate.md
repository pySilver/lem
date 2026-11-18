# A bug and a question

A bug is investigated before anyone writes a criterion: "typically the root-cause-investigation is
needed to unerstand what triggers the bug that we aim to correct" (the owner, 2026-11-16). A
question is the same work with a question in place of the bug, and its answer is the whole
task.

1. **A place, the worktree and the state.** `lem project may-start SLUG`, and the worktree on the
   task's branch, as steps 1 and 2 of `stages/start.md` say: the investigator runs the project's
   tests, so it takes a place. A task queued there starts its investigator when its turn comes,
   not a lead: its `queued` block carries the line `investigation: bug` or `investigation:
   question`, and `lem project tasks` gives either no `investigation` yet or one whose `call` is
   `not-reproduced`, which waits for the second investigator. Then write the state:

   ```bash
   lem project state SLUG building "an investigator reproduces the bug and finds its cause" "investigation: bug" "type: fix, because WHY"
   ```

   with `an investigator finds the answer`, `investigation: question` and the line `type:
   question, because WHY` for a question. The
   board draws a block with an `investigation:` line as the investigation.
2. **Start the investigator**, a fresh builder (`spawn-builder`) with the brief

   ```
   Read SKILL_DIR/prompts/investigator.md and follow it.
   request: TASK_DIRECTORY/ask.txt
   type: fix or question
   worktree: the path `lem project worktree-dir SLUG` prints
   branch: the branch of step 2 of "Open the task"
   task directory: TASK_DIRECTORY
   ```

   Log its start as it starts, `lem project log SLUG investigation.start
   type=fix` (or `type=question`); the record of step 3 is its end. Then go back to his next
   message: its reply wakes you, and the line of step 5 of "Open the task" (`stages/new.md`) told
   him already. No investigation has been timed yet.
3. **Read its report.** Its reply is the path of `investigation.md` in the task directory. When
   its agent refused it the write, its reply is the whole report: write it into that file word
   for word, with one line at the top that says who copied it and why. The report is knowledge of
   the code for the criteria, as the scout's is; you still read no diff and write no code. Then
   write what it found, which the board shows and the landing reads:

   ```bash
   lem project log SLUG investigation type=fix call=CALL "line=ONE LINE" where=PATH:SYMBOL reproduced:=true|false
   ```

   `call` is the report's: `small`, `full`, `not-a-bug` or `not-reproduced` for a fix, and
   `answer` for a question (`type=question`), which has no `reproduced`. `line` is the cause, the
   answer, or what was tried, in one line. `where` is the cause's place, which a plain cause has.
   When you take another call than the report's (a one-rule fix whose cause is in reach of a
   topic is not a small change), log yours and tell the owner why in one line.
4. **The path**, from the call:
   - *small*: a small change, with its one criterion the rule that removes the cause, in his
     words made exact, and with nothing careful: read the cause, its place and how far the report
     says it reaches against each topic, as step 1 of "Open the task" reads an ask. The
     reproducing test is the criterion's test: the small change's builder names it under the
     criterion. Tell him in one line, as step 5 of "Open the task" says, and go on with "A small
     change" (`stages/new.md`).
   - *full*: a full change with an interview and no scout, whose interview starts from the cause
     ("the total adds the refund as a payment, in `billing/invoice.py:total`; should the refund
     lower the total, or stand as a line of its own?"). Write the state `held` with the line `the
     interview waits for the owner` first: the investigator's place is free again. Then read
     `stages/interview.md` and follow it.
   - *not a bug*: tell him what the code does in his case and why, as one run (`SKILL.md`, "What
     the owner has to understand is told as one run"), with where each step was read. Write the
     state `answered` with that in one line, and `lem land clean SLUG`: the worktree goes, and a
     branch with commits of its own stays, the reproducing test among them, with how to delete it;
     a branch with none, which the base holds whole, goes.
   - *not reproduced*: tell him each try in one line, and ask him for one more fact: the record,
     the input, the time, what he saw. Write the state `held` with the line `the investigation
     waits for one more fact`. Write his answer into `task.md`, add one line to the brief,
     `tried before:` with the report's tries, and start a fresh investigator from step 1, which
     takes a place again or queues it.
   - *answer*, for a question: show him the answer as the report gives it, with where each
     part was read. Write the state `answered` with the answer in one line, and `lem land clean
     SLUG`.
   `lem project state SLUG answered` refuses a task with no `investigation.md` or no record whose
   call is `not-a-bug` or `answer`. For an answered task that came from a ticket, the tracker
   then comments the answer on the ticket and changes no status (its "answer"): tell the owner
   which status the ticket has. A task that goes on keeps the report in its directory, and
   its pull request names the cause in one line, from the record.
5. **A task from the report.** He can start one with `/lem new` and the report's path, as he can
   with a backlog item: the new task's ask is his words, and the report its written context. Copy
   the report into the new task's directory as `investigation.md`, name it in its `task.md`, and
   take its path in step 4 of "Open the task": when the report and his words settle what is wanted, that is a full
   change from a complete request, and when they ask for one plain change, a small change. The
   answered task's branch may hold a test the new task can take.
