"""The `Harness` port on Claude Code (the design's part 4).

`launch` gives the line a login shell runs to start a task's session (`claude_launch`), with
`--plugin-dir` only where the project loads no installed plugin of Lem (`plugin_folder`,
`claude_plugin`). BRIEF is the task's `session.md`, whose folder names the task.

A transcript counts for a task by the rule of the design's part 3: read across every task's
`sessions.jsonl`, each path once, by its first prompt, and by the line's task when the prompt
names none, so that a fork logged under another task counts for the task its first prompt
names (`claude_transcript`). A task that ended keeps its `sessions.jsonl`, so its forks still
count. The signs of one transcript read its end, its subagents and its process
(`claude_signs`); the tokens read every reply once (`claude_tokens`).
"""

import shutil
from pathlib import Path
from typing import TYPE_CHECKING

from lem.adapters import (
    claude_launch,
    claude_plugin,
    claude_processes,
    claude_signs,
    claude_tail,
    claude_tokens,
    claude_transcript,
)
from lem.ports.harness import Missing, Seat, Signs, Tokens, Transcript
from lem.store import places, sessions

if TYPE_CHECKING:
    from datetime import datetime

    from lem.ports.place import Place
    from lem.records.sessions import SessionLine


class ClaudeHarness:
    """Claude Code for the seats of one workspace, and its transcripts."""

    def __init__(self, place: Place, table: claude_processes.Table) -> None:
        """Keep where the adapter works, and the machine's process table."""
        self.place = place
        self.table = table

    def launch(self, seat: Seat, brief: str, cwd: Path, plugin_dir: Path | None) -> str:
        """The line a login shell runs to start the seat's agent on `brief`, in `cwd`."""
        plugin = self.plugin_folder(plugin_dir) if plugin_dir else None
        tokens = claude_launch.compaction(self.place.home, self.place.environ)
        words = claude_launch.launch_words(seat, Path(brief), plugin, tokens)
        return " ".join(claude_launch.shell_word(word) for word in words)

    def plugin_folder(self, plugin_dir: Path) -> Path | None:
        """The folder `--plugin-dir` names for this checkout, `plugin_dir`; None when the
        project loads the installed plugin."""
        if claude_plugin.selected(self.place.checkout, self.place.environ) is not None:
            return None
        return plugin_dir

    def transcripts(self, task: str) -> tuple[Transcript, ...]:
        """The transcripts that count for `task`, each once, by the time its first session
        started."""
        named: dict[str, str | None] = {}
        found: dict[str, Transcript] = {}
        for line in logged(self.place.checkout / places.STATE):
            path = line.transcript
            if path not in named:
                named[path] = claude_transcript.task_named(Path(path))
            if (named[path] or line.task) == task:
                found.setdefault(path, Transcript(path=path, claude=line.claude))
        return tuple(found.values())

    def signs(self, transcript: Transcript) -> Signs:
        """The newest sign of the transcript and its subagents, whether a shell command of its
        session runs, and whether its turn runs."""
        return claude_signs.signs_of(transcript, self.table)

    def tokens(self, transcripts: tuple[Transcript, ...]) -> Tokens:
        """The tokens the transcripts and their subagents spent."""
        return claude_tokens.tokens_of(transcripts)

    def available(self, seat: Seat) -> Missing | None:
        """Whether the seat's agent can run here: Claude Code on the PATH."""
        if seat.agent != claude_launch.AGENT:
            return Missing(error="missing", said=f"{seat.agent} is no Claude Code")
        path = self.place.environ.get("PATH", "")
        found = shutil.which(claude_launch.AGENT, path=path)
        return None if found else Missing(error="missing", said="no claude on the PATH")


class ClaudeHarnessLooks(ClaudeHarness):
    """The port, and what a task's session reads beside it."""

    def main_sign(self, transcript: Transcript) -> datetime | None:
        """The newest sign of the transcript's main thread alone, beside the port: the
        session's turn is that of the transcript whose main thread wrote the newest turn."""
        return claude_tail.file_sign(Path(transcript.path))


def logged(state: Path) -> list[SessionLine]:
    """Every session line of every task of the workspace, by the time each started."""
    folder = state / "tasks"
    if not folder.is_dir():
        return []
    named = (path.name for path in folder.iterdir())
    slugs = sorted(name for name in named if places.SLUG.fullmatch(name))
    lines = [line for slug in slugs for line in sessions.read(folder / slug)]
    return sorted(lines, key=lambda line: line.at)


def bind(place: Place) -> ClaudeHarnessLooks:
    """Claude Code for the place's workspace, with this machine's process table."""
    return ClaudeHarnessLooks(place, claude_processes.Machine())
