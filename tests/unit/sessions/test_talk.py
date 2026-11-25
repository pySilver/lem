"""`lem session talk`: the owner's turns and the agent's, copied word for word from the session's
own transcript into the task's talk.md, less another topic."""

import json
from typing import TYPE_CHECKING

import pytest

from lem.adapters import claude_talk, claude_talk_turns
from lem.app.sessions import talking
from lem.kernel.errors import Refusal
from unit.sessions.world import SLUG, here_of, made

if TYPE_CHECKING:
    from pathlib import Path


def owner(text: object, at: str, **more: object) -> dict[str, object]:
    """A prompt the owner typed."""
    record = {"type": "user", "timestamp": at, "origin": {"kind": "human"}}
    return {**record, "message": {"content": text}, **more}


def agent(text: str, at: str) -> dict[str, object]:
    """The agent's reply, with a tool's call that is no words."""
    parts = [{"type": "text", "text": text}, {"type": "tool_use", "name": "Bash"}]
    return {"type": "assistant", "timestamp": at, "message": {"content": parts}}


TALK = (
    owner("an old topic", "2026-11-25T09:00:00Z"),
    agent("an old answer", "2026-11-25T09:00:05Z"),
    owner(
        "<command-message>lem</command-message><command-name>/lem:lem</command-name>"
        "<command-args>add a gift note</command-args>",
        "2026-11-25T10:00:00Z",
    ),
    owner("the skill's text", "2026-11-25T10:00:01Z", isMeta=True),
    agent("Which page?", "2026-11-25T10:00:10Z"),
    {"type": "user", "message": {"content": [{"type": "tool_result"}]}},
    agent("The checkout page, I think.", "2026-11-25T10:00:20Z"),
    owner("by the way, the build is slow", "2026-11-25T10:01:00Z"),
    agent("It is the cache.", "2026-11-25T10:01:10Z"),
    {
        "type": "user",
        "origin": {"kind": "task-notification"},
        "message": {"content": "x"},
    },
    owner("the checkout page", "2026-11-25T10:02:00Z"),
    {
        "type": "assistant",
        "isSidechain": True,
        "message": {"content": [{"type": "text", "text": "sub"}]},
    },
)


def transcript(home: Path, records: tuple[dict[str, object], ...]) -> dict[str, str]:
    """A transcript of the session `c1` under Claude Code's folder `home`, and the
    environment that names it."""
    path = home / "projects" / "repo" / "c1.jsonl"
    path.parent.mkdir(parents=True)
    path.write_text("".join(f"{json.dumps(one)}\n" for one in records) + "not json\n")
    return {
        "CLAUDE_CONFIG_DIR": str(home),
        "CLAUDE_CODE_SESSION_ID": "c1",
        "HOME": "/x",
    }


def test_the_talk_is_copied_from_the_owners_turn_less_another_topic(
    tmp_path: Path,
) -> None:
    here = here_of(tmp_path / "repo")
    made(here)
    environ = transcript(tmp_path / "claude", TALK)
    turns = claude_talk_turns.turns(claude_talk.own_transcript(environ))
    got = talking.copied(here, SLUG, turns, ("add a gift", ("by the way",)))
    assert (got.turns, got.owner_turns, got.lem_turns) == (3, 2, 1)
    assert [(one.words, one.lem_turns) for one in got.left_out] == [
        ("by the way, the build is slow", 1)
    ]
    text = (here.folder(SLUG) / "talk.md").read_text()
    assert "/lem add a gift note" in text
    assert "Which page?\n\nThe checkout page, I think." in text
    assert "the skill's text" not in text
    assert "an old topic" not in text
    assert "sub" not in text.split("## ")[-1]


def test_a_start_or_a_leave_no_turn_of_his_has_is_refused(tmp_path: Path) -> None:
    here = here_of(tmp_path / "repo")
    made(here)
    environ = transcript(tmp_path / "claude", TALK)
    turns = claude_talk_turns.turns(claude_talk.own_transcript(environ))
    for asked in (("never said", ()), ("add a gift", ("never said",)), ("", ())):
        with pytest.raises(Refusal):
            talking.copied(here, SLUG, turns, asked)


def test_a_transcript_of_another_form_or_no_session_is_refused(tmp_path: Path) -> None:
    environ = transcript(
        tmp_path / "claude", ({"type": "user", "message": {"content": "x"}},)
    )
    with pytest.raises(Refusal, match="no prompt's origin"):
        claude_talk_turns.turns(claude_talk.own_transcript(environ))
    with pytest.raises(Refusal) as none:
        claude_talk.own_transcript({"HOME": str(tmp_path)})
    assert none.value.code == "no-claude-session"
