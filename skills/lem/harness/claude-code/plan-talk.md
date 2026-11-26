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
   `MODEL` and `EFFORT` are the `model` and the `effort` that `lem seat show SLUG planner`
   prints, the seat in use for the task: a stand-in while one holds that seat, else the settings'
   `seats.planner`, parsed from its one line, `claude/MODEL:EFFORT`. Keep its `seat`, the line you
   opened: a failure names it. A defender's seat always names its model and its effort. The seat's
   `agent` can only be `claude`, since this agent's file is the only one the contract was checked in.
   `PLUGIN` is the `plugin_dir` that `lem --repo MAIN session plugin-dir` prints, so that the
   defender loads the plugin of the same build as the app, as the task's session does
   (`task-session.md`): when the project has no enabled install of the plugin `lem@lem`, it is the
   app's own data folder; when it loads the installed plugin, it is null, and the line leaves out
   `--plugin-dir \"PLUGIN\"`.
2. **Confirm it runs**: the command prints the new session's id; keep it, since the lead's wait
   takes it (`lem session wait SLUG --until planned,held,blocked --companion ID --quiet
   TASK_DIR/talk-turns.md`). In `agtermctl tree --json` the node with that id has a `foreground`
   that ends in the `claude` line, and its `parent` is this session. Only a node that is gone at
   once means the command failed; then open it again with `--wait` and read its screen with
   `agtermctl session text --target ID`. Never open a second pair for a task whose first one
   runs; a lead after a restart finds it in the tree by its name. The defender reads the model and
   effort from the status line in the pair with `agtermctl session text --target "$AGTERM_SESSION_ID"
   --pane primary --socket "$AGTERM_SOCKET"` and puts those values in the plan's talk section.
   A status line of the owner's own may show neither: write `unread` for each value it does not show.
   A pair whose screen shows an error of `second-opinion.md` (`command not found:
   claude`, no login, no tokens or a usage limit, a model it does not know), at once or after the
   open with `--wait` of a node that was gone at once, is a seat that failed: close what is left
   of it (step 4), and run

   ```bash
   lem seat failed SLUG planner --seat "LINE" --error KIND --said "ITS WORDS"
   ```

   `LINE` being the `seat` you opened, `KIND` one of `missing`, `login`, `tokens`, `usage-limit` and `model`, and
   `ITS WORDS` the line of the error on its screen. It prints a seat to open, the fallback that
   stands in for the planner from now on: say its `say` in one line and open the pair at step 1
   on that seat. Or it prints `blocked: true`: the task is `blocked` with the seat and the error;
   write no state over it, and take the block as `stages/plan.md`, step 4.3, says for one, which
   marks this session as waiting before its line to the owner.
3. **Read its two screens** when the lead's wait names the file in `quiet` (`stages/plan.md`, step
   4.3): the defender's pane with `agtermctl session text --target ID --pane primary --socket
   "$AGTERM_SOCKET"`, and the reviewer's with `--pane split` in its place. Look on each for one of
   the errors of `second-opinion.md`, in the last lines the agent wrote.
4. **Close it** once the lead's wait ended (`stages/plan.md`, step 4), or when the task is
   dropped: `agtermctl session close --target ID --socket "$AGTERM_SOCKET"`. Its experts and the
   reviewer's pane end with it.

Not run yet: a pair opened from a task's session, with `--plugin-dir` or without it.
