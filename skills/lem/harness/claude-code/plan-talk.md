# Claude Code: the plan talk's pair

A part of `../claude-code.md`, read when a lead opens the pair (`open-task-session`).

## The plan talk's pair

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
   `agent` can only be `claude`, since this agent's file is the only one the contract was checked in.
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
