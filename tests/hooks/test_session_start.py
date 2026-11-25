"""The `session-start` hook: a task's session on record in one framed line the store reads, the
plugin's folder for the session's commands, and the task's record and handoff after a compaction.
It touches no file of another checkout, follows no link, and a folder it cannot write leaves the
session silent."""

import json
from typing import TYPE_CHECKING

from hooks.claude_code import ROOT, SLUG, hooked, started, workspace
from lem.store import sessions

if TYPE_CHECKING:
    from pathlib import Path


def test_a_tasks_session_is_put_on_record_in_one_framed_line_the_store_reads(
    tmp_path: Path,
) -> None:
    folder = workspace(tmp_path / "repo")
    env_file = tmp_path / "env"
    for source in ("startup", "resume"):
        ran = hooked(
            "session-start",
            started(tmp_path / "repo", source),
            CLAUDE_ENV_FILE=str(env_file),
            AGTERM_SESSION_ID="S-7",
        )
        assert (ran.returncode, ran.stdout) == (0, b"")
    read = sessions.read(folder)
    assert [(line.source, line.claude, line.pane, line.task) for line in read] == [
        ("startup", "c0ffee", "S-7", SLUG),
        ("resume", "c0ffee", "S-7", SLUG),
    ]
    assert read[0].transcript == "/claude/projects/x/c0ffee.jsonl"
    body = (folder / sessions.SESSIONS).read_bytes()
    assert body.startswith(b"\n")
    assert body.endswith(b"}\n")


def test_every_session_keeps_the_plugins_folder_for_its_commands(
    tmp_path: Path,
) -> None:
    env_file = tmp_path / "env"
    for slug in ("", SLUG):
        ran = hooked(
            "session-start", b"{}", CLAUDE_ENV_FILE=str(env_file), LEM_TASK=slug
        )
        assert (ran.returncode, ran.stdout) == (0, b"")
    assert env_file.read_text() == f"export LEM_PLUGIN_ROOT='{ROOT}'\n" * 2


def test_a_session_that_is_no_tasks_is_put_on_no_record(tmp_path: Path) -> None:
    folder = workspace(tmp_path / "repo")
    for slug in ("", "Fix_The_Login", "other-task", "-x", "a--b"):
        ran = hooked("session-start", started(tmp_path / "repo"), LEM_TASK=slug)
        assert (ran.returncode, ran.stdout) == (0, b"")
    assert not (folder / sessions.SESSIONS).exists()


def test_an_unwritable_task_folder_is_silent_and_the_plugin_still_kept(
    tmp_path: Path,
) -> None:
    folder = workspace(tmp_path / "repo")
    folder.chmod(0o555)
    try:
        ran = hooked(
            "session-start",
            started(tmp_path / "repo"),
            CLAUDE_ENV_FILE=str(tmp_path / "env"),
        )
    finally:
        folder.chmod(0o755)
    assert (ran.returncode, ran.stdout, ran.stderr) == (0, b"", b"")
    assert not (folder / sessions.SESSIONS).exists()
    assert (tmp_path / "env").read_text() == f"export LEM_PLUGIN_ROOT='{ROOT}'\n"


def test_after_a_compaction_the_task_and_its_handoff_come_back(
    tmp_path: Path,
) -> None:
    folder = workspace(tmp_path / "repo")
    (folder / "handoff.md").write_text(
        "task: fix-the-login · from build\n\n## Settled\n"
    )
    record = {
        "task": {"status": "building", "hold": None},
        "journal": [
            {"kind": "state", "line": "the plan has 3 tasks"},
            {"kind": "span", "name": "lead"},
            {"kind": "state", "line": "task 2 of 3"},
        ],
    }
    (folder / "task.json").write_text(json.dumps(record))
    ran = hooked("session-start", started(tmp_path / "repo", "compact"))
    said = ran.stdout.decode()
    assert "Lem's task fix-the-login, after the compaction." in said
    assert "status: building; hold: none; newest state line: task 2 of 3" in said
    assert "## Settled" in said
    assert len(sessions.read(folder)) == 1


def test_a_compaction_whose_line_was_not_kept_or_no_session_start_gives_nothing(
    tmp_path: Path,
) -> None:
    folder = workspace(tmp_path / "repo")
    (folder / "handoff.md").write_text("task: gift-note · from build\n")
    folder.chmod(0o555)
    try:
        failed = hooked("session-start", started(tmp_path / "repo", "compact"))
    finally:
        folder.chmod(0o755)
    other_event = json.loads(started(tmp_path / "repo", "compact"))
    other_event["hook_event_name"] = "PreCompact"
    wrong = hooked("session-start", json.dumps(other_event).encode())
    assert (failed.returncode, failed.stdout) == (0, b"")
    assert (wrong.returncode, wrong.stdout) == (0, b"")
    assert not (folder / sessions.SESSIONS).exists()


def test_a_folder_that_is_gone_puts_nothing_on_record(tmp_path: Path) -> None:
    folder = workspace(tmp_path / "repo")
    gone = tmp_path / "repo" / ".lem" / "worktrees" / SLUG
    ran = hooked("session-start", started(gone))
    assert (ran.returncode, ran.stdout) == (0, b"")
    assert not (folder / sessions.SESSIONS).exists()


def test_a_state_folder_linked_into_another_checkout_is_not_touched(
    tmp_path: Path,
) -> None:
    other = workspace(tmp_path / "other")
    (other / "handoff.md").write_text("task: gift-note · from build\n")
    mine = tmp_path / "mine"
    (mine / ".git").mkdir(parents=True)
    (mine / ".lem").mkdir()
    (mine / ".lem" / "state").symlink_to(tmp_path / "other" / ".lem" / "state")
    for source in ("startup", "compact"):
        ran = hooked("session-start", started(mine, source))
        assert (ran.returncode, ran.stdout) == (0, b"")
    assert not (other / sessions.SESSIONS).exists()


def test_a_link_at_the_environment_file_or_the_sessions_file_is_never_followed(
    tmp_path: Path,
) -> None:
    folder = workspace(tmp_path / "repo")
    target = tmp_path / "target"
    target.write_text("kept\n")
    (tmp_path / "env").symlink_to(target)
    (folder / sessions.SESSIONS).symlink_to(target)
    ran = hooked(
        "session-start",
        started(tmp_path / "repo", "compact"),
        CLAUDE_ENV_FILE=str(tmp_path / "env"),
    )
    assert (ran.returncode, ran.stdout) == (0, b"")
    assert target.read_text() == "kept\n"
