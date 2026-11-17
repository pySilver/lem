# plan

The lead's first stage. A plan here is short and written by the task's lead, which then gives
each of its tasks to a fresh builder. It exists so the builder has thought before typing and so a reviewer can tell what was meant; it is not argued line
by line before the build. Only a careful or large plan is talked through with the reviewer, over
a list of questions that closes with the reviewer's first turn, by its defender and not by you
(`stages/talk.md`).

1. **Write the plan** as one file in the settings' `plans` path, named `YYYYMMDD-<slug>.md`, and
   commit it as your first commit: after a bug, the investigator's test comes before it. It opens with the acceptance criteria, because they are the
   owner's document: he reads them and not the rest of the plan, and they become the tests.
   - `## Acceptance criteria`, in the form `python3 SKILL_DIR/scripts/criteria.py --help` shows.
     First run `python3 SKILL_DIR/scripts/criteria.py approved SLUG`. When the owner approved
     criteria at his interview, they are your criteria: copy the section word for word, numbered the
     same, and add only the test lines under each, at the end of the build. A criterion whose change
     keeps behavior (a rename, a version bump, a refactor) is held by the suite: its line is `- no
     test: the change keeps behavior; the suite holds it`, and the checks before the pull request
     run the whole suite, which proves it. Its builder runs the tests of the files it changes and
     of their direct callers, as every builder does, and no builder runs the whole suite. You may break a criterion's
     text into other lines; you may not change a word of it. The plan follows the task's
     `directions.md` too, when the task directory has one. A criterion or a direction the code shows
     you cannot keep, or a criterion that is missing, is a decision of the build (`stages/build.md`,
     "A choice in the build") with its own record (`decisions.py criterion`), never a silent edit:
     `show`, `record` and `red` refuse a plan whose criteria are not the approved ones with each
     recorded change, word for word, or whose `Size:` is not the approved size. Criteria approved
     as a small change do not reach a lead: a small change has one builder and no plan
     (`stages/new.md`, "A small change"), and one that is a full change after all comes to you
     with his approval of its criteria as a full change. A plan's size is always `full`:
     `criteria.py` and `land.py` refuse a plan that says `Size: small`;
   - with no approved criteria (a full change from a complete request, a night plan), write them.
     A criterion is one business rule of the request in plain language with one concrete example,
     with real names and values: what a person of the project would see, never how the code does
     it. Take them from the outcome and the "done when" of `task.md`, now that you have read the
     code. A rule you cannot write without guessing what the owner wants is not yours to guess:
     the criteria wait for him, as for a doubt of the personas below, with the criterion as you
     would guess it and each other reading beside it as a proposal. The first line of that section
     is `Size: full`, with the reason after `because`, also for a plan of one criterion: a plan
     never makes a change small. One plain change with nothing careful is a small change, which
     has one builder and no plan (`stages/new.md`, "A small change"), and Lem chose this path for
     the task before you started. When the code shows you that it is one, still write the full
     change, and say in the report that it was a small change, for Lem's next call of a size;
   - then the personas read the criteria you wrote. Here
     the read always runs, as the only approval of this path: the owner's word to skip it belongs
     to an interview (`stages/new.md`, "The interview and the acceptance criteria", step 5), and the
     landing refuses one that comes after a lead started. The read is the persona panel's "Reading
     acceptance criteria" mode (`load-skill`), run by you while you write the rest of the plan. You
     have no paired agent of the other family, so one family answers: the panel's own persona
     agents, started the way the `lem-panel` skill starts a persona, never as a builder:
     `lem-builder` has no persona among its jobs. Log its start as it starts, `python3
     SKILL_DIR/scripts/project.py --repo WORKTREE log SLUG criteria.read.start by=lead`. Write the
     event the landing reads, in the form `stages/new.md` gives ("The interview and the
     acceptance criteria", step 5), with `by=lead`, your one family, and the `digest` field of what `python3
     SKILL_DIR/scripts/criteria.py --repo WORKTREE digest SLUG` prints for the plan's criteria. A
     persona agent that did not answer is named in `silent` with why. A read in which nobody
     answered is written down too, in the form `stages/new.md` gives for it, and started once more;
     after a second one in a row, freeze the criteria as below, write the state line `the criteria
     were not read: nobody answered twice`, and build: the pull request is not green for it. Nobody
     confused: freeze the criteria they read, `python3 SKILL_DIR/scripts/criteria.py --repo WORKTREE
     approve SLUG --read`, which takes the plan's criteria and refuses any other text than the one
     the read names. It freezes the task's first contract only, and is refused once the task has any
     approval: from then on a criterion the build changes has its record (`decisions.py criterion`),
     and the size is his to change. It is never his yes. The build starts with no wait, and your
     next state block says `nobody confused, read by N personas, one model family`, where he sees it
     and can stop the task. The landing refuses a full change with no such event. A doubt: the
     first line of code waits. Write `report.md` with the criteria and the answers that flagged
     them on top, quoted, and the line `the criteria wait for the owner`; write the state `held`
     with that line, and stop. Leave a flagged criterion as you wrote it: what you would change goes
     beside it, as a proposal, and he decides;
   - run `python3 SKILL_DIR/scripts/criteria.py record SLUG`: it refuses a section that does not
     have the form, or that departs from the approved criteria, and it puts the criteria where
     the board and Lem's status show them;
   - `## Tasks`: a numbered list of one to seven tasks, each an outcome a reviewer can check
     alone and one builder can finish in a context of its own, with the criteria it serves and
     the files it expects to touch. The landing counts the numbered lines under that heading:
     a plan of more than three is large, gets a plan talk before any code (step 4) and a review
     round at the least, and a plan with no such list is refused there;
   - the documentation task, last, when the change makes a document false: a guide, the README,
     the agent document, the style guide, a page of help. Write it like any other task, with the
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
   Before writing, read the style guide files that cover the files the plan touches and the
   project's lessons (`project.py path lessons`). `python3 SKILL_DIR/scripts/project.py rules
   FILE ...` prints those style guide files, the ones with no scope of their own too: do not
   match a file's `paths:` by eye.
   When the branch already holds a plan (a night draft, a builder that stopped at the plan), do
   not write another: read it against the code as it is now, and commit a fix for what the code
   has outgrown.
2. **Is the task careful?** Two tests, and one yes is enough:
   - *a topic*: the project's topics (`flow.topics` in `project.py --repo WORKTREE show`, which
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
   plan is large, read `talk` in `python3 SKILL_DIR/scripts/project.py --repo WORKTREE tasks`
   for this task: the newest `plan.talk` of its event log, or null.
   - *null*: write `report.md` with what says so (the topic, the pattern, the owner's word, or
     the count); write the state `planned` with the line `needs a session: careful` or
     `needs a session: large, N tasks`; and stop. The plan talk of step 4 needs the reviewer's
     pane and the mailbox, and a builder has neither (the harness file, `spawn-builder`). Lem
     opens a companion session for the talk, and its agent, the plan's defender, starts from your
     plan (`prompts/defender.md`, `stages/talk.md`).
   - *a record*: the talk is done, and you lead the build of the plan it left: skip step 4, take
     the questions it left open at step 5, and go on. Read the `## Plan talk` section first: a
     repair changed the plan after you or another builder wrote it. Every plan has you start a
     builder for each of its tasks, which the harness file checked from a `worker` subagent and
     not yet from a `lem-builder`: when your agent refuses you the start of a builder, write the
     state `blocked` with that refusal, and stop.
   When your brief says `stop after the plan: yes`, take the plan's decisions through step 5
   first, then stop the same way with the line `the owner reads the plan`; a night plan whose
   step 5 found a decision of the owner's stops with step 5's line instead.
4. **A careful or large plan gets a plan talk before any code**, in the companion Lem opens for
   it: the defender holds the talk with the reviewer by `stages/talk.md`, and writes its record
   into the plan as `## Plan talk` and into the event log as `plan.talk`. You do not read that
   file: you stopped at step 3 before the talk, or the talk is done and its record is in the
   plan. A task that becomes careful after its plan, by the owner's word, by the review's call or
   by an edit of `.lem/project.toml`, gets no talk afterwards: the landing's full
   review reads the code that exists.
5. **A decision that is the owner's is asked, and the work goes on.** For each decision of the
   plan: a ruling, a test or a probe answers it → quote that. It is cheap to undo → take it and
   log it with `decisions.py log SLUG --by lead` (`stages/build.md`, "A choice in the build"). It
   turns on a claim that can be argued both ways ("this will not scale", "nobody uses that") → the
   `lem-dialectic` skill settles the claim first. Its options each cost a person something and
   nothing answers it → it is the owner's, and it takes the one path every such decision takes,
   at plan time as in the build: `stages/build.md`, "A choice in the build", step 2. The persona
   panel reads it first, and a clear answer of theirs is taken and logged; an unclear one is
   asked with `decisions.py ask`, whose card has to tell the owner one run without the code:
   - `--case`: one concrete case in numbered steps that ends badly, with real names and values
     and where each step was read, and `--case-was reproduced` or `--case-was derived`;
   - `--cause`: one line on why the case became possible and how far the same cause reaches;
   - an `--option` for each, as what a person would see and what it costs, and `--recommended`
     with `--why`, what you would choose;
   - `--said`: what the personas answered.
   Then tell Lem and give it to the experts, as that step says, and go on to step 6: the build
   takes the tasks that do not depend on it, and the wait ends as that section's steps 3 and 4
   say. The state `held` is not for such a decision. A builder whose plan is careful or large and
   has no talk yet has stopped at step 3 before this; the builder that leads after the talk takes
   this step for the plan's own decisions.
   A question the plan talk left open is a decision of this step like any other, with the two
   positions as what it rests on, and the defender takes it before it stops. One that is the
   owner's is asked the same way, and its `--said` holds both positions and what the personas
   answered, or why they were not asked. A design choice about a decision of the plan (a layer
   over a decision with no cite, a decision two questions named, or a changed decision that
   brought issues of its own) is an honest comparison of both sides: one option is the kept
   decision with each mechanism that guards it, the other the reversed decision with the tasks
   and the criteria it changes and each issue the reviewer raised against it, and `--said` holds
   both. A design choice of the talk is always asked so, never taken by the defender or the
   builder: the defender is one of the two positions that did not settle.
   A night plan is the exception: its brief has the line `night: yes`, nobody is there to answer,
   and a night never takes a decision of the owner's by its wait or by the experts, so
   `decisions.py ask` refuses there. Write each such decision into `report.md` under "for the
   owner", with the same case, cause and options, write the state `planned` with the line `the
   plan ends on a decision of the owner's`, and stop (`stages/night.md`, step 4).
6. **Go on to `build`.** Write the state `building` with the line `plan committed, N tasks`.
