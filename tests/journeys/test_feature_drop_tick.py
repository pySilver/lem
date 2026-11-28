"""The drop of a feature and the parts comment on its issue, on a real repository and
`LocalForge` (`docs/plans/2026-11-27-a-feature-in-parts.md`, "The drop" and "A part's ticket
step"; step 36e).

The owner's `/lem drop x` drops each of its two open parts and then the feature: the part's pull
request stays open, each branch keeps its commits on origin, and the line names the one command
that deletes `feature/x`, which Lem never runs.

`lem issue tick x` writes the parts comment on the feature's issue from the records, over the
in-memory issues of `fakes/issues.py`: posted at the split, edited when a part's end changes the
text, and a tick that a stop cut off after its edit, run again, edits nothing.
"""

import dataclasses
from typing import TYPE_CHECKING

import pytest

from fakes.issues import REPO, FakeIssues
from fakes.repo import git_env
from journeys.test_feature_parts import (
    FEATURE,
    FEATURE_BRANCH,
    FIRST,
    SECOND,
    THREE,
    approved_feature,
    built,
    feature,
    made,
    ok,
    proposed,
    record_of,
    shaped,
)
from journeys.test_skeleton import lem
from lem.adapters.tracker_gh_facts import Issue
from lem.app import wiring
from lem.ports.place import Place

if TYPE_CHECKING:
    from pathlib import Path

    from journeys.test_skeleton import World

type Capsys = pytest.CaptureFixture[str]

WHY = "the owner has a better idea"
ISSUE = Issue(
    number=42,
    url=f"https://github.com/{REPO}/issues/42",
    title="The docs, in three parts",
    body="The README and the notes.",
    state="open",
    author="ann",
)


def test_the_drop_of_a_feature_drops_its_two_open_parts_and_names_the_delete(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    feature(capsys, world)
    shaped(capsys, world, FIRST, "the README says recieve; fix it")
    shaped(capsys, world, SECOND, "the notes say hello")
    built(capsys, world, SECOND, {"NOTES.md": "Hello.\n"})
    pull = proposed(capsys, world, SECOND)["result"]["pull"]
    pushed = world.repo.head_of(f"docs/{SECOND}")
    assert pushed is not None

    said = ok(capsys, world, "task", "move", FEATURE, "dropped", "--line", WHY)
    done = said["result"]
    assert [(part["slug"], part.get("pull")) for part in done["parts"]] == [
        (FIRST, None),
        (SECOND, pull["url"]),
    ]
    assert done["delete"] == f"git push origin --delete {FEATURE_BRANCH}"
    assert pull["url"] in said["say"]
    assert (
        f"the owner deletes it with git push origin --delete {FEATURE_BRANCH}"
        in (said["say"])
    )
    for slug in (FIRST, SECOND, FEATURE):
        assert record_of(world, slug)["task"]["status"] == "dropped"
    # the pull request stays open, and every branch keeps its commits on origin
    assert [found.state for found in world.forge.pulls.values()] == ["open"]
    assert world.repo.head_of(FEATURE_BRANCH) is not None
    assert world.repo.head_of(f"docs/{SECOND}") == pushed


def ticketed(world: World, monkeypatch: pytest.MonkeyPatch) -> FakeIssues:
    """The project's tracker made GitHub's, and the in-memory issues bound as its tracker."""
    settings = world.checkout / ".lem" / "settings.toml"
    with settings.open("a", encoding="utf-8") as found:
        found.write('\n[tracker]\nkind = "github"\n')
    fake = FakeIssues(issues={42: ISSUE})
    place = Place(
        checkout=world.checkout, home=world.folder / "home", environ=git_env()
    )
    ports = dataclasses.replace(wiring.bound(place), tracker=fake)
    monkeypatch.setattr(wiring, "bound", lambda place: ports)
    return fake


def test_a_tick_cut_off_after_its_edit_edits_nothing_when_it_runs_again(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    fake = ticketed(world, monkeypatch)
    path = approved_feature(capsys, world, "--ticket", "42", "--ticket-repo", REPO)
    ok(capsys, world, "task", "split", FEATURE, "--file", path)
    assert record_of(world, FEATURE)["task"]["ticket"]["id"] == "#42"
    for slug in THREE:
        assert record_of(world, slug)["task"].get("ticket") is None

    posted = ok(capsys, world, "issue", "tick", FEATURE)
    assert posted["result"]["did"] == ["posted the parts comment"]
    lines = fake.threads[42][-1].text.splitlines()
    assert lines[0] == f"- [ ] {FIRST}: the README says receive"
    assert lines[-1] == f"lem: {FEATURE} parts"

    ok(capsys, world, "task", "move", SECOND, "dropped", "--line", WHY)
    fake.cut_after_edit = True
    cut = lem(capsys, world.checkout, "issue", "tick", FEATURE)
    assert cut["code"] == 3, cut
    fake.cut_after_edit = False
    assert f"- [ ] {SECOND}: the notes say hello (dropped)" in fake.threads[42][-1].text

    again = ok(capsys, world, "issue", "tick", FEATURE)
    assert again["result"]["did"] == []
    assert [call[0] for call in fake.writes()] == ["comment", "edit_comment"]
    assert len(fake.threads[42]) == 1
