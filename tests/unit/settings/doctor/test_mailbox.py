"""The mailbox row checks the command and its Claude Code hook."""

import json
from shlex import quote
from typing import TYPE_CHECKING

import pytest

from lem.cli.doctor.mailbox import mailbox_row
from unit.settings.doctor.stage import MAILBOX_EVENTS, Stage

if TYPE_CHECKING:
    from pathlib import Path


def test_the_mailbox_needs_its_command_and_the_waiter_for_each_event(
    tmp_path: Path,
) -> None:
    stage = Stage(tmp_path)
    stage.mailbox_settings()
    assert not mailbox_row(stage.look()).found
    program = stage.tool("mailbox-chat.py")
    row = mailbox_row(stage.look())
    assert (row.need, row.found, row.detail) == ("required", True, str(program))


@pytest.mark.parametrize("event", MAILBOX_EVENTS)
def test_the_mailbox_row_names_each_missing_event(tmp_path: Path, event: str) -> None:
    stage = Stage(tmp_path)
    stage.tool("mailbox-chat.py")
    others = tuple(other for other in MAILBOX_EVENTS if other != event)
    settings = stage.mailbox_settings(events=others)
    row = mailbox_row(stage.look())
    assert not row.found
    assert row.detail == f"mailbox hook is missing for {event} in {settings}"


@pytest.mark.parametrize("text", [None, "{broken json", '{"hooks": []}'])
def test_settings_that_do_not_read_fail_the_mailbox_row(
    tmp_path: Path, text: str | None
) -> None:
    stage = Stage(tmp_path)
    stage.tool("mailbox-chat.py")
    if text is not None:
        stage.write("home/.claude/settings.json", text)
    row = mailbox_row(stage.look())
    assert not row.found
    assert row.detail == f"cannot read {stage.home / '.claude' / 'settings.json'}"


@pytest.mark.parametrize(
    "fields",
    [
        {"command": "mailbox-chat.py codex-hook"},
        {"command": "echo 'mailbox-chat.py claude-hook'"},
        {"type": "prompt"},
        {"asyncRewake": False, "async": True},
    ],
)
def test_only_a_command_hook_that_rewakes_counts(
    tmp_path: Path, fields: dict[str, object]
) -> None:
    stage = Stage(tmp_path)
    stage.tool("mailbox-chat.py")
    stage.mailbox_settings(hook_fields=fields)
    assert not mailbox_row(stage.look()).found


def test_the_mailbox_uses_only_the_active_user_settings(tmp_path: Path) -> None:
    stage = Stage(tmp_path)
    program = stage.tool("mailbox-chat.py")
    stage.mailbox_settings()
    look = stage.look(CLAUDE_CONFIG_DIR=str(stage.root / "other config"))
    assert not mailbox_row(look).found
    stage.mailbox_settings(
        "other config/settings.json",
        hook_fields={"command": f"{quote(str(program))} claude-hook"},
    )
    assert mailbox_row(look).found


def test_disabled_hooks_fail_the_mailbox_row(tmp_path: Path) -> None:
    stage = Stage(tmp_path)
    stage.tool("mailbox-chat.py")
    settings = stage.mailbox_settings()
    before = json.loads(settings.read_text(encoding="utf-8"))
    stage.write(
        "home/.claude/settings.json", json.dumps({**before, "disableAllHooks": True})
    )
    row = mailbox_row(stage.look())
    assert not row.found
    assert row.detail == f"disableAllHooks is true in {settings}"
