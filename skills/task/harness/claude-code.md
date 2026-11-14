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

Inside agterm (`AGTERM_SESSION_ID` is set), the `huddle:huddle` skill: one page, each option with
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

The `Agent` tool with `subagent_type: "second-opinion"` when the session lists it, otherwise
`subagent_type: "general-purpose"` on the session's own model, told to change no file. When a
Codex is paired in the adjacent agterm pane, it is the other model family: send it the request
through the `mailbox-chat` skill instead, and say in the report which of the two read the plan.

## fan-out

Several `Agent` calls in one message. The `Workflow` tool only when the owner asked for one.

## show-page

Inside agterm, an HTML file opened as an overlay of this session
(`agtermctl session overlay open --html FILE --target "$AGTERM_SESSION_ID"`). Elsewhere, the text
in the reply.
