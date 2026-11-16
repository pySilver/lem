# Amendment to the three-touches plan (owner's notes of 2026-11-16)

Written by the Lem design session, 2026-11-16 about 00:40 CET, for the session that builds
`docs/plans/2026-11-15-three-touches.md`. The owner read the explainer page of the flow and sent
eleven notes. They are his rulings; his words are quoted. Where a note left something open, the
design under it is the design session's and is marked "design". Fold this into the plan file and
into AGENTS.md.

Task 1 (stories as the contract, red-on-base) and task 7 (the queue goes) are not touched. Tasks
2, 3, 4, 5 and 8 change, and two steps are new: the polish pass and the review routing.

## 1. Who the user is

"Assume that persone that works with Lem will be a skillful developer with many years of
experience. Not a business person. Its just a developer that does a lot of things in many
projects, so his attention is limited. But he may tell to use this and that technology or reivew
options during interview."

- No text of Lem calls the user a product owner or writes for a business reader. The README, the
  pages and the pull request text address a senior developer.
- The stories stay in plain language: they are the contract, and he said plain rules are easier
  to check. They are not a sign that the reader is not technical.
- The interview may be technical. What he names there (a technology, a library, an approach, an
  option he picked between two) is recorded as **directions** beside the stories, and the plan
  must follow them. A plan that departs from a direction is a decision of section 6.

## 2. Where his attention goes

"Current doc advertise like there will be possibilities when Lem will offload the execution
without too much asking. Yes, its possible in some rare situations where whole context is already
in some ticket along with defined outcome. But most of the time there will be interview and there
will be user stories to check by Lem user. PR review - not necessarily, I think most of the time
if everything is green he will be merging it blindly. There is little reason to have one more
look when extensive revmux did best check possible."

This replaces the earlier line "nobody confused: the build starts and does not wait" as the usual
case. Design, from his words:

- **The usual request:** an interview, then the stories, in one sitting while he is there. The
  personas read the stories first; he gets the stories and the directions with the personas'
  result on top, and he approves or changes them. Then the run goes on without him.
- **The rare request:** the whole context and a defined outcome are already written (a ticket, a
  backlog item with its options settled, a night plan he starts). No interview. The personas
  read the stories; nobody confused: the build starts and he can stop it; a doubt: it waits for
  him. Lem says which path it took and why, in one line, and he can say "interview me".
- A correction (one story, his own sentence, not careful) still shows the story and goes on.
- **The pull request is a report he may not read.** Its first line says green or not green. Green
  means: the gate and the other machine checks passed, the review ran with at least one source
  and left no must-fix, no decision was taken by timeout, no story changed. Anything that is not
  green comes before everything else, each as one line with its reason. A green pull request
  needs no read from him.
- A person still merges by default; the agent may merge a green, not careful request where the
  project allows it, as planned.

## 3. Personas

"Personas reviews are useful in many cases: read stories before human reads them, any confusion
raised by persnas check will drag attention and may turn into design change. Lem user can't be
everything and think as different users of the app, so Personas checks helps pick better
decisions."

No change to the plan. A persona's confusion may change the design, not only a story's wording:
the lead answers a doubt by changing the stories or the plan before he asks the owner to approve.

## 4. The polish pass (new step)

"Polishing step, sadly is unavoidable (most likely). I've tried many rules etc but polishing step
shows that there are some drifted comments, ugly code, leftovers and so on always to be found. An
Agent explained to me that this step is looking for very specific things, ulike other steps and
review profiles and this is why it actually does good cleanup."

Design:

- A fresh builder, after the last task of the plan and before the machine checks and the review,
  so the review reads the code as it will merge.
- Its brief is a short fixed list of specific things, and nothing general: a comment or docstring
  the change made false; leftovers (debug output, dead code, an unused name, a commented-out
  block, a marker of the task's own work); code that works and reads badly inside the change; a
  document the change made false (section 10). It changes no behavior: the stories' tests pass
  before and after, and the pass says so.
- The old closing pass becomes this step. Its rule for a defect outside the task stays (section 5).
- A fix after a must-fix gets the same list in its builder's brief; no second polish pass.
- The mybaze polish (`.claude/commands/polish.md` in `/Users/Silver/Projects/GitHub/mybaze`) is
  the model for what such a pass looks for; read it for the list, do not copy its rounds.

## 5. Out of scope goes to the backlog

"During interview and execution there will be some defects that are out-of-scope. This is where
backlog helps."

- In the interview and in the build: a defect outside the request is filed as a backlog item in
  the project's backlog path, in `lem-backlog`'s format. Cheap and safe ones are fixed in the
  polish pass, as ruled before. The pull request lists what was filed.
- Filing never needs him.

## 6. A decision during the build (replaces task 3's rule)

"During execution there will be situations where someone needs to decide something. Tech lead
should first gather personas opionions and if its clear choice - pick it, log the even so it will
be presented at PR review time. If choice is unclear - one can try to reach a Human and if there
is decision taken in 15 min, then Tech Lead picks a recommended action and logs the event so it
gains visibility at final review session."

Read with his context, the last sentence means: if **no** decision comes within 15 minutes.

- The stories and the directions stay true: the lead decides and logs it. Unchanged.
- Otherwise the personas the choice concerns give their opinions first.
  - A clear choice: the lead takes it, logs it, and the pull request shows it.
  - An unclear one (the personas split, or doubt): Lem asks the owner through `tools.ask`, or the
    Inbox when he is away, with the personas' answers and a recommendation. His answer within the
    wait decides. No answer: the lead takes the recommended action, logs it as "taken by
    timeout", and the pull request is not green for that line.
- Design: the wait is a setting, `flow.decision_wait`, default 15 minutes. Work that does not
  depend on the choice goes on during the wait.
- Design, kept from his earlier "correct": a step a later "no" cannot reverse (the fixed list of
  four kinds) is never taken by timeout. It waits for him, and the rest goes on. Told to him as
  the one exception.

## 7. A degraded review is a review

"Revmux can have degraded run, as well as personas check. Thats fine - just log and proceed. Its
still a review and read, it's just not perfect. It can happen for various reasons: tokens limit,
model at capacity etc. So partial failure is fine."

- This overturns the sentence in `stages/review.md` that a round with a dead source is run again
  before anything is closed. A partial round and a partial panel count. The record and the pull
  request say which sources and which model families answered and which did not, and why.
- Design: a round or a panel in which nothing answered is no review. Try it once more; after
  that the request is not green ("not reviewed") and goes to him as such.

## 8 and 9. The review is routed (replaces task 4's "one read" as the default)

"'One read' at the end is really useful only for small simple changes. Some limited fixes, prose
updates etc. Serious changes usually require revmux run."

"It will be useful if routing Agent will decide what revmux profiles are worthy to be run in this
particular plan judging by the diff and knowing what profiles do what. So documentation does not
trigger security or architecture checks."

Design:

- Before the review, a routing step reads the diff, the stories and the project's review
  configuration (each profile and lens with what it is for) and chooses:
  - **one read** for a small, simple change: a limited fix, prose, a change that touches only
    documentation. The fixed "documentation skips the read" rule goes: documentation gets the
    one read, or a documentation profile where the project has one, and nothing else.
  - **a review round with the profiles that fit** for every other change. A change that does not
    touch what a profile is about does not run it.
  - **the project's full set** for a careful request. That is a floor the router cannot go
    under; it may add, never drop.
- The router writes its choice and one reason per profile it ran and per profile it left out;
  the pull request shows both. A wrong routing is a correction for the retro.
- Who routes: the agent that starts the review (Lem's fresh review agent, or the session lead).
  No code decides it and no keyword list; the profiles' own descriptions are what it reads. So
  the starter set that `/lem init` writes must give every profile and lens a one-line "for what";
  check what revmux's own config lets a profile say about itself before inventing a field.
- The plan talk stays for a careful or large plan.

## 10. The documentation step

"There is a documentation update step. It belongs to a plan, but yeah - it worth mentioning."

- A plan whose change makes a document false ends with a documentation task, written by the
  planner like any other task. The polish pass checks that no document the change made false was
  missed. The flow, the README and the board name the step.

## 11. The shipped skills are for the times he steps in

"Looks like all those cool skills of Lem are useful in interactive mode when human actually does
review things (at any point) and they are actually here to help him work with context"

- The README says it in those terms: the run needs none of them from him; `/lem ask`,
  `/lem annotate`, `/lem backlog`, `/lem interview-me`, `/lem dialectic`, `/lem root-cause` and
  the board are what he uses when he steps in, at any point, to get the context back fast.

## The flow, amended

Request → interview (usual) → stories and directions → the personas read → he approves →
plan (a plan talk when careful or large) → build, one builder per task, the documentation task
last → polish pass → machine checks → routed review (one read, or a round with the profiles
that fit, or the full set) → pull request with green or not green first → merge.

## Tasks, amended

2. The personas read the stories, **and he approves them after an interview**. Done when: after
   an interview the stories and directions reach him with the personas' result on top and the
   build waits for his yes; a request with its whole context written starts with no wait when
   nobody is confused, and says which path it took.
3. A decision does not stop the task for more than the wait. Done when: a clear choice of the
   personas is taken and shown in the pull request; an unclear one asks him, and after the wait
   the recommended action is taken and the pull request is not green for it; an irreversible
   step is never taken by timeout.
4. The review is routed. Done when: a documentation change gets one read and no security or
   architecture profile; a feature gets a round with the profiles that fit, each with its
   reason; a careful request gets the full set; a partial round counts and says what answered;
   a round with no answer is "not reviewed".
5. The pull request says green or not green first. Done when: a green one needs no read; each
   line that is not green stands before the rest with its reason.
8. As before, with the user as a senior developer, the two modes (the run, and the tools for
   stepping in), and the board's lanes following the amended flow.
9. New: the polish pass. Done when: a change that leaves a false comment, a debug line and a
   dead name comes out of the pass without them, with the stories' tests unchanged and passing,
   and an outside defect is fixed when cheap or filed.
10. New: the documentation task and its check in the polish pass.

The explainer page for the owner is rebuilt from this: `/tmp/agdoc/topic-lem-three-touches-editorial.html`.
