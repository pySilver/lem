<!-- lem: old form -->
# talk

The plan talk of a careful or large plan, before any code. This is the defender's stage: the
agent of the pair the task's lead opens under its session for the talk (`prompts/defender.md`). It
takes this stage and `stages/plan.md`, step 5, for the questions the talk leaves open, and nothing
else of the lead's; a lead never reads this file. The lead wrote the plan and waits at
`stages/plan.md`, step 4, and then reads the record this stage leaves in the plan, its `## Plan
talk` section.

The defender and the reviewer argue the plan through the mailbox to find the obstacle
the planner did not see and a better design. The owner asked for the talk in a pair: "two
agents of specific models and efforts have a chat about the plan under some rules that
disallow endless discussion ... gives a visibility if Owner want to have a look. Companion is
closed once discussion is done" (2026-11-16). A
one-shot read does not do that: "there is no interaction between plan writer and reviwer, so
they cannot look for a better design together, this proces just makes the writer satisfy the
reviewer without actually changing the approach" (the owner, 2026-11-15). Nor may the talk run
without an end: "I don't want them to argue till the end of days" (the owner, 2026-11-16). A
plan is prose, and each repair is new prose that the next turn reads: a stored price, then
its invalidation, then the bulk import that skips it, then the nightly repair, then the race
with checkout. So the questions are a closed list, each gets one repair, and a question that
comes back stops, as revmux stops a loop whose finding of the last round arrives again. The
rules:

- **Open the seat** with `second-opinion`, on the seat that `lem project --repo WORKTREE seat SLUG
  reviewer` prints, at its effort, and log its start at the talk's first open, so that the board
  draws the talk from it:

  ```bash
  lem project --repo WORKTREE log SLUG plan.talk.start reviewer=AGENT
  ```

  The first message names the plan's path, the worktree, the task, the rule files
  `lem project rules` prints for the plan's files, and the code the plan rests on, by path and
  symbol, and asks for the full list.
- **The list closes with the reviewer's first turn.** That turn is a full read of the plan: a
  numbered list of questions, the most expensive first, each with the position of the plan it
  challenges, its mechanism, and its place (a section of the plan, or a file and symbol). Keep
  the list as it came, before you change anything: the next two rules are checked against it.
  The list may be empty: a reviewer that found no question says so in that turn, and you
  close at once. That talk has two turns and no question, and its record says so.
- **The turns go into `talk-turns.md`** in the task directory as they come, so that a talk that
  loses an agent goes on from that file: first the reviewer's list word for word, as it came,
  then one line for each later turn and question, with who wrote the turn, the question's number
  and how it stands (`closed`, `holds` with its why, the repair's commit, or the refutation's
  cite). A repair's line goes in before its commit, as `N: repairing`, and gets the commit after
  it; the commit's message names the question by its number (`question 3`). The lead's wait
  watches that file: a talk whose file has not changed for 45 minutes wakes the lead, which reads
  both screens for an error (`stages/plan.md`, step 4).
- **A talk that goes on.** When `talk-turns.md` is there as you start, an agent of the talk before
  you stopped: go on from it, never from a new list. Open the reviewer on the seat `lem project
  seat` prints, and make its first message name the plan and the rest as above, then the list and
  the turns so far, word for word from the file, and the questions still open. That reviewer's
  first turn answers the open questions by their numbers; the list stays closed, and a question
  it raises is "raised, not argued". A line `N: repairing` with no commit: read the branch's log
  for a commit whose message names question N. One there is the repair: write its commit on the
  line. None means the repair was never committed, and it is still that question's one repair.
  A file that holds no list yet is no talk to go on from: the new reviewer's first turn is the
  list.
- **A seat that fails.** A reviewer whose agent gives one of the four errors of `second-opinion`,
  at its open or later in the talk, is replaced the same way, in the same pane: `second-opinion`
  says what `lem project seat-failed` prints and what you open then, and the new reviewer goes on
  from `talk-turns.md` as above. A block ends the talk: after `seat-failed` wrote `blocked`, close
  the reviewer's pane and stop, with no record and no event. The owner's "go on" opens the pair
  again, and its defender goes on from the file.
- **One repair per question.** For each question, repair the plan and commit, or refute the
  question with a cite. Check each of its claims in the code before you answer. The reviewer
  answers each question by its number only:
  `closed`, when the repair or the refutation holds, or `holds`, with why. A question that
  holds gets one more answer from you: a refutation of that why with a cite, or the repair
  when your first answer was a refutation; never a second repair. A refutation of the repair's
  own new text is the same question, not a new one.
- **A question that holds a second time stops.** It closes as a design choice: the plan's
  design against the smallest option it was priced against. Do not edit the plan to settle it in
  the talk: it goes to `stages/plan.md`, step 5, as a decision in doubt with both positions as
  its facts, and the ladder decides it after the talk; only the breaker (`stages/breaker.md`)
  takes it to the owner.
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
- **A repair that adds a mechanism says what it sits on.** The owner, 2026-11-16: "Sometimes
  the fix in the plan, even during discussion is just another layer of patching. It stays ugly
  but in a different way. And due to cap and rules it goes that way." So a repair that adds a
  guard, a job, an invalidation, a cache, a flag, a sync or a retry names a fifth thing beside
  the four: which decision of the plan made the case possible (by its line in the plan's
  decisions), what that decision rests on (an acceptance criterion, a ruling, existing code, or only
  the planner's choice), and how far it reaches. The reviewer answers such a repair with
  `closed, at the cause` or `closed, layer over D`, or `holds, layer over D`, D being that
  decision. This is a Fable second opinion's form (2026-11-16):
  - a layer over a decision with a cite (a criterion, a ruling, existing code) stays, and the
    record names it;
  - a layer over a decision with no cite is not the repair: the one repair changes that
    decision instead. When you keep such a decision, the question closes at once as a design
    choice; so does a second question that names a decision another question named;
  - a repair that changed a decision (one the record counts as `root`) can be no better than the
    layer it replaced: the changed decision may bring issues of its own. Each issue the reviewer
    finds in the changed decision is a hold of the same question, never a new question, since it
    is a flaw in the repair's own new text. Your one answer to it is a refutation with a cite,
    never a second repair; when the question held before the repair, or the refutation does not
    close it, it has held a second time and closes as a design choice. The owner asked about this
    case on 2026-11-16: "whether it will catch an issue where fix should be applied at root
    level (whatever it calls) and that change would trigger number of other issues (sign that
    such change is probably not the best solution)";
  - the ladder's options of such a design choice compare both sides honestly (`stages/plan.md`, step 5): the kept
    decision with each mechanism that guards it, against the reversed decision with the tasks
    and the criteria it changes and each issue the reviewer raised against it;
  - no root-cause run: Fable advised against one here, because it examines a failure that
    happened, and it has no bound.
  Open: whether a fresh agent should read the repaired plan once more at the end. What would
  say yes: the review before the pull request finds a defect in a mechanism the record names
  while the talk's `layer` was 0. Until a review shows that, no such read runs.
- **What a person of the project would see** is not the two agents' to settle. A question
  about it stays open, and `stages/plan.md`, step 5, takes it up the ladder after the talk, with
  both positions. It never goes to the owner from here.
- **The close.** When each question of the list has ended, settled, a design choice or open,
  write `nothing further`; the reviewer adds no turn after that.
Commit every repair before any code. Then write the record into the plan, as a section
`## Plan talk` after `## Tasks`, and commit it:

- who argued the plan: each reviewer that sat, in the order they sat, with its agent, its model
  and effort as its pane's status line showed them, and for a stand-in the seat it stood in for
  and why; and you, with the model and effort the `defender:` line of the task's state gives,
  which the lead read from your pane's status line;
- the list, numbered as the reviewer gave it, each question with how it ended: settled, with
  its cite and after it the words "settled by the two, not checked by the review"; a design
  choice, with the two positions, each with its cite, and the decision `stages/plan.md`, step 5, logs; or open, with
  the two positions and where it went (`stages/plan.md`, step 5, takes it);
- each mechanism a repair added, with the decision it sits on and the reviewer's word: at the
  cause, or a layer over that decision and its cite;
- each question raised after the first turn, marked "raised, not argued", with its mechanism
  and place;
- each addition that was refused as unpriced;
- what changed in the plan, by question and by task.
Agreement carries no authority: the review before the pull request reads a settled position
as a claim, not as a fact. Then close the reviewer's pane (the harness file, `second-opinion`)
and write the one event the landing reads:

```bash
lem project --repo WORKTREE log SLUG plan.talk reviewer=AGENT turns:=N questions:=N settled:=N open:=N repaired:=N design:=N unargued:=N root:=N layer:=N shared:=N
```

`turns` counts each message of either side, of every reviewer that sat and every defender, as
`talk-turns.md` holds them; `reviewer` is the agent of the reviewer that sat last; `questions`,
the questions of the reviewer's first list; `settled` and `open`, how many of them ended each way, a design choice counted as open;
`design`, the open ones that closed as a design choice; `repaired`, the questions whose answer
changed the plan; `unargued`, the questions raised after the list; `root`, the repairs that
changed a decision of the plan; `layer`, the layers over a cited decision that stayed; and
`shared`, the decisions that two questions named. The script refuses a record of fewer than two
turns: a floor against an empty record, not a measure of a good talk. A talk of no question is
the reviewer's empty list and your close, `turns:=2 questions:=0` with every other count 0, and
the script refuses a question raised after an empty list in a talk of two turns, since no turn
was left to raise it in. It refuses counts that do not agree: settled and open that do not add
up to questions, more design choices than open questions, more repairs than questions, and more
repairs at the cause and layers together than repairs.
The rules keep a talk within 4 × questions + 2 turns: the list, two answers of each side on each
question, and the close. That bound is derived from these rules in a Fable second opinion
(2026-11-16), not measured, and it is yours to keep. A talk that went over it, or in which a
second question on a decision did not close as a design choice, is still a fact: write it down
as it ran. The script takes the record and adds the bound to it as `bound`, and the pull
request's line of the talk and the board say that the talk went over. A record the script
refused would leave the pair open and the request unproposed for ever. The landing refuses a request whose plan says `careful: yes` or has more than three
tasks with no such event, and the pull request's checks show the newest one. A task that becomes
careful after its plan, by the owner's word, by the review's call or by an edit of
`.lem/settings.toml`, gets no talk afterwards: the landing's full review reads the code that
exists. A one-shot read of a careful
plan, before this talk replaced it, took nine minutes and found three design failures before any
code (convertiser-server, 2026-11-14). In another repository a plan round before any code found
at least one major finding in 7 of 9 plans whose records tell majors from minors, and the largest
found 19 (mybaze, 2026-09-25 to 2026-11-03, counted by one reader from that project's notes).
Both were reads, not talks; no talk is measured yet. A plan that is neither careful nor large has
no talk, and that is what the skip can cost.
