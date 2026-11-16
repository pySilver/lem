# Claude Code

You run in Claude Code. This file answers `README.md` beside it.

## load-skill

The `Skill` tool. Do not load a skill whose instructions are already in context.

- the question gate: the `lem-gate` skill of this repository.
- the persona panel: the `lem-panel` skill of this repository. It finds the cast and the profile
  through the project's settings.
- the review tool: `revmux:revmux`. It reads the project's lenses, prompts and profile from
  `./.revmux` at the root of the checkout and from no other path, and `revmux init` writes its
  starter set there (config, lenses, prompts). That folder is revmux's own, so it stays there in
  every project, and the settings' `review` path names it; Lem never moves or links it, and
  the learn stage writes a lesson into a lens, the profile or the rejected findings there.
  What a profile or a lens is for: `revmux config`, run in the main checkout, prints each
  profile with its `description` and its `roster` (the lenses each of its agents carries), and
  each lens with its `description`. That output is what the review agent of `stages/land.md`
  reads when it routes a review; the same lines head the files `prompts/profiles/NAME.md` and
  `lenses/NAME.md`. In the starter set that `revmux init` writes, the profile for one small
  read is `focused` ("for a small or time-boxed change": two agents), and the full set is the
  profile the config names as its default, `comprehensive`. A project with other profiles says
  in its `AGENTS.md` which one is its small read. A round runs one profile (`--profile NAME`),
  or a set of lenses in the place of a profile's roster (`--lenses a,b`); no run with
  `--lenses` was made here.
  A review before a proposal runs in the main checkout, so that it reads the review folder as
  the project has it and not as the change under review left it, with `--workdir` set to the
  task's worktree and `--tasks-dir` set to the folder `reviews/` of the task directory. So the
  round leaves nothing in the worktree, which the landing needs clean; revmux puts the round in
  `reviews/SLUG/RUN/`, and the review agent puts the command's output and its log beside it.
  The `revmux:revmux` skill is written for a session with a person: its questions to the user,
  its status lines and its offers after a round are not for a review agent, which prepares the
  round itself, asks nobody and stops after its two files.
  Checked on 2026-11-16 in a trial repository, with revmux v0.2.7: a fresh agent with the
  brief of `prompts/review.md` chose `focused` for a change of 38 lines, ran
  `revmux --task SLUG --run 01-initial --profile focused --workdir WORKTREE --tasks-dir
  TASK_DIR/reviews --no-tui` from the main checkout, and both checkouts were clean after it.
  The round took 66 seconds (revmux's own `duration_ms`), and both of its agents answered.
  Checked on revmux v0.2.7, 2026-11-15, with `revmux config`: it reports `./.revmux` as its
  `project_dir`. The flag `--config-dir PATH` does not name a project folder: it puts PATH in
  the place of the user's own config folder, and no project folder is reported then.
- the tracker: the skill the settings' `tracker.kind` names, `lem-linear` for `linear`. The
  tracker's server is an MCP server, and Claude Code shows its tools as `mcp__SERVER__NAME`, with
  the settings' `tracker.server` as SERVER. A session that was running when the server was added
  does not have them, and a new one does (seen on 2026-11-14 with the Linear server). In a new
  session they may be listed by name only and load on their first use, through the tool search
  (seen on 2026-11-15). A builder
  gets the tools of a server the owner added for all his projects; one added for a single folder
  may be absent in a task's worktree, which is another folder (not tested). Checked on
  2026-11-15 in the first task that came from a ticket: Lem's session, in auto mode, read the
  ticket, changed its status two times and wrote one comment, with the owner's go for those
  writes named in its prompt.
- the rules folder. Claude Code loads `.claude/rules/` by itself: a file with a `paths:` list
  when a matching file is read, the others in every session. Codex and the review tool's agents
  load nothing by themselves, so a brief, a review request and a review round name the files
  `project.py rules` prints. That command reads the same `paths:` list with the glob forms
  Claude Code's page on that folder gives (read 2026-11-15), and finds rule files in subfolders
  and through links as that page says Claude Code does. For a review round, the files go into
  the review context the `revmux:revmux` skill writes, as paths to read first. Checked by the session that started Lem, in
  Claude Code 2.1.325 on 2026-11-14, with all tools off so that only a loaded rule could give
  the answer: a linked file in a real rules folder is loaded; a rule with a `paths:` line
  reached through a link is loaded when a matching file is read and not before; an `@` import
  line inside a rules file is not expanded, so a rules file cannot stand in for a moved one.

## ask-owner

What the settings' `tools.ask` names (`project.py show`), for every question that asks the owner
to choose or to approve:

- `lem-ask`, unless the settings say otherwise: Lem's own page, each option with what the
  owner would see and what it costs. The owner does not have to type `/lem ask` for it; Lem opens the page. It
  is a part of Lem, not a tool of the machine: the machine check has no row for it, and no page
  for the owner lists it as one. The setup links its `lem-ask` command for a home; where it is not
  on `PATH` (Lem linked into one repository), run it by its path, `bin/lem-ask` in that skill's
  folder.
- `terminal`: the question in the conversation, as a numbered list with the recommended option
  first.
- any other name, the developer's own asker: a skill of that name when the session lists one,
  otherwise a command of that name, given the path of a markdown file that holds the question.
  What it prints is the answer.

The question itself has one form whatever shows it: one concrete case, the options with what the
owner would see for each, the recommended one with its reason, and the shortest way to answer.
Three kinds of question stay in the terminal under every value: a value the owner types (a name,
a path, a number), a bare go-ahead on a step just described, and a fixed, trivial choice that
needs no context. The owner's global instructions say how a question is told; they outrank this
file.

When the owner is away (he left before he answered, or a question starts at a time he said he is
not there), Lem has no channel of its own. Where his own instructions name one, such as an inbox
he reads away from the Mac, the question goes there, with the same case and options; otherwise
it waits for him, and the task's state says what waits. Not checked in a run.

Lem takes him as away on two facts only, never on a guess from his silence: his own words in
this session that he is away or leaves (until he types again), or a question of this turn that
went to his away channel because his instructions sent it there. For a choice of a build that
waits, that is what `decisions.py settle SLUG N --away` stands on (`stages/new.md`).

## spawn-builder

The `Agent` tool with `subagent_type: "lem-builder"` when the session lists an agent of that
name, and with `subagent_type: "lem:lem-builder"` otherwise. Lem brings that agent:
`agents/lem-builder.md` in Lem's repository. Its body holds the builder's standing rules, so a
brief stays short and no builder misses one; its frontmatter sets the model and the effort,
because a subagent on another model than the session's does not take the session's effort. There
is no fallback to another agent type: when the session lists neither name, the setup is not
done; say so, name `doctor.py`, and stop.

The two names are the two ways Lem reaches a session. Linked by the setup, the file is in
`~/.claude/agents/` or the repository's `.claude/agents/`, and its name is `lem-builder`. Loaded
as the plugin `lem`, Claude Code puts the plugin's name before it, `lem:lem-builder`, and the
plain name answers "Agent type 'lem-builder' not found" (checked on 2026-11-15 in Claude Code
2.1.325, with the plugin loaded through `--plugin-dir` and through a project's settings; the
plugin's agent ran on the model its file names).

A project that wants another builder (another model, more rules) keeps a file named
`lem-builder.md` in its own `.claude/agents/`. That agent is `lem-builder`, so the rule above
picks it in both forms. Beside linked files, Claude Code takes the project's definition before
the user's (its documentation gives the order: managed, the `--agents` flag, the project, the
user, a plugin; https://code.claude.com/docs/en/sub-agents, read 2026-11-15); beside the plugin,
the two agents have two names, and a call of `lem-builder` reached the project's file in the
same check. No setting of Lem's is involved.

The brief gives the task's worktree as an absolute path; do not pass `isolation: "worktree"`,
since the task already has its worktree. Agents run in the background and you are told when one
ends: never predict a builder's report, and never poll for it. A builder's end reaches you twice,
as its message and then as a notification that points at that message. Act on the first; the
second needs no act.

Claude Code may refuse a builder the write of its report file. In the first task that ran
through Lem (a scratch repository, 2026-11-15, Claude Code 2.1.325) the lead's write of
`report.md` was refused with "Subagents should return findings as text, not write report files",
and the write of the same file by the next builder, when the file existed, was accepted. So a
builder never counts on that write: when it is refused, its reply is the whole report, and the
one who started it writes the file from the reply, as the stage files say. A builder that takes
another tool to get the file written goes around a guard, and it must not.

A builder can start builders of its own with the same tool, so a builder leads a plan of any size,
also the build of a careful or large plan after its talk. Checked on 2026-11-14 in Claude Code
2.1.325: a subagent of the type `worker`, which like `lem-builder` names no tool list and so
inherits every tool, called `Agent`, and the nested agent's reply came back to it. Not run yet: the
same from a `lem-builder`. The persona agents of a lead's read of its stories start the same way: on
2026-11-16 a `worker` subagent on Opus, standing in for a lead, started two persona subagents and
had both answers in 25 seconds (07:23:25Z to 07:23:50Z); not checked from a `lem-builder`, which has
the same tools. The scout of an interview is a builder too, with `prompts/scout.md` as its brief,
and so is the investigator of a bug or a question, with `prompts/investigator.md`. A
builder has no pane of its own, so no reviewer sits beside it and the owner cannot type to it. A
careful or large plan gets a companion session for its talk for that reason: the talk needs the
reviewer's pane and the mailbox.

## open-task-session

A companion session of this one, which runs Claude Code with the brief's file named in its first
prompt. Lem opens one for a plan talk only: its agent is the plan's defender
(`prompts/defender.md`), and the companion is closed when the talk is done.

1. **The brief** is the task's `brief.md`, with its two lines for `tell-coordinator`:
   `coordinator: SESSION:PANE`, with this session's `AGTERM_SESSION_ID` and this pane's
   `AGTERM_PANE_ID`, and `socket: PATH`, with this session's `AGTERM_SOCKET`. Lem writes them at
   each start of a lead, for a builder too.
2. **Open the session**:

   ```bash
   agtermctl session new --parent "$AGTERM_SESSION_ID" --cwd WORKTREE --name SLUG --no-select \
     --command "LOGIN_SHELL -l -c 'claude --model MODEL --effort EFFORT \"Read BRIEF and follow it.\"'" --socket "$AGTERM_SOCKET"
   ```

   `MODEL` and `EFFORT` are the settings' `seats.planner` (`project.py show`). Leave a flag out
   when the seat does not name its value: the agent's own default holds then, as for the
   reviewer's pane. The seat's `agent` can only be `claude`, since this file is the only one the
   contract was checked in.

   `LOGIN_SHELL` is the owner's login shell by absolute path
   (`dscl . -read /Users/NAME UserShell`), not the shell of your own Bash tool. agterm starts the
   command with its own `PATH`, and only the login shell finds `claude` the way the owner's
   terminal does: on a Mac whose login shell is fish, `zsh -lc` answered `command not found:
   claude`. The line has no command substitution, so zsh and fish read it the same way. Pass no
   flag that widens the session's permissions: it runs in the permission mode the owner's
   settings give a new session.
3. **Confirm it runs**: the command prints the new session's id. In `agtermctl tree --json` the
   node with that id has a `foreground` that ends in the `claude` line. Its `parent` is this
   session, or, when this session is itself a companion, this session's own parent: agterm makes
   a companion's companion its sibling, so the task's session then sits beside Lem's and not
   under it. That is a good open, and the board goes to the same place. Only a node that is gone
   at once means the command failed; then open it again with `--wait` and read its screen with
   `agtermctl session text --target ID`. Never open a second session for a task whose first one
   runs. Write the id in the task's state. Then read the model and the effort from the status
   line on that screen, and write them in the state as `defender: MODEL, EFFORT`, never the ones
   you asked for: the talk's record names them, as it names the reviewer's.
4. **Send it a message** later (the owner's answers, a changed base):
   `agtermctl msg send --stdin --to ID:left --socket "$AGTERM_SOCKET" < FILE`. The mailbox hook of
   the mailbox chat hands it to the agent there at the end of its turn. When the session is gone,
   open one again: the new lead reads the task's files.
5. **Close it** when the talk is done, once `project.py tasks` gives the task a `talk`, or when the
   task is dropped: `agtermctl session close --target ID --socket "$AGTERM_SOCKET"`. Its experts
   and the reviewer's pane end with it.

Under agterm's rerun restore mode a relaunch of agterm starts each session's command again. A
lead started that way is a fresh agent with the same brief; `prompts/lead.md` tells it to read the
task's state first, so it goes on or stops.

Checked on 2026-11-14 with agterm 0.41.1 in its rerun restore mode: a companion session opened
with this line through a fish login shell, Claude Code ran its prompt there, and `foreground` and
`parent` read back from the tree. Checked on 2026-11-15 in a scratch repository, in the first
careful task that ran through Lem: Lem, itself in a companion session, opened the task's session
this way and it came up as Lem's sibling; its lead stopped at Codex's trust prompt with the
state `held`; Lem sent it the owner's answer as in step 4; the lead then had the plan read,
started a builder, had the diff reviewed and wrote `ready`, and the task landed. The task's
event log holds each state with its time. Not run yet: a relaunch of agterm with a companion
open, a companion for a plan talk alone and closed at its end, and the launch line with
`--model` or `--effort`.

## tell-coordinator

From a plan talk's companion, and from a builder that leads a task, with the address from the
brief's `coordinator:` line and the socket from its `socket:` line:

```bash
agtermctl msg send "lem: SLUG is STATUS" --to SESSION:PANE --socket SOCKET
```

Write both values literally, as the brief gives them: a builder writes no shell variable
(`agents/lem-builder.md`), and `agtermctl` does not read `AGTERM_SOCKET` by itself (the agterm
skill: "`agtermctl` never reads it automatically"). Lem writes the two lines into the brief at
each start of a lead (`stages/new.md`, "Start a lead"), from its own `AGTERM_SESSION_ID`,
`AGTERM_PANE_ID` and `AGTERM_SOCKET`, so a Lem that started after the brief was first written
gets the line.

One line, after the report and the state are written, and at once after `decisions.py ask` with
`lem: SLUG choice N waits`. It reaches Lem as mail that starts with
`[agterm mailbox, not a peer chat message]`; Lem reads the task's state or `decisions.py
pending`, never the line's claim. Mail is kept in memory only, so a pane that was restarted has
lost it. A lost end of a task costs nothing but time: the state block is on disk, and `/lem
status` shows it. A lost choice costs the owner part of his wait, so Lem also runs
`decisions.py pending` at each of its turns (`stages/new.md`, "When a choice waits for the
owner").

A builder runs as a subagent inside Lem's own session, so its line goes from Lem's pane to Lem's
pane: the sender `agtermctl` takes by default (`--as`, from the `AGTERM_SESSION_ID` and
`AGTERM_PANE_ID` the subagent inherits) is the recipient itself. Checked on 2026-11-16 with agterm
0.41.1, in a throwaway session that ran no agent: a message sent with `--as` and `--to` the same
pane was accepted (`delivered` named that pane), and `msg read` as that pane returned it with
`from` and `to` equal. The mailbox chat's waiter for Claude Code, which wakes an idle agent, takes
any mail of its pane between two turns and reads no sender (`mailbox-chat.py`, its `Waiter`).
Checked on 2026-11-16 with agterm 0.41.1 and Claude Code 2.1.325, in a real Lem session: a
background command of that session sent `lem: wake-probe choice 1 waits` with `agtermctl msg send
--to SESSION:PANE --socket SOCKET` to the session's own pane, 20 seconds after the session ended
its turn, and the line reached the idle session as a turn of its own (`[agterm mailbox, not a
peer chat message]`, from the session's own address). The sender was a background command, not
a subagent: that a line a builder sends wakes Lem the same way is not checked. Until a run shows
it, `decisions.py pending` at each of Lem's turns is what makes sure that no choice is missed.

Checked on 2026-11-14: this command, run by Claude Code in a companion session, put its line in
the mailbox of the pane that opened the session. Checked on 2026-11-15, in the same careful
task: the lead sent this line at each of its two stops, and each one reached the idle Lem as a
turn of its own, 20 seconds after the lead's `held` state and 2 seconds after its `ready` state
(the times of the two states are in the task's event log, the times of the two turns in the
transcript of Lem's session).

## second-opinion

The reviewer is a second agent in the split pane of the session that asks (the companion of a plan
talk, for a careful or large plan); the owner reads both panes. `project.py show` gives the seat as
`seats.reviewer`: its `agent` (`claude` or `codex`) and, when the project or this machine set them,
its `model`, its `effort` for the review of a diff and its `plan_effort` for the talk over a plan.
When `agent` is null, ask the owner once and write the answer into `.lem/project.toml`.

The seat may be this machine's own for a while: the usual reviewer is down, or out of tokens.
`/lem reviewer AGENT [MODEL [EFFORT [PLAN_EFFORT]]]` runs `project.py reviewer` with those words,
which writes the seat into `.lem/project.local.toml`, a file git does not track; `/lem reviewer
default` removes it. Never change the seat by yourself. When the reviewer does not answer, or
says it is out of tokens, ask the owner once whether the other agent reviews for now, and write
the seat on his yes. While `project.py show` lists `seats.reviewer` under `local.overrides`,
every report says that the reviewer is this machine's choice, and "same family" when it is.

1. **Is a reviewer there?** `mailbox-chat.py status` names the other pane and what serves it:
   `claude`, `codex` or `none`.
2. **Open the seat** when there is no split or nothing serves it:
   - `agtermctl session split on --target "$AGTERM_SESSION_ID" --socket "$AGTERM_SOCKET"`;
   - write the launch line to a file and type it into the right pane with
     `agtermctl session type --stdin --pane right --target "$AGTERM_SESSION_ID" --socket "$AGTERM_SOCKET" < FILE`.
     The line starts the agent with the reviewer's brief, `prompts/reviewer.md` in this skill's
     directory, by absolute path:
     - Codex: `codex "$(cat PATH/prompts/reviewer.md)"`. A Codex pane receives mail only after
       its first prompt, and the brief is that prompt. With a model, add `-m MODEL` before the
       prompt; with an effort, `-c model_reasoning_effort=EFFORT`.
     - Claude Code: `claude --append-system-prompt "$(cat PATH/prompts/reviewer.md)" "You are the reviewer. Wait for the first message."`
       With a model, add `--model MODEL`; with an effort, `--effort EFFORT`.
     The effort is `plan_effort` when the pane is for a plan talk, and `effort` otherwise.
     Leave a flag out when the seat does not name its value: the agent's own default holds then.
     The reviewer's pane is new for each review, so a plan talk simply starts with its own effort.
   - read the model and the effort back from the pane's status line, and name those in the
     report, never the ones you asked for. In one repository seven or more tasks were reviewed on
     another model than the run's log said (mybaze, 2026-11-07, from that project's
     retrospective of 2026-11-08).
   - read `agtermctl tree --json` and confirm the session's `splitForeground` is that agent, then
     `mailbox-chat.py status` again.
   - Codex asks "Trust this folder?" the first time it starts in a repository, and it saves the
     answer in the owner's Codex configuration. That answer is the owner's: tell the owner that
     the reviewer's pane waits for it, and do not type into the pane. `mailbox-chat.py status`
     says `codex` once the pane listens.
   Under agterm's Live sessions mode, `agtermctl session restart --pane-id ID --command LINE` starts
   the same line without typing; in the other restore modes it is refused.
3. **Send the request** through the `mailbox-chat` skill: what to review (the plan's path, or the
   range of commits), the directory to work in, the task it belongs to and the style guide files
   that cover it (`project.py rules`, with the plan's files or `--range`). A message that names git goes from a file, never a heredoc.
4. **The reply arrives in this pane by itself.** Never poll for it, and check every claim it makes
   about the code with your own read before you act on it.
   A reply that may not be whole ("so far", a numbered point with no end, no closing `Changed:`
   line for a diff) is answered in the same turn: accept or dispute its points and ask whether
   more follows. End the turn to wait only when the reviewer said that more follows. In one run a
   reply that ended "Source inspection only so far" was taken as partial, both panes waited 137
   minutes, and the reviewer answered in about 90 seconds once asked (mybaze, 2026-09-29, from
   that project's notes).
5. **A reviewer is fresh for each review.** Before the next one, `agtermctl session split close`
   on this session ends the pane and its agent, and step 2 opens a new one. The dispute of a
   review's points and the check of the fixes it asked for belong to that review and stay in its
   pane. A plan talk is one review: every turn of it goes to the same pane.
   A new pane is not always a new Codex. With agterm's cookbook recipe for Codex session resume
   installed, a `codex` typed in a session continues that session's conversation: its wrapper
   keeps the session's Codex thread in `~/.codex/agterm/SESSION-ID` (the id in lower case). On
   2026-11-14 four reviewer panes opened one after the other all registered the same thread, and
   the pane's status line went on from 12% of the context to 17%, 32% and 40%. So before the
   launch of step 2, remove that file when it is there; after the launch, the pane's status line
   must show a context near zero. With the file removed, the fifth pane of that day started at
   2% and registered a new thread. A reviewer that carries the last review reads the next one
   with it.

Say in the report which family reviewed. Two agents of one family agree more easily than two of
different ones; the report says "same family" when that was the case.

Checked on 2026-11-14 with agterm 0.41.1 in its rerun restore mode and a fish login shell: a
split opened on a background session, Codex started by the typed line with the reviewer's brief,
its name read back from `splitForeground`, and one review went to it and came back through the
mailbox. The reply waited in the mailbox while the coordinator's turn ran, and reached it only
when the coordinator read its mail. Not run yet: a Claude Code reviewer started this way, and a
launch with a model or an effort flag (the flags are in each command's `--help`, read the same
day: `codex -m`, `codex -c`, `claude --model`, `claude --effort`).

## fan-out

Several `Agent` calls in one message. The `Workflow` tool only when the owner asked for one.

## ask-experts

Both in one message, so that they start at one moment; `BRIEF`, `WORKTREE` and each answer file
are the paths `experts.py brief` printed.

- `fable`: the `Agent` tool with `subagent_type: "Plan"`, `model: "fable"` and the prompt
  `Read BRIEF and follow it. Your reply is your answer, in the form the brief's last section
  gives, and nothing else.` The `Plan` agent has no edit or write tool, so it reads; it has Bash,
  so the brief's "change no file" is what keeps it from a write there. It runs in the
  background, and its reply reaches you as its message: write that reply into its answer file
  word for word, without the indent Claude Code puts before each line of a subagent's report,
  then run `experts.py record`.
- `astra`: the `Bash` tool with `run_in_background`, on this line:

  ```bash
  codex exec -m gpt-6-astra -c model_reasoning_effort=high -s read-only --skip-git-repo-check --ephemeral -C WORKTREE -o ANSWER - < BRIEF > ANSWER.log 2>&1
  ```

  `-` reads the prompt from stdin, and the brief file is that stdin, so it ends: a Codex in the
  background whose stdin stays open waits for input and never starts (seen 2026-11-16, a headless
  Codex review). `-o` writes its last message into the answer file. You are told when the command
  exits; then run `experts.py record`. A non-zero exit, or an answer file that is not there, is
  an expert that did not answer: the skill's step 3 says what follows.

Checked on 2026-11-16 in a scratch repository, Claude Code 2.1.325 and codex-cli 0.169.0, on a
toy choice of two options with two stories and one file: both started in one message (`date -u`
read 13:23:11Z in the call before it). `fable` answered in 12.1 seconds (the subagent's
`duration_ms`, 12093) and `astra` in 18 seconds (13:23:18Z to 13:23:36Z, `date -u` around the
command); both picked the same option, each answer was recorded by `experts.py record` as it
came, `decisions.py settle --away` took the pick, and both checkouts were clean after it. That
was started from a subagent, the way a builder that leads starts them; not run yet from a
`lem-builder` or from a task's session. One run of a toy choice: a real choice, with a plan and
more files to read, takes longer, and that time comes out of the owner's wait.

## A session's name

`agtermctl session rename "Lem init · REPO" --target "$AGTERM_SESSION_ID" --socket "$AGTERM_SOCKET"`
names this session, and `agtermctl session context 'TEXT' --target ...` puts one line about the
work into the title bar. A stage that runs for a repository the session did not start in (the
onboarding) does both, with the repository's name in each.

## show-page

An HTML file opened as an overlay of this session
(`agtermctl session overlay open --html FILE --cwd DIR --target "$AGTERM_SESSION_ID" --socket "$AGTERM_SOCKET"`,
where `DIR` is the absolute path of the folder that holds `FILE`). The `--cwd` is what lets the
page read the `lem.css` beside it: agterm's help says of `--cwd` with `--html` "grants read
access inside this directory; relative links resolve beside FILE. Without --cwd, the page has no
file access."
A document the owner should mark up (a plan, a draft profile) goes through the settings'
`tools.annotate`: a skill of that name when the session lists one, otherwise a command of that
name given the file's path. `/lem annotate FILE` is the same for a file the owner names. The
default is `webrev`, the tool Lem recommends and does not bring: a recipe of the agterm cookbook
that the developer installs (the machine check's `webrev skill` row has its guide). An owner who
prefers another tool, plannotator for one, names it in the settings.
When the session has no skill and no command of the name the settings give, say so once, with
that name and, for `webrev`, the guide to install it by; then give the owner the file's path to
read as it is, and take the notes in the conversation. Do not install it unasked.

## The correction hook

For a project that keeps a correction queue (`stages/learn.md`). The hook exits at once in every
repository whose settings do not say `corrections.collect = true`. That line is in the tracked
settings file, so it is the repository's yes: it holds for everybody who works there with the
hook and an OpenRouter key, and everybody can read it in git. Say that to the owner before he
says yes, in those words. One person says no for themselves with `collect = false` under
`[corrections]` in `.lem/project.local.toml`; that file can never say yes.

How the hook gets there depends on how Lem reached the session.

- **Lem as a plugin** (the skill list shows `lem:lem`): the hook comes with the install,
  from the plugin's `hooks/hooks.json`. Nobody registers anything, and the `setup.py` command
  below is not for this form: it would add the same hook a second time.
- **Lem linked by the setup**: the owner registers the hook with one command of Lem's setup, on
  the day of the onboarding or any later day, and takes it out the same way. `CLONE` is Lem's
  clone: two folders above the real path of `SKILL_DIR`.

```bash
python3 CLONE/scripts/setup.py --corrections on --project ROOT   # for this repository
python3 CLONE/scripts/setup.py --corrections on                  # for every repository of this home
python3 CLONE/scripts/setup.py --corrections off                 # with --project ROOT when it went in that way
```

Name the first form. The yes is one project's (`corrections.collect`), and a hook in the home
settings starts a process on every message in every repository only to find that out. The
second form is for an owner with many repositories that use Lem: say that it exists, in one
line. Print no JSON for him to paste. The command adds one
`UserPromptSubmit` hook to Claude Code's settings (`~/.claude/settings.json`, or the checkout's
`.claude/settings.local.json`), keeps the rest of the file, and refuses a file it cannot read,
one that holds the hook in another form, and for one repository a settings file that is a link
out of it. `setup.py --check` says whether it is registered.

- It needs Python 3.11 or newer as `python3`. Under an older one it judges nothing, and says so
  in its log. It finds `python3` and `git` on the hook's `PATH`, as any hook does; with no `git`
  there it queues nothing and has nowhere to say so, since its log is in the git directory. The
  model's client is Lem's own `jev.py`, run by its path. It needs `OPENROUTER_API_KEY` in the
  environment Claude Code starts with.
- It prints nothing and does not wait for the model: a detached copy asks it. The hook's own two
  waits, for its input and for each of its git calls, end after two seconds each, a bound chosen by guess
  on 2026-11-15. The `timeout` of 10 seconds above is the value its source ran with in one
  repository since 2026-11-07; it is not a measurement.
- What fails goes to `corrections.log` in Lem's folder of the git directory, and
  `corrections.py list` counts it.
- You do not run that command. A hook that sends the owner's messages to an outside service is
  his to add, and Claude Code's classifier refuses the step to an agent (the next section).

Run: the setup's command on a real settings file (the owner, in a scratch repository,
2026-11-15: registered in that checkout's local settings, as another session read it); and the
plugin's hook starting on each message, with the plugin's folder in `CLAUDE_PLUGIN_ROOT`
(2026-11-15, Claude Code 2.1.325, three headless sessions with a probe line). Not run yet: a
message that went through the hook to the model in a real session. The hook's two halves are
tested with a stand-in for the model, and the command with settings files in a throwaway home.

## What the owner does himself

Some steps are not an agent's, with or without the owner's yes in the conversation.

- **A folder's trust.** Claude Code asks whether the owner trusts a folder the first time a
  session starts in it, and Codex asks the same. That holds for a repository an agent made
  minutes before. The answer is kept in the owner's configuration, so it is his: say which
  session waits and where, and go on with other work. Do not answer the prompt, and do not go
  around it: on 2026-11-15 the classifier refused a move of a new repository below a folder the
  owner already trusts. A task's worktree is inside the project's checkout, which the owner
  trusted when Lem's session started there.
- **What the classifier refuses in auto mode.** In one repository it refused these to the agent
  after the owner's yes, and the owner ran them himself (mybaze, 2026-11-07, from that project's
  notes): a push to another repository than the session's own, the registration of a hook that
  sends prompts to an outside service, and the install of a scheduler, whose login agent counts
  as persistence. When the classifier refuses a step, give the owner the exact command on one
  line and go on. Never send the step again in another form.
