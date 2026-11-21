# Claude Code

You run in Claude Code. This file answers `README.md` beside it.

It is the core: what every phase needs, read once per session. Each other capability and
role has a part of its own in `claude-code/` beside this file, which a session reads at the first
use of that capability, once:

| Part | Answers |
| --- | --- |
| `claude-code/ask-owner.md` | `ask-owner` |
| `claude-code/review-tool.md` | the review tool |
| `claude-code/tracker.md` | the tracker |
| `claude-code/task-session.md` | `open-task-session` for a task's own session: its launch, the context's number, a wake-up, the session's transcript (`lem session talk`) |
| `claude-code/plan-talk.md` | `open-task-session` for the plan talk's pair |
| `claude-code/second-opinion.md` | `second-opinion`: the reviewer's pane |
| `claude-code/ask-experts.md` | `ask-experts` |
| `claude-code/ask-merger.md` | `ask-merger` |
| `claude-code/show-page.md` | `show-page`, and the board |
| `claude-code/take-screenshot.md` | `take-screenshot` |
| `claude-code/start-nap.md` | `start-nap` |
| `claude-code/correction-hook.md` | the correction hook |
| `claude-code/onboarding.md` | what only `/lem init` needs |
| `claude-code/owner-steps.md` | what the owner does himself: a folder's trust, agterm's keymap |

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
- the review tool: `claude-code/review-tool.md`.
- the tracker: `claude-code/tracker.md`.
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

## fan-out

Several `Agent` calls in one message. The `Workflow` tool only when the owner asked for one.

## mark-waiting

`agtermctl session status blocked --blink --auto-reset --target "$AGTERM_SESSION_ID"`: the sidebar
marks the session, and the mark goes back to idle once the owner visits it (the options of
`agtermctl session status --help`, read 2026-11-21). Not run yet.

## Auto mode

**What the classifier refuses in auto mode.** It refuses these to the agent also after the
owner's yes (mybaze, 2026-11-07): a push to another repository than the session's own, the
registration of a hook that sends prompts to an outside service, and the install of a scheduler, whose login agent counts
as persistence. When the classifier refuses a step, give the owner the exact command on one
line and go on. Never send the step again in another form. It blocked the merge agent's merge,
`lem land merge SLUG --by merger`, in one task's session and let it through in another
(pySilver/lem-scratch#12, 2026-11-21), so no step rests on that call: the board's server runs it.
