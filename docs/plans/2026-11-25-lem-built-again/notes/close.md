# What still needs its step after close preparation

- **Trial R2.** Run the breaker's Help from the board and end the talk without a decision.
  Check that the answer remains on record and the page offers Help, Park and Drop again.
- **Sessions and ask.** The Stop selector returns silence in `hooks/stop.py`. It does not preserve
  the mark for an unanswered question or check the terminal tree. Restore the mark before A5.
- **Add-ons outside.** The peer warning can outlive a successful relay. Also check when a malformed
  peer setting should appear as a board warning. The current loader refuses a port of the wrong
  type before the workspace page can show the warning.
- **Board views.** `board/templates/task/now.html` can show the task's opening line, but
  `board/views/panel/now.py` supplies no opening. Show the line while the opening state is the
  newest. The timeline has a close time for each check run. It does not get live command
  completions from a run still in progress. The decision label parser also treats a colon in
  single quotes as a separator.
- **Landing and sessions.** The proposal omits the criteria wait from its read line
  (`app/landing/pr_read.py`). The merge read needs proof that the seat kept with the exact brief
  survives a retry and a setting change.
- **Lem's project settings.** The `checks.commands` entry in `.lem/settings.toml` names the
  former shell runner. Align it with the rebuilt test entry before proving setup from a new
  Lem worktree.
