"""The `Harness` port on Claude Code (the design's part 4).

`launch` gives the line a login shell runs to start a task's session: `LEM_TASK=SLUG`, which the
`session-start` hook reads, then `claude`, the seat's model and effort, `--plugin-dir` with the
app's plugin folder, and the first prompt, `Read BRIEF and follow it.`. BRIEF is the task's
`session.md`, whose folder names the task. Each word is quoted for sh, zsh and fish alike: bare
when it needs no quote, in double quotes when it holds nothing those read inside them, so that
the usual line stays readable in agterm's tree.

A transcript counts for a task by the rule of the design's part 3: read across every task's
`sessions.jsonl`, each path once, by its first prompt, and by the line's task when the prompt
names none, so that a fork logged under another task counts for the task its first prompt
names (`claude_transcript`). The signs read the transcript's end (`claude_turns`); whether a
shell command of the session runs, and the tokens of a task, are not read in this slice.
"""

import re
import shlex
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

from lem.adapters import claude_transcript, claude_turns
from lem.kernel.errors import Fault, Refusal
from lem.ports.harness import Missing, Seat, Signs, Tokens, Transcript
from lem.store import places, sessions

if TYPE_CHECKING:
    from collections.abc import Mapping

    from lem.ports.place import Place
    from lem.records.sessions import SessionLine

# A backslash or a line break: no quote carries it to every login shell (fish reads a
# backslash inside quotes as an escape).
UNQUOTABLE = re.compile(r"[\\\n]")
# What sh, zsh and fish read inside double quotes.
DOUBLE_QUOTED = re.compile(r"[\"$`\\]")
AGENT = "claude"


def shell_word(word: str) -> str:
    """`word` as one word of sh, zsh and fish alike; refused when no quote carries it."""
    if UNQUOTABLE.search(word):
        raise Refusal(
            "unquotable",
            f"{word!r} holds a backslash or a line break, which the launch line cannot "
            "carry to every login shell",
            "the owner moves the folder, or writes the seat, without them",
        )
    if shlex.quote(word) == word:
        return word
    return shlex.quote(word) if DOUBLE_QUOTED.search(word) else f'"{word}"'


def launch_words(seat: Seat, brief: Path, plugin_dir: Path | None) -> list[str]:
    """The words of the launch line, before their quotes."""
    slug = brief.parent.name
    words = [f"LEM_TASK={slug}", AGENT]
    if seat.model:
        words.extend(("--model", seat.model))
    if seat.effort:
        words.extend(("--effort", seat.effort))
    if plugin_dir is not None:
        words.extend(("--plugin-dir", str(plugin_dir)))
    words.append(f"Read {brief} and follow it.")
    return words


class ClaudeHarness:
    """Claude Code for the seats of one workspace, and its transcripts."""

    def __init__(self, state: Path, environ: Mapping[str, str]) -> None:
        """Keep the workspace's state folder and the environment the command started with."""
        self.state = state
        self.environ = environ

    def launch(self, seat: Seat, brief: str, cwd: Path, plugin_dir: Path | None) -> str:
        """The line a login shell runs to start the seat's agent on `brief`, in `cwd`."""
        words = launch_words(seat, Path(brief), plugin_dir)
        return " ".join(shell_word(word) for word in words)

    def transcripts(self, task: str) -> tuple[Transcript, ...]:
        """The transcripts that count for `task`, each once, by the time its first session
        started."""
        named: dict[str, str | None] = {}
        found: dict[str, Transcript] = {}
        for line in self.logged():
            path = line.transcript
            if path not in named:
                named[path] = claude_transcript.task_named(Path(path))
            owner = named[path] or line.task
            if owner == task:
                found.setdefault(path, Transcript(path=path, claude=line.claude))
        return tuple(found.values())

    def signs(self, transcript: Transcript) -> Signs:
        """The newest sign of the transcript and whether its turn runs."""
        records = claude_turns.newest_first(Path(transcript.path))
        sign = claude_turns.newest_sign(records)
        return Signs(sign=sign, turn=claude_turns.turn_of(records))

    def tokens(self, transcripts: tuple[Transcript, ...]) -> Tokens:
        """The tokens of no transcript; the tokens of a task are not read in this slice."""
        if transcripts:
            raise Fault(
                "tokens: the Claude Code adapter's slice does not read them; the step "
                "sessions does"
            )
        return Tokens()

    def available(self, seat: Seat) -> Missing | None:
        """Whether the seat's agent can run here: Claude Code on the PATH."""
        if seat.agent != AGENT:
            return Missing(error="missing", said=f"{seat.agent} is no Claude Code")
        found = shutil.which(AGENT, path=self.environ.get("PATH", ""))
        return None if found else Missing(error="missing", said="no claude on the PATH")

    def logged(self) -> list[SessionLine]:
        """Every session line of every task of the workspace, by the time each started."""
        folder = self.state / "tasks"
        if not folder.is_dir():
            return []
        named = (path.name for path in folder.iterdir())
        slugs = sorted(name for name in named if places.SLUG.fullmatch(name))
        lines = [line for slug in slugs for line in sessions.read(folder / slug)]
        return sorted(lines, key=lambda line: line.at)


def bind(place: Place) -> ClaudeHarness:
    """Claude Code for the place's workspace."""
    return ClaudeHarness(place.checkout / places.STATE, place.environ)
