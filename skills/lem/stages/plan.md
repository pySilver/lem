# plan

The lead's first stage. A plan here is short and written by the task's lead, which then gives
each of its tasks to a fresh builder. It exists so the builder has thought before typing and so a reviewer can tell what was meant; it is not argued line
by line before the build. Only a careful or large plan is talked through with the reviewer, over
a list of questions that closes with the reviewer's first turn, by its defender and not by you
(`stages/talk.md`).

Before the plan, look at the other tasks (`lem project tasks`). When the code you read shows that
this task builds on what another task changes and that task has not ended (it is not landed,
answered or dropped; its plan names the function, the table or the file this task needs, and the
base does not have it yet), the plan
would be written against code that does not exist. Then write no plan: stop with the state

```bash
lem project --repo WORKTREE state SLUG queued "WHAT THIS TASK NEEDS FROM THE OTHER, IN ONE LINE" "after: OTHER-SLUG"
```

and `report.md` as `stages/build.md` gives it; then `handoff.md`, and close this session as step 7
of "The request" (`stages/new.md`) says. `lem project may-start` keeps the task in the queue until
that task is landed or answered, and the board's server opens its session then, or wakes it when
it still runs; its lead finds the base with the other task's change in it. When that task is
dropped, it stays queued for the owner's word (step 7 of "The request"). A dropped task is no task
to queue behind again: what a task started past a dropped task still needs of it, its plan builds
inside it. Two tasks that only touch the same file each go on: when the first one merges, the
later pull request is brought onto the base if the forge calls it conflicting.

An order that the owner gave stays. His order is the first line of a `queued` block of this task,
`the owner's order: "HIS WORDS"`, or his words in the ask of `task.md` that put the whole task
after another task ("After gift-note-in-export: ...", "when the gift note task lands"). You never
remove it, also when the code shows that this task needs nothing of the other one: only his own
record removes it, a decision `--by owner` on the order in `lem decisions --repo WORKTREE list
SLUG` (`stages/start.md`, "`/lem build`"), which you read before the ask, so his words in
`task.md` do not bring back an order he removed. A task that started all the same while the task
he named has not landed or been answered gets no plan and no code: queue it as above, with his words as the first
line, the words of his that give the order on one line,

```bash
lem project --repo WORKTREE state SLUG queued "the owner's order: \"After gift-note-in-export\"" "after: gift-note-in-export"
```

and name his words in your report. When you see no need for his order, the block gets one more
line, which the board shows while the task waits: that you see no need for the order, why, and
that "start SLUG now" starts the task; when the task is queued already, write its block again
with each of its lines and that one. Your report says the same. A task he named that ended has met his order: go on.

1. **Write the plan** as one file at the path `lem project --repo WORKTREE plan-file SLUG`
   prints (`path`; its name is the settings' `paths.plan_file`, `YYYY-MM-DD-<slug>.md` unless they say otherwise), and
   commit it as your first commit: after a bug, the investigator's test comes before it. It opens with the acceptance criteria, because they are the
   owner's document: he reads them and not the rest of the plan, and they become the tests. Read
   `SKILL_DIR/prompts/writing.md` before you write it; the plan and your report take its forms.
   - `## Acceptance criteria`, in the form `lem criteria --help` shows.
     First run `lem criteria approved SLUG`. When the owner approved
     criteria at his interview, they are your criteria: copy the section word for word, numbered the
     same, and add only the test lines under each, at the end of the build. A criterion whose change
     keeps behavior (a rename, a version bump, a refactor) is held by the suite: its line is `- no
     test: the change keeps behavior; the suite holds it`, and the checks before the pull request
     run the whole suite, which proves it. Its builder runs the tests of the files it changes and
     of their direct callers, as every builder does, and no builder runs the whole suite. You may break a criterion's
     text into other lines; you may not change a word of it. The plan follows the task's
     `directions.md` too, when the task directory has one. A criterion or a direction the code shows
     you cannot keep, or a criterion that is missing, is a decision of the build (`stages/build.md`,
     "A choice in the build") with its own record (`lem decisions criterion`), never a silent edit:
     `show`, `record` and `red` refuse a plan whose criteria are not the approved ones with each
     recorded change, word for word, or whose `Size:` is not the approved one. Criteria approved
     for the fast track do not reach a lead: the fast track has one builder and no plan
     (`stages/new.md`, "The fast track"), and a task that needs the standard track after all comes to you
     with his approval of its criteria for that track. A plan's criteria always say `Size: full`:
     `criteria.py` and `land.py` refuse a plan that says `Size: small`;
   - with no approved criteria (the standard track from a complete request), write them.
     A criterion is one business rule of the request in plain language with one concrete example,
     with real names and values: what a person of the project would see, never how the code does
     it, and a case or a chart where `prompts/writing.md`, "In the acceptance criteria", asks for
     one. Take them from the outcome and the "done when" of `task.md`, now that you have read the
     code. A rule you cannot write without guessing what the owner wants is not yours to guess:
     the criteria wait for him, as for a doubt of the personas below, with the criterion as you
     would guess it and each other reading beside it as a proposal. The first line of that section
     is `Size: full`, with the reason after `because`, also for a plan of one criterion: a plan
     never puts a task on the fast track. One plain change with nothing careful takes the fast track, which
     has one builder and no plan (`stages/new.md`, "The fast track"), and Lem chose this path for
     the task before you started. When the code shows you that it is one, still write the plan,
     and say in the report that the fast track would have fit, for Lem's next call of a track;
   - then the personas read the criteria you wrote. Here
     the read always runs, as the only approval of this path: the owner's word to skip it belongs
     to an interview (`stages/interview.md`, step 5), and the
     landing refuses one that comes after a lead started. The read is the persona panel's "Reading
     acceptance criteria" mode (`load-skill`), run by you while you write the rest of the plan. You
     have no paired agent of the other family, so one family answers: the panel's own persona
     agents, started the way the `lem-panel` skill starts a persona, never as a builder:
     `lem-builder` has no persona among its jobs. Log its start as it starts, `lem
     project --repo WORKTREE log SLUG criteria.read.start by=lead`. Write the
     event the landing reads, in the form `stages/interview.md` gives (step 5), with `by=lead`, your one family, and the `digest` field of what `lem
     criteria --repo WORKTREE digest SLUG` prints for the plan's criteria. A
     persona agent that did not answer is named in `silent` with why. A read in which nobody
     answered is written down too, in the form `stages/interview.md` gives for it, and started once more;
     after a second one in a row, freeze the criteria as below, write the state line `the criteria
     were not read: nobody answered twice`, and build: the pull request is not green for it. Nobody
     confused, and your brief says `request by: someone else`: the criteria wait for his yes all
     the same, since nobody at the terminal read that request; stop as for a doubt, below, with
     the line `the criteria wait for the owner` and `nobody confused` beside it. Nobody
     confused otherwise: freeze the criteria they read, `lem criteria --repo WORKTREE
     approve SLUG --read`, which takes the plan's criteria and refuses any other text than the one
     the read names. It freezes the task's first contract only, and is refused once the task has any
     approval: from then on a criterion the build changes has its record (`lem decisions criterion`),
     and the track is his to change. It is never his yes. The build starts with no wait, and your
     next state block says `nobody confused, read by N personas, one model family`, where he sees it
     and can stop the task. The landing refuses a task on the standard track with no such event.
 A doubt: the
     first line of code waits. Write `report.md` with the criteria and the answers that flagged
     them on top, quoted, and the line `the criteria wait for the owner`; write the state `held`
     with that line, and put them to him here, by steps 6 and 7 of `stages/interview.md`; after
     his yes, build on. Leave a flagged criterion as you wrote it: what you would change goes
     beside it, as a proposal, and he decides. A task that runs without him (`mode` is `alone` in
     `lem project --repo WORKTREE tasks`) waits for nothing of this, a request somebody else
     wrote among it: each flagged criterion is a
     decision in doubt whose personas split, and it climbs `stages/ladder.md` from the dialectic,
     level 3. Write it as the level that settled it picked, log it with that level (`--option` as
     you wrote it, `--option` as the persona expected it), freeze the criteria with `lem criteria
     --repo WORKTREE approve SLUG --file PLAN --alone`, and build. The pull request is not green
     for it;
   - run `lem criteria record SLUG`: it refuses a section that does not
     have the form, or that departs from the approved criteria, and it puts the criteria where
     the board and Lem's status show them;
   - when the change builds a flow, a rule with branches or a state that moves, one chart of it
     under `## How it works`, after the criteria, below the sentence it shows, or a criterion's own
     chart directly under it;
   - `## Tasks`: a numbered list of one to seven tasks, each an outcome a reviewer can check
     alone and one builder can finish in a context of its own, with the criteria it serves and
     the files it expects to touch. The landing counts the numbered lines under that heading:
     a plan of more than three is large, gets a plan talk before any code (step 4) and a review
     round at the least, and a plan with no such list is refused there;
   - the documentation task, last, when the change makes a document false: a guide, the README,
     the agent document, the rules in `.claude/rules`, a page of help. Write it like any other task, with the
     documents it corrects by path and what in each one the change makes false; it serves no
     criterion unless a criterion is about a document. The landing's polish pass checks that no
     document the change made false was missed; it is the check, not the place where documents are
     written;
   - the decisions the plan takes, each with the answer it assumes and what the answer rests on;
   - what it will not verify, and why;
   - `## The bar`, only when the change has to lower it (a lint or type suppression, a skipped
     or deleted test, fewer assertions in a test): one line for each such file, `- PATH: REASON`.
     The landing refuses a lowered bar with no reason, and with one the pull request is not
     green: the owner reads that line himself. So lower it only where the mark is right.
   Before writing, read the rule files that cover the files the plan touches and the
   project's lessons (`lem project path lessons`). `lem project rules
   FILE ...` prints those rule files, the ones with no scope of their own too: do not
   match a file's `paths:` by eye.
   When the branch already holds a plan (a builder that stopped at the plan), do
   not write another: read it against the code as it is now, and commit a fix for what the code
   has outgrown.
2. **Is the task careful?** Two tests, and one yes is enough:
   - *a topic*: the project's topics (`flow.topics` in `lem project --repo WORKTREE show`, which
     gives the main checkout's table, so a branch cannot lift one), each a sentence of the
     owner's about what must never go wrong here. Read the plan against each one: does a task
     change how that thing behaves, or could a defect in a task reach it? No code matches a
     topic, and no file name settles it: a price is computed in more places than `billing/`.
     This is your judgment, and a person can overlook a danger that you see in the code, so say
     what you see. In doubt, yes.
   - *a pattern*: the plan starts product code that other code will copy (a first service
     layer, a first use of a library in the product). A test, a check or a tool of the
     developer's is no such pattern: a new kind of test makes no plan careful.
   A brief with the line `careful: the owner says so` is a yes too, whatever the two tests
   give: the owner called the task careful before its plan, in the ask or later.
   Write the call into the plan as one line under its title, before `## Acceptance criteria` (a line
   that is no criterion is refused inside that section), `careful: yes` or `careful: no`, with the
   one sentence of why: the topic in the owner's words and the task that reaches it, the pattern, or
   what you checked to say that none is reached. The landing reads the call there and nowhere
   else, and a yes stays a yes: a later commit that writes `no` does not take back the talk or
   the full review. The same line goes into your next state block, where the owner reads it on
   the board while the task builds, and into the report. Yours is not the last look: the agent
   that reviews the diff before the pull request reads the change against the same topics, and
   a careful call of its own makes the request careful whatever the plan said.
   An outcome that needs more than seven tasks is two asks: say so in the report, and plan the
   first.
3. **A careful or large plan is talked through before a builder leads its build.** A plan is
   large when `## Tasks` has more than three numbered tasks. When step 2 says careful, or the
   plan is large, read `talk` in `lem project --repo WORKTREE tasks`
   for this task: the newest `plan.talk` of its event log, or null.
   - *null*: the talk of step 4 comes first.
   - *a record*: the talk is done, and you lead the build of the plan it left: skip step 4, take
     the questions it left open at step 5, and go on. Read the `## Plan talk` section first: a
     repair changed the plan after you wrote it.
   When your brief says `stop after the plan: yes`, take the plan's decisions through step 5
   first, then write the state `planned` with the line `the owner reads the plan`, show him the
   plan to mark up (`show-page`), and wait in this session for his "build" or "drop".
4. **A careful or large plan gets a plan talk before any code**, in a pair you open under this
   session: its agent, the plan's defender (`prompts/defender.md`), holds the talk with the
   reviewer in its other pane by `stages/talk.md`, and writes its record into the plan as `##
   Plan talk` and into the event log as `plan.talk`. You do not read that file.
   1. Write `report.md` with why the plan is talked through (the topic, the pattern, the owner's
      word, or the count), and `talk-brief.md` in the task directory, with this and nothing more:

      ```
      Read `skills/lem/prompts/defender.md` in the folder that `lem version` prints as `root`, and follow it; when `lem version` fails, stop and say that `lem` is not on the PATH, with `lem doctor` as the check.
      task: SLUG
      branch: the task's branch
      worktree: the worktree's absolute path
      task directory: the task directory's absolute path
      ```

   2. Open the pair (`open-task-session`, the plan talk's) with that file, on the seat that `lem
      project --repo WORKTREE seat SLUG planner` prints, and write the state `building` with the
      lines `the plan talk runs`, `lead: session` and `defender: MODEL, EFFORT`, as the pair's
      status line shows them (the harness file says how to read them). A pair whose agent gives
      an error at its open is a seat that failed, and the harness file says how its stand-in
      opens, or the block of step 3 comes. When `lem project state` refuses that `building`
      because the task is `blocked` with `the seat that failed:`, a seat of the pair failed before
      you wrote it: write nothing over the block, and go on at step 3, whose wait gives it.
   3. `run-in-background` with `lem session wait SLUG --until planned,held,blocked --companion ID
      --quiet TASK_DIR/talk-turns.md`, `ID` the pair's id from its open and `TASK_DIR` the task
      directory, where the defender keeps the talk's turns as they come. Its end wakes you:
      - `planned` with `the plan talk is done`: close the pair (`open-task-session`), write the
        state `building` with the line `lead: builder`, and go on at step 3, which now finds the
        record.
      - `held`: the defender tripped the breaker. Close the pair and take it up as
        `stages/breaker.md` says under "After it".
      - `blocked`: a seat of the talk gave an error, and no fallback could stand in for it. Close
        the pair, mark this session as waiting for the owner (`mark-waiting`), then say the
        block's first line in one line, the last text of your turn, and wait. On his "go on",
        run `lem project --repo WORKTREE seat-again SLUG`, which writes `building` again and
        names the seat it tries again, and open the pair at step 2 once more: its defender goes
        on from `talk-turns.md`.
      - `"companion"`: the pair is gone and no state came. Read `talk` in `lem project --repo
        WORKTREE tasks` and the plan's `## Plan talk` first. A record there means the talk ended
        and its defender stopped before its state: go on as on `planned`. No record: open the
        pair once more at step 2; when that one is gone with no record too, write the state
        `held` with the line `the plan talk's pair ended twice with no record: its screen is the
        owner's to read`.
      - `"quiet": true`: `talk-turns.md` has not changed for 45 minutes, and an agent that stopped
        at a limit and stays live in its pane sends nothing. Read the screen of each pane of the
        pair (the harness file says how). One of the four errors of the seats (the harness file's
        `second-opinion`) on the defender's pane is `lem project --repo WORKTREE seat-failed SLUG
        planner`, on the reviewer's pane `lem project --repo WORKTREE seat-failed SLUG
        reviewer`, each with `--seat` the seat that `lem project seat` gave when that pane
        opened, which it still prints while no stand-in came after. Then close the pair: on a
        seat to open, open the pair at step 2 again, whose defender goes on from
        `talk-turns.md`; on `blocked: true`, take the block above. No error on either screen: run
        the same wait again, since a slow agent is no error. The 45 minutes are the guard's
        number for a session with no sign of work (the owner's, 2026-11-22), taken here as a
        guess for a talk.
   A task that becomes careful after its plan, by the owner's word, by the review's call or
   by an edit of `.lem/settings.toml`, gets no talk afterwards: the landing's full
   review reads the code that exists.
5. **A decision of the plan in doubt climbs the ladder, and the work goes on.** A decision the
   lead may take is logged with `--by lead` (`stages/build.md`, "A choice in the build", step 1).
   One in doubt takes `stages/ladder.md`, whose pick is taken at once and written into the plan;
   only a pick the breaker stops (`stages/breaker.md`) holds the task. Then go on to step 6. A
   plan whose talk is due takes this step after the talk, for its own decisions.
   A question the plan talk left open climbs the ladder like any other, with the two positions as
   its facts, and the defender takes it before it stops. A design choice about a decision of the
   plan (a layer over a decision with no cite, a decision two questions named, or a changed
   decision that brought issues of its own) is an honest comparison of both sides: one option is
   the kept decision with each mechanism that guards it, the other the reversed decision with the
   tasks and the criteria it changes and each issue the reviewer raised against it. The kept
   decision is the one the plan holds as the talk left it, after its repairs, never the one the
   plan held before them. Both are the
   ladder's options, and the pick of level 1 is the kept decision: the plan stands until a level
   settles otherwise, and the defender is one of the two positions that did not settle. The pick
   is taken: the defender writes the reversed decision into the plan when a level picks it, and
   trips the breaker when it changes the rule of an approved criterion.
6. **Go on to `build`.** Write the state `building` with the line `plan committed, N tasks`.
