# new

`/lem new <what>`, or `/lem <what>` in plain words, in any session, opens one task in an agterm
session of its own. `<what>` is the owner's words, a ticket or a backlog item. The session he typed
it in only opens the task ("Open the task"), and goes on with its own work. The task's own session
reads the request and chooses its path ("The request"), and carries the fast track to its merge
("The fast track"). Each other path is a file of its own beside this one, and the step that
chooses the path names it.

## Open the task

The part of the session where the owner typed the request. The night takes the same steps, with no
talk to copy and no focus. The board's "+" and a backlog item's "Start a task" are the board
server's: it names the task by a fixed rule (an item's file's stem, else the first five plain words
of his text), runs step 3 with his words or the item's path as the ask, and step 5 with no focus.

1. **An ask that is a ticket.** When the ask is a ticket's id or its URL and `lem project show`
   gives a `tracker`, the tracker reads it (`load-skill` the tracker, its "read"): its title is
   the ask. When the settings have no tracker, say that this project has none, and ask the owner
   for the ask in his words. When `lem project tasks` already lists a task with this ticket that is
   not `dropped` or `answered`, open no second one: say which task it is and where it stands.
2. **The slug.** Two to five plain words that say what the owner gets ("report-dates-stay-whole"),
   never a code. A slug that a `landed`, an `answered` or a `dropped` task has is taken, since that
   task's files stay under it: add a word, as `task-dir` says when it refuses.
3. **The task directory**, with the ask as the owner gave it:

   ```bash
   lem project task-dir SLUG --ask "THE OWNER'S WORDS"
   ```

   For a ticket, add `--ticket ID`, and `--branch NAME` when the tracker gives a branch name for it:
   it checks that name. It refuses a ticket another task holds, and a slug whose branch origin has
   already, a teammate's: take another slug. For `/lem plan <what>`, the ask is
   the whole line as he typed it, `/lem plan` included: the task's session reads his wish for a plan
   there.
4. **Copy the talk**, when he spoke of the request in this conversation. The task's session is no
   fork of this one, so the turns that led to the ask go to it as a file:

   ```bash
   lem session talk SLUG --from "THE FIRST WORDS OF HIS TURN WHERE THE TOPIC BEGAN"
   ```

   The turn is the one where he began to speak of this ask, also when the `/lem` line came later;
   type its first words as he typed them, a `/lem` line as it is. Add one `--leave "FIRST WORDS"`
   for each turn of his in between that is another topic. It copies the turns word for word into
   `talk.md` in the task directory, also those from before a compaction, and refuses with the fix
   when no turn of his starts with those words.
5. **Open its session**: `lem session open SLUG --why new --focus`. Say its `say` in one line, and
   go back to what this session was doing. Read no code and choose no type or track: the task's
   own session does.

## The request

The task's own session, in the shape, from its first message.

1. **The type and the track of the request**, from the ask's words alone, before anything reads
   the code. The type is a Conventional Commits type and the branch's type; the track is the fast
   track or the standard track, and step 4 takes it. The words after each type are hints for your
   judgment, not a list to match; no code matches them, as none routes a review:
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
   commits (`prompts/small.md`), and stops when the fast track does not fit. An ask that starts with
   `/lem plan` asks for a plan to read, and a plan is the standard track's: the ask takes the
   standard track, with its interview, its criteria, the personas' read and his yes, and the lead
   stops at the committed plan; the line of step 5 says so ("Standard track, because you asked for
   its plan: ..."). A plan's criteria always say `Size: full`, and `criteria.py` and `land.py`
   refuse a plan that says `Size: small`.
   In the same look, read the ask's words against each topic of `flow.topics` in `lem project
   show`, the sentences of what must never go wrong here. No code matches a topic and no file
   name settles one: the question is whether the change the ask wants could reach that thing.
   When it could, the line of step 5 names it first. When the investigator's report or the scout's
   comes in, read its facts against the topics again: a topic it finds in reach that the ask's words
   did not show is told to the owner in one line, the same way (the scout lists the topics in reach,
   with the file and symbol that show each). An ask in reach of a topic never takes the fast track.
   The lead makes its own call on the plan (`stages/plan.md`, step 2), and the agent that reviews
   the diff makes the last.
   **One question when the read is not clear.** When the words and what you looked at do not
   settle the track, the type or whether it is careful, ask once, in one line with your guess
   first: "I read this as a fix for the fast track: one rule in `shop/dates.py`. Fast track?
   (y/n)", or "Is the 0 wrong today, a fix, or do you want a new rule for refunds, a feat?" (his
   example of 2026-11-16: "From such input its kinda hard to deduct if we want to investigate the
   bug or its a feature request."). One question at most; his answer settles it, and you go on. A
   clear read asks nothing. While he is away, and for a task of the night (`night` in `lem project
   tasks`), ask nothing: take the standard track, and careful in doubt. The type goes into
   `task.md` with its reason, and as the line `type: TYPE, because WHY` into the task's first state
   block (step 4); `lem project state` refuses that line in any other form, and `lem project
   tasks` gives it as `type`. When he changes the type later, write a state block with the new
   line.
2. **The branch** is `<type>/<slug>` with the type of step 1, unless the project's `AGENTS.md`
   gives its own scheme. For a question, choose the type of the change its answer would most likely
   lead to, and say why in the line of step 5; its branch gets a commit only when the investigator
   reproduces a bug. The branch's type binds nobody; each commit carries its own. For a ticket,
   the branch is the name the tracker gives for it, when it gives one: the tracker and its
   automation find the work by that name.
3. **`task.md`** in the task directory:
   - the ask, verbatim; for a ticket, its id, its link, its title and its description as written;
   - the type, with its reason (step 1);
   - the outcome in one or two sentences, as the person it is for would see it, under `## Outcome`.
     For the standard track from a complete request (step 4), where no interview writes it again,
     it is the story of `prompts/writing.md` instead (read it then);
   - done when: the evidence that shows the outcome, each line something a command or a look at
     the product can show;
   - out of scope, when the ask has an obvious neighbor this task leaves alone.
   Write it from the ask, `talk.md` when it is there, the project's profile and the rulings. Do
   not read the code for it: a "done when" line that needs the code is the lead's to sharpen in its
   plan. A line you put out of scope by yourself is a decision taken without the owner: log it with
   `lem decisions log SLUG --by lem`.
4. **Which path.** Choose one:
   - *the investigation first*, for a fix whose cause the ask does not show and for a question:
     a fresh builder reproduces the bug and finds its cause, or answers the question, before
     anyone writes a criterion: after step 7, read `stages/investigate.md` and follow it. For a
     fix, its report then takes one of the paths below; a question ends with its answer.
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
     `git log`; in doubt it is somebody else's), and every item of the night, is a complete request
     too and gets no interview, and its criteria wait for his yes: its brief carries the line
     `request by: someone else`, and its lead stops for him after the personas' read, also when
     nobody was confused (`stages/plan.md`, step 1). He reads on one page what will be built before
     it is built. Lem is no filter of the tickets that come in: nothing scans one for an attack,
     since the people who write a team's tickets are the team.
   - *the standard track with an interview*, for every other ask: the interview, then the criteria
     he approves, here in this session: after step 6, read `stages/interview.md` and follow it.
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
   feat/gift-note-in-export. Standard track: an interview here now, then acceptance criteria for
   your yes. After that it runs to the pull request without you. Wrong read? /lem be-careful.` A
   topic in reach goes first: `Careful: this changes how a customer is charged. feat: ...`. A fix
   investigated first: `fix: "an invoice shows its total after a refund". Branch
   fix/invoice-total-after-refund. An investigator finds the cause first. Then I tell you what it
   found: the fast track, the standard track, or no bug.` The standard track from a complete
   request names what stands in for the interview (`the ticket says what is wanted`).
   A decision you took for him at step 3 is a second line. Nothing repeats this line later: the
   next thing he hears is a question of the interview, the criteria, or the pull request. A task
   of the night tells nobody: the night's report names it.
6. **The brief** of a lead, on the standard track, also one with an interview: write it now, with
   every line the ask already gives, so that a `/lem be-careful` during the interview writes its
   line into it (`stages/correct.md`) and the lead finds the same answers. Write `brief.md` in the
   task directory, with this and nothing more:

   ```
   Read SKILL_DIR/prompts/lead.md and follow it.
   task: SLUG
   branch: the branch of step 2
   worktree: the path `lem project worktree-dir SLUG` prints
   task directory: the task directory's absolute path
   stop after the plan: no
   ```

   For a complete request that somebody else wrote, and for a task of the night, add the line
   `request by: someone else`. The brief says nothing about the code, so it cannot say anything
   wrong about it. The ask is in `task.md`, in the owner's words. The brief is a file because a
   task may wait in the queue or get a second lead, and each start has to find the same answers:
   an ask of `/lem plan` writes `stop after the plan: yes` here, and that line is what keeps a
   plan from being built. When the owner called the task careful in the ask, add the line
   `careful: the owner says so` and log his words, as `stages/correct.md` says. The lead still
   writes the plan: it reads that line as a yes (`stages/plan.md`, step 2), and the plan talk
   needs a plan to talk about.
7. **Does it wait for another task?** Only when the later ask needs what the earlier one
   changes: it names the earlier one's result, or it makes no sense before that result exists.
   Ask it here before the fast track's builder, an investigator or the lead of a complete request.
   On the standard track with an interview, the interview and his yes come first, while he is
   there, and `stages/start.md` asks it after them (step 1). The scout and the criteria then read
   a base without the earlier task's result: a criterion that the result makes false is a change
   of the criteria, and the pull request is not green for it.
   Then write the later one's state as `queued` with the line `after: SLUG` of the earlier one,
   and with `investigation: bug` or `investigation: question` when its investigation comes first
   (step 4); write `handoff.md` (`prompts/session.md`, "A change of phase"), and close this
   session, `lem session close SLUG --why handoff --when-unselected` with `run-in-background`. The
   board's server opens the task's session when that task is `landed` or `answered`, so it builds
   on what the earlier one changed. When that task is dropped, it stays `queued`, and "Waits for
   you" asks the owner to start it or to drop it. Two asks that only name the same thing (the same
   screen, the same file, the same function) each start on their own. Do not read the code to find
   an overlap the asks do not show; the landing settles that one, as a conflict at its rebase
   (`stages/land.md`, step 2).
8. **The path's first step**: `stages/investigate.md`, "The fast track" below, or
   `stages/interview.md`. On the standard track from a complete request this session is the lead:
   take `stages/start.md`, and then follow `brief.md`; nothing is handed over, since nothing was
   said yet that the lead would lose.

## The fast track

One criterion, his own sentence made exact, nothing careful and no question open: one builder makes
it, the landing checks it and one read reviews it, and it waits for nothing. It stays in this
session from the request to the merge, with no fresh agent at a phase: a fresh session starts at
about 84,000 tokens (a second opinion's median of 10 sessions, 2026-11-20), which a typo must not
pay three times.

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
   branch: the branch of step 2 of "The request"
   worktree: the path `lem project worktree-dir SLUG` prints
   task directory: the task directory's absolute path
   ```

   Then step 7 of "The request", and its builder starts as `stages/start.md` says, with the state
   `building` and the lines `small change: one builder` and the type line of step 1. There is no
   lead: the one builder is the fresh builder of the one task, as the owner's rule on a fresh
   builder for each task has it.
3. **When it stops**, its reply is its report, of five lines at most, and you write `report.md`
   in the task directory from it word for word. Its state says what follows:
   - `ready`: the landing, `stages/land.md`, here in this session, with the fast track's steps
     there, up to its pull request with no question on the way: the push and the pull request of
     `lem land propose` are the owner's standing word in the settings he approved, not a step to
     ask about;
   - `held` with `the criteria wait for the owner: the small change is a full change` (a line the
     record keeps in these words, and the board says as "the task takes the standard track"): its builder
     found a topic in reach, a second rule, a decision the criterion does not settle, a lowered bar,
     or more than one plain change. Tell him in one line that it takes the standard track and why, from
     the report. Write the lead's brief of step 6 of "The request" over the fast track's, then
     take `stages/interview.md` here: it reads the builder's `report.md` as the scout's report,
     and its commits stay on the branch for the lead. His approval of the criteria on the
     standard track replaces the fast track's.
