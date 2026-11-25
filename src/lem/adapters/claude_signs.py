"""The signs of work of one Claude Code transcript, for the `Harness` port on Claude Code
(`harness_claude`).

Its newest sign is the newest of its main thread and of each of its subagents
(`ID/subagents/agent-*.jsonl` beside it, each with an `agent-*.meta.json` that is no
transcript); its turn is its main thread's alone, since an interview's scout runs in the
background while the session's turn has ended on its question to the owner. A shell command of
the session runs when a direct child of its Claude Code process sources the shell's snapshot.

When no process file of the transcript's folder names the session, when its pid is gone, or
when the process table does not read, the signs do not read: `Signs()`, with no sign, no shell
and no turn. With no process to read there is no evidence that no shell runs, and a guard that
restarted such a session could put two agents on one task.
"""

from pathlib import Path
from typing import TYPE_CHECKING

from lem.adapters import claude_processes, claude_tail
from lem.ports.harness import Signs

if TYPE_CHECKING:
    from datetime import datetime

    from lem.ports.harness import Transcript

# The mark of a Bash tool's command line: it sources the shell's snapshot first. A subagent's
# Bash command has the same parent and the same form (seen with a subagent's `sleep 40`,
# 2026-11-22).
SNAPSHOT = "shell-snapshots/snapshot-"


def signs_of(transcript: Transcript, table: claude_processes.Table) -> Signs:
    """The signs of `transcript`, read now; `Signs()` when its process does not read."""
    path = Path(transcript.path)
    pids = claude_processes.pids_of(path, transcript.claude)
    commands = claude_processes.children(table, pids)
    if commands is None:
        return Signs()
    shell = any(SNAPSHOT in command for command in commands)
    return Signs(sign=newest_sign(path), shell=shell, turn=claude_tail.file_turn(path))


def newest_sign(path: Path) -> datetime | None:
    """The newest sign of the transcript at `path` and of its subagents."""
    subagents = sorted((path.with_suffix("") / "subagents").glob("agent-*.jsonl"))
    signs = (claude_tail.file_sign(each) for each in (path, *subagents))
    return max((sign for sign in signs if sign is not None), default=None)
