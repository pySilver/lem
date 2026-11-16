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
   with this ticket that is not `dropped`, do not open a second one: say which task it is and
   where it stands.
1. **The slug and the branch.** A slug of two to five plain words that say what the owner gets
   ("report-dates-stay-whole"), never a code. The branch is `<type>/<slug>` with a semantic type
   (`feat`, `fix`, `chore`, `docs`), unless the project's `AGENTS.md` gives its own scheme. Take
   the type from the ask alone: `fix` when the ask says that something is wrong today, `feat`
   when it asks for something that is not there, and `feat` when you cannot tell. The branch's
   type binds nobody; each commit of the lead carries its own. A slug that a `landed` or a
   `dropped` task has is taken, since that task's files stay under it: add a word, as
   `task-dir` says when it refuses. For a ticket, the branch is the
   name the tracker gives for it, when it gives one: the tracker and its automation find the
   work by that name.
2. **The task directory.** `project.py task-dir SLUG --ask "the owner's words"` keeps the ask as
   the owner gave it, for the board and the status. For a ticket, add `--ticket ID`, and the ask
   is the ticket's title; the command refuses a ticket another task holds. Then write `task.md`:
   - the ask, verbatim; for a ticket, its id, its link, its title and its description as written;
   - the outcome in one or two sentences, as the person it is for would see it;
   - done when: the evidence that shows the outcome, each line something a command or a look at
     the product can show;
   - out of scope, when the ask has an obvious neighbor this task leaves alone.
   Write it from the ask, the project's profile and the rulings. Do not read the code for it: a
   "done when" line that needs the code is the lead's to sharpen in its plan. A line you put out
   of scope by yourself is a decision taken without the owner: log it, once the task directory
   is there, with `decisions.py log SLUG --by lem`.
3. **Which path.** Choose one, and tell the owner in one line which one and why:
   - *a correction*: the ask is one rule in his own sentence, and it names nothing careful (no
     danger topic of `flow.topics`, no path a careful pattern matches). Write its one story and
     approve it in his name, as "A correction" below says, then go on with step 4.
   - *the rare path*: the whole context and a defined outcome are written already: a ticket whose
     description says what is wanted and how to tell that it is done, a backlog item whose
     options are settled, a night plan he starts. No interview: the lead writes the stories from
     the code and has the personas read them (`stages/plan.md`, step 1). He can say "interview
     me", and then it is the usual path. Go on with step 4.
   - *the usual path*, for every other ask: the interview, then the stories he approves, as
     "The interview and the stories" below says, all in one sitting while he is there. Then go on
     with step 4.
4. **The brief.** Write `brief.md` in the task directory, with this and nothing more:

   ```
   Read SKILL_DIR/prompts/lead.md and follow it.
   task: SLUG
   branch: the branch of step 1
   worktree: the path `project.py worktree-dir SLUG` prints
   task directory: the task directory's absolute path
   lead: builder
   stop after the plan: no
   ```

   The brief says nothing about the code, so it cannot say anything wrong about it. The ask is in
   `task.md`, in the owner's words. The brief is a file because a task may wait in the queue or
   get a second lead, and each start has to find the same answers: `/lem plan <what>` writes
   `stop after the plan: yes` here, and that line is what keeps a queued plan from being built.
   When the owner called the task careful in the ask, write `lead: session`.
5. **Does it wait for another task?** Two asks that name the same thing (the same screen, the
   same file, the same command) run one after the other. Write the later one's state as `queued`
   with the line `after: SLUG` of the earlier one, and stop here: it starts when that task is
   `landed` or `dropped`, so it builds on what the earlier one changed. Do not read the code to
   find an overlap the asks do not show; the landing line settles that one (`stages/land.md`,
   step 1).
6. **Start its lead**, as the next section says. Open the board when this session has not
   opened it yet (`SKILL.md`, Status); it stays in the sidebar beside your session.
7. **Tell the owner**, in a few lines: the task's plain name, the outcome and the "done when"
   lines as you wrote them, each decision you took for him (what you put out of scope), and that
   the report comes after the landing. Then go back to the owner's next message. Do not wait for
   the lead and do not watch it.

`/lem build <task>` is for a task whose state is `drafted` or `planned`: change its brief to
`stop after the plan: no` and start its lead. A path to a plan file names its task too: the
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
Then ask what the owner's word was about, when it is not plain. A topic or a path the settings
already name, which the lead read wrong, is a lesson about that judgment (`stages/learn.md`).
Something no setting names may be a rule for later tasks or a wish for this one task: only the
owner knows, and only his yes puts a topic or a path into the settings.

## The interview and the stories

The usual path, between step 2 and the brief. He is there for it, and it ends with stories he
approved, which the lead may not change without the record saying so.

1. **Start the scout and the interview at once.** The scout is a fresh read-only agent that
   reads the code around the ask and returns facts, not a plan: `spawn-builder` with the brief

   ```
   Read SKILL_DIR/prompts/scout.md and follow it.
   request: TASK_DIRECTORY/ask.txt
   checkout: the main checkout's absolute path
   task directory: TASK_DIRECTORY
   ```

   The interview does not wait for it, so it costs him no wait: on 2026-11-16 a scout took 26.7 s
   in a tiny repository and 116.5 s in Lem's own, 12 files opened in each (one request each).
   Its reply is its report: write it word for word into `scout.md` in the task directory. It is
   the one place where knowledge of the code comes up to you, and only as facts for the stories:
   you still read no diff and write no code.
2. **The interview.** One question at a time through `ask-owner`, each with your own guess, so
   that he reacts and does not compose. The `lem-interview-me` skill holds the method
   (`load-skill`). A fact of the scout's report may go into a later question ("the export already
   writes an empty cell for a missing value; keep that for the note?"). It may be technical: he
   is a developer. Stop when you can write the outcome and each rule without a guess.
3. **The directions.** What he names in the interview, a technology, a library, an approach, an
   option he picked between two, is a direction. Write `directions.md` in the task directory, one
   line each, with his words. The lead's plan follows them; a plan that departs from one is a
   decision of the build (`stages/build.md`, "A choice in the build"). Then write `task.md` again
   with the outcome and the "done when" his answers gave.
4. **The stories**, when the scout's report is in and not before. Write them from his words, the
   directions, the project's profile and the report, in the form `stories.py --help` shows: the
   `## Stories` heading, the `Kind:` line, and numbered stories, each a business rule in plain
   language with one concrete example, with real names and values. No test lines: the lead adds
   those. Keep the file in the task directory, and for each story the facts of the report that
   shaped it, for his page.
5. **Show them, and start the personas' read in the same moment.** Show him the stories and the
   directions at once (`show-page`, or in the conversation), so that he reads while the personas
   do. The read is the persona panel's "Reading stories" mode (`load-skill`), here in your
   session with the paired agent of the other family, so that both families answer; without one
   the panel says that one family answered. On 2026-11-16 a read with two families of two
   personas over two stories took 2 min 9 s from the stories shown to both families' answers
   written (one request, one repository). When the answers are in, write the one event the
   landing reads:

   ```bash
   python3 SKILL_DIR/scripts/project.py log SLUG stories.read by=lem personas:=N families:='["FAMILY", ...]' stories:=N flagged:=N
   ```

   `flagged` counts the stories that an answer called unexpected, confusing or wrong, and each
   story on which the two families split: a split counts as a doubt.
6. **Ask for his yes** through `ask-owner`, on one page:
   - the personas' result on top, for each persona and each model family; a split between the
     families in one line at the top ("the Opus answers doubt story 1, the Sol answers do not");
   - each story, with the scout's facts that shaped it beside it;
   - a story a persona flagged as you wrote it, with the answers that flagged it quoted beside
     it. Never reword it before he sees it: what changes it is his;
   - the directions.
   He approves, or changes a story, a direction or the set. Write each change in his words into
   the stories file or `directions.md`. When he approved before the read was in and a story is
   flagged, put that story and its answers to him before you go on.
7. **Freeze them**: `python3 SKILL_DIR/scripts/stories.py approve SLUG --file FILE`. The stories
   are then kept word for word with a digest, and the plan's stories have to be those, with
   only the test lines added: a story the build changes, adds or drops is a decision of the
   build, and the pull request is not green for it. Go on with step 4 of "Open the task".

When he leaves before he answers, write the state `held` with the line `the stories wait for the
owner`, and put the page to him again the way `ask-owner` says for an owner who is away. His
answer goes on from step 6. A task with that line has no lead: when it is approved, write the
brief and start one.

## A correction

One story, his own sentence made exact, and nothing careful: it is shown and it does not wait.
Write the story file as step 4 above says, with `Kind: correction, because ...`, show it to him,
and approve it in his name:

```bash
python3 SKILL_DIR/scripts/stories.py approve SLUG --file FILE --correction
```

Tell him in the same line that you took it as a correction and that he may say "this is a
feature". The personas do not read a correction's one story; the pull request says so. When he
says "this is a feature", it takes steps 5 to 7 of the usual path; a story he changes after its
lead started is a decision of the build (`decisions.py log SLUG --by owner --story N --was TEXT`).

## When a task is dropped

The owner says that a task is not wanted, at any point before its landing. Write the state
`dropped` with his reason in one line. Close the task's session when it has one, and remove its
worktree the way the project does; the branch stays, because its commits are on no other branch
(`land.py clean` does both and says so). For a task that came from a ticket, the tracker then
says so on the ticket (its "drop") and changes no status: tell the owner which status the ticket
has, since where it goes now is his call. Then look at the queue, as the last section says.

## Start a lead

Every start goes this way: a new task, `/lem build`, a queued task whose turn came, and a lead
that is started again after it stopped.

1. **A place.** `project.py may-start`. On exit 1 the task waits: write its state as `queued`,
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
3. **The lead.** Write the state `building` first, with the line `lead: builder` or
   `lead: session` as the brief says, so the next `may-start` counts this task. For a task that
   came from a ticket, the tracker then marks the ticket as started (its "start"); it writes
   nothing when the project's settings say that the tracker moves its own tickets. Then, for a
   builder, `spawn-builder` with one line: `Read TASK_DIRECTORY/brief.md and follow it.` For a
   session, `open-task-session` with the same file; write the state again with the line
   `session: ID` and the id the session got, so the board can show the session and it can be
   closed after the landing. When the task's session is still there, the start is one message to
   it with what changed (the owner's answers, a settled blocker) instead of a second session.

A lead that is started again is a fresh agent with the same brief. It finds the plan, the report,
the decisions and the commits on the branch; that is the whole handover.

## When a choice waits for the owner

A lead that meets a choice the personas leave unclear asks it with `decisions.py ask`, and the
task goes on without it (`stages/build.md`, "A choice in the build"). A session's lead tells you
with the line `lem: SLUG choice N waits`. A builder that leads cannot wake you, so run
`python3 SKILL_DIR/scripts/decisions.py pending` at each of your turns: its `waiting` list is what
needs his answer. A task that was dropped or landed while a choice waited is under `ended`, and
its choices need no answer.

1. **Ask him at once**, through `ask-owner`: the personas' answers on top (`said`), then what the
   choice is, the options, the recommended one with its reason, and the time the wait ends, in
   his clock (`deadline` is in UTC). After that time the lead takes the recommended option and
   the pull request is not green for it. A choice with `irreversible` set has no such time: say
   which of the four kinds it is, and that only that part of the plan waits for his word.
2. **Write his answer**: `decisions.py answer SLUG N --chose OPTION --words TEXT`. `--chose` is
   the option his answer takes, word for word as the choice has it; the script refuses any
   other text. `--words` is his answer as he gave it, when it is not that text, and `--why`
   his reason, when he gave one, in his words. Never put the recommendation's reason there:
   the record keeps that one beside it. When he decided something that none of the options
   says, settle the choice with it: `decisions.py answer SLUG N --instead TEXT`, with `--words`
   and `--why` as above. Never log it as a new decision: the choice would wait for ever, and an
   irreversible one would hold the pull request. When the choice carries a story, say also
   whether his decision changed it (`--story-changed --was "the story's text before"`) or kept
   it true (`--story-kept`); the script refuses neither and both. His decision may also change a
   story that no option touched: before you write it, read his words against each story of the
   plan (`stories.py show SLUG`), and when one is no longer true, add
   `--story-changed --story N --was "its text before"`. Left out, a changed story would give a
   green pull request. When you cannot tell what he decided, ask him again. A lead in a session gets the answer as one message too; a builder
   that leads finds it at its next `decisions.py wait`.
3. **An answer after the wait** is written down the same way, and the script says it is late,
   also when nobody wrote the timeout yet: it writes the timeout then, and the recommended
   option stands. When the answer differs from what was taken, it is his correction: tell the
   lead while the task builds, and after that it is a new ask. The pull request names it either
   way.

## When a lead stops

A builder's reply is the path of its report. A session's lead sends one message that starts with
`lem:` and names the task. Either is only a wake-up. The fact is the task's newest state block:
`project.py tasks`, then read the task's `report.md`.

A lead whose agent refused it the write of `report.md` says so in its state (`report in the
reply`), and its reply is the whole report. Write that text into `report.md` word for word, with
one line at the top that says who copied it and why. Change nothing in it. The harness file says
when this happens.

Act on the status:

- **`ready`**: the task joins the landing line. Run `stages/land.md` when no task is in
  `landing`; a `ready` task waits there in the order of its state's time.
- **`planned`**: the report says why the lead stopped at the plan.
  - *It needs a session* (`needs a session: careful`, or `needs a session: large` for a plan of
    more than three tasks): change the brief to `lead: session`, and start a lead. Its plan talk
    needs the reviewer's pane, which a builder does not have.
  - *The owner asked for the plan only*: show the owner the plan through the settings'
    `tools.annotate`, and leave the task as it is until the owner says build or drop.
- **`held`**: the report holds one or more decisions that are the owner's, each in the form
  `stages/plan.md` gives under "A held decision". Take each through the `lem-gate` skill, then the
  `lem-panel` skill with the project's cast; the panel writes the card the owner sees. The card
  reaches him through `ask-owner`, which shows it as the settings' `tools.ask` says: that key
  outranks the way of asking either skill names. Put the report's run above the card, with whether it was reproduced or derived,
  and its one line on why the case became possible and how far the same cause reaches. Ask all
  held decisions of one task in one go. An answer to a choice the record holds as asked is
  written with `decisions.py answer SLUG N --chose OPTION --words TEXT`, or `--instead TEXT` for
  a decision of his that is none of the options, as the section above says; only an answer to a
  held decision of the report, which the record does not hold, is logged with
  `decisions.py log SLUG --by owner`. Then start a lead. The `lem-panel` skill asks for what users would see under each option; that is in
  the report, and what is missing there the lead adds, not you.
  A lead of the rare path that holds the task because a persona doubted its stories puts the
  stories and the answers on top of its report, with the line `the stories wait for the owner`.
  Put them to him as step 6 of "The interview and the stories" says, with the lead's read as the
  result on top, freeze his answer with step 7, and start a lead: it copies the approved stories.
  A task is also `held` when a step is the owner's to do and no decision at all: a trust prompt
  of the reviewer's agent, a command an agent is refused. Tell the owner that step as it is, with
  where he does it; it needs no gate and no panel. The lead goes on when the step is done.
- **`blocked`**: the report says what the lead could not settle and what it tried. A missing
  tool, a base branch that does not build, a conflict with another task: settle it, then start a
  lead. An approach that failed twice goes to a fresh builder with a different approach, as
  `stages/build.md` says: add one line to the brief, `do not repeat:` and what the report says
  the two tries assumed. When only the owner can settle it, write the state `held` and ask.
- **anything else**, or no new state block: the lead ended without its last step. Start a lead;
  it reads the state and the report and goes on. After a second such stop, write `blocked` and
  tell the owner what the reply or the session's screen shows.

After any of these, look at what is owed and at the queue. A task that ended with a
`ticket_owed` in `project.py tasks` gets those steps from the tracker now. Take the `queued` tasks in the order of their state's
time, leave out each one whose `after:` task is neither `landed` nor `dropped`, and start a lead
for the first that is left. Step 1 of "Start a lead" decides whether there is a place.
