# Lem

Lem is the `lem` skill and the skills it ships: one flow for a unit of work in any repository, with each project's settings kept
in that project's repository. `README.md` says what it does, the pages in `docs/` say how it
works, and this file says how to change it.

## Rules for a change here

- **The skill knows no project.** No repository, product, path or person of a real project appears
  in `skills/lem/SKILL.md`, the stage files, the harness files or the templates, except as the
  dated source of a measurement ("convertiser-server, 2026-11-14"). What a project needs to say,
  it says in its own `.lem/` folder or its own `AGENTS.md`.
- **A stage names a capability or a role, never a tool.** `spawn-builder`, `second-opinion`,
  `ask-owner`, `fan-out`, `show-page`, `load-skill`; the question gate, the persona panel, the
  review tool. `skills/lem/harness/README.md` is the contract. A tool's name belongs in the one
  harness file of its agent. A skill this repository ships is named by its name, which is the
  same in every agent: `lem-NAME`, which the owner calls as `/lem NAME`. Every skill, agent and
  command of the plugin carries Lem's name, so that none meets a developer's own.
- **A harness file exists only for an agent the contract was checked in.** Do not write one from
  another project's notes about an agent.
- **A number in a skill file carries its source and date.** A rule that rests on a measurement
  says so; a rule that rests on a guess says that instead (`READ_AT` in `land.py`).
- **One stage file per subcommand, read only when it runs, and a part that only one path reads
  is a file of its own.** `SKILL.md` holds what is true in every stage. A rule that one stage
  needs goes in that stage. A part of a stage that only one of its paths needs (the interview,
  an investigation, the polish pass) is a file beside it, and the step that chooses the path
  names that file in one line: a task on the fast track reads nothing that only the standard track needs.
- **A task's phases stay apart.** `plan` and `build` are the lead's, in the build phase. A step
  that reads a task's code or its diff goes to the lead, a builder or a fresh agent (the
  investigator, the review, the merge agent), never into the shape (`new`, `interview`) or the
  landing (`land`).
- **Scripts are standard-library Python, 3.11 or newer**, print JSON for an agent to read, and
  refuse a wrong input with exit 1 and a message that names the fix. No silent default for a
  choice that is the owner's (`project.py init` with no base it can tell asks for `--base`).
  Every string a script prints or writes for a person, its `--help` too, says "the owner";
  comments, function docstrings and the stage files keep their voice.
- **A change is measured by what it costs a developer on a small task** (the touches it asks of
  him, the waits, the agents it starts) as well as by what it guards.
- **Documentation describes the current state.** No changelog paragraphs, no "previously". A
  chart in `README.md` or `docs/` writes each node's and each edge's text in double quotes, and is
  drawn once before it is committed.
- **A maintainer's session with nobody at the terminal reads `docs/free-hour.md` first.** It works in a
  worktree of this clone, on a branch, and never pushes: `main` of this repository is what every
  project's next update of the plugin installs. The scheduled
  `/lem night` of this repository is such a session too, and it opens no task here: asked on
  2026-11-21 whether a night here may open pull requests, the owner answered "A3 no".
- **Lem is not released, so a change keeps no reading of the form before it.** A change to the
  settings, a record, an event, a state or a command reads and writes the new form only, and the
  maintaining session corrects the repositories that use Lem by hand. When Lem has users, this
  rule changes.
- **A new ruling of the owner is one bullet of `docs/rulings/rulings.md`**, under the heading of
  its group: the rule in one sentence, in bold; only where the sentence alone could mislead, at most
  three lines more, with his words in quotes only where they are the rule or its limit; his day in
  parentheses at the end. No history in a bullet.
- **A ruling that replaces another takes its bullet's place**, and git keeps the old one. A ruling
  that changes a part of another changes that bullet's words. A bullet leaves the list only on the
  owner's word.
- **A rule that a test or one place now holds may move to `docs/rulings/history.md`, on his
  word**: a line of its first part with the test's name, which `tests/unit/test_agents_md.py` finds
  or fails, or a line of its second part with the place's path. A rule goes back to the list when
  its test or its place no longer holds it: the session that sees it moves it at once and tells him.
- **A new choice of the maintaining session is a bullet of the list's last part**, "Choices of the
  maintaining session", with `decided` before its day, **when no code, test or text can show it**;
  otherwise it is in the message of the commit that made it. The `decided` lines of the history are
  the choices that were files until 2026-11-21 and that a test or one place holds.

## The owner's rulings

`docs/rulings/rulings.md` is the list of the owner's rulings in force, one bullet for each under
the twelve groups, and in its last part the choices of the maintaining session that are open to
him. Read it whole once in a session, before a change to Lem. A change that adds a part to Lem (a
skill, a hook, a command, a key of the settings, a tool it needs) reaches each bullet of "What Lem
is, and who it is for". A ruling is reopened only by asking him.

`docs/rulings/history.md` holds the rulings and choices that left the list, each still in force:
each with the test that holds it, or the one place that says it. Read it when a change touches a
test or a place it names.

## Checks

```bash
bash tests/all.sh              # every suite below at the same time, one log each, a line of ok, FAIL and SKIP per suite
python3 tests/pick.py --base main  # the suites to run for what the branch changed (or name the files); all.sh still runs before main moves
python3 -B -m unittest discover -s tests/unit  # the unit level: one file for each script, its rules called in one process; all.sh runs it as the suite unit
```

The loop: the unit level after each edit; while a task is in work, only the one block that holds
the journey it changes; the blocks that `tests/pick.py` names once for a task, at its end;
`tests/all.sh` once before `main` moves. A block is never run before a change to count it: the
counts of the last full run are the before. A rule that takes facts and returns a result is a
unit case, a call of its function; a fact only git can show is a check in a block, in a throwaway
repository. A journey is run once, not once for each input. A check that makes a dated name or
reads the time keeps the value it made and checks that value, and it never counts on a step that
takes under a second, since `tests/all.sh` runs every suite at once.

Each suite says how many checks it holds (`collected N`, `tests/checks.sh`), and a check that
cannot run here prints a `SKIP` line of its own. A suite whose `ok` and `SKIP` lines do not add up
to that count fails, and so does one that runs over its time limit (`LEM_TEST_LIMIT`, 30 minutes).
With `LEM_TEST_TIMES=FILE` each check of a block appends its seconds to FILE, so one run shows
which checks hold the time.

One suite alone, in the order of `tests/all.sh`:

```bash
bash tests/lem-settings.sh     # the settings and the places of what Lem reads, a task's state and the event log, the rule picker, the criteria and their check on the base (each lem-* block sources tests/lib.sh)
bash tests/lem-machine.sh      # the machine check, the correction queue and its hook, the plugin's files
bash tests/lem-state.sh        # the state folder git never sees, and the owner's status
bash tests/lem-decisions.sh    # a task's decisions, each taken by a level of the ladder, and the circuit breaker from its trip to his help, park, drop and resume
bash tests/lem-land-shop.sh    # the landing from `ready` through the checks and one read to a pull request, the merge agent's read and the merge, on the stand-in for gh
bash tests/lem-land-local.sh   # the landing in two halves of about equal time: decisions, criteria and the personas' read in the pull request's text here,
bash tests/lem-land-review.sh  # and the polish pass, the review, the bar, what makes a request careful and who merges it here
bash tests/lem-land-backlog.sh # what a review saw outside the change, filed as backlog items
bash tests/lem-land-github.sh  # the forge's own cases, and a remote that is not GitHub, which lands nothing
bash tests/lem-land-guards.sh  # the landing's guards and refusals, each next step run as the refusal names it
bash tests/lem-land-small.sh   # the fast track's landing, and what keeps it safe
bash tests/lem-serial.sh       # checks.serial under the repository's one lock, and checks.setup in a new worktree
bash tests/lem-naps.sh         # the [naps] settings and lem project may-nap
bash tests/lem-command.sh      # the command lem: each name, its arguments, stdin and exit status, help, and that no text names a script by its path
bash tests/lem-picker.sh       # the task picker, with a stand-in for agtermctl
bash tests/lem-session.sh      # a task's own session (lem session) with a stand-in for agtermctl, and the copy of the talk
bash tests/lem-serve.sh        # the board server and lem board over HTTP, on the afternoon of tests/board-showcase.py: the routes, each page's words, the stream, the jump to a session, the start on demand
bash tests/lem-board-act.sh    # the owner's acts from the board, and the server's duties across tasks, with a stand-in for lem session
bash tests/lem-peers.sh        # two machines under one address: two board servers on this Mac, a join, the loop guard, a machine that does not answer
bash tests/test-gate-panel.sh  # the panel's cast, in its one place
bash tests/test-ask.sh         # lem-ask's spec checks and every template; loads pages in headless Chrome when one is installed
bash tests/test-ask-expert.sh  # the experts' brief of a question in words, its folder and the record of each answer, one expert alone; no expert runs
bash tests/test-site.sh        # the page on GitHub Pages, from pages.yml's own copy step; its drawn page in headless Chrome when one is installed
bash tests/shellcheck.sh       # ShellCheck over tests/*.sh, one check for each file, or over the files named
python3 tests/pick.py --check  # the map of tests/pick.py: every file read by a suite, every suite in all.sh
bash tests/test-lem.sh         # every lem-* block at the same time, with its output in order; all.sh runs each as a suite of its own
```

A change to a script comes with its test. A change to a stage file has no test: its test is a
real task, so say in the commit which task showed the need.

To run a clone of Lem in one session, without the plugin's install, load its folder as the plugin
(Claude Code 2.1.325, 2026-11-17: the session listed every `lem:` skill and `lem:lem-builder`):

```bash
claude --plugin-dir /path/to/lem   # the plugin from this folder, for this session only, with its skills, agent, commands and hooks
```

A task's session that `lem session open` starts gets `--plugin-dir` with the clone's folder when
no Lem is installed (`plugin_dir` in `session.py`). With an older Lem installed for the project, the
`lem` on that session's `PATH` is still the installed one (lem-scratch, Claude Code 2.1.330,
2026-11-21): a real task is tried with the release installed.

## Layout

Each script's module docstring says what it does and why; this list says where each thing is.

- `skills/lem/SKILL.md`: the entry point, what holds in every stage, and "One session for each
  task".
- `skills/lem/stages/`: one file for each subcommand, read only when it runs. `new.md` opens a task
  in its own session, and its "The request" and "The fast track" are that session's first steps;
  `interview.md` (the interview and the criteria) and `investigate.md` (a bug, a question) are the
  rest of the shape. `start.md` starts the build, `plan.md` and `build.md` are the lead's, `talk.md`
  is the plan talk, which only its defender reads, `ladder.md` a decision in doubt and `breaker.md`
  the circuit breaker. `land.md` is the land phase, `polish.md` its step 3, on the standard
  track only, and `conflict.md` what an open pull request takes when GitHub calls it conflicting.
  `status.md`, `away.md`, `correct.md`, `park.md`, `night.md`, `init.md`, `learn.md`
  and `nap.md` are the owner's other commands and the scheduled ones.
- `skills/lem/prompts/`: the standing briefs: `session.md` (a task's session: what it reads, a
  change of phase, a wake-up, what it never does), `lead.md`, `defender.md` and `reviewer.md` (the
  plan talk's pair), `scout.md`, `investigator.md`, `small.md` (the fast track's one builder),
  `landing.md` (a builder of a landing), `review.md` (the review before a pull request), `merge.md`
  (the merge agent), `writing.md` (how a document for the owner is written, from the interview to
  the merge agent) and `nap.md`.
- `skills/lem/templates/`: `profile.md` and `persona.md`, which onboarding fills; `handoff.md`, the
  hand-over between two agents of a task; `breaker.md`, the breaker's document.
- `skills/lem/harness/`: the capability contract, `README.md`, and one file for each agent, a core with
  its parts in a folder of the agent's name (`claude-code/`).
- `skills/lem/scripts/`, each a command of `lem` or a module the commands share:
  - `project.py` (`lem project`): a repository's settings and the one place of each file Lem reads
    beside them (`PLACES`), a task's state and directory, the event log, the owner's status and its
    watch, `waiting` (the one list of what waits for the owner), `prune` (what the state folder
    keeps, `state.keep_days`, which one machine's `.lem/project.local.toml` may set for itself), and
    the machine's `load` and `handoff` numbers.
  - `session.py` (`lem session`): a task's own session in agterm, its change of phase, its wake-up,
    the handoff's check and the copy of the talk; `session_hook.py`: the plugin's `PreCompact` and
    `SessionStart` hooks of a task's session (every source: the record of each Claude Code session of
    the task, and after a compaction the task's files); `lem_tokens.py`: the tokens a task's Claude
    Code sessions spent, from their transcripts, for the merge brief.
  - `land.py` (`lem land`): the landing, one refusable step at a time, from `ready` through the
    checks and the review to a pull request on GitHub, the merge agent's read, the merge and the
    cleanup.
  - `criteria.py` (`lem criteria`): a task's acceptance criteria, and the check that each one's
    tests pass on the branch and fail on the base. `decisions.py` (`lem decisions`): a task's
    decisions, each taken without the owner, and its breakers.
  - `serve.py` (`lem serve`): the machine's one board server, with the owner's acts, the jump to a
    session, the tailnet door and the duties across tasks, the hourly `lem project prune` of each
    workspace among them; `serve_hook.py`: the SessionStart hook
    that starts it. Its parts: `lem_board_model.py` (the model, pure functions over the files),
    `lem_board_pages.py` (the pages of a workspace), `lem_board_task.py` (the board of one task),
    `lem_artifacts.py` (a task's files on one map), `lem_html.py` (`h()`, which escapes every text),
    `lem_push.py` (the notifications) and `lem_peers.py` (another machine joined with `--join`).
  - `board.py` (`lem board`): makes sure the server runs and opens a board, or with `--page FILE`
    any page of Lem, as a companion. `picker.py` (`lem picker`): agterm's picker over the tasks.
  - `doctor.py` (`lem doctor`): the machine check. `corrections.py` (`lem corrections`): the
    optional queue of the owner's corrections and its hook. `jev.py` (`lem-jev`): the client of the
    Jev model.
  - `lem_state.py` (the state folder and Lem's home folder), `lem_plans.py` (a plan's file
    name), `lem_sibling.py` (a sibling's command in the same process) and `lem_python.py` (a
    Python of 3.11 or newer for `bin/lem` and the hooks).
- `skills/lem/assets/`: what `lem serve` sends under `/assets/`. `board.css` is the board's look,
  the phone's too; `lem.css` and `lem.js` are the look and the palette every page of Lem shares, and
  a new page for the owner links both and brings no style of its own. `push.css` and `sw.js` are the
  notifications', `icons/` the board's icons, and `handover.html` the pattern of the onboarding's
  page. `vendor/` holds what `tools/board-kit` builds: `board-app.js`, the board's one script,
  `board-icons.json` and `mermaid.min.js`.
- `tools/board-kit/`: the maintainer's build of `vendor/`, which nobody who installs the plugin
  runs: the built files are committed. Its `README.md` says how to build and how to add a Stimulus
  controller to `controllers/`.
- Lem's home folder, `$XDG_CONFIG_HOME/lem` or `~/.config/lem` (`lem_state.config()`):
  `owner.jsonl`, the owner's away and back; `machine.toml`, this machine's settings, `[load]`,
  `[serve]`, `[peers]`, `[seats]` (`merger` and `session`, for a repository whose settings name
  none) and `[handoff]`; `workspaces.json`, the repositories the server shows; and what the server
  and the checks keep there: `serve.lock`, `serve.log`, `load.lock`, the push key `push-key.pem` and
  the devices `push.json`.
- `.lem/`: Lem's own settings, profile, cast and lessons, in the places every repository has them.
  Its `state/`, which git ignores, is the state of a repository's Lem: the tasks, the event log,
  the night reports, the naps, the experts' folders, a panel's copies, the panels' folders
  (`panels/`, which `lem cast run-dir` makes), and `forge.json`, the board
  server's last look at GitHub. `lem project prune` removes from it what is older than
  `state.keep_days`, and makes the events of each task that ended before then one summary event of
  the log. `.lem/worktrees/` holds
  the tasks' worktrees. `.revmux/` is the review tool's configuration for this repository.
- The naps, an optional part: `prompts/nap.md` is written after the owner's own nap routine and
  keeps its voice (a change is tried with one real nap, and its dream is read: a brief that makes a
  report of it is wrong); `stages/nap.md` starts one and `lem project may-nap` says whether one
  may. No page shows them; the retro reads their waking notes.
- `docs/`: the guides the README links, each in STE like the README, each with one job and an aim
  of under 800 words, or a bit more when needed: `flow.md` (how a task goes, with the one diagram), `when-lem-needs-you.md`,
  `pull-request.md` (what green means, the merge review, the merge, a conflict), `board.md` (the
  board, the phone, two machines under one address, the server), `install.md`, `linear.md` and
  `github-issues.md`; and `settings.md`, the reference, one table for each table of the settings,
  one to one with `project.py` (`tests/lem-settings.sh` checks it). How Lem works inside is in this file and the
  skill. Beside them: `free-hour.md` (how an unattended maintainer's session may change Lem),
  `rulings/`, with `rulings.md`, the list of the owner's rulings and of the session's choices open
  to him, and `history.md`, what a test or one place holds of them, `backlog/`, Lem's own deferred
  work, and `plans/`, the plans that built Lem, each finished one
  with a status line that names its commits and where later decisions changed it; the redesign of
  2026-11-20 is `plans/2026-11-20-a-session-for-each-task.md` and its folder.
- `tests/`: the suites of "Checks". `unit/` is the unit level, a `test_*.py` for each script;
  `lib.sh` is what each `lem-*.sh` block sources, `checks.sh` how every suite counts its checks,
  `suites.sh` and `limit.py` what `all.sh` and `test-lem.sh` share, and `pick.py` the map of which
  suite reads which file. `board-showcase.py` writes the demo afternoon that `lem-serve.sh` serves,
  and makes the board's pictures through headless Chrome (`board-cdp.mjs`, which needs Node).
  `.github/workflows/ci.yml` runs `all.sh` when someone starts it by hand.
- `.claude-plugin/`, `bin/` and `hooks/`: what Claude Code reads to load this repository as the
  plugin `lem`, the one way Lem installs. `bin/lem` is Lem's one command: `lem NAME` runs the script
  NAME stands for, and `lem help` lists them; `lem-ask` and `lem-jev` are links to it.
  `hooks/hooks.json` starts, each through `lem_python.py`, the correction hook, the SessionStart
  hook of the board server and the two hooks of a task's session. Every text and every message of a
  script says `lem NAME`, so one permission rule, `Bash(lem *)`, covers them on every machine and
  after every update.
- `agents/lem-builder.md`: the builder, as a Claude Code agent definition; its body is the builder's
  standing rules, and `harness/claude-code.md` says how it is used and overridden.
- `assets/`: the logo (`lem.svg`, the animated scene with both skies), the figure alone
  (`lem-mark.svg`), and the night file of each (`*-night.svg`), which `night.py` writes in the night
  palette, with the scene's night sky in its own colors. `assets/screens/` holds the board's
  pictures, light and dark, made by `tests/board-showcase.py`: `board-*` (the kanban), `task-*` (a
  task on "Overview"), `backlog-*` and `phone-*`. The README shows `board-*` and `phone-*`,
  `docs/board.md` `phone-*`, `docs/when-lem-needs-you.md` `task-*`, the site all three, and no page
  `backlog-*`.
- `site/`: Lem's page on GitHub Pages, `index.html` and `style.css`, written from the README and the
  guides in their STE, in the board's look (the six hues of `lem.css` at the same values), light or
  dark by the visitor's theme, with the copy buttons as its one script and nothing from another
  host. `.github/workflows/pages.yml`, started by hand only, copies it with the logo, the figure
  alone (the tab icon) and the six pictures into `_site/` at their repository paths and publishes
  that; `tests/test-site.sh` runs that copy step as written. A change to the README or a guide
  changes `site/index.html` in the same commit where the page says the same thing.
- `skills/lem-ask/`, `skills/lem-interview-me/`, `skills/lem-dialectic/`, `skills/lem-root-cause/`,
  `skills/lem-gate/`, `skills/lem-panel/`, `skills/lem-linear/`, `skills/lem-github/`,
  `skills/lem-ask-expert/`: the skills Lem names and ships. `lem-github` is Lem's own, with
  `scripts/issues.py` (`lem issue`: the GitHub tracker's check, the read of an issue, and its
  writes at a task's start, landing, drop and answer, through `gh`). `lem-ask-expert` is Lem's
  own, with `scripts/experts.py` (`lem experts`: the brief of a question in words and the record of the experts' answers, in a folder of
  `.lem/state/experts/`). `lem-panel`'s `scripts/cast.py` (`lem cast`) finds the cast, copies it
  into a project, keeps the copies a panel read in Lem's state folder, and makes each panel's own
  folder there, in `.lem/state/panels/`. `NOTICE` says where each
  came from.

## The shipped skills are copies, not yet under the rules above

Each was copied from where it worked and changed only as far as the new layout needed. Their text
still names Claude Code's tools,
and lem-ask's Stop hook (`skills/lem-ask/hooks/hooks.json`) is registered by nothing. Bring one under
the capability rule when a second agent has to run it, not before.

The set is deliberately small. A tool with its own life (revmux, agterm, the mailbox chat, webrev,
agdoc, the backlog recipe, cronn, plannotator-tui, Codex) is checked for by `doctor.py` and never
copied in. The backlog's item format is the recipe's, and Lem's builders read it in rule 6 of
`agents/lem-builder.md`; no builder loads the recipe's skill, which is the owner's own tool.
