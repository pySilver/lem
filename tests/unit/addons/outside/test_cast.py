"""The project cast, worktree selection and its scratch folders, on disposable Git."""

import os
from datetime import datetime
from pathlib import Path

import pytest

from fakes.command import lem
from fakes.repo import RealRepo, run_git, write
from lem.addons.cast import front, person, project, setup
from lem.kernel.errors import Refusal

CAST = ".lem/personas/"
SELLER = CAST + "seller.md"
PROFILE = ".lem/profile.md"
SETTINGS = ".lem/settings.toml"
PERSON = b"# The seller\n\nSells gifts.\n"


def test_frontmatter_and_copy(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PATH", str(tmp_path))
    path = tmp_path / "seller.md"
    state = tmp_path / "state"
    text = '---\n# A comment\n\nseats: ["claude/opus:high", "codex/gpt-6.2-sol:high"]\n---\n\n# The seller\n'
    path.write_text(text, encoding="utf-8")
    found = person.read(path, state)
    assert found.path == str(path)
    assert tuple(seat.name for seat in found.seats) == ("opus",)
    assert found.seats[0].effort == "high"
    assert tuple(seat.name for seat in found.left_out) == ("sol",)
    assert found.seats_from == "file"
    copy = Path(found.person)
    assert copy.read_text() == "# The seller\n"
    os.utime(copy, (1, 1))
    assert person.read(path, state).person == found.person
    assert copy.stat().st_mtime > 1
    path.write_bytes(PERSON)
    default = person.read(path, state)
    assert default.person == str(path)
    assert default.seats_from == "default"
    assert default.seats[0].name == "opus"
    assert default.left_out[0].name == "sol"


def test_invalid_frontmatter_names_the_file_and_fix(tmp_path: Path) -> None:
    path = tmp_path / "seller.md"
    for bad in (
        "---\nseats: []",
        "---\nother: false\n---\n",
        '---\nseats: ["claude/opus:high"]\nseats: []\n---\n',
        '---\nseats: ["gemini/pro:high"]\n---\n',
        '---\nseats: ["claude/opus:high", "claude/opus:low"]\n---\n',
    ):
        path.write_text(bad)
        with pytest.raises(Refusal) as refused:
            person.read(path, tmp_path / "state")
        assert str(path) in refused.value.why
        assert front.SEATS_LINE in refused.value.fix


def test_checkout_uses_its_own_people_and_profile(tmp_path: Path) -> None:
    repo = RealRepo.init(tmp_path / "repo", {SELLER: PERSON, PROFILE: b"# Shop\n"})
    found = project.resolve(repo.checkout)
    assert found.layer == "project"
    assert found.source == "checkout"
    assert found.personas[0].person == str(repo.checkout / SELLER)
    assert found.profile and found.profile.path == str(repo.checkout / PROFILE)
    shown = lem("--repo", str(repo.checkout), "cast")
    assert shown.code == 0, shown.stdout
    assert not (Path(person.__file__).parent / "__pycache__").exists()
    assert (
        run_git(repo.checkout, "status", "--porcelain", "--untracked-files=all") == ""
    )


def test_default_branch_updates_reach_a_worktree_without_its_own_edit(
    tmp_path: Path,
) -> None:
    repo = RealRepo.init(
        tmp_path / "repo", {SELLER: PERSON, PROFILE: b"# Shop\n"}, branch="trunk"
    )
    checkout = repo.checkout
    (checkout / ".git/refs/remotes/origin/HEAD").unlink(missing_ok=True)
    worktree = tmp_path / "task"
    run_git(checkout, "worktree", "add", "-b", "task", str(worktree))
    write(
        checkout, {CAST + "buyer.md": b"# The buyer\n", PROFILE: b"# A bigger shop\n"}
    )
    run_git(checkout, "add", ".lem")
    run_git(checkout, "commit", "-m", "add a buyer")
    local = project.resolve(worktree)
    assert local.source.startswith("trunk at ")
    assert {found.stem for found in local.personas} == {"seller", "buyer"}
    assert local.profile and Path(local.profile.path).read_text() == "# A bigger shop\n"
    assert run_git(worktree, "status", "--porcelain", "--untracked-files=all") == ""
    run_git(checkout, "push", "origin", "trunk")
    pushed = project.resolve(worktree).profile
    assert pushed and pushed.path == local.profile.path
    run_git(checkout, "branch", "--set-upstream-to=origin/trunk", "trunk")
    repo.outside_commit("trunk", {CAST + "operator.md": b"# The operator\n"})
    run_git(checkout, "fetch", "origin")
    remote = project.resolve(worktree)
    assert remote.source.startswith("origin/trunk at ")
    assert remote.profile and remote.profile.path == local.profile.path
    assert {found.stem for found in remote.personas} == {"seller", "buyer", "operator"}
    write(worktree, {SELLER: b"# A seller in the task\n"})
    own = project.resolve(worktree)
    assert own.source == "checkout"
    assert tuple(found.stem for found in own.personas) == ("seller",)
    assert own.profile == remote.profile
    run_git(worktree, "add", SELLER)
    run_git(worktree, "commit", "-m", "edit the persona in the task")
    assert project.resolve(worktree).source == "checkout"


def test_missing_and_stale_cast_and_init(tmp_path: Path) -> None:
    repo = RealRepo.init(tmp_path / "repo", {"README.md": b"Test\n"})
    checkout, work = repo.checkout, tmp_path / "task"
    run_git(checkout, "worktree", "add", "-b", "task", str(work))
    with pytest.raises(Refusal, match="no personas"):
        project.resolve(work)
    built = setup.init(checkout)
    assert Path(built["dir"]).is_dir()
    with pytest.raises(Refusal, match="in use"):
        setup.init(checkout)
    assert project.resolve(checkout).profile is None
    write(checkout, {PROFILE: b"# Project\n"})
    run_git(checkout, "add", ".lem")
    run_git(checkout, "commit", "-m", "write the cast")
    found = project.resolve(work)
    assert found.personas and found.profile
    with pytest.raises(Refusal, match="default branch"):
        setup.init(work)
    assert not (work / CAST).exists()


def test_index_only_and_invalid_settings_are_refused(tmp_path: Path) -> None:
    repo = RealRepo.init(tmp_path / "repo", {CAST + "README.md": b"Index\n"})
    with pytest.raises(Refusal, match="no personas"):
        project.resolve(repo.checkout)
    with pytest.raises(Refusal, match="in use"):
        setup.init(repo.checkout)
    assert (repo.checkout / CAST / "README.md").read_text() == "Index\n"
    write(repo.checkout, {SETTINGS: b"[unrecognized]\nsetting = true\n"})
    with pytest.raises(Refusal, match="unrecognized"):
        project.resolve(repo.checkout)
    wrong = lem("--repo", str(tmp_path / "missing"), "cast")
    assert wrong.code == 2


def test_panel_folder_lives_in_the_main_checkout(tmp_path: Path) -> None:
    repo = RealRepo.init(tmp_path / "repo", {"README.md": b"Test\n"})
    work = tmp_path / "task"
    run_git(repo.checkout, "worktree", "add", "-b", "task", str(work))
    day = datetime.now().astimezone().date()
    panel = lem("--repo", str(work), "cast", "run-dir", "one-task")
    assert panel.code == 0
    target = repo.checkout / ".lem" / "state" / "panels" / f"{day}-one-task"
    assert panel.result() == {"dir": str(target)}
    assert target.is_dir()
    with pytest.raises(Refusal, match="exists"):
        setup.run_dir(work, "one-task")
    assert (
        run_git(repo.checkout, "status", "--porcelain", "--untracked-files=all") == ""
    )


def test_persona_seats_allow_the_agent_to_supply_defaults(tmp_path: Path) -> None:
    text = '---\nseats: ["claude/opus", "codex", "claude:low"]\n---\n'
    found, _ = front.frontmatter(text, tmp_path / "seller.md")
    assert [(seat.agent, seat.model, seat.effort) for seat in found] == [
        ("claude", "opus", None),
        ("codex", None, None),
        ("claude", None, "low"),
    ]
