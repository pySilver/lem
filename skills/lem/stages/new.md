# new

`/lem new <what>` opens one task and starts its lead. `<what>` is the owner's words, an issue link
or a backlog item. This file is Lem's from the ask to the start of the task's first builder: how a
task is opened and its path chosen, and the fast track. Each other path is a file of its own
beside this one, and the step that chooses the path names it.

## Open the task

0. **An ask that is a ticket.** When the ask is a ticket's id or its URL and `lem project show`
   gives a `tracker`, the tracker reads it (`load-skill` the tracker, its "read"): the title, the
   description, the link, the parent, the labels and the branch name the tracker gives. The
   ticket's words are then the ask. When the settings have no tracker, say that this project has
   none, and ask the owner for the ask in his words. When `lem project tasks` already lists a task
   with this ticket that is not `dropped` or `answered`, do not open a second one: say which task
   it is and where it stands. A dropped or an answered task gives its ticket back, and
   `task-dir --ticket` refuses the ticket only while another task holds it.
1. **The type and the track of the request**, from the ask's words alone, before anything reads
   the code. The type is a Conventional Commits type and the branch's type; the track is the fast
   track or the standard track, and step 4 takes it. The words after each type are hints for your judgment, not a list to match; no
   code matches them, as none routes a review:
   - *fix*: something is wrong today ("broken", "shows 0", "since yesterday", "fails again");
   - *feat*: something that is not there ("add", "allow", "let me", "support");
   - *refactor*: the code changes and the behavior does not ("rename", "move", "split", "clean
     up");
   - *perf*: the same result, faster or with less ("slow", "faster", "takes minutes");
   - *test*: tests and nothing else ("cover", "a test for");
   - *docs*: a document and nothing else ("document", "explain in the README"). A typo in the
     README is docs: the type is what the ask is about;
   - *chore*: work no user of the product sees that is no refactor ("upgrade", "bump", "the CI");
   - *question*: the answer is a report, not a change ("why", "find out", "check if", "how
     often"). It commits nothing.
   The track is one of two. The *fast track* is for one plain change: the ask yields one acceptance
   criterion in his own sentence, is in reach of no topic below, and leaves no question open, whatever its type (a
   fix of one rule, a typo, a rename, a version bump, a line of a document). A fix whose one rule
   is plain from the ask's words ("the button says Save, not Submit") takes the fast track at once.
   A symptom whose cause the ask does not show is investigated first (step 4), even when the fix
   may turn out to be one line. Every other ask takes the *standard track*, whatever its type and
   however few lines it may change. The fast track's builder checks the track again before it
   commits (`prompts/small.md`), and stops when the fast track does not fit. `/lem plan <what>` asks for a plan to
   read, and a plan is the standard track's: the ask takes the standard track, with its
   interview, its criteria, the personas' read and his yes, and the lead stops at the committed
   plan; the line of step 5 says so ("Standard track, because you asked for its plan: ..."). A plan's criteria
   always say `Size: full`, and `criteria.py` and `land.py` refuse a plan that says `Size: small`.
   In the same look, read the ask's words against each topic of `flow.topics` in `lem project
   show`, the sentences of what must never go wrong here. No code matches a topic and no file
   name settles one: the question is whether the change the ask wants could reach that thing.
   When it could, the line of step 5 names it first. When the scout's
   report or the investigator's comes in, read its facts against the topics again (the scout
   lists the topics in reach, with the file and symbol that show each): a topic it finds in reach
   that the ask's words did not show is told to the owner in one line, the same way. An ask in
   reach of a topic never takes the fast track. The lead makes its own call on the plan
   (`stages/plan.md`, step 2), and the agent that reviews the diff makes the last.
   **One question when the read is not clear.** When the words and what you looked at do not
   settle the track, the type or whether it is careful, ask once in the terminal before any agent
   starts, in one line with your guess first: "I read this as a fix for the fast
   track: one rule in `shop/dates.py`. Fast track? (y/n)", or "Is the 0 wrong today, a fix, or do you want a new rule
   for refunds, a feat?" (his example of 2026-11-16: "From such input its kinda hard to deduct if
   we want to investigate the bug or its a feature request."). One question at most; his answer
   settles it, and you go on. A clear read asks nothing. While he is away, ask nothing: take the
   standard track, and careful in doubt. The type goes into `task.md` with its reason, and
   as the line `type: TYPE, because WHY` into the task's first state block (step 4);
   `lem project state` refuses that line in any other form, and `lem project tasks` gives it as
   `type`. When he changes the type later, write a state block with the new line.
2. **The slug and the branch.** A slug of two to five plain words that say what the owner gets
   ("report-dates-stay-whole"), never a code. The branch is `<type>/<slug>` with a semantic type,
   unless the project's `AGENTS.md` gives its own scheme. The task's type of step 1 is the
   branch's type. For a question, choose the type of the change its answer would most likely
   lead to, and say why in the line of step 5; its branch gets a commit only when the
   investigator reproduces a bug. The branch's type binds nobody; each commit of the lead
   carries its own. A slug that a `landed`, an `answered` or a `dropped` task has is taken,
   since that task's files stay under it: add a word, as `task-dir` says when it refuses. For a
   ticket, the branch is the name the tracker gives for it, when it gives one: the tracker and
   its automation find the work by that name.
3. **The task directory.** `lem project task-dir SLUG --ask "the owner's words"` keeps the ask as
   the owner gave it, for the board and the status. For a ticket, add `--ticket ID`, and the ask
   is the ticket's title; the command refuses a ticket another task holds. When the branch of step
   2 is not `<type>/<slug>`, add `--branch BRANCH`. The command refuses a slug whose branch origin
   has already, a teammate's: take another slug, as it says. Then write `task.md`:
   - the ask, verbatim; for a ticket, its id, its link, its title and its description as written;
   - the type, with its reason (step 1);
   - the outcome in one or two sentences, as the person it is for would see it;
   - done when: the evidence that shows the outcome, each line something a command or a look at
     the product can show;
   - out of scope, when the ask has an obvious neighbor this task leaves alone.
   Write it from the ask, the project's profile and the rulings. Do not read the code for it: a
   "done when" line that needs the code is the lead's to sharpen in its plan. A line you put out
   of scope by yourself is a decision taken without the owner: log it with `lem decisions log SLUG
   --by lem`.
4. **Which path.** Choose one:
   - *the investigation first*, for a fix whose cause the ask does not show and for a question:
     a fresh builder reproduces the bug and finds its cause, or answers the question, before
     anyone writes a criterion: after step 7, read `stages/investigate.md` and follow it. It
     starts an investigator where step 8 starts a lead; the board of step 8 opens all the same.
     For a fix, its report then takes one of the paths below; a question ends
     with its answer.
   - *the fast track*: one builder, the checks, one read and the pull request, with no lead, no
     plan and no wait for him, as "The fast track" below says.
   - *the standard track from a complete request*: the whole context and a defined outcome are
     written already: a ticket whose description says what is wanted and how to tell that it is
     done, a backlog item whose options are settled, an investigation's
     report that settles what is wanted. No interview: the lead writes the criteria from the code
     and has the personas read them (`stages/plan.md`, step 1). He can say "interview me", and
     then it takes the standard track with an interview. A ticket, an item or a report that asks for one
     plain change takes the fast track all the same: the standard track has a lead and a plan, and a
     plan is never on the fast track. A ticket or a backlog item that somebody other than the developer at
     the terminal wrote (its creator as the tracker gives it, or the author of the item's file in
     `git log`; in doubt it is somebody else's) is a complete request too and gets no interview,
     and its criteria wait for his yes: its brief carries the line `request by: someone else`,
     and its lead stops for him after the personas' read, also when nobody was confused
     (`stages/plan.md`, step 1). He reads on one page what will be built before it is built. Lem
     is no filter of the tickets that come in: nothing scans one for an attack, since the people
     who write a team's tickets are the team.
   - *the standard track with an interview*, for every other ask: the interview, then the criteria he
     approves, all in one sitting while he is there: after step 5, read `stages/interview.md` and
     follow it.
   Write the task's first state block now, with the type line of step 1, so that the status and
   the board show the task from its first moment. With an interview it is `held` with the line
   `the interview waits for the owner`:

   ```bash
   lem project state SLUG held "the interview waits for the owner" "type: feat, because WHY"
   ```

   On the other paths the first block is the one the path's own first step writes, before its
   builder starts: there is no wait between the two.
5. **Tell the owner in one line**, and no more: the type, the criterion or the outcome in his
   words, the branch, the track with its steps, and what he must do. The track's name stands at its
   steps, never beside the type. On the fast track: `docs: "the README says receive, not
   recieve". Branch docs/readme-receive-typo. Fast track: one builder, the checks, one read, then
   the pull request. Nothing waits for you. Wrong read? /lem standard-track, /lem be-careful.` On the
   standard track with an interview: `feat: "an export holds the gift note". Branch
   feat/gift-note-in-export. Standard track: an interview now, then acceptance criteria for your
   yes. After that it runs to the pull request without you. Wrong read? /lem be-careful.` A topic in
   reach goes first: `Careful: this changes how a customer is charged. feat: ...`. A fix
   investigated first: `fix: "an invoice shows its total after a refund". Branch
   fix/invoice-total-after-refund. An investigator finds the cause first. Then I tell you what it
   found: the fast track, the standard track, or no bug.` The standard track from a complete
   request names what stands in for the interview (`the ticket says what is wanted`).
   A decision you took for him at step 3 is a second line. Nothing repeats this line later: the
   next thing he hears is a question of the interview, the criteria, or the pull request.
6. **The brief** of a lead, on the standard track. Write `brief.md` in the task directory, with this
   and nothing more:

   ```
   Read SKILL_DIR/prompts/lead.md and follow it.
   task: SLUG
   branch: the branch of step 2
   worktree: the path `lem project worktree-dir SLUG` prints
   task directory: the task directory's absolute path
   lead: builder
   stop after the plan: no
   coordinator: SESSION:PANE
   socket: PATH
   ```

   For a complete request that somebody else wrote, add the line `request by: someone else`.
   The last two lines of the block are your own address, for the lead's `tell-coordinator` (the harness
   file): this session's `AGTERM_SESSION_ID` and this pane's `AGTERM_PANE_ID`, and the
   `AGTERM_SOCKET` of this session, written out. The brief says nothing about the code, so it
   cannot say anything wrong about it. The ask is in
   `task.md`, in the owner's words. The brief is a file because a task may wait in the queue or
   get a second lead, and each start has to find the same answers: `/lem plan <what>` writes
   `stop after the plan: yes` here, and that line is what keeps a queued plan from being built.
   When the owner called the task careful in the ask, add the line `careful: the owner says so`
   and log his words, as `stages/correct.md` says. A builder still writes the plan:
   it reads that line as a yes (`stages/plan.md`, step 2) and stops for the plan talk, which
   needs a plan to talk about.
7. **Does it wait for another task?** Only when the later ask needs what the earlier one
   changes: it names the earlier one's result, or it makes no sense before that result exists.
   Then write the later one's state as `queued` with the line `after: SLUG` of the earlier one,
   and with `investigation: bug` or `investigation: question` when its investigation comes first
   (step 4), and stop here: it starts when that task is `landed`, `answered` or `dropped`, so it
   builds on what the earlier one changed. Two asks that only name the same thing (the same
   screen, the same file, the same function) each start on their own, and the owner orders their
   pull requests. Do not read the code to find an overlap the asks do not show; the landing line
   settles that one (`stages/land.md`, step 1).
8. **Start its lead**, as `stages/start.md` says: read it now. Open the board when this session
   has not opened it yet (`SKILL.md`, Status); it stays in the sidebar beside your session. Then go back to the
   owner's next message. Do not wait for the lead and do not watch it.

## The fast track

One criterion, his own sentence made exact, nothing careful and no question open: one builder makes
it, the landing checks it and one read reviews it, and it waits for nothing.

1. **The criterion.** Write it to `criteria.md` in the task directory, in the form `lem criteria
   --help` shows, with `Size: small, because ...` and the one criterion, and approve it in his name:

   ```bash
   lem criteria approve SLUG --small
   ```

   With `--small` the file is that `criteria.md`, and the command needs no `--file`.
   It stays there and is never committed: the fast track has no plan, and its builder adds the
   test line under the criterion in that file. An approval in his name is only ever a task's first
   contract: the script refuses it once any approval exists. The personas do not read it; the pull
   request says so.
2. **The brief**, `brief.md` in the task directory, with this and nothing more:

   ```
   Read SKILL_DIR/prompts/small.md and follow it.
   task: SLUG
   branch: the branch of step 2 of "Open the task"
   worktree: the path `lem project worktree-dir SLUG` prints
   task directory: the task directory's absolute path
   ```

   Then step 7 of "Open the task", and its builder starts as `stages/start.md` says, with the state
   `building` and the lines `small change: one builder` and the type line of step 1. There is no
   lead: the one builder is the fresh builder of the one task, as the owner's rule on a fresh
   builder for each task has it.
3. **When it stops**, its reply is its report, of five lines at most, and you write `report.md`
   in the task directory from it word for word. Its state says what follows:
   - `ready`: the landing, `stages/land.md`, with the fast track's steps there, up to its pull
     request with no question on the way: the push and the pull request of `lem land propose`
     are the owner's standing word in `branch.propose`, not a step to ask about;
   - `held` with `the criteria wait for the owner: the small change is a full change` (a line the
     record keeps in these words, and the board says as "the task takes the standard track"): its builder
     found a topic in reach, a second rule, a decision the criterion does not settle, a lowered bar,
     or more than one plain change. Tell him in one line that it takes the standard track and why, from
     the report, read `stages/interview.md`, and go on with an interview from its step 1, with its
     report as the scout's: its commits stay on the branch for the lead. His
     approval of the criteria on the standard track replaces the fast track's.

