# new

`/lem new <what>`, or `/lem <what>` in plain words, in any session, opens one task in an agterm
session of its own. `<what>` is the owner's words, a ticket or a backlog item. The session he typed
it in only opens the task ("Open the task"), and goes on with its own work. The task's own session
reads the request and chooses its path ("The request"), and carries the fast track to its merge
("The fast track"). Each other path is a file of its own beside this one, and the step that
chooses the path names it.

## Open the task

The part of the session where the owner typed the request. The night takes the same steps, with no
talk to copy. The board's "+" and a backlog item's "Start a task" are the board
server's: it names the task by a fixed rule (an item's file's stem, with the first free `-2`, `-3`
after it when a task of that stem ended, else the first five plain words of his text), runs step 3
with his words or the item's path as the ask, and step 5. It refuses an item that a task that has
not ended holds, and names that task.

1. **An ask that is a ticket.** When the ask is a ticket's id or its URL and `lem project show`
   gives a `tracker`, the tracker reads it (`load-skill` the skill `tracker.kind` names, its
   "read"): what the read gives as the ask is the ask, word for word (the ticket's text, its title
   only when the text is empty, never the comments under it), and that is what `--ask` takes in
   step 3. When the settings have no tracker, say that this project has none, and ask the owner
   for the ask in his words. When `lem project tasks` already lists a task with this ticket that is
   not `dropped` or `answered`, open no second one: say which task it is and where it stands.
2. **The slug.** Two to five plain words that say what the owner gets ("report-dates-stay-whole"),
   never a code. A slug that a `landed`, an `answered` or a `dropped` task has is taken, since that
   task's files stay under it (past `state.keep_days`, its small record alone), and so is the slug
   of an open task with other words: add a word, as `task-dir` says when it refuses.
3. **The task directory**, with the ask as the owner gave it:

   ```bash
   lem project task-dir SLUG --ask "THE OWNER'S WORDS"
   ```

   For a ticket, add `--ticket ID`, and `--branch NAME` when the tracker gives a branch name for it:
   it checks that name. For a GitHub issue (`tracker.kind` is `github`), add `--ticket-repo
   OWNER/REPO` too, the repository of the issue's address that the read gave, never origin's as it
   is now: the tracker writes only to the issue that was read. It refuses a ticket another task holds, and a slug whose branch origin has
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
5. **Open its session**: `lem session open SLUG --why new`. It opens with no focus: the owner stays
   here, and the task's session never takes the focus, also when it has a question only he can
   answer (`prompts/session.md`, "While the owner is needed"). `task-dir` and `session open`
   put the repository's main checkout into the machine's list of workspaces, so the board's server
   shows it from its first task, as "Starting" until its session writes a state. Say its `say` in one line,
   start its `then` (`lem session wait SLUG --first-line`) with `run-in-background`, and go back
   to what this session was doing. When that command ends, say its `say` as it is, in one line:
   the task's first line, where the owner corrects its read. When its `say` is null, say nothing.
   Read no code and choose no type or track: the task's own session does.

## The request

The task's own session, in the shape, from its first message.

**A request a resume made.** A task directory that holds `resumed-from.txt` and no state is the
new request `lem project resume` made from a task the release stop blocked (`stages/park.md`). It
holds the notes of the task it came from: `task.md`, `criteria.md`, `handoff.md` and the others
the old task had. Read them before the first question, and take the steps below from them: ask
only what they do not answer, and put the old `criteria.md` to the owner as the proposal of the
criteria, for his yes. Its branch is the one the resume made, `git branch --list '*/SLUG'`, with
the old task's commits: step 2 takes it as it is, whatever type step 1 takes. With no such branch
(the resume found none), step 2 names one as for any request.

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
   stops at the committed plan; the line of step 8 says so ("Standard track, because you asked for
   its plan: ..."). A plan's criteria always say `Size: full`, and `criteria.py` and `land.py`
   refuse a plan that says `Size: small`.
   In the same look, read the ask's words against each topic of `flow.topics` in `lem project
   show`, the sentences of what must never go wrong here. No code matches a topic and no file
   name settles one: the question is whether the change the ask wants could reach that thing.
   When it could, the task's first state block carries the line `careful: WHAT IT COULD REACH`
   (`careful: this changes how a customer is charged`), and the line of step 8 names it first.
   When the investigator's report or the scout's comes in, read its facts against the topics
   again: a topic it finds in reach that the ask's words did not show is told to the owner in one
   line, the same way (the scout lists the topics in reach, with the file and symbol that show
   each). An ask in reach of a topic never takes the fast track.
   The lead makes its own call on the plan (`stages/plan.md`, step 2), and the agent that reviews
   the diff makes the last.
   In the same look, read whether the owner's words put the whole task after another task: "after
   X", "when X lands", "once X is merged", with capital letters and a colon or without, whether or
   not the task needs anything of X. That is his order, and step 7 queues the task by it. X is a
   task that `lem project tasks` lists, named by its slug or in his own words ("when the gift note
   task lands"). Words with "after" that order no tasks are no order: "after a refund the invoice
   shows 0" is a symptom; and an ask that only names a task ("the card of gift-note-in-export cuts
   its title") is about that task, not after it. A task that landed or was answered has met his
   order already: the order adds no wait, and step 7 still reads the need, as for an ask with no
   order. A task that was dropped never brings its result: step 7 queues the task after it all the
   same, and it stays `queued` for his word, as that step says. When his words name no task you can tell (a slug with a typo,
   words that fit no task or more than one), never start the task against the order: the order is
   a read for the one question below.
   **One question when the read is not clear.** When the words and what you looked at do not
   settle the track, the type, whether it is careful or the order, ask once, in one line with your
   guess first, after the state `held` with the line `the request waits for one answer` (`lem
   project state SLUG held "the request waits for one answer"`), so that the board shows the
   question as his: "I read this as a fix for the fast track: one rule in `shop/dates.py`. Fast track?
   (y/n)", or "Is the 0 wrong today, a fix, or do you want a new rule for refunds, a feat?" (his
   example of 2026-11-16: "From such input its kinda hard to deduct if we want to investigate the
   bug or its a feature request."). A question on the order names each answer, so that no answer
   has two readings: each open task that fits his words, and "no order": "Queue this after
   gift-note-in-export, after gift-note-on-invoice, or no order?". When one task fits, or none,
   it names your guess, another task and "no order": "Queue this after gift-note-in-export, after
   another task (name it), or no order?". When another read is unclear too, the one line holds that
   guess beside it, and the order keeps its answers: "Fast track, and queued after
   gift-note-in-export, after another task (name it), or no order?". His yes queues the task after
   the task you guessed, and a task he names queues it after that one. His "no order" is his word that no order holds: log it, `lem
   decisions log SLUG --by owner --what "the order of the ask" --chose "no order" --why "his
   answer" --words "HIS WORDS"`, and step 7 still reads the need. An answer that still names no
   task you can tell holds the task for him, as below. One question at most; his answer settles
   it, and you go on. A clear read asks nothing. While he is away, and for a task of the night
   (`night` in `lem project tasks`), ask nothing: take the standard track, and careful in doubt.
   For the order, when exactly one open task fits his words, take that one: step 7 queues the task
   after it, its queued block and the line of step 8 say which task you took, and you log the read,
   `lem decisions log SLUG --by lem`. When none fits, or more than one, write the state `held` with
   the first line `the order waits for the owner: "HIS WORDS"`, the words of his that give the
   order on one line, and the type line; it puts the task into the list of what waits for him (`lem
   project waiting`). That block names no path, so it prints no `say`: the task gets its first line
   when he answers, since a line said while he is away reaches nobody, and its row in "Waits for
   you" tells him that it waits. Start nothing: the task waits for his answer to the one question
   (`prompts/session.md`, "What comes next"). Then the first block that names its path prints the
   first line, with the type line of the hold when it has none: the `queued` block of step 7 for a
   task he names, or the first block of step 8 for "no order". The type goes into
   `task.md` with its reason, and as the line `type: TYPE, because WHY` into the task's first state
   block (step 8); `lem project state` refuses that line in any other form, and `lem project
   tasks` gives it as `type`. When he changes the type later, write a state block with the new
   line.
2. **The branch** is `<type>/<slug>` with the type of step 1, unless the project's `AGENTS.md`
   gives its own scheme, or a resume made it (above). For a question, choose the type of the change its answer would most likely
   lead to, and say why in one line after the line of step 8; its branch gets a commit only when
   the investigator reproduces a bug. The branch's type binds nobody; each commit carries its own.
   For a ticket, the branch is the name the tracker gives for it, when it gives one: the tracker
   and its automation find the work by that name.
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
   `lem decisions log SLUG --by lem --what "out of scope: THE LINE" --chose "left out of this task"
   --why "WHY"`.
4. **Which path.** Choose one:
   - *the investigation first*, for a fix whose cause the ask does not show and for a question:
     a fresh builder reproduces the bug and finds its cause, or answers the question, before
     anyone writes a criterion: at step 8, read `stages/investigate.md` and follow it. For a
     fix, its report then takes one of the paths below; a question ends with its answer.
   - *the fast track*: one builder, the checks, one read and the pull request, with no lead, no
     plan and no wait for him but his yes to the one criterion of a ticket or an item somebody else
     wrote, as "The fast track" below says: its steps 1 and 2, the criterion and the brief, come
     before step 7.
   - *the standard track from a complete request*: the whole context and a defined outcome are
     written already: a ticket whose description says what is wanted and how to tell that it is
     done, a backlog item whose options are settled, an investigation's
     report that settles what is wanted. No interview: the lead writes the criteria from the code
     and has the personas read them (`stages/plan.md`, step 1). He can say "interview me", and
     then it takes the standard track with an interview. A ticket, an item or a report that asks for one
     plain change takes the fast track all the same: the standard track has a lead and a plan, and a
     plan is never on the fast track. When somebody else wrote it, its one criterion still waits for
     his yes before the builder starts, while he is there ("The fast track", step 1). A ticket or
     a backlog item that somebody other than the developer at the terminal wrote (its creator as
     the tracker gives it, or the author of the item's file in
     `git log`; in doubt it is somebody else's), and every item of the night, is a complete request
     too and gets no interview, and its criteria wait for his yes: its brief carries the line
     `request by: someone else`, and its lead stops for him after the personas' read, also when
     nobody was confused (`stages/plan.md`, step 1). He reads on one page what will be built before
     it is built. Lem is no filter of the tickets that come in: nothing scans one for an attack,
     since the people who write a team's tickets are the team.
   - *the standard track with an interview*, for every other ask: the interview, then the criteria
     he approves, here in this session: at step 8, read `stages/interview.md` and follow it.
   Steps 5 to 7 write what the line of step 8 reads, and step 8 writes the task's first state
   block, which says that line; a task that waits by step 7 gets its first block there.
5. **The fast track's criterion and brief**: on the fast track, steps 1 and 2 of "The fast track"
   below, now, so that the line of step 8 quotes the criterion.
6. **The brief** of a lead, on the standard track, also one with an interview: write it now, with
   every line the ask already gives, so that a `/lem be-careful` during the interview writes its
   line into it (`stages/correct.md`) and the lead finds the same answers. Write `brief.md` in the
   task directory, with this and nothing more:

   ```
   Read `skills/lem/prompts/lead.md` in the folder that `lem version` prints as `root`, and follow it; when `lem version` fails, stop and say that `lem` is not on the PATH, with `lem doctor` as the check.
   task: SLUG
   branch: the branch of step 2
   worktree: the path `lem project worktree-dir SLUG` prints
   task directory: the task directory's absolute path
   stop after the plan: no
   ```

   For a complete request that somebody else wrote, and for a task of the night, add the line
   `request by: someone else`. The brief says nothing about the code, so it cannot say anything
   wrong about it. Its first line, as the first line of every brief a stage writes, names the
   standing text by its place in the plugin and never by a folder: the plugin's folder changes with
   each update, and the `lem` on the reader's PATH is the Lem loaded when it starts. The ask is in
   `task.md`, in the owner's words. The brief is a file because a task may wait in the queue or
   get a second lead, and each start has to find the same answers: an ask of `/lem plan` writes
   `stop after the plan: yes` here, and that line is what keeps a plan from being built. When the
   owner called the task careful in the ask, add the line `careful: the owner says so` and log his
   words, as `stages/correct.md` says. The lead still writes the plan: it reads that line as a yes
   (`stages/plan.md`, step 2), and the plan talk needs a plan to talk about.
7. **Does it wait for another task?** In two cases, and in no other:
   - *his order*, as step 1 read it, while the task he named has not landed or been answered;
   - *a need*: the later ask needs what the earlier one changes, while the earlier one has not
     ended (not landed, answered or dropped): it names the earlier one's result, or it makes no
     sense before that result exists.
   His order queues the task here, on every track. A need is asked here before the fast track's
   builder, an investigator or the lead of a complete request. On the standard track with an
   interview, the interview and his yes come first, while he is there, and `stages/start.md` asks
   the need after them (step 1). The scout and the criteria then read a base without the earlier
   task's result: a criterion that the result makes false is a change of the criteria, and the pull
   request is not green for it.
   Then write the later one's state as `queued`. Its first line is his order, `the owner's order:
   "HIS WORDS"`, the words of his that give the order as he typed them, on one line (a line break
   becomes a space), or for a need what the task needs from the earlier one, in one line. Then the
   line `after: SLUG` of the earlier one, the type line of step 1 and the `careful:` line of step 1
   when a topic is in reach (each when no block before it has one: the hold of step 1 has them),
   and the line of the path that step 8 takes when the wait ends: `then: the interview`, `then: the
   fast track` or `then: the lead`, or for an investigation that comes first (step 4) its line
   `investigation: bug` or `investigation: question` in its place. A task you put after the one
   open task that fits his words, while he was away (step 1), gets the line `the one open task that
   fits his words`. The first line is read from the order, the `then:` line and that line, so `lem
   project state` refuses a line that starts as one of them in another form, with the form in its
   message. It is the first block that names the task's path, also after the hold of step 1: say
   its `say` as step 8 says.

   ```bash
   lem project state SLUG queued "the owner's order: \"After gift-note-in-export\"" "after: gift-note-in-export" "type: feat, because WHY" "then: the interview"
   ```

   Write `handoff.md` (`prompts/session.md`, "A change of phase"), and close this session, `lem
   session close SLUG --why handoff --when-unselected` with `run-in-background`. When that task is
   `landed` or `answered`, the board's server opens the task's session, or wakes it when it still
   runs, and the session goes on where it stopped (`prompts/session.md`, "What comes next"), so it
   builds on what the earlier one changed. When that task is dropped, the result it waited for
   never comes: it stays `queued`, no session opens for it, and the owner says whether it starts
   without that result or is dropped too. Its row of "Waits for you" names his two words, "start
   SLUG now" and `/lem drop SLUG`, which he types in any Lem session of this repository. `lem
   project may-start SLUG` refuses it, and prints the commands of his "start SLUG now", composed
   from the task's newest block: for his order, the log of his words, then the `queued` block again
   with each of its lines but the `after:` line and with `the owner's order was removed: "HIS
   WORDS"`; for a need, that block alone. On his word (his "start it", too, where the talk is about
   this task), run `lem project may-start SLUG` once more and run the commands it prints then, as
   printed, with his words in place of `HIS WORDS` as it says; never ones printed before his word,
   since a `/lem standard-track SLUG` between the two changes the block they copy. Then the task
   goes on as `stages/start.md`, "`/lem build`", says. On his `/lem drop SLUG`, drop it
   (`stages/correct.md`, "drop"). A dropped task is no task to queue behind again: what a task
   started past it still needs is planned inside it. Only his word removes his
   order before that task lands or is answered: his "start SLUG now" (`stages/start.md`, "`/lem
   build`"). Two asks that only name the same thing (the same screen, the same file, the same
   function) each start on their own. Do not read the code to find an overlap the asks do not show;
   the landing settles that one, as a conflict at its rebase (`stages/land.md`, step 2).
8. **The first state block, and the line.** The task's first state block names its path and
   carries the type line of step 1, and the `careful:` line of step 1 when a topic is in reach.
   After the hold of an order that named no task (step 1), it is the first block after his answer
   that names the path, and the hold's type and `careful:` lines stand for its own.
   The path's first step writes it, before anyone starts:
   - with an interview, here, then `stages/interview.md`:

     ```bash
     lem project state SLUG held "the interview waits for the owner" "type: feat, because WHY"
     ```

   - an investigation: step 1 of `stages/investigate.md`, after the worktree, then its step 2;
   - the fast track: steps 1 to 3 of `stages/start.md`, the state `building` with `small change:
     one builder`, then its step 4 and step 3 of "The fast track" below. For a ticket or an item
     somebody else wrote, while he is there, the first block is the wait for his yes of "The fast
     track", step 1, and the builder's block comes after his yes;
   - the standard track from a complete request: steps 1 to 3 of `stages/start.md`, the state
     `building` with `lead: builder`. This session is the lead: then follow `brief.md`; nothing is
     handed over, since nothing was said yet that the lead would lose;
   - a task that waits: the `queued` block of step 7. When its wait ends, its session takes the
     path of its `then:` or `investigation:` line here (`prompts/session.md`, "What comes next"),
     and that block, no longer the first, prints no `say`.

   That `lem project state` call prints `say`, the task's first line to the owner, which the script
   composes from the task's files: the type, the criterion of `criteria.md` or else the outcome of
   `task.md` (else the ask) in his words, the branch of the brief or of the worktree, the track with
   its steps, what he must do, and the `careful:` line first. **Say the `say` as it is, as your
   first words to him in this session** (after the one question of step 1, when the read needed
   it), and no more. No scout, investigator or builder starts before it is said: the branch, the
   track and a careful topic are in no other line, and it is where he corrects your read. On the
   fast track it reads `docs: "the README says receive, not recieve". Branch
   docs/readme-receive-typo. Fast track: one builder, the checks, one read, then the pull request.
   Nothing waits for you. Wrong read? /lem standard-track, /lem be-careful.` A task that waits by
   his order says so on every track, in place of "Nothing waits for you" on the fast track, before
   the steps of its track, which run when the wait ends: `feat: "the export keeps the notes in
   their order". Branch feat/export-notes-in-order. It waits for gift-note-in-export, as you said;
   "start export-notes-in-order now" starts it before that. Then the standard track: an interview
   here, then acceptance criteria for your yes. After that it runs to the pull request without you.
   Wrong read? /lem be-careful.` One you put after the one open task that fits his words, while he
   was away, says which: `It waits for gift-note-in-export, the one open task that fits "when the
   gift note lands"; ...`. A task that waits by a need says `It waits for gift-note-in-export, and
   starts when that task lands or is answered.` in the same place. The first line of a task held
   for his order comes with his answer, one time. A call that prints no `say` for a task of the
   day, other than that hold, wrote no first block: look at its lines again. A decision you took for him at step 3 is a second line, in your words.
   Nothing repeats the first line later: the next thing he hears is a question of the interview,
   the criteria, or the pull request; the board shows it on the task's Overview until its next
   block. A task of the night gets no `say` and tells nobody: the night's report names it.

## The fast track

One criterion, his own sentence made exact, nothing careful and no question open: one builder makes
it, the landing checks it and one read reviews it, and it waits for nothing but a task that step 7
puts it after and, for a ticket or an item somebody else wrote, his yes to that criterion. It stays
in this session from the request to the merge, with no fresh agent at a phase: a fresh session
starts at about 84,000 tokens (a second opinion's median of 10 sessions, 2026-11-20), which a typo must not pay three times. A task that step 7 queues closes this session
there once he leaves it; when the wait ends, the board's server opens a session for it, or wakes
this one when it still runs, and that session takes it on at its builder (`prompts/session.md`, "A
queued task").

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
   A request that is not his own sentence, a task of the night (`night` in `lem project tasks`) or a
   ticket or an item somebody else wrote, gets no approval in his name: write the brief of step 2
   first, with the line `request by: someone else` for such a ticket or item. The script refuses
   `--small` for such a task, `--alone` for his own request, and `--alone` while the task runs with
   him (`mode` in `lem project tasks`):
   - *While he is there*, the criterion of a ticket or an item somebody else wrote waits for his
     yes before its builder starts: nobody at the terminal read that request. Its first block, at
     step 8 of "The request", is this wait, with the type line of step 1:

     ```bash
     lem project state SLUG held "the criteria wait for the owner: a small change that someone else asked for" "type: fix, because WHY"
     ```

     Say its `say`, which tells him that the criterion waits for his yes. Then show him the
     criterion as `criteria.md` has it, its case with it, and ask in one line: "Approve this
     criterion? (y/n)". A yes to one criterion he can read above it is a fixed choice with no
     other context, so it stays in the conversation, as a yes to a guess does in the interview
     (`stages/interview.md`, step 2). The board shows the same wait in "Waits for you", with its
     approval. While it waits, keep the watch of his mark (`stages/away.md`, "The watch"). On his
     yes, `lem criteria approve SLUG --file TASK_DIR/criteria.md`: his approval, and the pull
     request is green for it. A change of his goes into `criteria.md` in his words first, then the
     same approval. A yes he gave on the board is on record already (`by: owner` in `lem criteria
     approved SLUG`), and the board's server wakes this session for it. After his approval,
     `stages/start.md`, whose `building` block carries no type line, since the wait has it: it
     starts the one builder. His No on the board carries his words on what the criterion should
     say (`note` of `board_answer`, `prompts/session.md`, "His answer on the board"): they are a
     change of his, written into `criteria.md` in his words, and then this held block is written
     again, so that the board asks his yes to the new text in a new row. His "standard", or a change that makes it more than one plain change, takes the
     standard track as `/lem standard-track` does.
   - *A task of the night, and such a ticket or item while he is away*: `lem criteria approve SLUG
     --file TASK_DIR/criteria.md --alone`, and its builder starts with no wait. Its pull request is
     then not green, since he did not approve the criterion, and the merge agent calls him. When
     his away mark comes while the criterion waits for his yes, approve it so and start the builder
     (`stages/away.md`).
2. **The brief**, `brief.md` in the task directory, with this and nothing more:

   ```
   Read `skills/lem/prompts/small.md` in the folder that `lem version` prints as `root`, and follow it; when `lem version` fails, stop and say that `lem` is not on the PATH, with `lem doctor` as the check.
   task: SLUG
   branch: the branch of step 2 of "The request"
   worktree: the path `lem project worktree-dir SLUG` prints
   task directory: the task directory's absolute path
   ```

   For a ticket or an item somebody else wrote, add `request by: someone else`, as step 6 of "The
   request" says. Steps 1 and 2 come at step 5 of "The request". Then its steps 7 and 8: its
   builder starts as `stages/start.md` says, after the state `building` with the lines `small
   change: one builder` and the type line of step 1, whose `say` is the first line. There is no
   lead: the one builder is the fresh builder of the one task, as the owner's rule on a fresh
   builder for each task has it.
3. **When it stops**, its reply is its report, of six lines at most, and you write `report.md`
   in the task directory from it word for word, but for its line of pictures: each picture it
   names goes in as a paragraph of its own, its link and its caption under it
   (`![WHAT IT SHOWS](media/NAME-before.png)`, then `*WHAT DIFFERS*` on the next line), so that
   the board draws a `-before`/`-after` pair side by side and the merge agent finds it. A `No
   picture:` line stays as the builder wrote it. Its state says what follows:
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
     standard track replaces the fast track's. So does an approval with `--alone` while the task
     still runs without him (a night's task, or his away mark), also over a fast-track approval
     that was `--alone` itself: both stay in the record, and the pull request is not green for it.
