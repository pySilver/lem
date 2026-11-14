# Claude Code

You run in Claude Code. This file answers `README.md` beside it.

## load-skill

The `Skill` tool. Do not load a skill whose instructions are already in context.

- the question gate: the `gate` skill of this repository.
- the persona panel: the `panel` skill of this repository. It finds the cast and the profile
  through the project's settings.
- the review tool: `revmux:revmux`, with `--config-dir` set to the settings' `review` path.
  Its starter set: `revmux init` at the root of the checkout always writes `./.revmux/`
  (config, lenses, prompts), whatever `--config-dir` says; when the settings' `review` path is
  another folder, move `.revmux` there afterwards. `revmux --config-dir PATH config` then
  prints that folder as its `config_dir` (checked on revmux v0.2.7).

## ask-owner

The `huddle` skill: one page, each option with what the owner would see and what it costs.
A value the owner types (a name, a path) is asked in the terminal. The owner's global
instructions say how a question is told; they outrank this file.

## spawn-builder

The `Agent` tool with `subagent_type: "worker"` when the session lists that agent type, otherwise
`subagent_type: "general-purpose"` with `model: "opus"`. The brief gives the task's worktree as an
absolute path and tells the builder to work only there; do not pass `isolation: "worktree"`, since
the task already has its worktree. Agents run in the background and you are told when one ends:
never predict a builder's report, and never poll for it.

A builder in a worktree session meets Claude Code's Bash guard. Tell it to write literal absolute
paths and plain commands: no shell variables, no `$(...)`, no loops, and a file instead of a
heredoc when the text names git.

A builder is one context with no pane of its own, so no reviewer sits beside it and the owner
cannot type to it. A careful or large task gets a session for that reason.

## open-task-session

A companion session of this one, which runs Claude Code with the brief's file named in its first
prompt.

1. **Write the brief** to a file in the task directory (`brief.md`). Add one line to it:
   `coordinator: SESSION:PANE`, with this session's `AGTERM_SESSION_ID` and this pane's
   `AGTERM_PANE_ID`.
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
a careful task), of the family the settings' `seats.reviewer` names (`claude` or `codex`); the
owner reads both panes. When the setting is null,
ask the owner once and write the answer into `.lem/project.toml`.

1. **Is a reviewer there?** `mailbox-chat.py status` names the other pane and what serves it:
   `claude`, `codex` or `none`.
2. **Open the seat** when there is no split or nothing serves it:
   - `agtermctl session split on --target "$AGTERM_SESSION_ID" --socket "$AGTERM_SOCKET"`;
   - write the launch line to a file and type it into the right pane with
     `agtermctl session type --stdin --pane right --target "$AGTERM_SESSION_ID" --socket "$AGTERM_SOCKET" < FILE`.
     The line starts the agent with the reviewer's brief, `prompts/reviewer.md` in this skill's
     directory, by absolute path:
     - Codex: `codex "$(cat PATH/prompts/reviewer.md)"`. A Codex pane receives mail only after
       its first prompt, and the brief is that prompt.
     - Claude Code: `claude --append-system-prompt "$(cat PATH/prompts/reviewer.md)" "You are the reviewer. Wait for the first message."`
   - read `agtermctl tree --json` and confirm the session's `splitForeground` is that agent, then
     `mailbox-chat.py status` again.
   Under agterm's Live sessions mode, `agtermctl session restart --pane-id ID --command LINE` starts
   the same line without typing; in the other restore modes it is refused.
3. **Send the request** through the `mailbox-chat` skill: what to review (the plan's path, or the
   range of commits), the directory to work in, the task it belongs to and the style guide files
   that cover it. A message that names git goes from a file, never a heredoc.
4. **The reply arrives in this pane by itself.** Never poll for it, and check every claim it makes
   about the code with your own read before you act on it.
5. **A reviewer is fresh for each review.** Before the next one, `agtermctl session split close`
   on this session ends the pane and its agent, and step 2 opens a new one.

Say in the report which family reviewed. Two agents of one family agree more easily than two of
different ones; the report says "same family" when that was the case.

Checked on 2026-11-14 with agterm in its rerun restore mode: a split opened on a background
session, a program started by a typed line, and its name read back from `splitForeground`. Not
run yet: a real reviewer started this way and a mail round trip with it.

## fan-out

Several `Agent` calls in one message. The `Workflow` tool only when the owner asked for one.

## show-page

An HTML file opened as an overlay of this session
(`agtermctl session overlay open --html FILE --target "$AGTERM_SESSION_ID" --socket "$AGTERM_SOCKET"`).
A document the owner should mark up (a plan, a draft profile) goes through the settings'
`tools.annotate`: a skill of that name when the session lists one (`webrev` by default), otherwise
a command of that name given the file's path.
