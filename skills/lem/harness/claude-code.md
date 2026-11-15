# Claude Code

You run in Claude Code. This file answers `README.md` beside it.

## load-skill

The `Skill` tool. Do not load a skill whose instructions are already in context.

- the question gate: the `lem-gate` skill of this repository.
- the persona panel: the `lem-panel` skill of this repository. It finds the cast and the profile
  through the project's settings.
- the review tool: `revmux:revmux`. It reads the project's lenses, prompts and profile from
  `./.revmux` at the root of the checkout and from no other path. So a project whose settings
  keep the review folder elsewhere (`.lem/review`) has a link `.revmux` that points at it, and
  git stores the link; `project.py migrate run` makes it. Its starter set: `revmux init` always
  writes `./.revmux/` (config, lenses, prompts); move that folder to the settings' `review` path
  and leave the link.
  Checked on revmux v0.2.7, 2026-11-15, with `revmux config`: through the link it reports
  `project_dir` as `./.revmux` and keeps the user's own folder as `config_dir`. The flag
  `--config-dir PATH` is not the way: it puts PATH in the place of the user's own config folder,
  and no project folder is reported.
- the rules folder. Claude Code loads `.claude/rules/` by itself: a file with a `paths:` line
  when a matching file is read, the others in every session. After `project.py migrate run`
  that folder holds a link for each moved rule. Checked by the session that started Lem, in
  Claude Code 2.1.325 on 2026-11-14, with all tools off so that only a loaded rule could give
  the answer: a linked file in a real rules folder is loaded; a rule with a `paths:` line
  reached through a link is loaded when a matching file is read and not before; an `@` import
  line inside a rules file is not expanded, so a rules file cannot stand in for a moved one.

## ask-owner

The `lem-huddle` skill, for every question that asks the owner to choose or to approve: one page,
each option with what the owner would see and what it costs. The owner never types `/lem huddle`;
Lem opens the page. Three kinds of question stay in the terminal: a value the owner types (a name,
a path, a number), a bare go-ahead on a step just described, and a fixed, trivial choice that
needs no context. The owner's global instructions say how a question is told; they outrank this
file.

## spawn-builder

The `Agent` tool with `subagent_type: "lem-builder"`. Lem brings that agent: `agents/lem-builder.md`
in Lem's repository, linked into `~/.claude/agents/` by the setup. Its body holds the builder's
standing rules, so a brief stays short and no builder misses one; its frontmatter sets the model
and the effort, because a subagent on another model than the session's does not take the
session's effort. There is no fallback to another agent type: when the session does not list
`lem-builder`, the setup is not done; say so, name `doctor.py`, and stop.

A project that wants another builder (another model, more rules) keeps a file of the same name in
its own `.claude/agents/`. Claude Code takes the project's definition before the user's (its
documentation gives the order: managed, the `--agents` flag, the project, the user, a plugin;
https://code.claude.com/docs/en/sub-agents, read 2026-11-15). No setting of Lem's is involved.

The brief gives the task's worktree as an absolute path; do not pass `isolation: "worktree"`,
since the task already has its worktree. Agents run in the background and you are told when one
ends: never predict a builder's report, and never poll for it.

A builder can start builders of its own with the same tool, so a builder leads a plan of more
tasks. Checked on 2026-11-14 in Claude Code 2.1.325: a subagent of the type `worker`, which like
`lem-builder` names no tool list and so inherits every tool, called `Agent`, and the nested
agent's reply came back to it. Not run yet: the same from a `lem-builder`. A builder has no pane
of its own, so no reviewer sits beside it and the owner cannot type to it. A careful task gets a
session for that reason.

## open-task-session

A companion session of this one, which runs Claude Code with the brief's file named in its first
prompt.

1. **The brief** is the task's `brief.md`. Add one line to it: `coordinator: SESSION:PANE`, with
   this session's `AGTERM_SESSION_ID` and this pane's `AGTERM_PANE_ID`.
2. **Open the session**:

   ```bash
   agtermctl session new --parent "$AGTERM_SESSION_ID" --cwd WORKTREE --name SLUG --no-select \
     --command "LOGIN_SHELL -l -c 'claude \"Read BRIEF and follow it.\"'" --socket "$AGTERM_SOCKET"
   ```

   `LOGIN_SHELL` is the owner's login shell by absolute path
   (`dscl . -read /Users/NAME UserShell`), not the shell of your own Bash tool. agterm starts the
   command with its own `PATH`, and only the login shell finds `claude` the way the owner's
   terminal does: on a Mac whose login shell is fish, `zsh -lc` answered `command not found:
   claude`. The line has no command substitution, so zsh and fish read it the same way. Pass no
   flag that widens the session's permissions: it runs in the permission mode the owner's
   settings give a new session.
3. **Confirm it runs**: the command prints the new session's id. In `agtermctl tree --json` the
   node with that id has `parent` set to this session and a `foreground` that ends in the
   `claude` line. A node that is gone at once means the command failed; open it again with
   `--wait` and read its screen with `agtermctl session text --target ID`. Write the id in the
   task's state.
4. **Send it a message** later (the owner's answers, a changed base):
   `agtermctl msg send --stdin --to ID:left --socket "$AGTERM_SOCKET" < FILE`. The mailbox hook of
   the mailbox chat hands it to the agent there at the end of its turn. When the session is gone,
   open one again: the new lead reads the task's files.
5. **Close it** after the landing: `agtermctl session close --target ID --socket "$AGTERM_SOCKET"`.

Under agterm's rerun restore mode a relaunch of agterm starts each session's command again. A
lead started that way is a fresh agent with the same brief; `prompts/lead.md` tells it to read the
task's state first, so it goes on or stops.

Checked on 2026-11-14 with agterm 0.41.1 in its rerun restore mode: a companion session opened
with this line through a fish login shell, Claude Code ran its prompt there, and `foreground` and
`parent` read back from the tree. Not run yet: a lead that took a whole task this way, a message
sent to a lead (step 4), and a relaunch of agterm with a lead's session open.

## tell-coordinator

In a task's session, with the address from the brief's `coordinator:` line:

```bash
agtermctl msg send "lem: SLUG is STATUS" --to SESSION:PANE --socket "$AGTERM_SOCKET"
```

One line, after the report and the state are written. It reaches Lem as mail that starts with
`[agterm mailbox, not a peer chat message]`; Lem reads the task's state, never the line's claim.
Mail is kept in memory only, so a pane that was restarted has lost it. That costs nothing but
time: the state block is on disk, and `/lem status` shows it.

Checked on 2026-11-14: this command, run by Claude Code in a companion session, put its line in
the mailbox of the pane that opened the session. Not run yet: the hook waking an idle Lem with it.

## second-opinion

The reviewer is a second agent in the split pane of the session that asks (a task's session, for
a careful task); the owner reads both panes. `project.py show` gives the seat as
`seats.reviewer`: its `agent` (`claude` or `codex`) and, when the project or this machine set
them, its `model`, its `effort` for the review of a diff and its `plan_effort` for the read of a
careful plan. When `agent` is null, ask the owner once and write the answer into
`.lem/project.toml`.

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
     The effort is `plan_effort` when the review is the read of a plan, and `effort` otherwise.
     Leave a flag out when the seat does not name its value: the agent's own default holds then.
     The reviewer's pane is new for each review, so a plan read simply starts with its own effort.
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
   that cover it. A message that names git goes from a file, never a heredoc.
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
   pane.
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

## show-page

An HTML file opened as an overlay of this session
(`agtermctl session overlay open --html FILE --target "$AGTERM_SESSION_ID" --socket "$AGTERM_SOCKET"`).
A document the owner should mark up (a plan, a draft profile) goes through the settings'
`tools.annotate`: a skill of that name when the session lists one (`lem-webrev` by default), otherwise
a command of that name given the file's path.

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
