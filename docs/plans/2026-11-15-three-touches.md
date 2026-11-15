# Three touches: stories, one read before the merge, a pull request

Written 2026-11-15 by the Lem design session (mybaze checkout) for the session that builds Lem,
which took it the same day and added "Read against the code" below. This replaces "build
first, review after" as Lem's default flow. The owner said on 2026-11-15 that it is built
directly, with a read by the other lab after each part, and not through Lem.

## Why

The owner chose "build first, review after" on 2026-11-14 from the convertiser-server
coordinator. There it lands on an integration branch; Lem lands on the base branch. On
2026-11-15 he read "land means that the commits of a task are on the base branch" and wrote:
"I think its very dangerous in most cases", and "Lem should be helpful companion for the 1st
class 10x developers, not a naive 'fail fast' developer".

The flow he had in mybaze is the opposite and he does not want it either: "every, even trivial
plan takes ages to implement … Real developers don't sit on each others laps all the time."

What he said works for him, in his words (2026-11-15, an interview in the design session):

- "I stopped reading all the plans. Does Product Owner reads the plan of Tech lead? No, not
  really. What I decided to do is to read the user stories and approve them. User stories then
  become unit tests and or e2e tests."
- "I decided to create those personas profiles and ask them to read first and only report to me
  if something bothers or confuse them, as this is a sign of misunderstanding or bad plan."
- "I think '3 touches' rule where attention of a Human is required is still valid: interview,
  plan approval, pr approval; But the thing is that Human needs to know that all the possible
  checks that were needed to be done **for that specific plan** were already made and it's
  either 'nobody confused' or 'some personas said it a questionable outcome'. I cannot be the
  judge all the time."
- "I would like to get more automated flow, so work cannot suddenly stop mid-exection. I believe
  in such event personas should carefully review best choice, sometimes it needs to do some
  limited research."
- On a review round over a plan: "there is no interaction between plan writer and reviwer, so
  they cannot look for a better design together, this proces just makes the writer satisfy the
  reviewer without actually changing the approach." And: "`revmux` author himself says that
  revmux is great for code reviews, not for prose reviews (plans)."
- "every project has personas, I don't see why we can have none when Lem is installed for a
  project".

He confirmed the statement below with "yes, thats correct" (after one correction, the personas
line).

## The confirmed intent

- **Result.** Lem takes a request to a pull request with three touches of the owner at most:
  the interview, the stories, the pull request. The interview happens only when the request is
  unclear.
- **For whom.** A senior developer who is product owner and tech lead at once, and whose
  attention is not always available.
- **His document** is the stories, in business language. They become the tests. The plan is the
  agents' document; he does not read it.
- **Who answers first.** The personas read the stories and every surprise before he does. Nobody
  confused: the build starts and does not wait; he gets "nobody confused" and can stop it. A
  persona confused or in doubt: the work waits and he gets the stories with the personas'
  answers on top. A small correction has one story, his own sentence; Lem shows it and does not
  stop.
- **The checks** are chosen by the agents for each plan, and every page for him lists the checks
  that ran and what each returned.
- **During the build nothing waits for him**, except a step that a later "no" cannot reverse.
- **No change reaches the base branch without a read.**
- **Out of scope:** pair planning of every plan, a review round over a plan, a review of each
  task of a usual request, a review queue after the merge, his approval of a plan, everything
  after the merge (deploy, flags, rollback).

## What backs the shape

`2026-11-15-three-touches/research-human-practice.md` (a research agent opened each source; the
design session did not) and three blind developer readers who each picked "one read before the
merge, depth by risk" from a neutral brief (`2026-11-15-three-touches/brief.md`). The findings
this design leans on:
one reviewer is the norm and more add little (Sadowski 2018, Rigby and Bird 2013); a change not
reviewed at once is rarely reviewed later (Rigby 2008, and 43 of 48 queued reviews open after 28
hours in convertiser-server); a heavier approval showed no better stability (DORA 2019); review
comments are mostly not about defects, so machine checks come first (Bacchelli and Bird 2013;
Stripe and Spotify's own reports); design talk up front only for an ambiguous or substantial
change (Ubl 2020, the Rust RFC rules).

The dissent to keep in view: in mybaze (2026-11-11, 215 transcripts) the review of each task
found a must-fix on 184 of 414 tasks and a review round over a plan found a major in at least
54% of plans. Nobody sorted those into defects a user would meet and the rest. If most were
real, one read is too thin. The flow below therefore measures itself (see "What Lem records").

## The flow

Words: a **request** is what the owner asks. A **story** is one business rule of the request in
plain language with one concrete example. The **plan** is the agents' list of steps. A **read**
is one independent agent reading a diff. A request is **careful** by today's rule (a listed
path, a named topic, a pattern other code will copy) or **large** when its plan has more than
three tasks.

1. **The request arrives** (`/lem <ask>`, a backlog item, a ticket). When the lead cannot write
   the stories without guessing what the owner wants, it interviews him first (touch 1).
2. **The stories.** The lead writes them at the top of the plan file, numbered. A request that
   yields one story and is not careful is a **correction**: the story is the owner's own sentence
   made exact, Lem shows it and goes on. The lead writes the call and one sentence of why; the
   owner can say "this is a feature".
3. **The personas read the stories** (every project of Lem has a cast). The lead picks the
   personas a story concerns and records who it left out and why. Each answers clear, confused
   or in doubt, with the reason.
   - Nobody confused or in doubt: the build starts. The owner gets the stories with "nobody
     confused" where he looks (the board, the Inbox when he uses it) and can stop the task.
   - Otherwise: the task is held and the owner gets the stories with the personas' answers on
     top, through `tools.ask` (touch 2). He approves, changes a story or drops the request.
4. **The plan.** Abstract steps, each naming the stories it serves. Nobody shows it to the owner
   for approval. A careful or large plan gets a **plan talk**: the lead and a reviewer of the
   other lab, through the mailbox, looking for the obstacle the planner did not see and for a
   better design. It goes on while a turn brings something new. A disagreement about what a
   person would see goes to the personas, not to the owner.
5. **The build.** One fresh builder per task, as ruled. Every story gets at least one test, and
   the plan records which.
6. **A surprise in the build never stops the task.**
   - The stories stay true: the lead decides and logs it with its why.
   - A story must change: the personas it concerns read the options, with a short check of
     outside facts when one decides it, and pick. The build goes on with their pick. The story's
     change is recorded: what it was, what it is, why, who said what.
   - The step cannot be reversed by a later "no", or the personas split: that part waits and the
     rest of the plan goes on. The owner gets the question with the personas' answers; the
     session is not blocked on it. "Cannot be reversed" is a short fixed list in the stage file:
     it destroys or rewrites data outside the worktree, writes to a system outside the
     repository beyond what the settings already allow (the tracker's ticket), sends something to
     a person, or spends money.
7. **Machine checks**, no model in them: the project's gate commands; every new test fails on
   the base commit; the change did not lower the bar without a stated reason (a new lint or
   type suppression, a skipped or deleted test, a removed assertion); the size of the diff.
8. **One read before the pull request.** A fresh agent of the other lab, through a small review
   profile of the project's review tool. It gets the owner's exact words, the stories, the diff
   and the rule files the picker gives for the changed files. It does not get the builder's
   reasoning. It labels each finding must-fix, should or nit; a must-fix names the input that
   fails or the story it breaks. Two rounds at most; after that the request goes to the owner as
   not clean, with the open findings, and looks different from a clean one.
   - A careful or large request gets the project's full review round over the branch in place
     of the small read.
   - A usual request whose read found a must-fix gets the full round after the fix. In mybaze
     this was the one sign that predicted a later major (5 of 15 branches against 1 of 15).
   - A diff that touches only documentation skips the read. A fixed path rule decides, never the
     agent, and files that agents read as rules (`AGENTS.md`, `CLAUDE.md`, rule files, `.lem/`,
     the review tool's folder, skill files) are not documentation.
   - A diff too large to read in one sitting is read task by task, in the plan's own cuts.
9. **The pull request** (touch 3). With a GitHub or GitLab remote, Lem opens it. With none, the
   branch is marked ready and `/lem land` puts it on the base branch on the owner's word. Its
   text, in this order: the request in his words; the stories, each with its tests, and every
   changed story with what it was, why it changed and what the personas said; the checks that
   ran for this plan and what each returned (gate, red-on-base, the bar, the read or the round
   with its rounds and verdict, the plan talk, the personas); the decisions with their reasons;
   the should findings left open; up to three places worth a human eye; for a careful request,
   whether it holds a migration and how to revert it; what was not done.
10. **The merge.** A person merges by default. A project may let the agent merge, and then only
    a request that is not careful, whose read is clean and whose stories did not change. After
    the merge Lem removes the worktree and the branch and updates the ticket.

## What goes away

- The review queue after the landing, with its script, its stage, its lane on the board, its
  scheduled pass and its README sections. An on-demand full round over a range may stay if the
  code makes it cheap; the queue does not.
- The review of each task in a careful session. The plan talk and the full round replace it.
- A second opinion on a plan from the review tool, wherever a stage still says so.
- Landing by push to the base branch as the meaning of `branch.land = "agent"`.

Not built here, file it: a mode for a long program of dependent branches that lands on an
integration branch, as convertiser-server works today.

## What Lem records, and the retro reports

Per request: the time from the request to the pull request; the read rounds and the must-fix
count; the stories that changed in the build; whether the personas stopped it; and, when a later
request fixes an earlier one, the link between them. The retro reports the medians and the
shares. Starting marks from one reader, all unmeasured estimates: more than one merge in twenty
followed by a fix request means the read is too thin; more than 15% two-round exits means the
builder's or the reader's brief is wrong; a correction that takes longer than an hour means a
step should go.

## Tasks, each an outcome

1. **Stories are the contract.** The plan file opens with numbered stories; the correction call
   is written with its why; `/lem status TASK` and the board show the stories; each story names
   its tests by the end of the build; the red-on-base check exists as a script with tests.
   Done when: a request with two stories ends with each story naming a test that fails on the
   base commit and passes on the branch; a correction shows one story and does not stop.
2. **The personas read the stories.** The panel's review mode over the stories, the pick of
   relevant personas with its record, the two outcomes, the page for touch 2.
   Done when: clear stories start the build with no wait and the owner can see "nobody
   confused"; a story a persona doubts holds the task and reaches the owner with the answers on
   top; his changed story replaces the old one before any code.
3. **A surprise does not stop the task.** The three ways, the changed-story record, the fixed
   list of irreversible steps, a hold on one part while the rest goes on.
   Done when: a builder that cannot satisfy a story gets the personas' pick and goes on, and the
   pull request shows the change first; an irreversible step holds only its own task.
4. **One read before the pull request.** The small profile, the reader's inputs and labels, two
   rounds, the escalation to a full round, the documentation rule, the bar check, large diffs.
   Done when: nothing can be marked ready without a read or the documentation rule; a must-fix
   without a failing input or a broken story is sent back to the reader, not to the builder.
5. **The task ends as a pull request.** Opening it on GitHub and GitLab, the ready state with no
   remote, the text in the order above, who may merge, the cleanup after a merge the owner did
   on the forge, the ticket.
   Done when: with a remote a request ends as an open pull request holding every part of the
   text; without one `/lem land` lands a ready branch; the agent refuses to merge a careful
   request or one with a changed story whatever the settings say.
6. **The plan talk.** For a careful or large plan, through the mailbox, with the stop rule; the
   per-task review leaves the careful session.
   Done when: a plan of four tasks gets a talk that ends in a settled position or a located
   disagreement, and a usual plan gets none.
7. **The queue goes.** With everything that names it.
8. **What the owner sees.** The board's lanes follow the touches (stories, building, reading,
   pull request, merged); the README's flow, words, commands and "what Lem writes" follow the
   new flow; the records and the retro's report.
   Done when: a developer who never saw Lem reads the README and can say what happens to their
   request, who reads it, and what reaches their main branch (the design session runs that
   blind read again).

## Read against the code

By the build session, 2026-11-15, before the first task. Each point is where the code or a
standing rule of Lem does not carry the flow as written, with what the build does about it.

1. **Only Lem talks to the owner** (`skills/lem/SKILL.md`, "Two levels"; a builder has no pane).
   So touch 1 is Lem's: `new` holds the interview when the request is unclear to Lem, and a lead
   that cannot write the stories without guessing stops as `held` with what it cannot tell.
2. **A builder that leads a task has no reviewer pane and no mailbox**, and the persona panel's
   second model family answers through the paired agent of a session. So the personas' read of
   the stories has one model family when a builder leads and two when a session does, and the
   record and the owner's page say which, in his terms ("read by N personas, one model
   family"). The lead runs it, so that clear stories start the build with no round trip through
   Lem; the personas read while the lead writes the plan, and only the first line of code waits
   for both. Decided by the design session on 2026-11-15, as its design and open to the owner,
   on one condition: a run shows that a builder that leads can start the persona agents. If it
   cannot, the lead stops after the stories and the plan, and Lem starts the read and then the
   builders.
3. **A plan talk needs a session**, for the same reason. A large plan (more than three tasks)
   therefore gets a session as its lead, as a careful one does today (`stages/plan.md`, step 3).
4. **Lem reads no diff** (`AGENTS.md`, "Lem's stages and a lead's stages stay apart"). The read
   before the pull request is a fresh agent that Lem starts and that changes nothing, as the
   review stage starts one today; a must-fix goes to a builder.
5. **"Every new test fails on the base commit" needs each story's tests as commands a script can
   run.** So the stories at the top of the plan have a fixed form, with each test as a command
   and its files, and `stories.py` is their one reader: for the check, the board and the text of
   the pull request.
6. **"The change did not lower the bar" is about one language's marks** (a lint or type
   suppression, a skipped test). The skill knows no project, so the patterns are a setting with
   the common ones as its default.
7. **`branch.land` keeps its two values and changes its meaning**: who merges the pull request.
   `agent` is no longer a push to the base branch.
8. **The task states** (`project.py`, `STATES`) follow landings: `ready`, `landing`, `landed`.
   The touches need a state for stories that wait for the owner, for the read, and for an open
   pull request. Task 8 names them; until then the old names stand.

## Not decided here

- The pull request path is tested in one private repository under the owner's account, on his
  yes; a local bare repository stands in for everything but the pull request itself.
