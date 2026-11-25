"""The `precompact` hook: the form of a task's compaction summary, the handoff's five headings with
the phase its session opened in; nothing for a session that is no task's."""

import json
from typing import TYPE_CHECKING

from hooks.claude_code import hooked, workspace

if TYPE_CHECKING:
    from pathlib import Path


def test_precompact_gives_the_handoffs_headings_with_the_phase(tmp_path: Path) -> None:
    folder = workspace(tmp_path / "repo")
    (folder / "session.md").write_text(
        "Read it.\n\ntask: fix-the-login\nphase: build\n"
    )
    event = json.dumps(
        {
            "cwd": str(tmp_path / "repo"),
            "trigger": "auto",
            "hook_event_name": "PreCompact",
        }
    ).encode()
    said = hooked("precompact", event).stdout.decode()
    assert said.startswith(
        "This summary is the handoff of task fix-the-login, phase build, under five "
        "headings: Settled; Open; Next step; Failed; Changed files"
    )
    assert hooked("precompact", event, LEM_TASK="").stdout == b""
    other = json.dumps({"cwd": str(tmp_path / "repo"), "hook_event_name": "Stop"})
    assert hooked("precompact", other.encode()).stdout == b""
