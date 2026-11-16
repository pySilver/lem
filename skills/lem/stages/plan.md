# plan

The lead's first stage. A plan here is short and written by whoever builds. It exists so the
builder has thought before typing and so a reviewer can tell what was meant; it is not argued line
by line before the build. Only a careful or large plan is talked through with the reviewer, one
question at a time (step 4).

1. **Write the plan** as one file in the settings' `plans` path, named `YYYYMMDD-<slug>.md`, and
   commit it as the branch's first commit. It opens with the stories, because they are the
   owner's document: he reads them and not the rest of the plan, and they become the tests.
   - `## Stories`, in the form `python3 SKILL_DIR/scripts/stories.py --help` shows. First run
     `python3 SKILL_DIR/scripts/stories.py approved SLUG`. When the owner approved stories at
     his interview, they are your stories: copy the section word for word, numbered the same,
     and add only the test lines under each, at the end of the build. You may break a story's
     text into other lines; you may not change a word of it. The plan follows the task's
     `directions.md` too, when the task directory has one. A story or a direction the code shows
     you cannot keep, or a story that is missing, is a decision of the build (`stages/build.md`,
     "A choice in the build"), never a silent edit: `show`, `record` and `red` refuse a plan whose
     stories differ from the approved ones without a decision for each difference. An approved
     correction that step 2 finds careful, or that needs a second story, is a feature: the
     record gets that decision, and the personas read its stories as the next bullet says;
   - with no approved stories (the rare path, a night plan), write them. A story is one
     business rule of the request in plain language with one concrete example, with real names
     and values: what a person of the project would see, never how the code does it. Take them
     from the outcome and the "done when" of `task.md`, now that you have read the code. A rule
     you cannot write without guessing what the owner wants is not yours to guess: it is a held
     decision (step 5), and Lem asks him. The first line of that section is your call,
     `Kind: feature` or `Kind: correction`, with the reason after `because`. A correction is a
     request that yields one story and is not careful (step 2): its story is the owner's own
     sentence made exact. Everything else is a feature. The owner may overrule the call, as he
     may the careful one;
   - then the personas read the stories you wrote, unless they are a correction's one story:
     the persona panel's "Reading stories" mode (`load-skill`), run by you while you write the
     rest of the plan. You have no paired agent of the other family, so one family answers: the
     panel's own persona agents, which a lead can start (the harness file, `spawn-builder`). Write
     the event the landing reads, `python3 SKILL_DIR/scripts/project.py --repo WORKTREE log SLUG
     stories.read by=lead personas:=N families:='["FAMILY"]' stories:=N flagged:=N`. Nobody
     confused: the build starts with no wait, and your next state block says `nobody confused,
     read by N personas, one model family`, where he sees it and can stop the task. A doubt: the
     first line of code waits. Write `report.md` with the stories and the answers that flagged
     them on top, quoted, and the line `the stories wait for the owner`; write the state `held`
     with that line, and stop. Leave a flagged story as you wrote it: what you would change goes
     beside it, as a proposal, and he decides;
   - run `python3 SKILL_DIR/scripts/stories.py record SLUG`: it refuses a section that does not
     have the form, or that departs from the approved stories, and it puts the stories where
     the board and Lem's status show them;
   - `## Tasks`: a numbered list of one to seven tasks, each an outcome a reviewer can check
     alone and one builder can finish in a context of its own, with the stories it serves and
     the files it expects to touch. The landing counts the numbered lines under that heading:
     a plan of more than three is large, gets a plan talk before any code (step 4) and a review
     round at the least, and a plan with no such list is refused there;
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
2. **Is the task careful?** Three tests, and one yes is enough:
   - *a path*: `project.py careful` over the files the plan names. A match is a yes that no
     judgment of yours overturns.
   - *a topic*: the project's danger topics (`flow.topics` in `project.py show`), each a
     sentence of the owner's about what must not go wrong here. Read the plan against each one:
     does a task change how that thing behaves, or could a defect in a task reach it? No code
     matches a topic, and no file name settles it: a price is computed in more places than
     `billing/`. This is your judgment, and a person can overlook a danger that you see in the
     code, so say what you see.
   - *a pattern*: the plan starts something other code will copy (a first service layer, a
     first use of a library, a new kind of test).
   Write the call into the plan as one line under its title, before `## Stories` (a line that
   is no story is refused inside that section), `careful: yes` or `careful: no`, with the one
   sentence of why: the path, the topic in the owner's words, the pattern, or what you checked
   to say that none is touched. The same line goes into your next state block, where the owner
   reads it on the board while the task builds, and into the report.
   An outcome that needs more than seven tasks is two asks: say so in the report, and plan the
   first.
3. **A builder does not lead a careful or large task.** A plan is large when `## Tasks` has more
   than three numbered tasks. When your brief says `lead: builder` and step 2 says careful, or the
   plan is large: write `report.md` with what says so (the path, the topic, the pattern, or the
   count); write the state `planned` with the line `needs a session: careful` or
   `needs a session: large, N tasks`; and stop. The plan talk of step 4 needs the reviewer's pane
   and the mailbox, and a builder has neither (the harness file, `spawn-builder`). Lem opens a
   session, and its lead starts from your plan. When your brief says `stop after the plan: yes`,
   stop the same way with the line `the owner reads the plan`.
4. **A careful or large plan gets a plan talk before any code.** This is the session's step, and
   it comes before step 5 lets any task be built. The lead and the reviewer argue the plan
   through the mailbox, one question at a time, to find the obstacle the planner did not see and
   a better design. A one-shot read does not do that: "there is no interaction between plan
   writer and reviwer, so they cannot look for a better design together, this proces just makes
   the writer satisfy the reviewer without actually changing the approach" (the owner,
   2026-11-15). The rules are the owner's own for two agents that argue a plan:
   - **Open the seat** with `second-opinion`, at the seat's `plan_effort`. The first message
     names the plan's path, the worktree, the task, the style guide files `project.py rules`
     prints for the plan's files, and the code the plan rests on, by path and symbol.
   - **One question at a time.** You state a position: what the plan does, the smallest option
     you priced it against, and the code that supports it. The reviewer refutes it with a cite or
     a concrete input that breaks it, or agrees with a cite. Check each of its claims in the code
     before you answer.
   - **An addition names four things or is refused**: a guard, a lock, a table, a worker, a
     column, a flag, a retry, from either side. The four: the failure it prevents, the input that
     produces that failure, whether that input is realistic here, and what breaks without it. A
     refused addition goes into the record as unpriced. "Argue why this fails" is answered with
     refutations of the plan as it stands, never with additions.
   - **No turn limit.** The talk goes on while each turn brings something new: a refutation, a
     cite, a checked fact, a changed position. A turn that only restates the one before ends that
     question. When the reviewer answers `nothing new`, or no question is left, close with
     `nothing further`; the reviewer adds no turn after that.
   - **What a person of the project would see** is not the two agents' to settle. A disagreement
     about it goes to the persona panel, in its reviewing mode, with both positions; its clear
     answer settles the question, and the record says the personas settled it. It never goes to
     the owner from here.
   Fix the plan for each refutation that holds, and commit it before any code. Then write the
   record into the plan, as a section `## Plan talk` after `## Tasks`, and commit it:
   - who argued the plan with you: the agent, and its model and effort as its pane's status line
     shows them;
   - each settled position with its cite, and after it the words "settled by the two, not
     checked by the review";
   - each disagreement left open: the two positions, each with its cite, and where it went
     (step 5 takes it);
   - each addition that was refused as unpriced;
   - what changed in the plan, by task.
   Agreement carries no authority: the review before the pull request reads a settled position
   as a claim, not as a fact. Then close the reviewer's pane (the harness file, `second-opinion`)
   and write the one event the landing reads, with a turn for each message of either side:

   ```bash
   python3 SKILL_DIR/scripts/project.py --repo WORKTREE log SLUG plan.talk reviewer=AGENT turns:=N settled:=N open:=N
   ```

   The script refuses a record of fewer than two turns, or one with no position settled and
   none left open. Those bounds are a floor against an empty record, not a measure of a good
   talk. The landing refuses a request whose plan says `careful: yes` or has more than three
   tasks with no such event, and the pull request's checks show the newest one. A task that
   becomes careful after its plan, by the owner's word or by a path its diff matches, gets no
   talk afterwards: the landing's full review reads the code that exists. A one-shot read of a careful plan, before this talk replaced it,
   took nine minutes and found three design failures before any code (convertiser-server,
   2026-11-14). In another repository a plan round before any code found at least one major
   finding in 7 of 9 plans whose records tell majors from minors, and the largest found 19
   (mybaze, 2026-09-25 to 2026-11-03, counted by one reader from that project's notes). Both
   were reads, not talks; no talk is measured yet. A plan that is neither careful nor large has
   no talk, and that is what the skip can cost.
5. **A held decision goes to the owner, the others do not.** For each decision of the plan: a
   ruling, a test or a probe answers it → quote that. It is cheap to undo → take it and log it
   with `decisions.py log SLUG --by lead` (`stages/build.md`, "A choice in the build"). It turns on a claim that can be argued both ways ("this will not scale",
   "nobody uses that") → the `lem-dialectic` skill settles the claim first. Its options each cost a
   person something and nothing answers it → it is held, and it is not yours to ask. Write it in
   `report.md` under "held", so that Lem can ask it without reading the code:
   - one concrete case in numbered steps that ends badly, with real names and values and where
     each step was read, and whether you reproduced it or derived it;
   - one line on why the case became possible and how far the same cause reaches;
   - the options, each as what a person would see and what it costs, and what you would choose.
   Then build the tasks that do not depend on a held decision. Write the state `held` and stop
   only when every task that is left depends on one. A builder whose plan is careful or large has
   stopped at step 3 before this, and the session that takes the plan over does step 4 first.
   A disagreement the plan talk left open is a decision of this step like any other, with the
   two positions as what it rests on. One that is held is not written under "held": ask it as a
   numbered choice, with `decisions.py ask` (`stages/build.md`, "A choice in the build", step 2),
   whose `--said` holds both positions and what the personas answered, or why they were not
   asked, and go on with the tasks that do not depend on it, as that section's steps 3 and 4 say.
6. **Go on to `build`.** Write the state `building` with the line `plan committed, N tasks`.
