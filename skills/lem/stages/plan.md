# plan

The lead's first stage. A plan here is short and written by whoever builds. It exists so the
builder has thought before typing and so a reviewer can tell what was meant; it is not argued line
by line before the build. Only a careful or large plan is talked through with the reviewer, over
a list of questions that closes with the reviewer's first turn (step 4).

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
     "A choice in the build") with its own record (`decisions.py story`), never a silent edit:
     `show`, `record` and `red` refuse a plan whose stories are not the approved ones with each
     recorded change, word for word, or whose `Kind:` is not the approved kind. An approved
     correction that step 2 finds careful, or that needs a second story, is a feature, and the
     kind is his only: it is a held decision (step 5), and Lem asks him;
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
     the event the landing reads, in the form `stages/new.md` gives ("The interview and the
     stories", step 5), with `by=lead`, your one family, and the digest of the plan's stories
     (`python3 SKILL_DIR/scripts/stories.py --repo WORKTREE digest SLUG`). A persona agent that
     did not answer is named in `silent` with why; a read in which nobody answered is started
     once more. Nobody confused: freeze the stories they read,
     `python3 SKILL_DIR/scripts/stories.py --repo WORKTREE approve SLUG --read`, which takes the
     plan's stories and refuses any other text than the one the read names. It freezes the task's
     first contract only, and is refused once the task has any approval: from then on a story the
     build changes has its record (`decisions.py story`), and the kind is his to change. It is
     never his yes. The build starts with no wait, and your next
     state block says `nobody confused, read by N personas, one model family`, where he sees it
     and can stop the task. The landing refuses a feature with no such event. A doubt: the
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
   - the documentation task, last, when the change makes a document false: a guide, the README,
     the agent document, the style guide, a page of help. Write it like any other task, with the
     documents it corrects by path and what in each one the change makes false; it serves no
     story unless a story is about a document. The landing's polish pass checks that no document
     the change made false was missed; it is the check, not the place where documents are
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
   through the mailbox to find the obstacle the planner did not see and a better design. A
   one-shot read does not do that: "there is no interaction between plan writer and reviwer, so
   they cannot look for a better design together, this proces just makes the writer satisfy the
   reviewer without actually changing the approach" (the owner, 2026-11-15). Nor may the talk run
   without an end: "I don't want them to argue till the end of days" (the owner, 2026-11-16). A
   plan is prose, and each repair is new prose that the next turn reads: a stored price, then
   its invalidation, then the bulk import that skips it, then the nightly repair, then the race
   with checkout. So the questions are a closed list, each gets one repair, and a question that
   comes back stops, as revmux stops a loop whose finding of the last round arrives again. The
   rules:
   - **Open the seat** with `second-opinion`, at the seat's `plan_effort`, and log its start, so
     that the board draws the talk from it:

     ```bash
     python3 SKILL_DIR/scripts/project.py --repo WORKTREE log SLUG plan.talk.start reviewer=AGENT
     ```

     The first message names the plan's path, the worktree, the task, the style guide files
     `project.py rules` prints for the plan's files, and the code the plan rests on, by path and
     symbol, and asks for the full list.
   - **The list closes with the reviewer's first turn.** That turn is a full read of the plan: a
     numbered list of questions, the most expensive first, each with the position of the plan it
     challenges, its mechanism, and its place (a section of the plan, or a file and symbol). Keep
     the list as it came, before you change anything: the next two rules are checked against it.
   - **One repair per question.** For each question, repair the plan and commit, or refute the
     question with a cite. Check each of its claims in the code before you answer. The reviewer
     answers each question by its number only:
     `closed`, when the repair or the refutation holds, or `holds`, with why. A question that
     holds gets one more answer from you: a refutation of that why with a cite, or the repair
     when your first answer was a refutation; never a second repair. A refutation of the repair's
     own new text is the same question, not a new one.
   - **A question that holds a second time stops.** It closes as a design choice: the plan's
     design against the smallest option it was priced against. Do not edit the plan to settle it:
     it goes to step 5 as a numbered choice, with both positions in `--said`.
   - **A question after the first turn is not argued.** It goes into the record as "raised, not
     argued", with its mechanism and place, and the review before the pull request checks it as a
     claim (`prompts/review.md`).
   - **A scope the plan puts out of the change is not a question.** A question that only restates
     a scope the plan writes as out of the change is answered with that line and closed. Only a
     line the plan held when the reviewer read it counts; one written to answer the question is a
     repair.
   - **An addition names four things or is refused**: a guard, a lock, a table, a worker, a
     column, a flag, a retry, from either side. The four: the failure it prevents, the input that
     produces that failure, whether that input is realistic here, and what breaks without it. A
     refused addition goes into the record as unpriced. "Argue why this fails" is answered with
     refutations of the plan as it stands, never with additions.
   - **What a person of the project would see** is not the two agents' to settle. A question
     about it goes to the persona panel, in its reviewing mode, with both positions; its clear
     answer settles the question, and the record says the personas settled it. One with no clear
     answer stays open, and step 5 takes it. It never goes to the owner from here.
   - **The close.** When each question of the list has ended, settled, a design choice or open,
     write `nothing further`; the reviewer adds no turn after that.
   Commit every repair before any code. Then write the record into the plan, as a section
   `## Plan talk` after `## Tasks`, and commit it:
   - who argued the plan with you: the agent, and its model and effort as its pane's status line
     shows them;
   - the list, numbered as the reviewer gave it, each question with how it ended: settled, with
     its cite and after it the words "settled by the two, not checked by the review"; a design
     choice, with the two positions, each with its cite, and the choice step 5 asks; or open, with
     the two positions and where it went (step 5 takes it);
   - each question raised after the first turn, marked "raised, not argued", with its mechanism
     and place;
   - each addition that was refused as unpriced;
   - what changed in the plan, by question and by task.
   Agreement carries no authority: the review before the pull request reads a settled position
   as a claim, not as a fact. Then close the reviewer's pane (the harness file, `second-opinion`)
   and write the one event the landing reads:

   ```bash
   python3 SKILL_DIR/scripts/project.py --repo WORKTREE log SLUG plan.talk reviewer=AGENT turns:=N questions:=N settled:=N open:=N repaired:=N design:=N unargued:=N
   ```

   `turns` counts each message of either side; `questions`, the questions of the reviewer's first
   list; `settled` and `open`, how many of them ended each way, a design choice counted as open;
   `design`, the open ones that held a second time; `repaired`, the questions whose answer
   changed the plan; and `unargued`, the questions raised after the list. The script refuses a
   record of fewer than two turns, or one with no question settled and none left open: a floor
   against an empty record, not a measure of a good talk. It refuses counts that do not agree:
   settled and open that do not add up to questions, more design choices than open questions,
   more repairs than questions. And it refuses more than 4 × questions + 2 turns: the list, two
   answers of each side on each question, and the close. That bound is derived from these rules
   in a Fable second opinion (2026-11-16), not measured. The landing refuses a request whose
   plan says `careful: yes` or has more than three tasks with no such event, and the pull request's checks show the newest one. A task that
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
   A question the plan talk left open is a decision of this step like any other, with the two
   positions as what it rests on. One that is held is not written under "held": ask it as a
   numbered choice, with `decisions.py ask` (`stages/build.md`, "A choice in the build", step 2),
   whose `--said` holds both positions and what the personas answered, or why they were not
   asked, and go on with the tasks that do not depend on it, as that section's steps 3 and 4 say.
   A design choice of the talk is always asked so, never taken by you: the lead is one of the two
   positions that did not settle.
6. **Go on to `build`.** Write the state `building` with the line `plan committed, N tasks`.
