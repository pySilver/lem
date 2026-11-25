"""The `gh` adapter (`lem.adapters.forge_gh`) against the `Forge` port's contract, with a stand-in
for `gh` on the test's PATH (`gh_standin.py`): a `LocalForge` over a real origin, answered in
gh's own JSON, that records every call. No call leaves the machine; trial S3 runs the same suite
against a scratch repository on GitHub.

Besides the contract: a text goes on gh's standard input whatever it holds, a merge pins its
head and its method, a rebase merge's base is the commit before the first one it replayed, and a
gh that is not on the PATH, has no login, or prints no address is said as such.
"""

import dataclasses
import json
import os
import shutil
import stat
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import msgspec
import pytest

from contract.suites.forge import TEXT, ForgeContract
from fakes.repo import RealRepo, git_env, run_git
from lem.adapters import forge_gh, forge_gh_pulls
from lem.kernel.errors import Refusal
from lem.ports.faults import Unanswered
from lem.ports.forge_facts import MergeDenied, MergeDone, MergeOutcome
from lem.ports.place import Place

TESTS = Path(__file__).resolve().parents[1]
LAUNCHER = """#!/bin/sh
exec {python} -I -B -c 'import runpy, sys; sys.path.insert(0, "{tests}"); \
runpy.run_module("contract.gh_standin", run_name="__main__")' "$@"
"""
FILES = {"README.md": b"one\n"}
# The origin's address as a checkout of a GitHub repository names it; git reaches the test's
# own origin through `url.<origin>.insteadOf`.
GITHUB = "https://github.com/owner/project.git"


@dataclass(frozen=True)
class GhWorld:
    """The adapter, the repository behind the stand-in, and the stand-in's state file."""

    forge: forge_gh.ForgeGh
    repo: RealRepo
    state: Path

    def push(self, branch: str, files: dict[str, bytes | None]) -> str:
        return self.repo.outside_commit(branch, files)

    def head(self, branch: str) -> str | None:
        return self.repo.head_of(branch)

    def settle(self, number: int, outcome: MergeOutcome) -> MergeOutcome:
        return outcome

    def calls(self) -> list[list[str]]:
        """Every call of gh, in order."""
        return json.loads(self.state.read_text()).get("calls", [])


def gh_world(folder: Path) -> GhWorld:
    """A real repository, the stand-in for `gh` first on the PATH, and the adapter over them."""
    repo = RealRepo.init(folder / "repo", dict(FILES))
    run_git(repo.checkout, "config", "remote.origin.url", GITHUB)
    run_git(repo.checkout, "config", f"url.{repo.origin}.insteadOf", GITHUB)
    state = folder / "gh-state.json"
    begun = {
        "origin": str(repo.origin),
        "checkout": str(repo.checkout),
        "teammate": str(repo.teammate),
    }
    state.write_bytes(msgspec.json.encode(begun))
    bin_folder = folder / "bin"
    bin_folder.mkdir()
    launcher = bin_folder / "gh"
    launcher.write_text(LAUNCHER.format(python=sys.executable, tests=TESTS))
    launcher.chmod(launcher.stat().st_mode | stat.S_IXUSR)
    path = f"{bin_folder}{os.pathsep}{os.environ['PATH']}"
    environ = {**git_env(), "PATH": path, "GH_STANDIN_STATE": str(state)}
    place = Place(checkout=repo.checkout, home=folder / "home", environ=environ)
    return GhWorld(forge=forge_gh.bind(place), repo=repo, state=state)


class TestForgeGh(ForgeContract):
    def world(self, folder: Path) -> GhWorld:
        return gh_world(folder)


def test_a_merge_pins_the_head_it_names_and_squashes(tmp_path: Path) -> None:
    world = gh_world(tmp_path)
    head = world.push("fix-the-login", {"a.txt": b"a\n"})
    opened = world.forge.open_pull("fix-the-login", "main", "Fix", "body")
    world.forge.merge(opened.number, head, "squash", TEXT)
    merging = [call for call in world.calls() if call[:2] == ["pr", "merge"]]
    assert len(merging) == 1
    assert merging[0][merging[0].index("--match-head-commit") + 1] == head
    assert "--squash" in merging[0]


def test_a_rebase_merge_replays_each_commit_and_reports_the_base_before_them(
    tmp_path: Path,
) -> None:
    world = gh_world(tmp_path)
    world.push("fix-the-login", {"a.txt": b"a\n"})
    head = world.push("fix-the-login", {"b.txt": b"b\n"})
    base = world.head("main")
    opened = world.forge.open_pull("fix-the-login", "main", "Fix", "body")
    done = world.forge.merge(opened.number, head, "rebase", TEXT)
    assert isinstance(done, MergeDone)
    assert done.base_parent == base
    assert world.forge.pull(opened.number).base_parent == base
    assert run_git(world.repo.origin, "rev-list", "--count", f"{base}..main") == "2"
    merging = [call for call in world.calls() if call[:2] == ["pr", "merge"]]
    assert "--rebase" in merging[0]


def test_a_text_goes_on_gh_standard_input_as_it_is(tmp_path: Path) -> None:
    world = gh_world(tmp_path)
    world.push("fix-the-login", {"a.txt": b"a\n"})
    text = (
        "**Not green.**\n\n- `--body` is a word of the text, not of gh\n"
        + "x" * 300_000
    )
    opened = world.forge.open_pull("fix-the-login", "main", "Fix", text)
    assert world.forge.pull(opened.number).body == text
    again = text.replace("Not green", "Green")
    assert world.forge.update_pull(opened.number, "Fix", again).body == again
    sent = [
        call for call in world.calls() if call[:2] in (["pr", "create"], ["pr", "edit"])
    ]
    assert all(call[call.index("--body-file") + 1] == "-" for call in sent)
    assert not any("--body" in call for call in sent)


def test_a_gh_with_no_login_is_refused_with_its_fix(tmp_path: Path) -> None:
    world = gh_world(tmp_path)
    state = json.loads(world.state.read_text())
    world.state.write_text(json.dumps({**state, "login": False}))
    with pytest.raises(Refusal) as refused:
        world.forge.find_pulls("fix-the-login", "main")
    assert refused.value.code == "gh-login"
    assert "gh auth login" in refused.value.fix


def test_github_reports_a_confirmed_queue_removal_and_its_reason(
    tmp_path: Path,
) -> None:
    world = gh_world(tmp_path)
    world.push("fix-the-login", {"a.txt": b"a\n"})
    opened = world.forge.open_pull("fix-the-login", "main", "Fix", "body")
    assert (opened.queued, opened.dequeued) == (None, None)
    state = json.loads(world.state.read_text())
    added = {"__typename": "AddedToMergeQueueEvent"}
    removed = {
        "__typename": "RemovedFromMergeQueueEvent",
        "reason": "a required check failed in the queue",
    }
    for events, active, queued, reason in (
        ([added, removed], False, None, removed["reason"]),
        ([removed, added], True, "the merge queue", None),
        ([removed, added], False, None, None),
        ([removed], True, "the merge queue", None),
    ):
        world.state.write_text(
            json.dumps({**state, "queue_events": events, "in_queue": active})
        )
        pull = world.forge.pull(opened.number)
        assert (pull.queued, pull.dequeued) == (queued, reason)


def test_no_gh_on_the_path_is_refused_by_name(tmp_path: Path) -> None:
    world = gh_world(tmp_path)
    only_git = tmp_path / "only-git"
    only_git.mkdir()
    (only_git / "git").symlink_to(shutil.which("git") or "/usr/bin/git")
    bare = dataclasses.replace(
        world.forge, environ={**world.forge.environ, "PATH": str(only_git)}
    )
    with pytest.raises(Refusal) as refused:
        bare.find_pulls("fix-the-login", "main")
    assert refused.value.code == "no-gh"


@pytest.mark.parametrize(
    ("said", "kind"),
    [
        ("GraphQL: Head branch was modified. Review and try the merge again.", "tip"),
        ("GraphQL: Pull Request has merge conflicts", "base"),
        ("GraphQL: Required status check is expected", "rule"),
    ],
)
def test_githubs_refusal_is_read_by_its_words(said: str, kind: str) -> None:
    ran = subprocess.CompletedProcess(["gh"], 1, stdout="", stderr=f"{said}\n")
    assert forge_gh_pulls.denied(ran) == msgspec.convert(
        {"kind": kind, "said": said}, MergeDenied
    )


def test_every_call_names_the_repository_of_origin_whatever_gh_repo_says(
    tmp_path: Path,
) -> None:
    world = gh_world(tmp_path)
    aimed = dataclasses.replace(
        world.forge, environ={**world.forge.environ, "GH_REPO": "someone/else"}
    )
    world.push("fix-the-login", {"a.txt": b"a\n"})
    opened = aimed.open_pull("fix-the-login", "main", "Fix", "body")
    assert aimed.repo().name == "owner/project"
    assert opened.number == 1
    pulls = [call for call in world.calls() if call[0] == "pr"]
    assert pulls
    assert all(call[call.index("--repo") + 1] == "owner/project" for call in pulls)


def test_an_origin_that_is_not_on_github_is_refused_by_name(tmp_path: Path) -> None:
    world = gh_world(tmp_path)
    run_git(world.repo.checkout, "config", "remote.origin.url", str(world.repo.origin))
    with pytest.raises(Refusal) as refused:
        world.forge.find_pulls("fix-the-login", "main")
    assert refused.value.code == "not-github"
    assert world.calls() == []


def test_a_lost_reply_before_the_merge_is_no_refusal(tmp_path: Path) -> None:
    world = gh_world(tmp_path)
    head = world.push("fix-the-login", {"a.txt": b"a\n"})
    opened = world.forge.open_pull("fix-the-login", "main", "Fix", "body")
    state = json.loads(world.state.read_text())
    world.state.write_text(json.dumps({**state, "lose": "before"}))
    with pytest.raises(Unanswered, match="error connecting"):
        world.forge.merge(opened.number, head, "squash", TEXT)
    assert world.forge.pull(opened.number).state == "open"


def test_a_lost_reply_after_the_merge_gives_the_merge_the_forge_shows(
    tmp_path: Path,
) -> None:
    world = gh_world(tmp_path)
    head = world.push("fix-the-login", {"a.txt": b"a\n"})
    opened = world.forge.open_pull("fix-the-login", "main", "Fix", "body")
    state = json.loads(world.state.read_text())
    world.state.write_text(json.dumps({**state, "lose": "after"}))
    outcome = world.forge.merge(opened.number, head, "squash", TEXT)
    assert isinstance(outcome, MergeDone)
    assert outcome.merged_head == head


def test_a_create_that_prints_no_address_is_said_as_such() -> None:
    with pytest.raises(Unanswered, match="printed no pull request address"):
        forge_gh_pulls.number_of("Warning: 2 uncommitted changes\n")
    assert forge_gh_pulls.number_of("https://github.com/o/p/pull/12\n") == 12


def test_a_rebase_counts_its_commits_from_githubs_total_not_a_list_it_caps(
    tmp_path: Path,
) -> None:
    world = gh_world(tmp_path)
    world.push("fix-the-login", {"a.txt": b"a\n"})
    head = world.push("fix-the-login", {"b.txt": b"b\n"})
    opened = world.forge.open_pull("fix-the-login", "main", "Fix", "body")
    world.forge.merge(opened.number, head, "rebase", TEXT)
    asked = [
        call for call in world.calls() if call[0] == "api" and "/pulls/" in call[1]
    ]
    assert asked == [["api", "repos/owner/project/pulls/1", "--jq", ".commits"]]
    assert not [call for call in world.calls() if "commits" in call and call[0] == "pr"]


def test_github_preserves_a_queue_removal_with_no_reason(tmp_path: Path) -> None:
    world = gh_world(tmp_path)
    world.push("fix-the-login", {"a.txt": b"a\n"})
    opened = world.forge.open_pull("fix-the-login", "main", "Fix", "body")
    state = json.loads(world.state.read_text())
    event = {
        "__typename": "RemovedFromMergeQueueEvent",
        "id": "removal-id",
        "createdAt": "2026-11-25T11:00:00Z",
        "reason": None,
        "head": {"oid": opened.head},
    }
    world.state.write_text(json.dumps({**state, "queue_events": [event]}))

    pull = world.forge.pull(opened.number)

    assert pull.dequeued == "GitHub removed the pull request from the merge queue"
    assert pull.queue_event is not None
    assert pull.queue_event.id == "removal-id"
    assert pull.queue_event.head == opened.head
    assert pull.queue_event.at.isoformat() == "2026-11-25T11:00:00+00:00"
