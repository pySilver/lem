# Claude Code: the plan talk's pair

A part of `../claude-code.md`, read when a lead opens the pair (`open-task-session`).

## The plan talk's pair

A companion session of the lead's, `SLUG · plan talk`, which runs Claude Code with
`talk-brief.md` named in its first prompt; its agent is the plan's defender
(`prompts/defender.md`), and the reviewer sits in its other pane (`second-opinion`).

1. **Open it**:

   ```bash
   agtermctl session new --parent "$AGTERM_SESSION_ID" --cwd "MAIN" --name "SLUG · plan talk" --no-select \
     --command "LOGIN_SHELL -l -c 'claude --model \"MODEL\" --effort \"EFFORT\" --plugin-dir \"PLUGIN\" \"Read BRIEF and follow it.\"'" --socket "$AGTERM_SOCKET"
   ```

   Keep every quote of the line: the login shell reads the inner command, and zsh stops a bare
   model such as `opus[1m]` with "no matches found". A path with a quote, a `$`, a backquote or a
   backslash breaks the line; then tell the owner in one line that the pair cannot open from that
   checkout, and hold the task.

   `LOGIN_SHELL` is the owner's login shell by absolute path, as `task-session.md` finds it
   (`dscl . -read /Users/NAME UserShell`), never `$SHELL`: in a task's session `$SHELL` gave
   `/bin/zsh`, whose login `PATH` has no `claude`, and the pair failed twice with "command not
   found: claude"; the login shell, fish, opened it (moved-base-merge-agent-call, 2026-11-22).
   `MAIN` is the main checkout, where the task's session stands too: the pair has the plugin and
   the folder's own Claude Code settings there, and reaches the task's worktree by its path, as
   the session does (`owner-steps.md`, "A folder's trust").
   `MODEL` and `EFFORT` are the `model` and the `effort` of the settings' `seats.planner`, which
   `lem project show` gives parsed from its one line, `claude/MODEL:EFFORT`; the settings refuse a
   defender's seat with no model or no effort. The seat's
   `agent` can only be `claude`, since this agent's file is the only one the contract was checked in.
   `PLUGIN` is the `plugin_dir` that `lem session plugin-dir` prints, so that the defender runs the
   Lem of the session that opens it, as the task's session runs the Lem that opened it
   (`task-session.md`): when this Lem is not the installed plugin (its folder is outside
   `~/.claude/plugins/`, or outside `plugins/` of `CLAUDE_CONFIG_DIR`), it is that folder; when it
   is the installed plugin, it is null, and the line leaves out `--plugin-dir \"PLUGIN\"`.
2. **Confirm it runs**: the command prints the new session's id; keep it, since the lead's wait
   takes it (`lem session wait SLUG --until planned,held --companion ID`). In `agtermctl tree
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

Not run yet: a pair opened from a task's session, with `--plugin-dir` or without it.
