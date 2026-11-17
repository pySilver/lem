# Inside Lem

This page gives the parts of Lem that a day of work does not need. They are the agents and their
briefs, the files of a task, the state folder, the event log, the board and the naps.
`skills/lem/SKILL.md` holds the full rules.

The name is from Stanisław Lem. In the logo, Lem is the tall figure in the middle. It builds
nothing. It holds the line that the other agents work on, and it answers to you for all of them.

## Two levels

```mermaid
flowchart LR
    you([You]) <-- requests, choices, reports --> lem[Lem<br/>one session for the repository]
    lem -- starts, reads the state and the report --> leadA[Lead of a full change<br/>a builder]
    lem -- starts for a small change --> one[The one builder<br/>of a small change]
    lem -- opens for a careful or large plan, closes after the talk --> leadB[Defender of the plan<br/>a companion session]
    leadB <-- the plan talk, before any code --> rev[Reviewer<br/>in the other pane]
    leadA -- each task of the plan --> b1[Builder: task 1]
    leadA -- each task of the plan --> b2[Builder: task 2]
    lem -- checks and proposes one branch at a time --> pr[(A pull request)]
```

There is one Lem for one repository. It is the session where you type `/lem`.

- **Lem** takes the requests, opens each task, and takes each branch through the checks and the
  review to a pull request. It writes no code.
- **Lem holds no details of a task.** It reads the request, the newest state block, the report,
  and the facts of the scout or the investigator. It does not read the plan, the diff or the
  output of a builder. Lem is the one context that knows each task. If it fills with the code of
  one task, it loses the others.
- **A lead** is a builder that owns one full change from its plan to its report. It gives each
  task of its plan to a new builder, also when the plan has one task. A lead never asks you a
  question.
- **A small change has no lead.** Lem starts its one builder directly.
- **The defender** is the agent of a companion session that Lem opens for the plan talk. The
  reviewer is in the other pane. The two argue the plan through the mailbox. Lem closes the
  companion after the talk, and a new builder leads the build.
- **A lead or a defender tells Lem at once** when a choice waits for you. Lem also looks for such
  choices at each of its turns, because a message can get lost.

## The agents and their briefs

Each agent gets a short brief that names a fixed text in `skills/lem/prompts/`. The builder agent
is `lem:lem-builder`, from `agents/lem-builder.md` of the plugin, on Opus at high effort. Its body
holds the rules of each builder. A project can replace it with its own
`.claude/agents/lem-builder.md`.

| Agent | Brief | What it does |
| --- | --- | --- |
| the scout | `scout.md` | reads the code around a request during the interview, and gives facts, not a plan. It changes nothing |
| the investigator | `investigator.md` | reproduces a bug as a test that fails and finds its cause, or answers a question |
| the builder of a small change | `small.md` | makes the one change, holds its criterion, and checks the topics before it commits |
| a lead | `lead.md` | writes the plan and starts a builder for each task |
| the defender | `defender.md` | holds the plan talk for the plan, with the reviewer |
| the reviewer | `reviewer.md` | the other side of the plan talk, in the other pane |
| a builder of the landing | `landing.md` | the polish pass, the repair of a conflict or of a failed check, or the fix of the findings of a review |
| the review agent | `review.md` | makes the careful call on the diff, selects the size of the review, runs it, and writes its record |

The stage files tell each role what to do: `skills/lem/stages/new.md`, `plan.md`, `build.md`,
`talk.md`, `land.md`, `init.md`, `learn.md` and `night.md`. A lead reads `plan.md` and
`build.md`. Only the defender reads `talk.md`.

`skills/lem/harness/README.md` is the contract between the stages and an agent. A stage names a
capability, for example `spawn-builder` or `ask-owner`. `skills/lem/harness/claude-code.md` says
what each capability is in Claude Code.

## The command `lem`

The scripts of Lem are one command, `lem`, which the plugin puts on the `PATH` of the agent. The
agents run it, and you do not type it. Because it is one command, the permission rule
`Bash(lem *)` covers all scripts, also after an update of the plugin.

- `lem NAME ARGS...` runs one script, for example `lem land start SLUG` or `lem project show`.
- `lem NAME --help` gives the help of that script.
- `lem help` lists the names: `project`, `land`, `criteria`, `decisions`, `board`, `doctor`,
  `corrections`, `experts`, `cast`, `gate-log`, `triage`, `release-platform`, `release-version`
  and `release-notes`.
- `lem version` prints the folder of the plugin, and its commit when that folder is a git clone.

The question page is a command of its own, `lem-ask`, and so is the client of the Jev decision
model, `lem-jev`.

## Where things are

```mermaid
flowchart TD
    subgraph checkout [The main checkout]
        toml[.lem/project.toml<br/>the settings, in git]
        local[.lem/project.local.toml<br/>the settings of this computer, not in git]
        profiles[.lem/profile.md, personas/, lessons.md<br/>in git]
        plans[docs/plans/ and docs/backlog/<br/>in git]
        wt[.lem/worktrees/<br/>one worktree for each task, not in git]
        state[.lem/state/<br/>the state of Lem, not in git]
    end
    wt -. writes the state .-> state
    state --> board[The board]
```

- The settings of a project are in its repository. `/lem init` writes them.
- `profile.md` says what the project is. `lessons.md` holds the corrections that have no better
  place. A correction of a stage of Lem goes there too, as a line that starts with the name of the
  stage. Lem reads the file before each command.
- `personas/` has one file for each person that a change affects, for example a customer. Each
  project of Lem has two personas or more. `/lem init` writes them from your answers.
- A repository that already has `.claude/rules` keeps that folder. It is the style guide, and the
  settings name it. Lem makes no copy and no link.
- `.revmux/` is the folder of the review tool. `/lem init` puts the starter set of that tool
  there. A lesson can change a file there, and Lem tells you each change and why.

## The state folder

The state of Lem is in `.lem/state/` of the main checkout, the first worktree that git lists. Each
worktree writes there. Git does not track the folder, and it stays after Lem removes a worktree.
`lem project state-dir` prints its path.

- `tasks/`: one folder for each task;
- `events.jsonl` and `events.js`: the event log, and the same log for the board;
- `watch.js`: the last look of the watch at the open pull requests;
- `landing.lock`: the lock of the one task in the landing;
- `alone.lock`: the lock of the commands under `checks.alone`;
- `decide-gate.jsonl`: the log of the question gate;
- `backlog-triage.json` and `backlog.js`: the sort of the backlog, and the backlog for the board;
- `corrections.jsonl`, `corrections-reviews.jsonl`, `corrections.log` and `corrections-claims/`:
  the correction queue;
- `night/`: the night reports;
- `retros/`: the proposals of a retro that ran with nobody there;
- `experts/`: one folder for each question that you gave to the experts with `/lem ask-expert`;
- `personas-cast/` and `personas-profile/`: the copies of the personas and of the profile that a
  persona panel read;
- `naps/`: one folder for each nap;
- the page of the board and its data files.

## The files of a task

`lem project task-dir SLUG` makes the folder of a task in `.lem/state/tasks/`, and prints it.

| File | What it holds | Who writes it |
| --- | --- | --- |
| `ask.txt` | your words as you gave them | Lem |
| `task.md` | the request, its type, the result, the "done when" lines, and what is out of scope | Lem |
| `ticket.txt`, `ticket-steps.txt` | the id of the ticket, and what Lem did to it | Lem |
| `scout.md` | the facts of the scout | Lem, from the reply of the scout |
| `investigation.md` | the report of the investigator | the investigator, or Lem from its reply |
| `directions.md` | what you named in the interview, one line each | Lem |
| `outside.md` | the defects outside the request that the interview found | Lem |
| `criteria.md` | the acceptance criteria as Lem writes them for your yes; for a small change, the one criterion and its test line | Lem, and the builder of a small change |
| `criteria.json` | the approved criteria, word for word, with a digest, who approved them and when | `lem criteria approve` only |
| `brief.md` | the brief of the lead, or of the builder of a small change | Lem |
| `state.md` | the state blocks, newest first | Lem and the lead, through `lem project state` only |
| `report.md` | what the lead did, and what it leaves to Lem | the lead that stops |
| `decisions.jsonl` | each decision, each choice and its answer, and each change of a criterion | `lem decisions` only |
| `experts/` | the brief and the two answers of the experts for each choice | the `lem-ask-expert` skill |
| `reports/` | one file for each builder of a plan | each builder |
| `landing.json`, `polish.json`, `gate/`, `read.json`, `reviews/` | the record of the landing, the input of the polish pass, the output of each check, and each review | `lem land` and the review agent |
| `notes.md`, `pr.md` | the notes of Lem, and the text of the pull request | Lem, and `lem land propose` |

A file that a later step needs goes into the task folder too, never into `/tmp`.

## The states of a task

| State | Means | Who acts |
| --- | --- | --- |
| `queued` | no lead runs: the limit of tasks was reached, or the task needs the result of the task that its `after:` line names | Lem, when a place is free or that task ends |
| `building` | a lead plans or builds, or a builder examines a bug or a question | the lead, or the investigator |
| `planned` | the plan is committed, and nothing builds it | Lem opens the plan talk, or you read the plan |
| `held` | it waits for you: the criteria, one more fact, a step that is yours, or a step that nobody can undo | you, through Lem |
| `blocked` | the lead stopped on something that it could not settle | Lem |
| `ready` | the report is written, and the branch waits for its checks | Lem |
| `landing` | the checks and the review run, or a builder repairs what they showed | Lem |
| `open` | a pull request is open, or the branch is ready to land | you merge; Lem, if the project lets an agent merge |
| `landed` | it is on the base branch | nobody |
| `drafted` | a plan of the night waits for your word | you |
| `dropped` | nobody will build it, or its pull request was closed with no merge | nobody |
| `answered` | it ended with a report and nothing to merge | nobody |

A decision of yours never puts a task in `held`. It waits its time while the other work continues.
`landed`, `dropped` and `answered` are the end. A task in one of them takes no new state and no
new lead.

## The event log

Each state block is also an event in `.lem/state/events.jsonl`, with the newest commit of the
worktree. The checks, the reviews, the decisions and the proposals are events too. The board draws
this log, so nobody runs a second command for it.

The start of each stage is an event, so that the time card of the board has a start and an end
for each span:

| Start | End | Who logs it |
| --- | --- | --- |
| `interview.start` | the first `criteria.read.start` or `criteria.approved` | Lem |
| `scout.start` | `scout` | Lem |
| `criteria.read.start` | `criteria.read` | Lem, or the lead for a complete request |
| `investigation.start` | `investigation` | Lem |
| `builder.start` | the next state block or step of the landing | the agent that starts the builder |
| `plan.talk.start` | `plan.talk` | the defender |
| `polish.start` | `polish` | `lem land` |
| `gate.start` | the last `gate` or `task.red` of that run | `lem land` |
| `review.start` | `review` | `lem land` |

## The board

`lem board` opens the board as a page in agterm, next to the session of Lem. The page is
`skills/lem/assets/board.html`, and `skills/lem/assets/lem.css` gives the look of each page of
Lem.

- The board reads files in the state folder, and it needs no server. It reads the event log again
  each two seconds.
- Each task is in a lane of who acts next. A card shows the status, the lead, the newest commit,
  the result of the checks and the newest review. A task that Lem proposed shows green or not
  green.
- The board says when Lem last checked the open pull requests, for example "checked 40s ago".
  When the last look is older than three intervals of the watch, or the watch ended, it says
  "nobody watches the pull requests" and tells you to type `/lem`. A page cannot ask GitHub
  itself.
- The board of one task adds its acceptance criteria with the result of their tests, and its state
  blocks. It also shows each check, each review with who answered, and where the time went.
- A line that waits for you says where you answer.

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="../assets/screens/task-dark.png">
    <img src="../assets/screens/task-light.png" alt="The board of one task that landed: its phases, where the time went for you, the builders and the personas, its acceptance criteria, its checks and its review" width="900">
  </picture>
</p>

*The board of one task, with demo data. The task is an example.*

- The second tab is the backlog. Its groups are "Needs you", "An agent can take it", "Waits for
  something" and "Decided against". An item whose place in the code is gone has a mark. You filter
  the items with words.
- Each backlog item has one action, "Start a task". After you confirm, it types `/lem new` and the
  path of the item into the session of Lem.

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="../assets/screens/backlog-dark.png">
    <img src="../assets/screens/backlog-light.png" alt="The backlog tab of the board: the items in groups by who can act" width="900">
  </picture>
</p>

*The backlog tab of the board, with demo data. The items are examples.*

- `lem board --no-open` writes the files again and opens nothing.
- The board is local. A second person with a second clone does not see it.
- `lem board --demo` marks the tasks of the state folder as examples, and the page then says so.

## Naps

Naps are an optional part of Lem. `naps.on = true` turns them on ([settings.md](settings.md#naps)).
A nap costs one short agent session, and nobody has shown that naps help.

- Lem takes a nap when a task ended or when only your word is left, and the last nap is
  `naps.gap_hours` old. Nothing waits for the nap.
- `/lem nap` starts a nap on your word, also when the naps are off.
- A nap is a new agent in the background. It reads the records of the recent tasks, dreams, makes
  one thing, and writes a waking note.
- The nap runs no command. It reads and writes only in the state folder, and it changes nothing in
  the repository.
- Each nap has a folder `.lem/state/naps/TIME-WORDS/` with `dream.md`, the thing it made, and
  `waking.md`. Lem removes a folder that is older than `naps.keep_days`.
- The board gets a third tab, Dreams, when a nap exists. It shows the newest naps.
- The retro reads the waking notes since the last retro. A note is only a candidate for a lesson.

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="../assets/screens/dreams-dark.png">
    <img src="../assets/screens/dreams-light.png" alt="The Dreams tab of the board: the newest naps, each with its dream, the thing it made and its waking note" width="900">
  </picture>
</p>

*The Dreams tab of the board, with demo data. The nap is an example.*

## The skills that Lem uses by itself

Each skill that comes with Lem has the id `lem-<name>`, and `/lem <name>` starts it. No skill
starts by itself from your words. Lem uses these skills without a command from you:

| Skill | Use |
| --- | --- |
| `lem-ask` | each question that asks you to choose or to approve, as a page |
| `lem-gate` | the question gate: it decides if a question must go to you at all. It starts in shadow mode: it logs its verdict next to your answer, and decides nothing |
| `lem-panel` | the personas of the project: an agent answers as each person that a decision affects |
| `lem-ask-expert` | each choice that waits for you: two experts answer it at the same time, and they change no file |
| `lem-linear` | the tickets of Linear. Lem checks the connection in `/lem init`, and again when it reads a ticket |
| `lem-interview-me` | the method of the interview |
| `lem-root-cause` | the method of the investigator, and of a builder after two failed tries |
| `lem-dialectic` | a claim that a plan rests on, before the plan takes it |
| `lem-backlog` | the format of a backlog item, and the sort of the backlog for the board |
