"""The rules of the plugin's hooks, called as functions: the main checkout from a task's worktree,
the task's name, the framed line the store reads, the other `lem`, the correction gate, the
server's start, and the task's state after a compaction."""

import json
from typing import TYPE_CHECKING

import pytest

from lem.hooks import corrections, other, precompact, serve, session, versions, where
from lem.kernel import folders, paths
from lem.records import sessions as records
from lem.store import sessions

if TYPE_CHECKING:
    from pathlib import Path


def test_a_worktree_reaches_the_state_of_its_main_checkout(tmp_path: Path) -> None:
    main = tmp_path / "repo"
    (main / ".git" / "worktrees" / "gift-note").mkdir(parents=True)
    (main / ".git" / "worktrees" / "gift-note" / "commondir").write_text("../..\n")
    tree = main / ".lem" / "worktrees" / "gift-note"
    (tree / "src").mkdir(parents=True)
    (tree / ".git").write_text(f"gitdir: {main}/.git/worktrees/gift-note\n")
    assert where.checkout_of(str(tree / "src")) == str(main.resolve())
    assert where.checkout_of(str(main)) == str(main.resolve())
    assert where.checkout_of("/") is None


def test_a_relative_gitdir_is_read_from_its_files_folder(tmp_path: Path) -> None:
    main = tmp_path / "repo"
    (main / ".git" / "worktrees" / "t").mkdir(parents=True)
    (main / ".git" / "worktrees" / "t" / "commondir").write_text("../..\n")
    tree = tmp_path / "t"
    tree.mkdir()
    (tree / ".git").write_text("gitdir: ../repo/.git/worktrees/t\n")
    assert where.checkout_of(str(tree)) == str(main.resolve())


@pytest.mark.parametrize(
    ("named", "slug"),
    [
        ("gift-note", "gift-note"),
        (" gift-note2 \n", "gift-note2"),
        ("", None),
        ("Gift-Note", None),
        ("gift_note", None),
        ("-gift", None),
        ("gift--note", None),
        ("../x", None),
    ],
)
def test_the_task_is_lem_task_when_it_is_a_tasks_name(
    named: str, slug: str | None
) -> None:
    assert where.slug_of({"LEM_TASK": named}) == slug


def test_the_framed_line_is_one_the_store_reads(tmp_path: Path) -> None:
    found: dict[str, object] = {
        "session_id": "c1",
        "transcript_path": "/t/c1.jsonl",
        "source": "fork",
    }
    frame = session.framed(found, "/s/tasks/gift-note", {"AGTERM_SESSION_ID": "S-1"})
    assert frame is not None
    assert frame.startswith(b"\n")
    assert frame.endswith(b"\n")
    state = tmp_path / "state"
    task = state / "tasks" / "gift-note"
    task.mkdir(parents=True)
    (state / folders.MARKER).write_bytes(folders.FORM)
    (task / sessions.SESSIONS).write_bytes(b'{"v": 1, "cut off' + frame)
    read = sessions.read(task)
    assert [(line.source, line.claude, line.pane) for line in read] == [
        ("fork", "c1", "S-1")
    ]
    assert session.VERSION == records.VERSION
    broken: tuple[dict[str, object], ...] = (
        {**found, "source": "later"},
        {**found, "session_id": ""},
        {},
    )
    for event in broken:
        assert session.framed(event, "/s/tasks/gift-note", {}) is None


def lem_file(folder: Path) -> str:
    """A command `lem` in `folder`."""
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "lem"
    path.write_text("#!/bin/sh\n")
    path.chmod(0o755)
    return str(path)


def test_another_lem_first_is_named_by_its_real_path(tmp_path: Path) -> None:
    own = lem_file(tmp_path / "app" / "bin")
    old = lem_file(tmp_path / "old")
    linked = tmp_path / "links"
    linked.mkdir()
    (linked / "lem").symlink_to(own)
    app = str(tmp_path / "app" / "bin")
    assert other.other_lem(f"{tmp_path / 'none'}:{app}", own) is None
    assert other.other_lem(f"{linked}:{old}", own) is None
    said = other.other_lem(f"{tmp_path / 'old'}:{linked}", own)
    assert said == (
        f"lem: {old} comes first on PATH, and it is not Lem's command {own}; the owner "
        f"puts {linked} before {tmp_path / 'old'} in his PATH"
    )
    assert (
        other.other_lem(f"{tmp_path / 'old'}", str(tmp_path / "gone" / "lem")) is None
    )


def test_the_hooks_root_is_the_apps_root() -> None:
    assert versions.app_root() == str(paths.root())


@pytest.mark.parametrize(
    ("prompt", "typed"),
    [
        ("fix the login", True),
        ("  ", False),
        ("/lem status", False),
        ("<command-name>/cost</command-name>", False),
        ("[peer chat] hello", False),
        ("This session is being continued from a previous one", False),
    ],
)
def test_a_correction_is_words_the_owner_typed(*, prompt: str, typed: bool) -> None:
    assert corrections.typed(prompt) is typed


def test_corrections_need_the_machines_yes_and_a_repository_of_lem(
    tmp_path: Path,
) -> None:
    home = tmp_path / "config"
    environ = {"XDG_CONFIG_HOME": str(home)}
    assert corrections.machine_says_yes(environ) is False
    (home / "lem").mkdir(parents=True)
    (home / "lem" / "machine.toml").write_text("[corrections]\ncollect = true\n")
    assert corrections.machine_says_yes(environ) is True
    (home / "lem" / "machine.toml").write_text("[corrections\n")
    assert corrections.machine_says_yes(environ) is False
    assert corrections.machine_says_yes({"XDG_CONFIG_HOME": "relative"}) is False
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    assert corrections.collects({"cwd": str(repo)}, {}) is False
    (repo / ".lem" / "state").mkdir(parents=True)
    (repo / ".lem" / "settings.toml").write_text("")
    assert corrections.collects({"cwd": str(repo)}, {}) is False
    (repo / ".lem" / "state" / folders.MARKER).write_bytes(folders.FORM)
    assert corrections.collects({"cwd": str(repo)}, {}) is True


def test_the_server_starts_in_a_repository_of_lem_unless_it_is_off(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    event: dict[str, object] = {"cwd": str(repo)}
    assert serve.wanted(event, {}) is False
    (repo / ".lem" / "state").mkdir(parents=True)
    (repo / ".lem" / "settings.toml").write_text("")
    (repo / ".lem" / "state" / "events.jsonl").write_text("")
    assert serve.wanted(event, {}) is False
    (repo / ".lem" / "state" / folders.MARKER).write_bytes(folders.FORM)
    assert serve.wanted(event, {}) is True
    assert serve.wanted(event, {"LEM_SERVE": "off"}) is False
    assert serve.wanted({}, {"CLAUDE_PROJECT_DIR": str(repo)}) is True


def test_the_state_after_a_compaction_reads_past_a_record_it_does_not_know(
    tmp_path: Path,
) -> None:
    assert precompact.newest_state(str(tmp_path)) == "the task's record does not read"
    (tmp_path / "task.json").write_text(json.dumps([1]))
    assert precompact.newest_state(str(tmp_path)) == "the task's record holds no task"
    record = {
        "task": {"status": "landing", "hold": {"kind": "blocked", "why": "red"}},
        "journal": [{"kind": "state", "line": 3}, "x"],
    }
    (tmp_path / "task.json").write_text(json.dumps(record))
    assert precompact.newest_state(str(tmp_path)) == (
        "status: landing; hold: blocked; newest state line: none written yet"
    )


def test_a_hard_link_of_the_apps_command_is_the_app(tmp_path: Path) -> None:
    own = lem_file(tmp_path / "app")
    (tmp_path / "hard").mkdir()
    (tmp_path / "hard" / "lem").hardlink_to(own)
    assert other.same(str(tmp_path / "hard" / "lem"), own)
    assert other.other_lem(f"{tmp_path / 'hard'}", own) is None
    assert other.same(own, str(tmp_path / "gone")) is False
