"""The stop of a task two releases back: the rule, the hold set once, the commands that end the
task pass it, and `BEFORE` is older than this Lem's own release."""

import json
from typing import TYPE_CHECKING

import pytest
from msgspec.structs import replace

from fakes.command import lem
from fakes.records import record
from lem.app.tasks import release, ticket
from lem.kernel import paths
from lem.kernel import release as running
from lem.kernel.errors import Refusal
from lem.model.task import release as rule
from lem.records.holds import ReleaseHold
from lem.records.tickets import Ticket
from lem.store import tasks
from unit.task.spaces import made, read, refusal, result, workspace

if TYPE_CHECKING:
    from pathlib import Path

    from lem.store.places import Workspace

SLUG = "gift-note"


def began_on(where: Workspace, slug: str, began: str) -> None:
    """The task `slug` begun on the release `began`."""
    revision = read(where, slug).revision
    tasks.update(where.state, slug, lambda one: replace(one, release=began), revision)


@pytest.mark.parametrize(
    ("began", "stops"),
    [
        ("1.2.0", False),
        ("1.1.0", False),
        ("1.1.5", False),
        ("1.0.9", True),
        ("0.3.1", True),
    ],
)
def test_a_task_of_this_release_or_of_the_release_before_goes_on(
    began: str, *, stops: bool
) -> None:
    assert rule.stops(replace(record(SLUG), release=began), "1.2.0", "1.1.0") is stops


def test_a_task_two_releases_back_stops_with_the_message_of_the_way_on() -> None:
    said = rule.say(SLUG, "1.0.0", "1.2.0", "1.1.0")
    assert said == (
        "gift-note began on Lem 1.0.0, and Lem 1.2.0 reads only tasks begun on 1.1.0 or "
        "1.2.0. Your branch and its commits stay. /lem drop gift-note, then /lem resume "
        "gift-note, starts a new task on 1.2.0 from that branch and from the notes the "
        "task left."
    )


def test_the_release_before_is_older_than_plugin_json() -> None:
    manifest = paths.root() / ".claude-plugin" / "plugin.json"
    version = json.loads(manifest.read_text(encoding="utf-8"))["version"]
    assert running.newer(version, rule.BEFORE)


def test_a_task_two_releases_back_stops_and_sets_its_hold_once(tmp_path: Path) -> None:
    where = workspace(tmp_path)
    made(where, SLUG, status="building")
    began_on(where, SLUG, "0.1.0")
    for _ in range(2):
        with pytest.raises(Refusal) as refused:
            release.checked(where.state, SLUG)
        assert refused.value.code == "release"
    hold = read(where, SLUG).task.hold
    assert isinstance(hold, ReleaseHold)
    assert (hold.began, read(where, SLUG).revision) == ("0.1.0", 3)


def test_a_task_of_this_release_goes_on_and_writes_nothing(tmp_path: Path) -> None:
    where = workspace(tmp_path)
    made(where, SLUG, status="building")
    assert release.checked(where.state, SLUG).revision == 1


def test_a_task_that_is_not_there_yet_is_no_stop_but_no_task(tmp_path: Path) -> None:
    where = workspace(tmp_path)
    with pytest.raises(Refusal) as refused:
        release.checked(where.state, SLUG)
    assert refused.value.code == "no-task"


def test_a_step_stops_and_the_tracker_steps_of_a_tasks_end_pass(tmp_path: Path) -> None:
    where = workspace(tmp_path)
    made(where, SLUG, status="dropped", ticket=Ticket(tracker="linear", id="MBZ-1"))
    began_on(where, SLUG, "0.1.0")
    with pytest.raises(Refusal):
        ticket.recorded(where.state, SLUG, "started", None)
    shown = ticket.recorded(where.state, SLUG, "dropped", None)
    assert shown.steps == ("dropped",)


def test_a_command_of_the_tree_stops_with_the_message(tmp_path: Path) -> None:
    where = workspace(tmp_path)
    made(where, SLUG, status="building")
    began_on(where, SLUG, "0.1.0")
    ran = lem("task", "move", SLUG, "planned", cwd=tmp_path)
    assert ran.code == 1
    refused = refusal(ran)
    assert refused["code"] == "release"
    assert refused["why"].startswith("gift-note began on Lem 0.1.0")
    dropped = lem("task", "move", SLUG, "dropped", "--line", "old", cwd=tmp_path)
    assert result(dropped)["status"] == "dropped"
    assert isinstance(read(where, SLUG).task.hold, ReleaseHold)
