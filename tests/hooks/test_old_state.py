"""The folders of Lem 0.3: no hook writes into a state folder of the Lem before or reads it, and the
correction hook takes no yes from a home folder of the Lem before."""

import json
from typing import TYPE_CHECKING

from hooks.claude_code import SELECTORS, files_of, hooked, old_workspace, started

if TYPE_CHECKING:
    from pathlib import Path


def test_a_state_folder_of_lem_0_3_is_neither_written_nor_read(tmp_path: Path) -> None:
    repo = old_workspace(tmp_path / "repo")
    home = tmp_path / "config" / "lem"
    home.mkdir(parents=True)
    (home / "machine.toml").write_text("[corrections]\ncollect = true\n")
    (home / "owner.jsonl").write_text('{"away": false}\n')
    before = files_of(tmp_path)
    compact = json.loads(started(repo, "compact"))
    inputs = (
        started(repo),
        json.dumps(compact).encode(),
        json.dumps({**compact, "hook_event_name": "PreCompact"}).encode(),
        json.dumps(
            {"prompt": "fix the login", "cwd": str(repo), "session_id": "c1"}
        ).encode(),
    )
    for selector in SELECTORS:
        for stdin in inputs:
            ran = hooked(selector, stdin, XDG_CONFIG_HOME=str(tmp_path / "config"))
            assert (ran.returncode, ran.stdout, ran.stderr) == (0, b"", b""), selector
    assert files_of(tmp_path) == before
