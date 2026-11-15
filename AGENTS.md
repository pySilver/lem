# Lem

Lem is the `lem` skill and the skills it ships: one flow for a unit of work in any repository, with each project's settings kept
in that project's repository. `README.md` says what it does; this file says how to change it.

## Rules for a change here

- **The skill knows no project.** No repository, product, path or person of a real project appears
  in `skills/lem/SKILL.md`, the stage files, the harness files or the templates, except as the
  dated source of a measurement ("convertiser-server, 2026-11-14"). What a project needs to say,
  it says in its own `.lem/` folder or its own `AGENTS.md`.
- **A stage names a capability or a role, never a tool.** `spawn-builder`, `second-opinion`,
  `ask-owner`, `fan-out`, `show-page`, `load-skill`; the question gate, the persona panel, the
  review tool. `skills/lem/harness/README.md` is the contract. A tool's name belongs in the one
  harness file of its agent. A skill this repository ships is named by its name, which is the
  same in every agent.
- **A harness file exists only for an agent the contract was checked in.** Do not write one from
  another project's notes about an agent.
- **A number in a skill file carries its source and date.** A rule that rests on a measurement
  says so; a rule that rests on a guess says that instead (`EXPIRE_AFTER` in `review_queue.py`).
- **One stage file per subcommand, read only when it runs.** `SKILL.md` holds what is true in
  every stage. A rule that one stage needs goes in that stage.
- **Lem's stages and a lead's stages stay apart.** `plan` and `build` are a lead's; the others
  are Lem's. A step that reads a task's code or its diff goes to a lead or to a fresh agent,
  never into `new`, `land` or `review`.
- **Scripts are standard-library Python, 3.11 or newer**, print JSON for an agent to read, and
  refuse a wrong input with exit 1 and a message that names the fix. No silent default for a
  choice that is the owner's (`project.py init --existing`).
- **Documentation describes the current state.** No changelog paragraphs, no "previously".
- **A session with nobody at the terminal reads `docs/free-hour.md` first.** A setup links Lem
  from this clone's main checkout, so an edit there is live at once in every repository that
  uses Lem. Such a session works in a worktree, on a branch, and never pushes.

## The owner's rulings

Decisions the owner took on 2026-11-14. Each is reopened only by asking him. A quote is his words.

- **agterm is a hard dependency**, and so is the mailbox chat from its cookbook. Lem does not run
  outside agterm.
- **One Lem for one repository.** It coordinates many tasks there. No ability across repositories.
- **Build first, review after.** The persona panel and the review tool with the project's own
  lenses stay; a plan argued question by question and a review of every plain task do not.
- **Claude Code first.** The harness file for Codex comes after that works. The reviewer may be
  Codex or a second Claude; Codex as the builder is wanted later.
- **Opinionated and small.** A developer may use their own tool for a role (`tools.annotate`). Out
  of scope: a peer-planning flow, a skill-activation hook, language-server plugins, output styles,
  a brainstorm skill, clipboard helpers, a writing-style skill.
- **A project can close branches** (`branch.protected`): a rewrite that lands on a branch of its
  own never lands on the release branches.
- **The monitor is required**, "as beautiful as it is now or better" than peer-planning's: a board
  of all tasks, and the board of one task on request.
- **The free hour may edit Lem's skills on a branch of the clone.** It never pushes; the owner or
  a session merges.
- **The first run is in a scratch repository**, then in a real project.
- **The correction hook is an optional part.** Lem recommends the correction queue and uses it
  only when the owner agrees. The hook and the client of its model are Lem's code, with no path
  into another tool's folder, and the owner registers the hook with Lem's setup: "I guess this
  should not be a cc-tools behaviour but Lem code instead … and it should be possible to setup
  during installation of the skill if needed or any time later" (2026-11-15). The form built from
  it is the session's design: `skills/lem/scripts/jev.py`, linked as the `jev` command, and
  `setup.py --corrections on|off`, which the owner runs and no agent does.
- **The logo is the owner's pick** ("The Line in the Field"). Change it only on his word. The
  night palette of its dark-theme version is his pick too.
- **Each task of a plan gets a fresh builder** ("I usually start fresh executor for every task..
  since forever"). No threshold decides it.
- **A small defect outside the task is fixed at the end**, in the landing's closing pass, and a
  larger one is offered to him as a backlog item ("Polishing step fixes it in place, right away
  if thats cheap small fixes and offer a backlog filing otherwise").
- **A builder's question about the outcome goes to the personas**, not to the reviewer.
- **Lem asks through its question page**, and he does not have to type it: "every question goes
  via huddle, unless its something fixed choice, trivial, without additional context". The page
  was named huddle then; it is `lem-ask` now, his call `/lem ask` and the command `lem-ask` ("I
  like your solution for huddle, then name and the way out. `/lem ask` is awesome", 2026-11-15).
  A project's settings may name another way to ask (`tools.ask`), which the same sentence of his
  approves.
- **A shipped skill's name follows `/lem`** ("/lem interview-me sounds perfect like a callout
  command"). The form that was built from it, the id `lem-<name>` and the dispatcher in
  `SKILL.md`, is the starting session's design and open to him.
- **The README is in ASD-STE100 Simplified Technical English**: "We need to use ASD-STE100
  Simplified Technical English (STE) style to describe what we offer here". One topic in each
  sentence, 20 words at most in an instruction and 25 in a description, the active voice, no
  "-ing" verb form except in a technical name, a vertical list for steps. Technical names stay
  exact. This file and the skill files keep their own voice. The README also has diagrams,
  examples and pictures of the board; an example that no run produced says that it is an
  illustration, and a picture of demo data says so in its caption.
- **The rules of an existing project stay where they are**: "ok rules stays for now"
  (2026-11-15). An adopted project's style guide is the folder its agent loads by itself
  (`.claude/rules`); Lem reads it and never moves or links a file of it, because "being able to
  share project rules between Codex and Claude Code is a huge benefit, especially for review
  rounds". Lem has no command that moves linked settings: `/lem migrate` "becomes pointless as
  personas is used in one or two of our projects so we can move those ad-hoc there", and
  `init --existing link` is how an adopted project names its folders. "For now" is his: a move
  of the rules is a new decision of his, and nothing here prepares one. The form built from it
  is the session's design: `project.py rules`, the one match of a change against the files'
  `paths:` scopes, whose answer goes to a builder's brief, the reviewer's message and a review
  round; one format, Claude Code's, until a project needs another.
- **Linear only, and the local backlog stays local**: Lem supports Linear and no other tracker
  now, built so that another can be added. A backlog item is never mirrored to Linear, never
  needs a ticket, and Lem creates no ticket from one unless he asks. Status names are carried by
  name in the settings ("Linear allows me to configure that", about the branch name: Lem takes
  what the tracker gives and assumes no shape).
- **Another program's settings stay where that program keeps them**: "I think we should not
  touch other apps settings. `.personas` are different, as its our invention". The review tool's
  folder is `.revmux` in every project, new or adopted; Lem never moves, links or reshapes it.
  A lesson may still change a file in it: "I believe learn stage should be able to modify
  profiles, lenses etc and be honest with Human what changes and why". So the learn stage writes
  a lens line, a profile line or a rejected finding there, and names each changed file, what
  changed and why. The cast and the profile are Lem's and move to `.lem`.
- **A developer may ask with a tool of their own**: "We also need a way out, to let dev avoid
  huddle if they prefer their own asker UI?", and of the key built from it, "I like your solution
  for huddle, then name and the way out". `tools.ask`, beside `tools.annotate` and allowed in the
  machine's own file: Lem's page (the default), `terminal`, or the name of a skill or a command.
  `TOOLS` in `project.py` is the one place that names Lem's own tool for each role.
- **The question page is a part of Lem, not a tool the machine has or lacks**: "it does not need
  to mention that 'huddle' dependency is satisfied as it's an internal lem feature" (the page's
  name at that time). The machine
  check has no row for it and no page for the owner lists it; the setup reports its link.
- **webrev is the recommended way to mark up a plan or a document**, before plannotator
  ("`/webrev` is awesome and needs to be recommended to use over plannotator"), and it is not a
  part of Lem. On "a dependency with an offered installation, and no copy in Lem": "yep, just
  like other things that we want to recommend to a developer that makes life easier: agdoc,
  webrev, plannotator-tui, mailbox, revmux" (2026-11-15). So none of the five is copied into
  Lem. webrev, agdoc and plannotator-tui are recommended tools: the machine check has a row and
  a guide for each, `tools.annotate` defaults to `webrev`, and Lem installs one only on a
  developer's yes. The mailbox and revmux stay required, as he ruled before; that reading of
  his sentence is the session's, not his words.
- **OpenRouter is the one way to the Jev model for now**: on a direct API beside it, "Ok. Lets
  keep that way for now" (`docs/backlog/no-direct-jev-api.md`).
- **What must not go wrong is named by topic as well as by path, and the agent says whether a
  task is careful**: "we analyze the project, then we suggest what are the dangerous zones or
  topics and let user provide more ... Later at a plan time we can understand if it touches
  anything whats dangerous and needs to be taken carefully. Works better than just code path",
  and "it would be nice to get a suggestion from Agent whether its should be safe run or not,
  human can overlook real danger" (2026-11-15). The form is a design from those words:
  `flow.topics` beside `flow.careful`, proposed at onboarding; the lead's call with one sentence
  of why in the plan, the state and the report; a path match that no judgment overturns; the
  owner's "this one is careful" at any time before the landing. No code matches a topic.
- **The owner learns at the end what was decided for him, each with a short why**: "human needs
  to know about such events in the end and what choices were taken with short 'why'". The
  report holds those lines itself.
- **The README tells a command he types from one a job or Lem runs**: "commands like this should
  be mentioned that it's not supposed to be run by human, but cron or agent?". Each shipped skill
  has a "use it when" and an example there: "how I am supposed to understand which skill does
  what and when I should use it?". It does not name `.personas` ("nobody uses `.personas` but
  me").
- **A check of the tracker is no command of the owner's**: "looks a bit pointless to have a
  command for that. mcp is either working or not". The onboarding and the first read of a ticket
  make the check.
- **A page for the owner has the board's look**: of the first onboarding's page, "a bit old
  school ... just a bit nicer fonts, colors, paddings, round boxes etc.". Every page links
  `skills/lem/assets/lem.css`, and a stage builds its page from a pattern beside it.
- **The backlog is a part of Lem, and its view is a tab of the board**: "Backlog tab - I like
  this idea" (2026-11-15), on the answer that three stages already live on the backlog (the
  night plan picks from it, the closing pass files into it, an ask starts from it). So
  `lem-backlog` stays a shipped skill, not a recommended outside tool, and the board's second
  tab shows the items by who can act, with one action that gives an item to Lem as an ask. The
  content follows a page of his own; no code of it is used.
- **A board of example tasks says so on the page**, and a line that waits for him says where he
  answers. He took a fixture's line for a real one on 2026-11-14.

Designs taken on 2026-11-14 and 2026-11-15 after a question of the owner's. They are open to
him, and they are not his rulings until he says so:

- **`/lem annotate FILE` is the owner's verb for marking up**, after "then shouldn't it be
  `/lem annotate`?": it runs what `tools.annotate` names, as `/lem ask` is his verb for a
  question.
- **`/lem build` takes a plan file too, and lists the waiting plans when it gets no name**,
  after "why not `/lem build <path to plan>` instead?". `/lem review ID` takes one item, after
  "do I get to choose what to review from the list or what?".
- **The correction hook is registered for one repository first**, after "should we place a hook
  per project or globally?": the yes is one project's, and a hook in the home settings starts on
  every message in every repository. The session that carried his notes decided it and told
  him; the home form stays for an owner with many repositories that use Lem.

Open with him, and not built: Lem as a Claude Code plugin that a project enables, in place of
links ("can we make it more self contained? lem is aimed to be per-project companion"), which he
wants tested in a scratch repository first; and the order of landing and review ("I think its
very dangerous in most cases", of commits that reach the base branch before a review).

- **The reviewer's seat is a table**, after "should we or can we specify model and effort level
  of the reviewer?": `[seats.reviewer]` with `agent`, `model`, `effort`, `plan_effort`.
- **Lem brings its own builder agent**, after "it feels like we need to bring our own lem-worker
  agent which product may override? ... someone elses setup may have none": `agents/lem-builder.md`
  (his `lem-worker`; named for the role every Lem text uses), on Opus at high effort, overridden
  by a project's own file of the same name.
- **One machine may name its own reviewer for a while**, after "I may want to have a session
  based reviewer ... Codex is down or I run out of tokens there": `.lem/project.local.toml`,
  untracked, read from the main checkout, limited to `[seats]` and `[tools]`, written by
  `/lem reviewer`. Lem never changes the seat by itself.

## Checks

```bash
bash tests/test-lem.sh        # Lem's scripts, in throwaway repositories; loads the board in headless Chrome when one is installed
bash tests/test-gate-panel.sh  # the gate's log and the panel's cast, with the paths a project's settings name
bash tests/test-ask.sh         # lem-ask's spec checks and every template; loads pages in headless Chrome when one is installed
shellcheck tests/*.sh
```

A change to a script comes with its test. A change to a stage file has no test: its test is a
real task, so say in the commit which task showed the need.

## Layout

- `skills/lem/SKILL.md`: the entry point and what holds in every stage.
- `skills/lem/stages/`: one file per subcommand.
- `skills/lem/harness/`: the capability contract and one file per agent.
- `skills/lem/scripts/`: `project.py` (a repository's settings, task state and the event log),
  `doctor.py` (the machine), `review_queue.py` (landed changes that wait for a review),
  `board.py` (opens the board), `land.py` (the landing, one refusable step at a time),
  `corrections.py` (the optional queue of the owner's corrections: its hook, and what a retro
  reads), `jev.py` (the client of the Jev decision model, which the hook runs by its path and
  the setup links as the `jev` command).
- `skills/lem/assets/board.html`: the board of all tasks and of one task, one page for both, and
  on the board of all tasks a second tab for the backlog.
  `lem.css` beside it is the look every page of Lem shares: its colors, its type, its header
  and the blocks of a page to read. `handover.html` is the pattern of the onboarding's page.
  A new page for the owner links `lem.css` and brings no style of its own.
- `skills/lem/templates/`: the shapes onboarding fills.
- `skills/lem/prompts/`: the standing briefs of a task's lead, of the three builders of a
  landing, and of the reviewer.
- `docs/`: `free-hour.md` (how an unattended session may change Lem), `linear.md` (how a
  project connects Linear), and `backlog/`, Lem's own deferred work.
- `scripts/setup.py`: the setup script. It links the skills, the builder agent and the `lem-ask`
  and `jev` commands from this clone into a home directory, never over something else, and runs
  the machine check. `--corrections on|off` registers the hook of the correction queue in the
  agent's settings or takes it out, and is the owner's to run. With `--project DIR` it links into one repository only. Use that for a trial: links in
  the home directory show Lem to every repository on the machine, also to one where an older
  flow still runs.
- `agents/lem-builder.md`: the builder, as a Claude Code agent definition. Its body is the
  builder's standing rules; `harness/claude-code.md` says how it is used and overridden.
- `skills/lem/references/`: the catalog of published style guides.
- `assets/lem.svg`: the logo, and `assets/lem-mark.svg`: the figure alone, for an icon.
  `assets/lem-night.svg` and `assets/lem-mark-night.svg` are the same drawings in the night
  palette, written by `assets/night.py`; the README shows the night one in a dark theme.
- `assets/screens/`: the README's pictures of the board, for a light and a dark theme, at two
  device pixels for each pixel. `board-*` and `task-*` are renders of
  `skills/lem/assets/board.html` over demo data, and so is `backlog-*`; `real-task-*` is the board of the first task
  that ran through Lem, over its real event log.
- `skills/lem-ask/`, `skills/lem-backlog/`, `skills/lem-interview-me/`, `skills/lem-dialectic/`,
  `skills/lem-root-cause/`, `skills/lem-release/`, `skills/lem-last-tag/`, `skills/lem-pr-review/`,
  `skills/lem-gate/`, `skills/lem-panel/`, `skills/lem-linear/`: the skills Lem names and ships.
  `NOTICE` says where each came from.

## The shipped skills are copies, not yet under the rules above

Each was copied from where it worked and changed only as far as the new layout needed. Their text
still names Claude Code's tools, `skills/lem-backlog` uses `${CLAUDE_SKILL_DIR}`,
and lem-ask's Stop hook (`skills/lem-ask/hooks/hooks.json`) is registered by nothing. Bring one under
the capability rule when a second agent has to run it, not before.

The set is deliberately small. A tool with its own life (revmux, agterm, the mailbox chat, webrev,
agdoc, cronn, plannotator, Codex) is checked for by `doctor.py` and never copied in, and a project that prefers its own tool for a
role says so in its settings or its `AGENTS.md`.
