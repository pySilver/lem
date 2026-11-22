---
worth: later
where: skills/lem/scripts/session_hook.py:keep_transcript
added: 2026-11-22
---
# A forked transcript of Claude Code's daemon is logged on the task of another pane

keep_transcript takes the task from LEM_TASK in the hook's environment, and a spare of Claude Code's background daemon keeps the environment of the pane that started the daemon. The forked transcript 6fe214ec of merge-leaves-board-lock was logged at 2026-11-22 10:45:56Z as a session.transcript of board-card-search. lem_tokens.py counts by task, so it counts that transcript for the wrong task, and maybe twice (not measured). The guard of a stopped session is safe from it since the record carries the agterm session (the field `session`) and the signs read only the newest open's session; the token count is not. In reach of the topic "A task's record is lost or wrong".

Seen by the investigator of task dead-tasks-woken-or-shown (its outside.md, 2026-11-22); the base commit has it.
