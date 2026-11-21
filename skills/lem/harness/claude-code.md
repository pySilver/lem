# Claude Code

You run in Claude Code. This file answers `README.md` beside it.

## lem

`lem` is a file in the plugin's `bin/`, and Claude Code puts that folder on the Bash tool's `PATH`
while the plugin is loaded, also in a subagent (Claude Code 2.1.326, 2026-11-17). It runs the
script a name stands for with the arguments as they came, and its output and exit status are the
script's. So one permission rule, `Bash(lem *)`, covers every script of Lem's on every machine and after every update of the plugin, whose folder
changes with each update. The rule covers a plain call: run each `lem` call alone and read what it
prints, never inside `$(...)`, before a pipe or after an `&&`, which make a command of another
shape that needs a rule of its own. Where the shell does not find it (`command not found`), run the same
script by its path, `python3 SKILL_DIR/scripts/NAME.py ARGS...`, or for a shipped skill's the
file in that skill's `scripts/` (`lem experts` is `python3
SKILL_DIR/../lem-ask-expert/scripts/experts.py`; `COMMANDS` in `SKILL_DIR/../../bin/lem` names
each file), and say once that `lem` was not on the `PATH`.

## load-skill

A skill this repository ships, `lem-NAME`: the `Read` tool on `SKILL_DIR/../lem-NAME/SKILL.md`,
where `SKILL_DIR` is the `lem` skill's directory, and then do what it says. In that file
a `SKILL_DIR` that the file names as its own directory is the folder of that file (`lem-linear`
names the `lem` skill's), and its scripts run through `lem`. The `Skill` tool refuses these
skills: each has `disable-model-invocation: true`, so that it starts only for Lem and puts no
description in a session's list of skills. Do not try the `Skill` tool on one first: its refusal
tells the agent not to follow the skill by other means (Claude Code 2.1.326, seen 2026-11-17),
and the read by its path is the one way these skills are meant to start. A skill of another tool (the review tool) is the `Skill` tool.
Do not load a skill whose instructions are already in context.

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
  A round's line, run from the main checkout: `revmux --task SLUG --run 01-initial --profile
  focused --workdir WORKTREE --tasks-dir TASK_DIR/reviews --no-tui`; both checkouts were clean
  after it (revmux v0.2.7, 2026-11-16). The flag `--config-dir PATH` does not name a project
  folder: it puts PATH in the place of the user's own config folder (revmux v0.2.7, 2026-11-15).
- the tracker: the skill the settings' `tracker.kind` names, `lem-linear` for `linear`. The
  tracker's server is an MCP server, and Claude Code shows its tools as `mcp__SERVER__NAME`, with
  the name the server was added under as SERVER (`linear` in `docs/linear.md`; a second
  workspace is a second server with a name of its own, and the skill says which one a ticket
  takes). A session that was running when the server was added
  does not have them, and a new one does (seen on 2026-11-14 with the Linear server). In a new
  session they may be listed by name only and load on their first use, through the tool search
  (seen on 2026-11-15). A builder
  gets the tools of a server the owner added for all his projects; one added for a single folder
  may be absent in a task's worktree, which is another folder (not tested).
- the rules folder. Claude Code loads `.claude/rules/` by itself: a file with a `paths:` list
  when a matching file is read, the others in every session. Codex and the review tool's agents
  load nothing by themselves, so a brief, a review request and a review round name the files
  `lem project rules` prints. That command reads the same `paths:` list with the glob forms
  Claude Code's page on that folder gives (read 2026-11-15), and finds rule files in subfolders
  and through links as that page says Claude Code does. For a review round, the files go into
  the review context the `revmux:revmux` skill writes, as paths to read first. A linked file in
  the rules folder is loaded, a rule with a `paths:` line reached through a link is loaded when a
  matching file is read, and an `@` import line inside a rules file is not expanded, so a rules
  file cannot stand in for a moved one (Claude Code 2.1.325, 2026-11-14).

## ask-owner

`lem-ask`, Lem's own page, for every question that asks the owner to choose or to approve: each
option with what the owner would see and what it costs. Lem opens the page each time it asks; the
owner types nothing for it. It is a part of Lem, not a tool of the machine: the machine check has
no row for it, and no page for the owner lists it as one. The plugin puts its `lem-ask` command on
the Bash tool's `PATH`. Outside agterm it exits 3 and opens nothing; then ask in the conversation,
as a numbered list with the recommended option first.

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

**A card in a task's session** waits for his answer with no time limit, and the session still
takes a wake-up meanwhile: run `lem-ask ask SPEC --timeout 86400` with the Bash tool's
`run_in_background`, and without `--follow`, so that the card takes no focus. The session's turn
then ends while the card is up, so a wake-up reaches it (the mailbox hook hands mail over between
two turns, "A wake-up"), and the end of the command wakes it with the answer. Exit 4 after that wait is `lem-ask wait PAGEID` the same way, again.
Exit 2 (`dismissed`) is a card he closed with no answer. Exit 0 with `status: "chat"`, or a `text`
with no option selected, is a question of his or a wish to talk: answer it in the session's
conversation, and put the card up again with the same spec. The overlay covers that session only,
so two tasks' sessions can show two cards at once, where one session shows one at a time (exit 5,
`busy`). Not run yet: a card in a task's session.

## spawn-builder

The `Agent` tool with `subagent_type: "lem-builder"` when the session lists an agent of that
name, and with `subagent_type: "lem:lem-builder"` otherwise. Lem brings that agent:
`agents/lem-builder.md` in Lem's repository. Its body holds the builder's standing rules, so a
brief stays short and no builder misses one; its frontmatter sets the model and the effort,
because a subagent on another model than the session's does not take the session's effort. There
is no fallback to another agent type: when the session lists neither name, Lem's plugin is not
installed here; say so, name `doctor.py`, and stop.

The plugin `lem` brings the agent, and Claude Code puts the plugin's name before it,
`lem:lem-builder`; the plain name then answers "Agent type 'lem-builder' not found" (Claude
Code 2.1.325, 2026-11-15).

A project that wants another builder (another model, more rules) keeps a file named
`lem-builder.md` in its own `.claude/agents/`. That agent is `lem-builder`, so the rule above
picks it first: beside the plugin the two agents have two names, and a call of `lem-builder`
reaches the project's file. No setting of Lem's is involved.

The brief gives the task's worktree as an absolute path; do not pass `isolation: "worktree"`,
since the task already has its worktree. Agents run in the background and you are told when one
ends: never predict a builder's report, and never poll for it. A builder's end reaches you twice,
as its message and then as a notification that points at that message. Act on the first; the
second needs no act.

Claude Code may refuse a builder the write of its report file, with "Subagents should return
findings as text, not write report files" (Claude Code 2.1.325, 2026-11-15). So a builder never
counts on that write: when it is refused, its reply is the whole report, and the
one who started it writes the file from the reply, as the stage files say. A builder that takes
another tool to get the file written goes around a guard, and it must not.

The lead is the task's session itself, so each builder of a plan is a subagent of that session,
one level down. The persona agents of a lead's read of its acceptance criteria start the same way.
The scout of an interview is a builder too, with `prompts/scout.md` as its brief, and so are the
investigator of a bug or a question, with `prompts/investigator.md`, and the one builder of the
fast track, with `prompts/small.md`: each starts from the task's session, and its reply comes there.
A builder has no pane of its own, so no reviewer sits beside it and the owner cannot type to it. A
careful or large plan gets a pair for its talk for that reason: the talk needs the reviewer's pane
and the mailbox.

## open-task-session

Two kinds: a task's own session, and the plan talk's pair that a lead opens under it.

### A task's own session

`lem session open SLUG` opens it, never a line of this file, so that its name, its place and one
session for each task hold the same way each time: run twice, it opens one, and prints the one
that runs with `already: true`. It writes `session.md` into the task directory and runs, in
agterm's own words:

```bash
agtermctl session new --workspace WS --cwd DIR --name SLUG --no-select --command "LOGIN_SHELL -l -c 'LEM_TASK=SLUG CLAUDE_CODE_AUTO_COMPACT_WINDOW=N claude \"Read TASK_DIR/session.md and follow it.\"'"
```

then `agtermctl session move --to top`, and with `--focus` `agtermctl session select`. `DIR` is the
task's worktree, else the main checkout. A trial on 2026-11-21 (agterm 0.41.1 serving and 0.43.0
installed, Claude Code 2.1.330) showed:

- The session opened at the top level of the workspace and was not selected; `move --to top` put
  it first, and the selection stayed where it was.
- `session new` takes no environment, so the two variables are in the launch line, and `ps eww`
  showed the variable in the Claude process. A builder inherits both.
- `LOGIN_SHELL` is the owner's login shell by absolute path (`dscl . -read /Users/NAME UserShell`):
  agterm starts the command with its own `PATH`, and only the login shell finds `claude` the way
  the owner's terminal does. The line passes no flag that widens the session's permissions.
- Claude Code showed its trust dialog for a folder it had never trusted, with "No, exit" selected
  first. Nothing of Lem answers it ("What the owner does himself").
- A session opened with a command leaves no shell when its agent ends: after `/exit` the session
  left agterm's tree at once. A task whose agent ended has no session, and the board says so.
- Each idle session posts agterm's "Claude is waiting for your input". One of the trial's two
  sessions closed 1.3 s after such a notice with no command of the trial's, most likely by a hand.

When `seats.session` names a model or an effort, `lem session open` puts them on the launch line;
otherwise the session runs the owner's default Claude. When this Lem is not the installed plugin (its folder is
outside `~/.claude/plugins/`, or outside `plugins/` of `CLAUDE_CONFIG_DIR`), the line adds
`--plugin-dir` with that folder, so that the task's session runs the Lem that opened it. That holds
where no Lem is installed: with an older Lem installed for the project, the `lem` on such a session's
`PATH` is the installed one (lem-scratch, Claude Code 2.1.330, 2026-11-21), so a clone is tried with
the installed plugin switched off. A launch with `--model` and `--effort` ran (the same day). Not run yet: a relaunch of agterm in its
rerun mode, which starts each session's command again: the agent then starts from its first
message, and `prompts/session.md` reads the state before anything else, so it goes on or stops.

`lem session close SLUG [--session ID] --why ...` logs the close and then runs `agtermctl session
close --target ID --undoable`. It refuses a session the owner has selected; with
`--when-unselected` it looks every 5 seconds (a guess) and closes it once he left it, so it runs in
the background. `lem session list` gives each task's newest session: whether it lives, runs an
agent and is selected, its phase, and `unanswered`, a wake-up still in its mailbox after 10
minutes.

### The context's number

`N` is `[handoff] tokens` of `~/.config/lem/machine.toml`, the owner's number for all his
repositories: 600,000 when the file has none, written with `lem project handoff --tokens N|default`
and shown by `lem doctor`. With 0 Lem sets nothing, and Claude Code compacts at its own trigger,
"at about 967K tokens by default" on a 1M window (Claude Code's model-config page, read
2026-11-21). Claude Code refuses a window under 100,000, and so does Lem. Past the number Claude
Code compacts the session by itself; background commands and background subagents keep running
through it (the context-window page, read 2026-11-21). The plugin brings two hooks for it, which
read no transcript and do nothing without `LEM_TASK`:

- `PreCompact` prints the summary's form, the five headings of `handoff.md`. Its output "becomes
  instructions for the compaction summary", 10,000 characters at most (the hooks reference, read
  2026-11-21).
- `SessionStart` with the source `compact` prints the task's newest state block and `handoff.md`
  with its time, under "the state is the truth; where the handoff is older, follow the state".

Both hooks ran in a compaction the owner's `/compact` started, in a landing session that waited for
a merge: the summary took the handoff's form, and the state came back after it (lem-scratch,
2026-11-21). Not run yet: a compaction at the number.

### The plan talk's pair

A companion session of the lead's, `SLUG · plan talk`, which runs Claude Code with
`talk-brief.md` named in its first prompt; its agent is the plan's defender
(`prompts/defender.md`), and the reviewer sits in its other pane (`second-opinion`).

1. **Open it**:

   ```bash
   agtermctl session new --parent "$AGTERM_SESSION_ID" --cwd WORKTREE --name "SLUG · plan talk" --no-select \
     --command "LOGIN_SHELL -l -c 'claude --model MODEL --effort EFFORT \"Read BRIEF and follow it.\"'" --socket "$AGTERM_SOCKET"
   ```

   `MODEL` and `EFFORT` are the `model` and the `effort` of the settings' `seats.planner`, which
   `lem project show` gives parsed from its one line, `claude/MODEL:EFFORT`. Leave a flag out when
   the seat does not name its value (`null`): the agent's own default holds then. The seat's
   `agent` can only be `claude`, since this file is the only one the contract was checked in.
2. **Confirm it runs**: the command prints the new session's id; keep it. In `agtermctl tree
   --json` the node with that id has a `foreground` that ends in the `claude` line, and its
   `parent` is this session. Only a node that is gone at once means the command failed; then open
   it again with `--wait` and read its screen with `agtermctl session text --target ID`. Never
   open a second pair for a task whose first one runs; a lead after a restart finds it in the tree
   by its name. Then read the model and the effort from the status line on that screen, and write
   them in the state as `defender: MODEL, EFFORT`, never the ones you asked for: the talk's record
   names them. A status line of the owner's own may show neither: write `unread` for each value
   the screen does not show.
3. **Close it** once the lead's wait ended (`stages/plan.md`, step 4), or when the task is
   dropped: `agtermctl session close --target ID --socket "$AGTERM_SOCKET"`. Its experts and the
   reviewer's pane end with it.

Not run yet: a pair opened from a task's session.

## A wake-up

Nothing of a task's session watches GitHub or another task. The board's server runs `lem session
wake SLUG --why merged|conflict|refused|queue|owner` (`owner` after his approval or his park on the board),
which sends `agtermctl msg send "lem: SLUG WHY" --to
ID:left` to the task's live session, or opens one when none lives. In the trial of 2026-11-21 the
idle agent took a turn within 15 s each time, five sends in two sessions, two of them after about
two minutes idle, with no `--socket` too (`agtermctl` finds the app's socket itself), and `ID:left`
reached a session with no split. The line arrived as `[agterm mailbox, not a peer chat message]
from outside agterm:` and its body, marked "NOT user input". So the session reads the files and
never the line. A wake reaches an agent only through the mailbox chat's waiter, a hook of the
owner's home settings (`mailbox-chat.py claude-hook`): the mailbox chat is a required tool of Lem,
and `lem doctor`'s row for it says so. Mail is kept in memory only, so a pane that was restarted
has lost it; a wake nobody took shows on the board after 10 minutes. Not run yet: a wake after an
hour idle.

## The session's transcript

`lem session talk SLUG --from TEXT [--leave TEXT ...]` copies the turns of the session it runs in,
the one where the owner typed the request, into the new task's `talk.md`, from the transcript
Claude Code keeps of it: the file `~/.claude/projects/*/ID.jsonl`, with `ID` from
`CLAUDE_CODE_SESSION_ID`, which Claude Code gives the Bash tool (`CLAUDE_CONFIG_DIR`, when it is
set, stands for `~/.claude`). Run it from that session, never from a builder's. The transcript
keeps the turns from before a compaction, so the copy is word for word after one too (495 owner
records before the first `compact_boundary` in one transcript of Lem's own repository, read
2026-11-19). One JSON record a line, read this way (40 transcripts of Lem's own repository,
Claude Code 2.1.328, 2026-11-19): an owner's turn is a `user` record whose `origin.kind` is
`human`, with no `isMeta` (the text a skill loads) and no `isCompactSummary`; a task's
notification, agterm's mail and a peer's message have another origin; a `/lem` line is a command
record (`<command-name>/lem:lem</command-name>` with its `<command-args>`), copied as `/lem ARGS`;
a record with a `tool_result` and one with `isSidechain` (a subagent's) are no turn; the agent's
turn is the text blocks of the `assistant` records between two prompts. A transcript in which no
prompt has an origin is refused, since the owner's turns cannot then be told from the rest.
Untested: whether `CLAUDE_CODE_SESSION_ID` follows a `/clear`.

## mark-waiting

`agtermctl session status blocked --blink --auto-reset --target "$AGTERM_SESSION_ID"`: the sidebar
marks the session, and the mark goes back to idle once the owner visits it (the options of
`agtermctl session status --help`, read 2026-11-21). Not run yet.

## second-opinion

The reviewer is a second agent in the split pane of the session that asks (the pair of a plan
talk, for a careful or large plan); the owner reads both panes. The settings hold the seat as one
line, `reviewer = "AGENT/MODEL:EFFORT"` under `[seats]`, and `lem project show` gives it parsed as
`seats.reviewer`: its `agent` (`claude` or `codex`), its `model` and its `effort`, each null when
the line leaves it out, and `seat`, the line as written. The effort is the one of its pane for the
plan talk, which is the one thing this pane opens for.
When `agent` is null, ask the owner once and write the answer into `.lem/project.toml` as that line.

The seat may be this machine's own for a while: the usual reviewer is down, or out of tokens.
`/lem reviewer AGENT/MODEL:EFFORT` (`/lem reviewer codex/gpt-6.2-sol:high`, or `/lem reviewer
claude` for the agent's own model and effort) runs `lem project reviewer` with that seat, which
writes it into `.lem/project.local.toml` in the same form, a file git does not track; `/lem
reviewer default` removes it. Never change the seat by yourself. When the reviewer does not answer, or
says it is out of tokens, ask the owner once whether the other agent reviews for now, and write
the seat on his yes. While `lem project show` lists `seats.reviewer` under `local.overrides`,
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
     `MODEL` and `EFFORT` are the seat's `model` and `effort` from `lem project show`. Leave a flag
     out when the seat does not name its value (`null`): the agent's own default holds then.
   - read the model and the effort back from the pane's status line, and name those in the
     report, never the ones you asked for. When the status line shows no model or no effort (a
     status line of the owner's own may hide them), the report says `unread` for each, never the
     seat's value.
   - read `agtermctl tree --json` and confirm the session's `splitForeground` is that agent, then
     `mailbox-chat.py status` again.
   - Codex asks "Trust this folder?" the first time it starts in a repository, and it saves the
     answer in the owner's Codex configuration. That answer is the owner's: tell the owner that
     the reviewer's pane waits for it, and do not type into the pane. `mailbox-chat.py status`
     says `codex` once the pane listens.
   Under agterm's Live sessions mode, `agtermctl session restart --pane-id ID --command LINE` starts
   the same line without typing; in the other restore modes it is refused.
3. **Send the request** through the `mailbox-chat` skill: the plan's path, the directory to work
   in, the task it belongs to and the rule files
   that cover it (`lem project rules`, with the plan's files or `--range`). A message that names git goes from a file, never a heredoc.
4. **The reply arrives in this pane by itself.** Never poll for it, and check every claim it makes
   about the code with your own read before you act on it.
   A reply that may not be whole ("so far", a numbered point with no end) is answered in the same
   turn: accept or dispute its points and ask whether
   more follows. End the turn to wait only when the reviewer said that more follows.
5. **A reviewer is fresh for each review.** Before the next one, `agtermctl session split close`
   on this session ends the pane and its agent, and step 2 opens a new one. The dispute of a
   review's points and the check of the fixes it asked for belong to that review and stay in its
   pane. A plan talk is one review: every turn of it goes to the same pane.
   A new pane is not always a new Codex. With agterm's cookbook recipe for Codex session resume
   installed, a `codex` typed in a session continues that session's conversation: its wrapper
   keeps the session's Codex thread in `~/.codex/agterm/SESSION-ID` (the id in lower case), and
   every pane opened after it continues that thread (2026-11-14). So before the launch of step
   2, remove that file when it is there; after the launch, the pane's status line must show a
   context near zero. A reviewer that carries the last review reads the next one
   with it.

Say in the report which family reviewed. Two agents of one family agree more easily than two of
different ones; the report says "same family" when that was the case.

Not run yet: a Claude Code reviewer started this way, and a launch with a model or an effort flag
(the flags are in each command's `--help`, read on 2026-11-14).

## fan-out

Several `Agent` calls in one message. The `Workflow` tool only when the owner asked for one.

## ask-experts

Both in one message, so that they start at one moment; `BRIEF`, `WORKTREE` and each answer file
are the paths `lem experts brief` printed.

Each entry of the `experts` list that `lem experts brief` printed is one expert to start, from the
settings' `seats.experts`: its `name`, which is the `--expert` word of `lem experts record`, its
`agent`, `model` and `effort`, each null when the seat leaves it out, and its `answer` file.
Start each by its agent, and never with a model or an effort the entry does not name:

- an entry whose `agent` is `claude`: the `Agent`
  tool with `subagent_type: "Plan"`, `model` the entry's `model` (left out when it is null), `effort`
  the entry's `effort` only when it names one, and the prompt
  `Read BRIEF and follow it. Your reply is your answer, in the form the brief's last section
  gives, and nothing else.` The `Plan` agent has no edit or write tool, so it reads; it has Bash,
  so the brief's "change no file" is what keeps it from a write there. It runs in the
  background, and its reply reaches you as its message: write that reply into its answer file
  word for word, without the indent Claude Code puts before each line of a subagent's report,
  then run `lem experts record`.
- an entry whose `agent` is `codex`: the `Bash`
  tool with `run_in_background`, on this line, with `-m MODEL` only when the entry names a model
  and `-c model_reasoning_effort=EFFORT` only when it names an effort:

  ```bash
  codex exec -m MODEL -c model_reasoning_effort=EFFORT -s read-only --skip-git-repo-check --ephemeral -C WORKTREE -o ANSWER - < BRIEF > ANSWER.log 2>&1
  ```

  `-` reads the prompt from stdin, and the brief file is that stdin, so it ends: a Codex in the
  background whose stdin stays open waits for input and never starts (seen 2026-11-16, a headless
  Codex review). `-o` writes its last message into the answer file. You are told when the command
  exits; then run `lem experts record`. A non-zero exit, or an answer file that is not there, is
  an expert that did not answer: the skill's step 3 says what follows.

Not run yet: the two experts started from a `lem-builder` or from a task's session (Claude Code
2.1.325 and codex-cli 0.169.0 ran them from a subagent on 2026-11-16).

## run-in-background

The `Bash` tool with `run_in_background`, on the plain command as the stage gives it: `lem project
owner watch --seen N` for the watch of the owner's mark, `lem land checks SLUG` for the task's
checks, `lem session wait SLUG --until STATE,...` for the end of another session's work (it looks
every 10 seconds, a guess), and the `lem session close` line that `lem session next` prints. Keep
the name of each background task you started, and while one runs start no second of its kind. The tool names the background task
and tells you when the command exits, also while the session waits between two of the owner's
messages: the Bash tool's description in Claude Code 2.1.328 (read 2026-11-19) says that it
"re-invokes you when it exits", and the end of a background `codex exec` woke an idle session
on 2026-11-19. Then read the output file it named: the command's JSON on exit 0; on exit 1 the
JSON of checks that were red, refused or stopped, with its `say`, before the last line, `land.py:
...`, which alone is there for any other refusal, and for the watch of the mark its last line,
`project.py: ...`. The tool's limit of 10 minutes (600000 ms, the
same description) is the foreground's, so a check suite of twelve minutes runs to its end here.

A background command that an earlier session started is not yours, and its end wakes that session
only. To stop a watch or a wait of yours, when the owner says so, the `TaskStop` tool with its name; a
watch then ends with exit 1 and says that it was stopped. Stop the checks
with `lem land checks SLUG --stop`, never with `TaskStop` alone: that ends the shell and may leave
the script's process running with its lock, while `--stop` reaches it by the process id the lock
names, also from another session.

## A session's name

`agtermctl session rename "Lem init · REPO" --target "$AGTERM_SESSION_ID" --socket "$AGTERM_SOCKET"`
names this session, and `agtermctl session context 'TEXT' --target ...` puts one line about the
work into the title bar. A stage that runs for a repository the session did not start in (the
onboarding) does both, with the repository's name in each.

## The board

`lem board` opens the board as a page companion of this session's group: agterm shows the board
server's address (`agtermctl session overlay open --url URL --persistent --js --companion`), with
its cookies kept, so that a folded column outlives a relaunch of agterm. agterm gives such a page no
bridge (an `--url` page has none: measured in agterm 0.41.1 on 2026-11-20), so what only agterm does, the jump to a session and
the open of a task's session (`lem session open`), the board asks of the server, which runs them
on this Mac.

## show-page

An HTML file opened as a page companion of this session's group, as the board opens, never
as an overlay that covers the session: `lem board --page FILE --name NAME`, with the file's
absolute path and a short name for the sidebar (the task's slug and what the page is, as
`gift-note page`). It opens the page with read access to the folder that holds it, so the page
reads the `lem.css` and `lem.js` beside it, and a second call with the same file reloads its companion. It
prints the companion's id, which `agtermctl session close --target ID` closes when the page is
done with. Outside agterm it refuses: give the owner the file's path to read. A question that
waits for an answer (`ask-owner`, the `lem-ask` page) and a text to mark up still open over the
session, since the session waits for their result.
A document the owner should mark up (a plan, a draft profile) opens with the `webrev` skill,
given the file's path: a recipe of the agterm cookbook that Lem needs and does not bring (the
machine check's `webrev skill` row is required and has its guide). When the session has no such
skill, say so once, with the guide to install it by; then give the owner the file's path to read
as it is, and take the notes in the conversation. Do not install it unasked.

## ask-merger

One agent, started as an expert is (`ask-experts`), on the `seat` that `lem land merge-review SLUG`
printed: its `agent`, its `model` and its `effort`, each null when the seat leaves it out, which is
then the agent's own default. `BRIEF` and `ANSWER` are the `brief` and `answer` paths the step
printed, and `WORKTREE` its `worktree`.

- `agent` is `claude`: the `Agent` tool with `subagent_type: "Plan"`, `run_in_background`, `model`
  the seat's model (left out when it is null, so the session's own model answers), `effort` only when
  the seat names one, and the prompt `Read BRIEF and follow it. Your reply is the review, and nothing
  else.` The `Plan` agent has no edit or write tool. Write its reply into `ANSWER` word for word,
  without the indent Claude Code puts before each line of a subagent's report.
- `agent` is `codex`: the `Bash` tool with `run_in_background`, `-m MODEL` only when the seat names a
  model and `-c model_reasoning_effort=EFFORT` only when it names an effort:

  ```bash
  codex exec -m MODEL -c model_reasoning_effort=EFFORT -s read-only --skip-git-repo-check --ephemeral -C WORKTREE -o ANSWER - < BRIEF > ANSWER.log 2>&1
  ```

  A non-zero exit, or no answer file, is a merge agent that did not answer: start it once more, and
  after a second such end tell the owner in one line that the task waits for his read.

Then `lem land merge-review SLUG --file ANSWER`.

## take-screenshot

A page: headless Chrome with a throwaway profile, which is removed after the picture. On macOS Chrome
needs `--use-mock-keychain` and a `--user-data-dir` of its own, or it asks the login keychain and
writes into the owner's profile. A desktop picture is one call:

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --use-mock-keychain \
  --user-data-dir="$(mktemp -d)" --hide-scrollbars --window-size=1440,900 --force-device-scale-factor=2 \
  --screenshot=media/NAME-after.png URL
```

A phone, a dark scheme, a click before the picture or a part of a page take the DevTools protocol:
`Emulation.setDeviceMetricsOverride` (390 x 844, `deviceScaleFactor` 2, `mobile` true),
`Emulation.setTouchEmulationEnabled`, `Emulation.setEmulatedMedia` with `prefers-color-scheme`,
`Page.navigate`, then `Page.captureScreenshot`. Lem's own `tests/board-cdp.mjs` is such a driver in
Node, with the steps as JSON; a project with Playwright or another driver of its own uses that. Both
ways were checked on 2026-11-20 with Chrome 157.0.8103.51 and Node 26.9.0 on macOS: the call above
wrote a 2560 x 1600 picture, and the driver a 780 x 1688 one of a phone. A screen that is no web page
(a native window, a terminal) has no way checked here: say in one line that no picture was taken, and
why.

## start-nap

`run-in-background`, on this line, where `STATE` is the folder `lem project
state-dir` printed, `TIME` the `time` that `lem project may-nap` gave, and `SKILL_DIR` this skill's
directory:

```bash
cd STATE && env -u AGTERM_SESSION_ID -u AGTERM_SOCKET -u AGTERM_PANE_ID -u AGTERM_PANE -u AGTERM_WINDOW_ID -u AGTERM_WORKSPACE_ID -u AGTERM_ENABLED -u AGTERM_AGENT_RE -u CLAUDECODE -u CLAUDE_CODE_SESSION_ID -u CLAUDE_CODE_CHILD_SESSION -u CLAUDE_CODE_MESSAGING_SOCKET -u CLAUDE_CODE_MESSAGING_TOKEN claude -p --safe-mode --restricted --tools Read,Write,Glob --permission-mode acceptEdits --permission-prompts none --no-session-persistence "Your nap's time, by the clock: TIME. The brief is on stdin." < SKILL_DIR/prompts/nap.md > naps/.last.log 2>&1
```

A nap is a `claude -p` session of its own and no subagent of yours: it starts with nothing of your
context, as the owner's own naps start in a fresh session, and its end brings you only the exit
status. `--restricted` takes away every tool that runs a command and keeps the file tools inside
the working directory (Claude Code 2.1.326, 2026-11-17), which is `STATE`, and `--tools` gives
back the three a nap needs. It gets no search tool: the state folder's `.gitignore` is `*`, so a
search there finds nothing and says so as if nothing were there (a nap in a scratch repository,
Claude Code 2.1.330, 2026-11-21). `--safe-mode` loads no `CLAUDE.md`, skill, plugin, hook or MCP server: the nap reads its brief and the folder and
nothing else, and the correction hook never takes the brief for a message of the owner's.
`acceptEdits` lets it write in its folder, and `--permission-prompts none` refuses whatever would
ask, since nobody is there to answer. `--no-session-persistence` keeps it out of the session files
of the home directory. `env -u` takes away the variables of agterm and of your own session, so the
nap opens no page and sends nothing to you. `naps/.last.log` keeps what it printed, and the next
nap writes over it. The prompt names the time, and `prompts/nap.md` comes on stdin whole.

`spawn-builder` does not fit a nap: a subagent runs with your session's tools and settings, so the
limits above would be words in its brief only, and Claude Code once refused a builder the write of
a report file (above), where a nap writes three.

Not run yet: the line from a task's session, and a nap cut short by the close of the session
that started it.

## The correction hook

For a project that keeps a correction queue (`stages/learn.md`). The hook exits at once in every
repository whose settings do not say `corrections.collect = true`. That line is in the tracked
settings file, so it is the repository's yes: it holds for everybody who works there with the
hook and a key of the Jev model, and everybody can read it in git. Say that to the owner before he
says yes, in those words. One person says no for themselves with `collect = false` under
`[corrections]` in `.lem/project.local.toml`; that file can never say yes.

The hook comes with the plugin, in its `hooks/hooks.json`, and nobody registers anything. It
starts on each message in every repository where the plugin is on.

A settings file may name the hook too (`~/.claude/settings.json`, or a checkout's
`.claude/settings.local.json`). Beside the plugin it
starts a second copy for each message; the first copy claims the message, so it is still judged
once, and the machine check's `correction hook` row names each such file with the entry to delete
from it by hand. Say that in one line, and do not edit the file: it is the owner's.

- It needs Python 3.11 or newer as `python3`. Under an older one it judges nothing, and says so
  in its log. It finds `python3` and `git` on the hook's `PATH`, as any hook does; with no `git`
  there it queues nothing and has nowhere to say so, since git names its state folder. The
  model's client is Lem's own `jev.py`, run by its path. It needs `JEV_API_KEY` in the
  environment Claude Code starts with (`OPENROUTER_API_KEY` of a machine set up before is read
  when it is not set), and `JEV_API_URL` there for a provider other than OpenRouter.
- It prints nothing and does not wait for the model: a detached copy asks it. The hook's own two
  waits, for its input and for each of its git calls, end after two seconds each, a bound chosen by guess
  on 2026-11-15. The `timeout` of 10 seconds in `hooks/hooks.json` is the value its source ran with in one
  repository since 2026-11-07; it is not a measurement.
- What fails goes to `corrections.log` in Lem's state folder (`.lem/state/`), and
  `lem corrections list` counts it.
- The yes is a line of the tracked settings, which a task's branch and the owner's review carry
  like any other change. A hook that sends the owner's messages to an outside service is his to
  turn on: the line goes in only on his yes, in his words.

## What the owner does himself

Some steps are not an agent's, with or without the owner's yes in the conversation.

- **A folder's trust.** Claude Code asks whether the owner trusts a folder the first time a
  session starts in it, and Codex asks the same. That holds for a repository an agent made
  minutes before. The answer is kept in the owner's configuration, so it is his: say which
  session waits and where, and go on with other work. Do not answer the prompt, and do not go
  around it. A task's session that opens in a folder never trusted shows the dialog with "No,
  exit" selected first (the trial of 2026-11-21), and waits there for him. A task's session opens in
  the main checkout, which he trusts, and works in the task's worktree by its path: a session started
  in the worktree itself has no plugin installed for the project and none of the folder's own
  Claude Code settings (lem-scratch, Claude Code 2.1.330, 2026-11-21).
- **agterm's keymap.** The line of the task picker (the `line` of the `task picker` row of
  `lem doctor`) goes into agterm's own file, `~/.config/agterm/keymap.conf`, and the owner adds
  it: another program's settings stay where that program keeps them (his ruling). Give him the
  line and `agtermctl keymap reload`, and do not edit the file, also on his yes.
- **What the classifier refuses in auto mode.** It refuses these to the agent also after the
  owner's yes (mybaze, 2026-11-07): a push to another repository than the session's own, the
  registration of a hook that sends prompts to an outside service, and the install of a scheduler, whose login agent counts
  as persistence. When the classifier refuses a step, give the owner the exact command on one
  line and go on. Never send the step again in another form. It blocked the merge agent's merge,
  `lem land merge SLUG --by merger`, in one task's session and let it through in another
  (pySilver/lem-scratch#12, 2026-11-21), so no step rests on that call: the board's server runs it.
