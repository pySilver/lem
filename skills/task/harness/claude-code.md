# Claude Code

You run in Claude Code. This file answers `README.md` beside it.

## load-skill

The `Skill` tool. Do not load a skill whose instructions are already in context.

- the question gate: `decide:gate`
- the persona panel: `decide:panel`. It reads the cast from `.personas/cast/`; a project whose
  settings name another personas path is not served by it yet, so say so instead of running it on
  a built-in cast.
- the review tool: `revmux:revmux`, with `--config-dir` set to the settings' `review` path.
  Its starter set: `revmux init` at the root of the checkout always writes `./.revmux/`
  (config, lenses, prompts), whatever `--config-dir` says; when the settings' `review` path is
  another folder, move `.revmux` there afterwards. `revmux --config-dir PATH config` then
  prints that folder as its `config_dir` (checked on revmux v0.2.7).

## ask-owner

Inside agterm (`AGTERM_SESSION_ID` is set), the `huddle` skill: one page, each option with
what the owner would see and what it costs. Elsewhere, `AskUserQuestion`. The owner's global
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

## second-opinion

The reviewer is a second agent in the split pane of this session, of the family the settings'
`seats.reviewer` names (`claude` or `codex`); the owner reads both panes. When the setting is null,
ask the owner once and write the answer into `.agents/project.toml`.

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

Inside agterm, an HTML file opened as an overlay of this session
(`agtermctl session overlay open --html FILE --target "$AGTERM_SESSION_ID"`). A document the
owner should mark up (a plan, a draft profile) goes through the `webrev` skill, or through
plannotator when the machine check found it. Elsewhere, the text in the reply.
