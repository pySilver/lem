"""The `gh` adapter (`lem.adapters.forge_gh`) against the `Forge` port's contract, with a stand-in
for `gh` on the test's PATH (`gh_standin.py`): a `LocalForge` over a real origin, answered in
gh's own JSON, that records every call. No call leaves the machine.

The slice that `slice-land` built for the plain path; `land-propose` takes it over with
`tests/contract/test_forge.py`, and trial S3 runs the same suite against a scratch repository on
GitHub.
"""

import json
import os
import stat
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import msgspec
import pytest

from contract.suites.forge import TEXT, ForgeContract
from fakes.repo import RealRepo, git_env
from lem.adapters import forge_gh, forge_gh_pulls
from lem.kernel.errors import Refusal
from lem.ports.forge_facts import MergeDenied, MergeOutcome
from lem.ports.place import Place

TESTS = Path(__file__).resolve().parents[1]
LAUNCHER = """#!/bin/sh
exec {python} -I -B -c 'import runpy, sys; sys.path.insert(0, "{tests}"); \
runpy.run_module("contract.gh_standin", run_name="__main__")' "$@"
"""
FILES = {"README.md": b"one\n"}


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
        return json.loads(self.state.read_text())["calls"]


def gh_world(folder: Path) -> GhWorld:
    """A real repository, the stand-in for `gh` first on the PATH, and the adapter over them."""
    repo = RealRepo.init(folder / "repo", dict(FILES))
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


def test_a_rebase_merge_is_refused_by_name_and_calls_nothing(tmp_path: Path) -> None:
    world = gh_world(tmp_path)
    head = world.push("fix-the-login", {"a.txt": b"a\n"})
    opened = world.forge.open_pull("fix-the-login", "main", "Fix", "body")
    with pytest.raises(Refusal) as refused:
        world.forge.merge(opened.number, head, "rebase", TEXT)
    assert refused.value.code == "not-built"
    assert "land-merge" in refused.value.fix
    assert not [call for call in world.calls() if call[:2] == ["pr", "merge"]]


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
