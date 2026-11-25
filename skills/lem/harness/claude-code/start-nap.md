<!-- lem: old form -->
# Claude Code: start-nap

A part of `../claude-code.md`, read when a session starts a nap.

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
a report file (`spawn-builder`), where a nap writes three.

Not run yet: the line from a task's session, and a nap cut short by the close of the session
that started it.
