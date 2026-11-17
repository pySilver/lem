# new

`/lem new <what>` opens one task and starts its lead. `<what>` is the owner's words, an issue link
or a backlog item. This file is Lem's from the ask to the landing line: how a task is opened, how
a lead is started, and what to do each time a lead stops.

## Open the task

0. **An ask that is a ticket.** When the ask is a ticket's id or its URL and `project.py show`
   gives a `tracker`, the tracker reads it (`load-skill` the tracker, its "read"): the title, the
   description, the link, the parent, the labels and the branch name the tracker gives. The
   ticket's words are then the ask. When the settings have no tracker, say that this project has
   none, and ask the owner for the ask in his words. When `project.py tasks` already lists a task
   with this ticket that is not `dropped` or `answered`, do not open a second one: say which task
   it is and where it stands. A dropped or an answered task gives its ticket back, and
   `task-dir --ticket` refuses the ticket only while another task holds it.
1. **The kind and the size of the request**, from the ask's words alone, before anything reads
   the code. The kind names what the ask is and gives the branch its type; the size picks the
   path (step 4). The words after each kind are hints for your judgment, not a list to match; no
   code matches them, as none routes a review:
   - *bug*: something is wrong today ("broken", "shows 0", "since yesterday", "fails again");
   - *feature*: something that is not there ("add", "allow", "let me", "support");
   - *correction*: one rule in his own sentence, with a cause that is plain from the ask ("the
     button says Save, not Submit"). A symptom whose cause the ask does not show is a bug, even
     when the fix may turn out to be one line;
   - *investigation*: the answer is a report, not a change ("why", "find out", "check if", "how
     often");
   - *chore*: work no user of the product sees ("upgrade", "rename", "move", "clean up");
   - *docs*: a document and nothing else ("document", "explain in the README"). A typo in the
     README is docs: the kind is what the ask is about.
   The size is one of two. A *small change* is one plain change: the ask yields one story in his
   own sentence, is in reach of no topic below, and leaves no question open, whatever its kind (a
   fix of one rule, a typo, a rename, a version bump, a line of a document). Every other ask is a
   *feature* in size, whatever its kind. When you cannot tell, take the small change and ask
   nothing: its builder checks it again before it commits (`prompts/small.md`), and stops when it
   is not. "Correction" stays the word of the scripts for a small change (`Kind: correction`,
   `stories.py approve --correction`); to the owner it is a small change.
   In the same look, read the ask's words against each topic of `flow.topics` in `project.py
   show`, the sentences of what must never go wrong here. No code matches a topic and no file
   name settles one: the question is whether the change the ask wants could reach that thing.
   When it could, the line of step 5 names it first. In doubt, say careful. When the scout's
   report or the investigator's comes in, read its facts against the topics again (the scout
   lists the topics in reach, with the file and symbol that show each): a topic it finds in reach
   that the ask's words did not show is told to the owner in one line, the same way. An ask in
   reach of a topic is never a small change. The lead makes its own call on the plan
   (`stages/plan.md`, step 2), and the agent that reviews the diff makes the last.
   When the words do not settle the kind between a bug and a feature, ask before step 2, as the
   first question of the interview, with your guess and what each answer would mean: "Is the 0
   wrong today, a bug, or do you want a new rule for refunds, a feature?" (2026-11-16, his
   example: "From such input its kinda hard to deduct if we want to investigate the bug or its a
   feature request.") His answer sets the kind. The kind goes into `task.md` with its reason, and
   as the line `kind: KIND, because WHY` into the task's first state block (step 4);
   `project.py state` refuses that line in any other form, and `project.py tasks` gives it as
   `kind`. When he changes the kind later, write a state block with the new line.
2. **The slug and the branch.** A slug of two to five plain words that say what the owner gets
   ("report-dates-stay-whole"), never a code. The branch is `<type>/<slug>` with a semantic type,
   unless the project's `AGENTS.md` gives its own scheme. The kind gives the type: `fix` for a bug
   and a correction, `feat` for a feature, `chore` for a chore and `docs` for docs. For an
   investigation, choose the type of the change its answer would most likely lead to, and say
   why in the line of step 5; its branch gets a commit only when the investigator
   reproduces a bug. The branch's type binds nobody; each commit of the lead carries its own. A
   slug that a `landed`, an `answered` or a `dropped` task has is taken, since that task's files
   stay under it: add a word, as `task-dir` says when it refuses. For a ticket, the branch is the
   name the tracker gives for it, when it gives one: the tracker and its automation find the
   work by that name.
3. **The task directory.** `project.py task-dir SLUG --ask "the owner's words"` keeps the ask as
   the owner gave it, for the board and the status. For a ticket, add `--ticket ID`, and the ask
   is the ticket's title; the command refuses a ticket another task holds. Then write `task.md`:
   - the ask, verbatim; for a ticket, its id, its link, its title and its description as written;
   - the kind, with its reason (step 1);
   - the outcome in one or two sentences, as the person it is for would see it;
   - done when: the evidence that shows the outcome, each line something a command or a look at
     the product can show;
   - out of scope, when the ask has an obvious neighbor this task leaves alone.
   Write it from the ask, the project's profile and the rulings. Do not read the code for it: a
   "done when" line that needs the code is the lead's to sharpen in its plan. A line you put out
   of scope by yourself is a decision taken without the owner: log it with `decisions.py log SLUG
   --by lem`.
4. **Which path.** Choose one:
   - *the investigation first*, for a bug and an investigation: a fresh builder reproduces the
     bug and finds its cause, or answers the question, before anyone writes a story, as "A bug
     and an investigation" below says. For a bug, its report then takes one of the paths below;
     an investigation ends with its answer.
   - *a small change*: one builder, the checks, one review and the pull request, with no lead, no
     plan and no wait for him, as "A small change" below says.
   - *the rare path*: the whole context and a defined outcome are written already: a ticket whose
     description says what is wanted and how to tell that it is done, a backlog item whose
     options are settled, a night plan he starts, an investigation's report that settles what is
     wanted. No interview: the lead writes the stories from the code and has the personas read
     them (`stages/plan.md`, step 1). He can say "interview me", and then it is the usual path.
   - *the usual path*, for every other ask: the interview, then the stories he approves, as
     "The interview and the stories" below says, all in one sitting while he is there.
   Write the task's first state block now, with the kind line of step 1, so that the status and
   the board show the task from its first moment. On the usual path it is `held` with the line
   `the interview waits for the owner`:

   ```bash
   python3 SKILL_DIR/scripts/project.py state SLUG held "the interview waits for the owner" "kind: feature, because WHY"
   ```

   On the other paths the first block is the one the path's own first step writes, before its
   builder starts: there is no wait between the two.
5. **Tell the owner in one line**, and no more: the size, the branch, the story or the outcome in
   his words, what happens now, and what he must do. A small change: `Small change,
   fix/date-column-nowrap: "the date column never wraps". One builder, the checks, one review,
   then the pull request. Nothing waits for you; say "feature" to give it stories.` A feature on
   the usual path: `Feature, feat/gift-note-in-export: "an export holds the gift note". An
   interview now, then stories for your yes; after that it runs to the pull request without
   you.` A topic in reach goes first: `Careful: this changes how a customer is charged. Feature,
   ...`. A bug: `Bug, fix/total-skips-credit-notes: "the total skips credit notes". A builder
   reproduces it and finds its cause first, and I tell you what it found.` The rare path names
   what stands in for the interview (`the ticket says what is wanted`). A decision you took for
   him at step 3 is a second line. Nothing repeats this line later: the next thing he hears is a
   question of the interview, the stories, or the pull request.
6. **The brief** of a lead, on the rare and the usual path. Write `brief.md` in the task
   directory, with this and nothing more:

   ```
   Read SKILL_DIR/prompts/lead.md and follow it.
   task: SLUG
   branch: the branch of step 2
   worktree: the path `project.py worktree-dir SLUG` prints
   task directory: the task directory's absolute path
   lead: builder
   stop after the plan: no
   coordinator: SESSION:PANE
   socket: PATH
   ```

   The last two lines are your own address, for the lead's `tell-coordinator` (the harness
   file): this session's `AGTERM_SESSION_ID` and this pane's `AGTERM_PANE_ID`, and the
   `AGTERM_SOCKET` of this session, written out. The brief says nothing about the code, so it
   cannot say anything wrong about it. The ask is in
   `task.md`, in the owner's words. The brief is a file because a task may wait in the queue or
   get a second lead, and each start has to find the same answers: `/lem plan <what>` writes
   `stop after the plan: yes` here, and that line is what keeps a queued plan from being built.
   When the owner called the task careful in the ask, add the line `careful: the owner says so`
   and log his words, as the paragraph on his word below says. A builder still writes the plan:
   it reads that line as a yes (`stages/plan.md`, step 2) and stops for the plan talk, which
   needs a plan to talk about.
7. **Does it wait for another task?** Only when the later ask needs what the earlier one
   changes: it names the earlier one's result, or it makes no sense before that result exists.
   Then write the later one's state as `queued` with the line `after: SLUG` of the earlier one,
   and stop here: it starts when that task is `landed`, `answered` or `dropped`, so it builds on
   what the earlier one changed. Two asks that only name the same thing (the same screen, the same
   file, the same function) each start on their own, and the owner orders their pull requests.
   The owner overturned such a wait: "start this bug now, on its own, and do not wait for the
   one-day task; I sort out the order of the pull requests myself" (a scratch repository,
   2026-11-17; the two tasks changed one function). Do not read the code to find an overlap the
   asks do not show; the landing line settles that one (`stages/land.md`, step 1).
8. **Start its lead**, as "Start a lead" says. Open the board when this session has not opened
   it yet (`SKILL.md`, Status); it stays in the sidebar beside your session. Then go back to the
   owner's next message. Do not wait for the lead and do not watch it.

`/lem build <task>` is for a task whose state is `drafted` or `planned`: change its brief to
`stop after the plan: no`, take out a `night: yes` line, since the owner is there now, and start
its lead. When its `report.md` or a state block of it says `needs a session:` and `project.py
tasks` gives it no `talk`, change the brief to `lead: session` first: that start opens the plan
talk's companion at once, where a builder would only stop at the plan again. A path to a plan file names its task too: the
file is `YYYYMMDD-<slug>.md`, and the slug is the task's. With no name, list the tasks in those
two states (`project.py tasks`), each with its ask and its plan's path, and ask which one: a
fixed choice, so it stays in the terminal. One such task needs no question.

The owner may say that a task is careful, at any time before its landing, whatever its lead
called it. At once, add the line `careful: the owner says so` to the task's brief, and log his
words with `decisions.py log SLUG --by owner`. The brief is what holds it: whoever reads the task's next stop reads
that line, also a Lem that started after this one, and the landing reads it too: the change
gets the project's full review set, its notes say whether it holds a migration, and a person
merges it whatever the settings say (`stages/land.md`). A task that still builds finishes its
build and goes to the landing like any other; nothing is built again for the word.
Then ask what the owner's word was about, when it is not plain. A topic the settings already
name, which the lead read wrong, is a lesson about that judgment (`stages/learn.md`). Something
no topic names may be a rule for later tasks or a wish for this one task: only the owner knows,
and only his yes puts a topic into the settings.

## The interview and the stories

The usual path, between step 5 and the brief. He is there for it, and it ends with stories he
approved, which the lead may not change without the record saying so.

1. **Start the scout and the interview at once.** A bug whose investigation found its cause has
   no scout: the investigation's report is its facts of the code, and wherever these steps name
   the scout's report, read that one. The scout is a fresh read-only agent that
   reads the code around the ask and returns facts, not a plan: `spawn-builder` with the brief

   ```
   Read SKILL_DIR/prompts/scout.md and follow it.
   request: TASK_DIRECTORY/ask.txt
   checkout: the main checkout's absolute path
   task directory: TASK_DIRECTORY
   ```

   The interview does not wait for it, so it costs him no wait: on 2026-11-16 a scout took 26.7 s
   in a tiny repository and 116.5 s in Lem's own, 12 files opened in each (one request each).
   Log the start of each, so that the board draws both: `python3 SKILL_DIR/scripts/project.py
   log SLUG scout.start` as the scout starts, and `project.py log SLUG interview.start` before
   the first question. Its reply is its report: write it word for word into `scout.md` in the
   task directory, and log `project.py log SLUG scout`, its end. It is the one place where
   knowledge of the code comes up to you, and only as facts for the stories: you still read no
   diff and write no code.
2. **The interview.** One question at a time, each with your own guess, so that he reacts and
   does not compose. A question he answers with a yes to your guess, or by typing a value (a
   name, a number, a word), is one line in the conversation: that is the owner's own exception
   to the page, "something fixed choice, trivial, without additional context". A question that
   sets two or more options side by side, each with what it changes for a person, goes on the
   question page (`ask-owner`), as his ruling says of every other question; put the options
   that are ready on one page, never one page per question. The questions come from the
   `lem-interview-me` method (`load-skill`); its restate and its explicit yes are the stories
   and his yes to them (steps 4 to 7), so nothing is restated before the stories and he says yes
   once. A fact of the scout's report may go into a later question ("the export already
   writes an empty cell for a missing value; keep that for the note?"). It may be technical: he
   is a developer. Stop when you can write the outcome and each rule without a guess.
3. **The directions.** What he names in the interview, a technology, a library, an approach, an
   option he picked between two, is a direction. Write `directions.md` in the task directory, one
   line each, with his words. The lead's plan follows them; a plan that departs from one is a
   decision of the build (`stages/build.md`, "A choice in the build"). Then write `task.md` again
   with the outcome and the "done when" his answers gave.
   A defect outside the request, that he names or that the scout's report shows, is no part of
   the task and is not lost: write it to `outside.md` in the task directory, one line each, with
   its place (`path` or `path:symbol`) and what is wrong. Do not ask him whether to file it, and
   do not put it into the stories. The landing's polish pass fixes a cheap one in place and files
   each other one in the backlog, and the pull request lists what was filed.
4. **The stories**, when the scout's report is in and not before. Write them from his words, the
   directions, the project's profile and the report, in the form `stories.py --help` shows: the
   `## Stories` heading, the `Kind:` line, and numbered stories, each a business rule in plain
   language with one concrete example, with real names and values. No test lines: the lead adds
   those. Keep the file in the task directory, and for each story the facts of the report that
   shaped it, for his page.
5. **Show them in the conversation, and start the personas' read in the same moment.** Write the
   stories as plain text, each with the scout's facts that shaped it beside it, and the
   directions, and say that the personas read them now. No page opens before the read is in.
   Log its start, `python3 SKILL_DIR/scripts/project.py log SLUG stories.read.start by=lem`; the
   record below is its end, and the end of the interview. The read is the persona panel's
   "Reading stories" mode (`load-skill`), here in your session with the paired agent of the other
   family, so that both families answer; without one the
   panel says that one family answered. A persona agent that does not answer leaves a partial
   read, which counts: the record says who did not answer and why. A read in which nobody
   answered is written down too, with `answered:=0`, `families:='[]'` and each source in
   `silent`, and started once more. After a second such read in a row the stories go on
   unread: the owner's yes of step 6 still freezes them, and the pull request is not green, with
   "the stories were not read" first. A partial read counts by his word of 2026-11-16 ("Thats
   fine - just log and proceed"); the second try is the amendment's design. The landing refuses a
   request whose newest read had no answer and was the first. When the answers are in, write the
   one event the landing reads:

   ```bash
   python3 SKILL_DIR/scripts/project.py log SLUG stories.read by=lem asked:=N answered:=N families:='["FAMILY", ...]' silent:='[{"name": "PERSONA, FAMILY", "why": "WHAT STOPPED IT"}]' stories:=N flagged:=N split:=true|false digest=DIGEST
   ```

   `asked` is the personas the panel asked and `answered` those of whom at least one family
   answered; `silent` names each source that gave no answer, `[]` when every one did. `flagged`
   counts the stories an answer called unexpected, confusing or wrong; `split` says whether the
   two families answered a story differently, which counts as a doubt too. `DIGEST` is the
   `digest` field of what `python3 SKILL_DIR/scripts/stories.py digest SLUG --file FILE` prints
   for the stories file the personas read, so that the record knows when he changes them after
   the read.

   **The read is his to skip, never yours.** When a story names a person other than the
   developer (a customer, a clerk, a reader of a file), the read starts and you ask nothing. When
   every story names only the developer, ask one fixed question in the terminal before the read
   starts, a fixed choice with no context: "The stories name only you. Skip the persona read?
   (y/n)". Never skip the read by your own judgment: you wrote the stories, and the author of a
   wrong reading sees it as clear (a Fable second opinion, 2026-11-16, which he agreed to). On his
   no, the read starts as above. On his yes, write his words, then take his approval of step 6 and
   freeze the stories with step 7, both before the brief:

   ```bash
   python3 SKILL_DIR/scripts/decisions.py log SLUG --by owner --what "the personas' read of the stories" --chose "no read: the stories name only the developer" --why "HIS ANSWER, AS HE TYPED IT"
   ```

   The landing knows his word by `--by owner` and those two texts, word for word, and takes it
   only with an approval of his after it and before any lead of the task started; the pull request
   then says "the stories: not read by the personas, on the owner's word (DATE); the owner
   approved them", and stays green, since the decision was his. On the rare path this question is never asked: there
   the read is the only approval (`stages/plan.md`, step 1), and the landing refuses a word to
   skip it that comes after the lead started.
6. **His yes.**
   - *He typed it in the conversation before the read was in*: take it, and freeze the stories
     (step 7). When the read is in and nobody is confused and the families agree, say so in one
     line and open no page. When a story is flagged or the families split, open the page below
     for that.
   - *Otherwise*, when the read is in, open one page through `ask-owner`:
     - the personas' result on top, for each persona and each model family, with a split
       between the families said first, in one line ("the Opus answers doubt story 1, the Sol
       answers do not");
     - each story, with the scout's facts that shaped it beside it;
     - a story a persona flagged as you wrote it, with the answers that flagged it quoted beside
       it. Never reword it before he sees it: what changes it is his;
     - the directions.
   He approves, or changes a story, a direction or the set. Write each change in his words into
   the stories file or `directions.md`. The personas do not read his own change again; the pull
   request then says that the stories changed after the read.
7. **Freeze them**: `python3 SKILL_DIR/scripts/stories.py approve SLUG --file FILE`, again after
   each change of his. The stories are then kept word for word with a digest, and the plan's
   stories have to be those, with only the test lines added: a story the build changes, adds or
   drops has its own record (`decisions.py story`), and the pull request is not green for it.
   Go on with step 6 of "Open the task". The landing refuses a feature whose stories nobody read
   and whose read he did not skip (step 5), and one whose read found a doubt with no yes of his
   after it.

When he leaves before he answers, write the state `held` with the line `the stories wait for the
owner`, and put the page to him again the way `ask-owner` says for an owner who is away. His
answer goes on from step 6. A task with that line has no lead: when it is approved, write the
brief and start one.

## A small change

One story, his own sentence made exact, nothing careful and no question open: one builder makes
it, the landing checks it and one read reviews it, and it waits for nothing. The owner, of a
polish agent with nothing to do on a typo: "That is exactly one of the cases that may frustrate
the Developer" (2026-11-16). The audit of that day counted 6 to 11 agents and 15 to 32 minutes
from a typo to its pull request, against about 4 minutes measured for a correction in the first
flow (unmeasured estimates built on the skill files' measurements; `AGENTS.md` has the ledger).

1. **The story.** Write it to `stories.md` in the task directory, in the form `stories.py --help`
   shows, with `Kind: correction, because ...` and the one story, and approve it in his name:

   ```bash
   python3 SKILL_DIR/scripts/stories.py approve SLUG --file TASK_DIRECTORY/stories.md --correction
   ```

   It stays there and is never committed: a small change has no plan, and its builder adds the
   test line under the story in that file. An approval in his name is only ever a task's first
   contract: the script refuses it once any approval exists. The personas do not read it; the pull
   request says so.
2. **The brief**, `brief.md` in the task directory, with this and nothing more:

   ```
   Read SKILL_DIR/prompts/small.md and follow it.
   task: SLUG
   branch: the branch of step 2 of "Open the task"
   worktree: the path `project.py worktree-dir SLUG` prints
   task directory: the task directory's absolute path
   ```

   Then step 7 of "Open the task", and its builder starts as "Start a lead" says, with the state
   `building` and the lines `small change: one builder` and the kind line of step 1. There is no
   lead: the one builder is the fresh builder of the one task, as the owner's rule on a fresh
   builder for each task has it.
3. **When it stops**, its reply is the path of its report, of five lines at most; when its agent
   refused it the write, the reply is the report itself, and you write `report.md` from it word
   for word. Its state says what follows:
   - `ready`: the landing, `stages/land.md`, with the small change's steps there, up to its pull
     request with no question on the way: the push and the pull request of `land.py propose`
     are the owner's standing word in `branch.propose`, not a step to ask about;
   - `held` with `the stories wait for the owner: the small change is a feature`: its builder
     found a topic in reach, a second rule, a decision the story does not settle, a lowered bar,
     or more than one plain change. Tell him in one line that it is a feature and why, from the
     report, and take the usual path from step 1 of "The interview and the stories", with its
     report as the scout's: its commits stay on the branch for the lead. His approval of the
     stories as a feature replaces the correction's.

When he says "feature" of a small change, or "this is a feature", it takes the usual path the
same way: the interview, the personas' read, and his approval, which replaces the correction's.
A builder that runs then finishes, and its commits stay on the branch for the lead. A change of
the kind is his only.

## A bug and an investigation

A bug is investigated before anyone writes a story: "typically the root-cause-investigation is
needed to unerstand what triggers the bug that we aim to correct" (the owner, 2026-11-16). An
investigation is the same work with a question in place of the bug, and its answer is the whole
task.

1. **A place, the worktree and the state.** `project.py may-start SLUG`, and the worktree on the
   task's branch, as steps 1 and 2 of "Start a lead" say: the investigator runs the project's
   tests, so it takes a place. A task queued there starts its investigator when its turn comes,
   not a lead: `project.py tasks` gives its `kind`, a bug or an investigation, and either no
   `investigation` yet or one whose `call` is `not-reproduced`, which waits for the second
   investigator. Then write the state:

   ```bash
   python3 SKILL_DIR/scripts/project.py state SLUG building "a builder reproduces the bug and finds its cause" "investigation: bug" "kind: bug, because WHY"
   ```

   with `investigation: question` and the kind line of an investigation for a question. The
   board draws a block with an `investigation:` line as the investigation.
2. **Start the investigator**, a fresh builder (`spawn-builder`) with the brief

   ```
   Read SKILL_DIR/prompts/investigator.md and follow it.
   request: TASK_DIRECTORY/ask.txt
   kind: bug or investigation
   worktree: the path `project.py worktree-dir SLUG` prints
   branch: the branch of step 2 of "Open the task"
   task directory: TASK_DIRECTORY
   ```

   Log its start as it starts, `python3 SKILL_DIR/scripts/project.py log SLUG investigation.start
   kind=bug` (or `kind=investigation`); the record of step 3 is its end. Then go back to his next
   message: its reply wakes you, and the line of step 5 of "Open the task" told him already. No
   investigation has been timed yet.
3. **Read its report.** Its reply is the path of `investigation.md` in the task directory. When
   its agent refused it the write, its reply is the whole report: write it into that file word
   for word, with one line at the top that says who copied it and why. The report is knowledge of
   the code for the stories, as the scout's is; you still read no diff and write no code. Then
   write what it found, which the board shows and the landing reads:

   ```bash
   python3 SKILL_DIR/scripts/project.py log SLUG investigation kind=bug call=CALL "line=ONE LINE" where=PATH:SYMBOL reproduced:=true|false
   ```

   `call` is the report's: `correction`, `usual`, `not-a-bug` or `not-reproduced` for a bug, and
   `answer` for an investigation, which has no `reproduced`. `line` is the cause, the answer, or
   what was tried, in one line. `where` is the cause's place, which a plain cause has. When you
   take another call than the report's (a one-rule fix whose cause is in reach of a topic is not
   a small change),
   log yours and tell the owner why in one line.
4. **The path**, from the call:
   - *correction*: a small change, with its one story the rule that removes the cause, in his
     words made exact, and with nothing careful: read the cause, its place and how far the report
     says it reaches against each topic, as step 1 of "Open the task" reads an ask. The
     reproducing test is the story's test: the small change's builder names it under the story.
     Tell him in one line, as step 5 of "Open the task" says, and go on with "A small change".
   - *usual*: the usual path, with no scout, whose interview starts from the cause ("the total
     adds the refund as a payment, in `billing/invoice.py:total`; should the refund lower the
     total, or stand as a line of its own?"). Write the state `held` with the line `the
     interview waits for the owner` first: the investigator's place is free again.
   - *not a bug*: tell him what the code does in his case and why, as one run (`SKILL.md`, "What
     the owner has to understand is told as one run"), with where each step was read. Write the
     state `answered` with that in one line, and `land.py clean SLUG`: the worktree goes, and the
     branch stays with its commits, the reproducing test among them.
   - *not reproduced*: tell him each try in one line, and ask him for one more fact: the record,
     the input, the time, what he saw. Write the state `held` with the line `the investigation
     waits for one more fact`. Write his answer into `task.md`, add one line to the brief,
     `tried before:` with the report's tries, and start a fresh investigator from step 1, which
     takes a place again or queues it.
   - *answer*, for an investigation: show him the answer as the report gives it, with where each
     part was read. Write the state `answered` with the answer in one line, and `land.py clean
     SLUG`.
   `project.py state SLUG answered` refuses a task with no `investigation.md` or no record whose
   call is `not-a-bug` or `answer`. For an answered task that came from a ticket, the tracker
   then comments the answer on the ticket and changes no status (its "answer"): tell the owner
   which status the ticket has. A task that goes on keeps the report in its directory, and
   its pull request names the cause in one line, from the record.
5. **A task from the report.** He can start one with `/lem new` and the report's path, as he can
   with a backlog item: the new task's ask is his words, and the report its written context. Copy
   the report into the new task's directory as `investigation.md`, name it in its `task.md`, and
   take its path in step 4: when the report and his words settle what is wanted, that is the rare
   path. The answered task's branch may hold a test the new task can take.

## When a task is dropped

The owner says that a task is not wanted, at any point before its landing. Write the state
`dropped` with his reason in one line. Close the task's companion when one is open, and remove its
worktree the way the project does; the branch stays, because its commits are on no other branch
(`land.py clean` does both and says so). For a task that came from a ticket, the tracker then
says so on the ticket (its "drop") and changes no status: tell the owner which status the ticket
has, since where it goes now is his call. Then look at the queue, as the last section says.

## Start a lead

Every start goes this way: a new task, `/lem build`, a queued task whose turn came, and a lead
that is started again after it stopped.

1. **A place.** `project.py may-start SLUG`, with the slug of the task whose lead starts: a task
   that builds already (its investigator called the path, its lead stopped) holds its place, and
   that place is not counted against it. On exit 1 the task waits: write its state as `queued`,
   unless it is `queued` already, tell the owner in one line which tasks hold the places, and
   stop here.
2. **The worktree.** When the task has one, use it. When it has none, make it at the path in the
   brief: from the task's branch when that branch exists (a night draft, a task whose worktree
   was removed), otherwise from the settings' base branch. Use the project's own worktree script
   when `AGENTS.md` names one, since it sets up what a plain worktree lacks (a test database, an
   environment); otherwise `git worktree add -b BRANCH PATH BASE` for a new branch, and
   `git worktree add PATH BRANCH` for a branch that exists. `project.py worktree-dir` already made the folder for worktrees one that
   git ignores. The worktree is in the checkout, not in the task's
   state directory: an agent's sandbox may not write inside the git directory, and the state has
   to outlive the worktree.
3. **The lead.** Write a lead's `coordinator:` and `socket:` lines again with your own
   values when they are not yours (a brief written by a Lem before you, or one with no such
   lines): a lead tells the session those lines name. A small change's brief has none: its
   builder's reply is its only word. Write the state `building` first, with the line `lead:
   builder` or `lead: session` as the brief says, or `small change: one builder` for a brief that
   names `prompts/small.md`, so the next `may-start` counts this task. A small change's builder
   gets one more line, its start for the board, as it starts: `python3
   SKILL_DIR/scripts/project.py log SLUG builder.start "job=the small change"`; its state of
   `ready` or `held` is its end. The task's first block
   carries the kind line of step 1 of "Open the task" too, when no block before it has one. For a task that
   came from a ticket, the tracker then marks the ticket as started (its "start"); it writes
   nothing when the project's settings say that the tracker moves its own tickets. Then, for a
   builder, `spawn-builder` with one line: `Read TASK_DIRECTORY/brief.md and follow it.` For
   `lead: session`, the plan talk's companion: `open-task-session` with the same file, its agent
   on the model and the effort of the settings' `seats.planner` when they name them; write the
   state again with the line `session: ID` and the id the session got, so the board can show the
   companion and it can be closed after the talk, and with the line `defender: MODEL, EFFORT` as
   the companion's status line shows them, which the talk's record names. When the companion is
   still there, the start is one message to it with what changed (the owner's answers, a settled
   blocker) instead of a second session.

A lead that is started again is a fresh agent with the same brief. It finds the plan, the report,
the decisions and the commits on the branch; that is the whole handover.

## When a choice waits for the owner

Every decision that is the owner's comes here, at plan time and in the build: a lead that meets
one, in its plan or in a task of it, has the personas read it and asks it with `decisions.py
ask` when they leave it unclear, and the task goes on without it (`stages/plan.md`, step 5, and
`stages/build.md`, "A choice in the build"). The defender of a plan talk asks the choices the
talk left open the same way. Either lead tells you at once with the
line `lem: SLUG choice N waits`, through `tell-coordinator`: the defender from its companion,
and a builder that leads from this session, where it runs. That line is the wake-up, and the
wait counts from the ask. A line can be lost (a pane that restarted, a brief with no
`coordinator:` line), and the harness file says that the builder's line was not yet seen to
wake an idle Lem, so also run `python3 SKILL_DIR/scripts/decisions.py pending` at each of your
turns: its `waiting` list is what needs his answer. At the same turns, run `land.py merged SLUG`
for each `open` task with a pull request, as `SKILL.md` says under Status: a merge he made on
the forge frees the queue. A task that was dropped or landed while a choice waited is under `ended`, and
its choices need no answer.

1. **Ask him at once**, through `ask-owner`, which shows it as the settings' `tools.ask` says.
   Above the card, the run: the choice's `case` in its numbered steps, whether it was
   reproduced or derived (`case_was`), and its `cause` line. On the card's top the two experts'
   answers (`advice`: each one's pick, or that none fits, with its reasons) beside the personas'
   (`said`), then what the choice is, the options, the recommended one with its reason, and the
   time the wait ends, in his clock (`deadline` is in UTC). The lead ran the persona panel
   (`lem-panel`) before the ask, so it is not run again here. The question gate (`lem-gate`) sits
   at this card: its judge, in shadow mode, logs its verdict beside his answer, its framing check
   reads the card before it goes out, and after his answer its last step asks whether the answer
   is a durable ruling. Its card step is this card. After that time the lead takes the option both experts
   picked (`experts_pick`), or the recommended one when they split, and the pull request is not
   green for it either way: say which of the two it will be. A choice with `irreversible` set has
   no such time: say which of the four kinds it is, that the experts' answers are advice only,
   and that only that part of the plan waits for his word.
   The lead gives each choice to the experts (the `lem-ask-expert` skill) right after its ask, and
   their answers take some seconds to minutes. When `advice` is not complete yet, say on the card
   that the experts were asked; the lead sends `lem: SLUG choice N advised` when both answers
   are in, and then you tell him both in one short message. When the task's
   directory has no `experts/choice-N.brief.md`, nobody gave the choice to them: run the
   `lem-ask-expert` skill yourself, at once.
2. **Write his answer**: `decisions.py answer SLUG N --chose OPTION --words TEXT`. `--chose` is
   the option his answer takes, word for word as the choice has it; the script refuses any
   other text. `--words` is his answer as he gave it, when it is not that text, and `--why`
   his reason, when he gave one, in his words. Never put the recommendation's reason there:
   the record keeps that one beside it. When he decided something that none of the options
   says, settle the choice with it: `decisions.py answer SLUG N --instead TEXT`, with `--words`
   and `--why` as above. Never log it as a new decision: the choice would wait for ever, and an
   irreversible one would hold the pull request. A choice carries no story: a story his answer
   changes is the lead's to record with `decisions.py story ... --choice N`, and the gate refuses
   the plan until it does. When you cannot tell what he decided, ask him again. A lead in a
   session gets the answer as one message too; a builder that leads finds it at its next
   `decisions.py wait`.
3. **An answer after the wait** is written down the same way, and the script says it is late,
   also when nobody wrote the timeout yet: it writes the timeout then, and what the timeout
   takes stands. When the answer differs from what was taken, it is his correction: tell the
   lead while the task builds, and after that it is a new ask. The pull request names it either
   way. An answer after the experts settled the choice is late in the same way.
4. **When he is away**, the choice does not wait its time for him: once both experts picked the
   same option, `decisions.py settle SLUG N --away` takes it at once, and the pull request is not
   green for it. He is away on two facts only, as the harness file's `ask-owner` says: his own
   words in this session that he is away or leaves, or a question of this turn that went to his
   away channel. His silence is no such fact. The script refuses when the experts split, when
   one has not answered, after the wait ended (the timeout takes it then) and always for an
   irreversible step; a choice it refuses waits its time. A defender whose companion is open
   gets one message with the option taken; a builder that leads finds it at its next
   `decisions.py wait`. Tell him at
   his return what was taken for him and the experts' reasons.

## When a lead stops

A builder's reply is the path of its report. The defender of a plan talk sends one message
that starts with `lem:` and names the task. Either is only a wake-up. The fact is the task's
newest state block: `project.py tasks`, then read the task's `report.md`.

A lead whose agent refused it the write of `report.md` says so in its state (`report in the
reply`), and its reply is the whole report. Write that text into `report.md` word for word, with
one line at the top that says who copied it and why. Change nothing in it. The harness file says
when this happens.

Act on the status:

- **`ready`**: the task joins the landing line. Run `stages/land.md` when no task is in
  `landing`; a `ready` task waits there in the order of its state's time.
- **`planned`**: the report says why the lead stopped at the plan.
  - *It needs a session* (`needs a session: careful`, or `needs a session: large` for a plan of
    more than three tasks): change the brief to `lead: session`, and start a lead. That opens
    the plan talk's companion, whose agent defends the plan against the reviewer in its other
    pane (`prompts/defender.md`): a builder has no pane for the reviewer.
  - *The talk is done* (`the plan talk is done`, after `lem: SLUG talk done`): read `talk` in
    `project.py tasks`, never the line's claim. A record there: close the companion
    (`open-task-session`), change the brief to `lead: builder`, and start a lead; the builder
    leads the build of the talked plan, one fresh builder for each of its tasks
    (`stages/plan.md`, step 3). Each choice the talk left open waits in `decisions.py pending`:
    ask it as the section above says. No record: the defender ended without its last step, so
    send it one message that says so, and close nothing.
  - *The owner asked for the plan only*: show the owner the plan through the settings'
    `tools.annotate`, and leave the task as it is until the owner says build or drop.
- **`held`**: the task waits for the owner on what is no decision with options; a decision of
  his never holds a task, since it is asked and waits its time while the work goes on (the
  section above). The state's line says which of four it is:
  - *the stories wait for the owner*: a lead of the rare path whose stories a persona doubted, or
    that met a rule it could not write without a guess, puts the stories and the answers on top
    of its report. Put them to him as step 6 of "The interview and the stories" says, with the
    lead's read as the result on top, freeze his answer with step 7, and start a lead: it copies
    the approved stories. A small change that its builder found to be a feature goes to him as
    "A small change" says, step 3;
  - *one more fact*: the investigation's, as "A bug and an investigation" says;
  - *a step that is his to do*, and no decision at all: a trust prompt of the reviewer's agent, a
    command an agent is refused. Tell the owner that step as it is, with where he does it; it
    needs no gate and no panel. When he says it is done, start a lead as "Start a lead" says:
    for a defender whose companion is still open that is one message to it, and otherwise a
    fresh lead that reads the state and goes on;
  - *choice N waits for the owner*: an irreversible step that every task left depends on. It is
    in `decisions.py pending` and asked as the section above says; start a lead after his answer.
- **`blocked`**: the report says what the lead could not settle and what it tried. A missing
  tool, a base branch that does not build, a conflict with another task: settle it, then start a
  lead. An approach that failed twice goes to a fresh builder with a different approach, as
  `stages/build.md` says: add one line to the brief, `do not repeat:` and what the report says
  the two tries assumed. When only the owner can settle it, it is a step that is his to do:
  write the state `held` with that step, and tell him where he does it.
- **anything else**, or no new state block: the lead ended without its last step. Start a lead;
  it reads the state and the report and goes on. After a second such stop, write `blocked` and
  tell the owner what the reply or the session's screen shows.

After any of these, look at what is owed and at the queue. A task that ended with a
`ticket_owed` in `project.py tasks` gets those steps from the tracker now. A `blocked` task whose
state has `the base is red` and an `after:` task that is `landed` gets the state `ready` again,
with the line `the base is green again`, and joins the landing line. Take the `queued` tasks in
the order of their state's time, leave out each one whose `after:` task is not `landed`,
`answered` or `dropped`, and start a lead, or the investigator of a bug or an investigation, for
the first that is left. Step 1 of "Start a lead" decides whether there is a place.
