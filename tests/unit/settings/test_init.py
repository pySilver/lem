"""`lem init`, `lem path` and `lem settings show` through the command, in a repository a test
makes: the team's file init writes, what it refuses, the places Lem reads, and the settings
where Lem is not set up."""

import re
import tomllib
from typing import TYPE_CHECKING

import msgspec
import pytest

from fakes.command import lem
from fakes.repo import RealRepo, run_git
from lem.app.init import template
from lem.settings import described
from lem.settings.team import Team
from unit.settings.given import refusal_of, slug

if TYPE_CHECKING:
    from pathlib import Path

GITHUB = "git@github.com:owner/repo.git"
# A key the template leaves as a comment, with its table: `# merger = "agent/model:effort"`.
COMMENTED = re.compile(r"^# (\w+) = ", re.MULTILINE)


def repository(
    folder: Path, *, url: str | None = GITHUB, head: bool = True
) -> RealRepo:
    """A repository with one commit, origin at `url` (none with None), and origin's default
    branch when `head`."""
    repo = RealRepo.init(folder / "repo", {"README.md": b"hello\n"})
    if url is None:
        run_git(repo.checkout, "remote", "remove", "origin")
    else:
        run_git(repo.checkout, "remote", "set-url", "origin", url)
    if head and url is not None:
        remotes = repo.checkout / ".git" / "refs" / "remotes" / "origin"
        remotes.mkdir(parents=True, exist_ok=True)
        (remotes / "HEAD").write_text("ref: refs/remotes/origin/main\n")
    return repo


def test_init_writes_lems_places_the_base_the_merge_agent_and_whole_seats(
    tmp_path: Path,
) -> None:
    repo = repository(tmp_path)
    ran = lem("init", cwd=repo.checkout / "")
    assert ran.code == 0, ran.stdout + ran.stderr
    written = tomllib.loads((repo.checkout / ".lem" / "settings.toml").read_text())
    assert written["branch"] == {
        "base": "main",
        "land": "agent",
        "history": "squash",
        "protected": [],
    }
    assert written["seats"]["reviewer"] == "codex/gpt-6.2-sol:high"
    assert written["seats"]["planner"] == "claude/opus:high"
    assert written["seats"]["experts"] == [
        "claude/fable:high",
        "codex/gpt-6.2-astra:high",
    ]
    assert written["flow"] == {"topics": []}
    ignore = (repo.checkout / ".lem" / ".gitignore").read_text().splitlines()
    assert ignore == ["settings.local.toml", "state/"]
    assert ran.result() == {
        "settings": str(repo.checkout / ".lem" / "settings.toml"),
        "base": "main",
        "reviewer": "codex/gpt-6.2-sol:high",
        "ignore": str(repo.checkout / ".lem" / ".gitignore"),
    }


def test_init_with_codex_no_seats_claude_and_one_expert(tmp_path: Path) -> None:
    repo = repository(tmp_path)
    ran = lem("init", "--base", "trunk", "--codex", "no", cwd=repo.checkout)
    assert ran.code == 0, ran.stdout
    written = tomllib.loads((repo.checkout / ".lem" / "settings.toml").read_text())
    assert written["branch"]["base"] == "trunk"
    assert written["seats"]["reviewer"] == "claude/opus:high"
    assert written["seats"]["experts"] == ["claude/fable:high"]


def test_init_refuses_a_settings_file_that_exists_and_changes_nothing(
    tmp_path: Path,
) -> None:
    repo = repository(tmp_path)
    (repo.checkout / ".lem").mkdir()
    (repo.checkout / ".lem" / "settings.toml").write_text("# mine\n")
    ran = lem("init", cwd=repo.checkout)
    assert ran.code == 1
    assert refusal_of(ran)["code"] == "settings-exist"
    assert (repo.checkout / ".lem" / "settings.toml").read_text() == "# mine\n"


def test_init_refuses_an_origin_elsewhere_than_github(tmp_path: Path) -> None:
    repo = repository(tmp_path, url="https://gitlab.com/owner/repo.git")
    ran = lem("init", cwd=repo.checkout)
    assert refusal_of(ran)["code"] == "not-github"
    assert not (repo.checkout / ".lem" / "settings.toml").exists()


def test_init_with_no_origin_writes_and_says_to_add_one(tmp_path: Path) -> None:
    repo = repository(tmp_path, url=None)
    ran = lem("init", "--base", "main", cwd=repo.checkout)
    assert ran.code == 0
    result = ran.result()
    assert isinstance(result, dict)
    assert "has no remote origin yet" in result["said"][0]


def test_init_refuses_a_checkout_whose_base_it_cannot_tell(tmp_path: Path) -> None:
    repo = repository(tmp_path, head=False)
    ran = lem("init", cwd=repo.checkout)
    assert refusal_of(ran)["code"] == "no-base"
    assert "--base" in refusal_of(ran)["fix"]


def test_init_over_another_tools_cast_links_and_moves_nothing(tmp_path: Path) -> None:
    repo = repository(tmp_path)
    cast = repo.checkout / ".personas" / "cast"
    cast.mkdir(parents=True)
    (cast / "ana.md").write_text("Ana\n")
    assert lem("init", cwd=repo.checkout).code == 0
    assert (cast / "ana.md").read_text() == "Ana\n"
    assert sorted(path.name for path in (repo.checkout / ".lem").iterdir()) == [
        ".gitignore",
        "settings.toml",
    ]
    shown = lem("settings", "show", cwd=repo.checkout).result()
    assert isinstance(shown, dict)
    assert shown["places"]["personas"]["exists"] is False
    assert shown["places"]["personas"]["path"] == str(
        (repo.checkout / ".lem" / "personas").resolve()
    )


def test_the_file_init_writes_holds_every_key_of_the_teams_file() -> None:
    text = template.written("main", "yes")
    held = COMMENTED.findall(text)
    tables = tomllib.loads(text)
    written = {key for table in tables.values() for key in table}
    keys = {
        key
        for field in msgspec.structs.fields(Team)
        for key in described.keys_of(Team, field.name)
    }
    assert written | set(held) == keys
    assert len(keys) == 21
    assert set(tables["checks"]) == {"commands", "setup", "serial"}


@pytest.mark.parametrize(
    ("name", "relative"),
    [
        ("profile", ".lem/profile.md"),
        ("personas", ".lem/personas"),
        ("cast", ".lem/personas"),
        ("lessons", ".lem/lessons.md"),
        ("worktrees", ".lem/worktrees"),
        ("state", ".lem/state"),
        ("rules", ".claude/rules"),
        ("review", ".revmux"),
        ("backlog", "docs/backlog"),
        ("plans", "notes/plans"),
        ("rulings", "notes/rulings.md"),
    ],
    ids=slug,
)
def test_path_gives_one_absolute_path_from_any_folder_of_the_checkout(
    tmp_path: Path, name: str, relative: str
) -> None:
    team = b"[paths]\nplans = 'notes/plans'\nrulings = 'notes/rulings.md'\n"
    repo = RealRepo.init(
        tmp_path / "repo", {".lem/settings.toml": team, "src/a.py": b""}
    )
    found = lem("path", name, cwd=repo.checkout / "src").result()
    assert found == {
        "path": str((repo.checkout / relative).resolve()),
        "exists": (repo.checkout / relative).exists(),
    }


def test_path_refuses_an_unknown_name_and_names_plan_files_command(
    tmp_path: Path,
) -> None:
    repo = RealRepo.init(tmp_path / "repo", {".lem/settings.toml": b""})
    unknown = lem("path", "plnas", cwd=repo.checkout)
    assert unknown.code == 2
    plan_file = lem("path", "plan_file", cwd=repo.checkout)
    assert plan_file.code == 2
    assert "lem task plan-file SLUG" in plan_file.stderr


def test_show_where_lem_is_not_set_up_gives_no_settings_and_the_machines(
    tmp_path: Path,
) -> None:
    repo = RealRepo.init(tmp_path / "repo", {".lem/project.toml": b"[old]\nx = 1\n"})
    run_git(repo.checkout, "remote", "set-url", "origin", GITHUB)
    shown = lem("settings", "show", cwd=repo.checkout).result()
    assert isinstance(shown, dict)
    assert shown["settings"] is None
    assert shown["from"]["load.start"] == "Lem's default"
    assert set(shown["load"]) >= {"now", "cores"}
    assert lem("init", "--base", "main", "--codex", "no", cwd=repo.checkout).code == 0
    ignore = (repo.checkout / ".lem" / ".gitignore").read_text().splitlines()
    assert ignore == ["settings.local.toml", "state/"]
