"""The setup a Codex plan reviewer needs to receive mail and answer it."""

import shlex
from typing import TYPE_CHECKING

import pytest

from lem.cli.doctor.rows import gathered
from unit.settings.doctor.stage import Stage, named

if TYPE_CHECKING:
    from pathlib import Path

ROW = "Codex reviewer mailbox"
REVIEWER = '[seats]\nreviewer = "codex/gpt-6.2-sol:high"\n'
START = """[[hooks.SessionStart]]
[[hooks.SessionStart.hooks]]
type = "command"
command = "mailbox-chat.py codex-hook"
"""


@pytest.mark.parametrize("missing", ["", "config.toml", "default.rules", "hooks.conf"])
def test_doctor_checks_the_codex_reviewers_mailbox(
    tmp_path: Path, missing: str
) -> None:
    stage = Stage(tmp_path)
    repo = stage.repository()
    stage.write("repo/.lem/settings.local.toml", REVIEWER)
    program = stage.tool("mailbox-chat.py")
    files = {
        "config.toml": ("home/.codex/config.toml", START),
        "default.rules": (
            "home/.codex/rules/default.rules",
            (
                f'host_executable(name="mailbox-chat.py", paths=["{program}"])\n'
                'prefix_rule(pattern=["mailbox-chat.py", "say", "--file"], decision="allow")\n'
            ),
        ),
        "hooks.conf": (
            "home/.config/agterm/hooks.conf",
            f"on message {shlex.quote(str(program))} agterm-hook\n",
        ),
    }
    for name, (path, body) in files.items():
        if name != missing:
            stage.write(path, body)

    tree = stage.worktree(repo, "a-task")
    row = named(gathered(stage.look(tree)), ROW)
    assert row.found is (not missing)
    assert row.need == "required"
    if missing:
        assert row.detail and missing in row.detail
        assert row.guide and "two-agent-mailbox-chat#setup" in row.guide


def test_doctor_omits_the_codex_mailbox_check_for_a_claude_reviewer(
    tmp_path: Path,
) -> None:
    stage = Stage(tmp_path)
    repo = stage.repository()
    assert ROW not in {row.name for row in gathered(stage.look(repo))}
