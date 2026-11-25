"""The Claude Code adapter's slice against the `Harness` contract: its launch line, the rule that
gives a transcript its task, and the signs of a transcript, on transcripts a test writes and a
stand-in script named `claude`: never the owner's Claude Code."""

import json
import shlex
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import msgspec
import pytest

from contract.suites.outside import HarnessContract
from lem.adapters import harness_claude
from lem.kernel.errors import Fault, Refusal
from lem.ports.harness import Missing, Seat, Signs, Transcript
from lem.ports.place import Place
from lem.records.sessions import SessionLine
from lem.store import sessions

if TYPE_CHECKING:
    from pathlib import Path

AT = datetime(2026, 11, 25, 10, 0, tzinfo=UTC)


def bound(checkout: Path, path: str = "/usr/bin:/bin") -> harness_claude.ClaudeHarness:
    """The adapter for the workspace `checkout`."""
    place = Place(checkout=checkout, home=checkout / "home", environ={"PATH": path})
    return harness_claude.bind(place)


class TestClaudeHarness(HarnessContract):
    @pytest.fixture(autouse=True)
    def checkout(self, tmp_path: Path) -> None:
        self.folder = tmp_path

    def harness(self) -> harness_claude.ClaudeHarness:
        return bound(self.folder)


def launch_line(brief: Path, seat: Seat, plugin: Path | None) -> list[str]:
    """The words a login shell reads in the launch line."""
    said = bound(brief.parent).launch(seat, str(brief), brief.parent, plugin)
    return shlex.split(said)


def test_the_launch_line_names_the_task_the_seat_the_plugin_and_the_brief(
    tmp_path: Path,
) -> None:
    brief = (
        tmp_path / "my repo" / ".lem" / "state" / "tasks" / "gift-note" / "session.md"
    )
    seat = Seat(agent="claude", model="opus[1m]", effort="high")
    plugin = tmp_path / "Lem's data"
    assert launch_line(brief, seat, plugin) == [
        "LEM_TASK=gift-note",
        "claude",
        "--model",
        "opus[1m]",
        "--effort",
        "high",
        "--plugin-dir",
        str(plugin),
        f"Read {brief} and follow it.",
    ]
    said = bound(tmp_path).launch(Seat(agent="claude"), str(brief), tmp_path, None)
    assert said == f'LEM_TASK=gift-note claude "Read {brief} and follow it."'
    with pytest.raises(Refusal, match="backslash or a line break"):
        launch_line(tmp_path / "a\\b" / "x" / "session.md", Seat(agent="claude"), None)


def transcript(path: Path, *records: object) -> str:
    """A transcript of `records`, one a line: a record that is no object is a line Lem passes
    over."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(f"{json.dumps(record)}\n" for record in records))
    return str(path)


def prompt(text: str, at: str = "2026-11-25T10:00:00Z") -> dict[str, object]:
    """A user record of `text`."""
    return {"type": "user", "timestamp": at, "message": {"content": text}}


def logged(state: Path, slug: str, path: str, claude: str, minute: int) -> None:
    """The line `session-start` appends for a session of `slug`, started at `minute`."""
    folder = state / "tasks" / slug
    folder.mkdir(parents=True, exist_ok=True)
    at = AT.replace(minute=minute)
    line = SessionLine(
        at=at, source="startup", claude=claude, transcript=path, task=slug
    )
    sessions.append(folder, line)


def test_a_transcript_counts_for_the_task_its_first_prompt_names(
    tmp_path: Path,
) -> None:
    state = tmp_path / ".lem" / "state"
    brief = f"Read {state}/tasks/gift-note/session.md and follow it."
    own = transcript(tmp_path / "c" / "own.jsonl", {"type": "summary"}, prompt(brief))
    fork = transcript(tmp_path / "c" / "fork.jsonl", prompt(brief))
    cleared = transcript(
        tmp_path / "c" / "cleared.jsonl", prompt("go on with the column")
    )
    logged(state, "gift-note", own, "c1", 1)
    logged(state, "gift-note", own, "c1", 2)
    logged(state, "board-search", fork, "c2", 3)
    logged(state, "board-search", cleared, "c3", 4)
    logged(state, "gift-note", str(tmp_path / "gone.jsonl"), "c4", 5)
    harness = bound(tmp_path)
    assert [found.claude for found in harness.transcripts("gift-note")] == [
        "c1",
        "c2",
        "c4",
    ]
    assert harness.transcripts("board-search") == (
        Transcript(path=cleared, claude="c3"),
    )


def reply(
    reason: str | None, *tools: str, sidechain: bool = False
) -> dict[str, object]:
    """An assistant record that stopped for `reason`, with a call of each of `tools`."""
    parts = [{"type": "tool_use", "name": tool} for tool in tools]
    return {
        "type": "assistant",
        "timestamp": "2026-11-25T10:05:00Z",
        "isSidechain": sidechain,
        "message": {"stop_reason": reason, "content": parts},
    }


@pytest.mark.parametrize(
    ("newest", "turn"),
    [
        ([reply("tool_use", "Bash")], "runs"),
        ([reply("end_turn")], "ended"),
        ([reply("tool_use", "AskUserQuestion")], "ended"),
        ([prompt("[Request interrupted by user]")], "ended"),
        ([reply("end_turn"), reply("tool_use", "Bash", sidechain=True)], "ended"),
        ([reply("end_turn"), reply(None)], "ended"),
        (
            [reply("tool_use", "Bash"), prompt("<command-name>/cost</command-name>")],
            "runs",
        ),
        ([prompt("a tool's result")], "runs"),
    ],
)
def test_the_turn_is_read_from_the_newest_record_that_decides(
    tmp_path: Path, newest: list[dict[str, object]], turn: str
) -> None:
    path = transcript(tmp_path / "t.jsonl", prompt("go"), *newest)
    signs = bound(tmp_path).signs(Transcript(path=path, claude="c1"))
    assert signs.turn == turn


def test_the_newest_sign_is_the_newest_turns_time(tmp_path: Path) -> None:
    path = transcript(
        tmp_path / "t.jsonl",
        prompt("go", "2026-11-25T10:00:00Z"),
        reply("end_turn"),
        {"type": "system", "timestamp": "2026-11-25T11:00:00Z"},
        "not a record",
    )
    signs = bound(tmp_path).signs(Transcript(path=path, claude="c1"))
    assert signs == Signs(sign=datetime(2026, 11, 25, 10, 5, tzinfo=UTC), turn="ended")
    assert msgspec.json.encode(signs)


def test_claude_is_available_when_it_is_on_the_path(tmp_path: Path) -> None:
    standin = tmp_path / "bin" / "claude"
    standin.parent.mkdir()
    standin.write_text("#!/bin/sh\nexit 0\n")
    standin.chmod(0o755)
    seat = Seat(agent="claude")
    assert bound(tmp_path).available(seat) == Missing(
        error="missing", said="no claude on the PATH"
    )
    assert bound(tmp_path, f"{standin.parent}:/usr/bin:/bin").available(seat) is None
    assert bound(tmp_path).available(Seat(agent="codex")) is not None


def test_the_tokens_of_a_task_say_by_name_that_the_slice_reads_none(
    tmp_path: Path,
) -> None:
    with pytest.raises(Fault, match=r"^tokens: "):
        bound(tmp_path).tokens((Transcript(path="/x", claude="c"),))


def test_the_first_prompt_reads_past_a_bad_time_and_takes_text_blocks_only(
    tmp_path: Path,
) -> None:
    state = tmp_path / ".lem" / "state"
    brief = f"Read {state}/tasks/gift-note/session.md and follow it."
    timed = transcript(
        tmp_path / "c" / "timed.jsonl",
        {**prompt(brief), "timestamp": "not a time"},
        prompt("go on"),
    )
    pictured = transcript(
        tmp_path / "c" / "pictured.jsonl",
        {
            "type": "user",
            "message": {
                "content": [
                    {"type": "text", "text": brief},
                    {"type": "image", "source": {}},
                ]
            },
        },
    )
    logged(state, "board-search", timed, "c1", 1)
    logged(state, "board-search", pictured, "c2", 2)
    harness = bound(tmp_path)
    assert [one.claude for one in harness.transcripts("gift-note")] == ["c1"]
    assert [one.claude for one in harness.transcripts("board-search")] == ["c2"]


def test_a_record_whose_time_does_not_read_still_decides_the_turn(
    tmp_path: Path,
) -> None:
    path = transcript(
        tmp_path / "t.jsonl",
        prompt("go"),
        reply("tool_use", "Bash"),
        {**reply("end_turn"), "timestamp": "2026-02-31T10:00:00Z"},
    )
    signs = bound(tmp_path).signs(Transcript(path=path, claude="c1"))
    assert signs == Signs(sign=datetime(2026, 11, 25, 10, 5, tzinfo=UTC), turn="ended")
