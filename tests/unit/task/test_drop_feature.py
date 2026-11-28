"""The owner's drop of a feature: each part that has not ended is dropped first, each by the drop
of any task, then the feature; the line names each open pull request and the one command that
deletes the feature's branch on origin, which Lem never runs
(`docs/plans/2026-11-27-a-feature-in-parts.md`, "The drop"). A task with no parts is dropped as
before, with no line of its own."""

from typing import TYPE_CHECKING

import msgspec
import pytest
from msgspec.structs import replace

from fakes.command import lem
from fakes.forge import LocalForge
from fakes.git import ModelGit
from fakes.ports import fake_ports
from fakes.records import MOMENT
from lem.app.tasks import drop_feature
from lem.kernel.envelope import Envelope
from lem.kernel.errors import Refusal
from lem.model.task import feature_drop, table
from lem.ports.forge_facts import Pull
from lem.records.landing.record import Landing
from lem.records.landing.record import Pull as LandingPull
from lem.records.landing.start import Started
from lem.store import tasks
from unit.task.spaces import last_line, made, read, refusal, result, workspace

if TYPE_CHECKING:
    from pathlib import Path

    from lem.app.wiring import Ports
    from lem.store.places import Workspace

FEATURE = "save-items"
BRANCH = f"feature/{FEATURE}"
PULL = "https://github.com/acme/shop/pull/7"
WHY = "the owner has a better idea"


def featured(where: Workspace) -> Ports:
    """The feature queued on its branch after three parts: one landed, one with its pull
    request open, one queued; the ports whose forge holds that pull request open."""
    after = ("save-endpoint", "ios-save-button", "android-saved-list")
    made(where, FEATURE, status="queued", branch=BRANCH, after=after)
    made(where, "save-endpoint", status="landed", part_of=FEATURE)
    made(where, "ios-save-button", status="open", part_of=FEATURE)
    pull = LandingPull(number=7, url=PULL, title="feat: the iOS button")
    tasks.update(
        where.state,
        "ios-save-button",
        lambda one: replace(one, landing=Landing(phase="open", pull=pull)),
        read(where, "ios-save-button").revision,
    )
    made(where, "android-saved-list", status="queued", part_of=FEATURE)
    shown = Pull(
        number=7,
        url=PULL,
        title=pull.title,
        state="open",
        head="a" * 40,
        head_ref="feat/ios-save-button",
        base=BRANCH,
    )
    git = ModelGit(checkout=where.checkout)
    return fake_ports(git, LocalForge(remote=git, pulls={7: shown}))


def test_the_drop_of_a_feature_drops_each_part_that_has_not_ended_then_the_feature(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path)
    given = featured(where)
    found = drop_feature.feature_dropped(where, FEATURE, WHY, given)
    assert isinstance(found, Envelope)
    done = msgspec.json.decode(found.outcome or b"{}")
    assert done == {
        "slug": FEATURE,
        "was": "queued",
        "status": "dropped",
        "parts": [
            {"slug": "ios-save-button", "was": "open", "pull": PULL},
            {"slug": "android-saved-list", "was": "queued"},
        ],
        "pull": None,
        "branch": BRANCH,
        "delete": f"git push origin --delete {BRANCH}",
    }
    statuses = [
        read(where, slug).task.status
        for slug in (FEATURE, "save-endpoint", "ios-save-button", "android-saved-list")
    ]
    assert statuses == ["dropped", "landed", "dropped", "dropped"]
    assert last_line(where, FEATURE) == WHY
    assert (
        last_line(where, "ios-save-button")
        == f"dropped with its feature {FEATURE}: {WHY}"
    )
    assert found.say == (
        f"the feature {FEATURE} is dropped, and with it each part that had not ended: "
        "ios-save-button, android-saved-list; these pull requests stay open, and closing "
        f"them is the owner's call: ios-save-button: {PULL}; the branch {BRANCH} keeps "
        "its commits on origin, and Lem never deletes it: the owner deletes it with "
        f"git push origin --delete {BRANCH}"
    )


def test_a_feature_whose_parts_ended_says_so_and_a_drop_run_again_is_refused(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path)
    made(where, FEATURE, status="queued", branch=BRANCH, after=("save-endpoint",))
    made(where, "save-endpoint", status="dropped", part_of=FEATURE)
    found = drop_feature.feature_dropped(where, FEATURE, WHY)
    assert isinstance(found, Envelope)
    assert found.say is not None
    assert found.say.startswith(
        f"the feature {FEATURE} is dropped; each of its parts had ended already; "
    )
    ran = lem("task", "move", FEATURE, "dropped", "--line", WHY, cwd=tmp_path)
    assert refusal(ran)["code"] == "ended"


def test_a_task_with_no_parts_is_dropped_as_any_task_with_no_line_of_its_own(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path)
    made(where, "lone-task", status="building", after=("other-task",))
    made(where, "other-task", status="building")
    found = drop_feature.feature_dropped(where, "lone-task", WHY)
    assert found == table.Moved(slug="lone-task", was="building", status="dropped")
    assert read(where, "other-task").task.status == "building"


def test_the_command_prints_the_drop_of_a_feature_with_its_line(tmp_path: Path) -> None:
    where = workspace(tmp_path)
    made(where, FEATURE, status="queued", branch=BRANCH, after=("save-endpoint",))
    made(where, "save-endpoint", status="shaping", part_of=FEATURE)
    ran = lem("task", "move", FEATURE, "dropped", "--line", WHY, cwd=tmp_path)
    assert result(ran)["delete"] == f"git push origin --delete {BRANCH}"
    assert f"git push origin --delete {BRANCH}" in str(ran.envelope()["say"])


def test_the_line_with_no_pull_request_and_no_branch_names_neither() -> None:
    done = feature_drop.FeatureDropped(
        slug=FEATURE,
        was="queued",
        status="dropped",
        parts=(feature_drop.PartDropped(slug="save-endpoint", was="shaping"),),
    )
    assert feature_drop.said(done) == (
        f"the feature {FEATURE} is dropped, and with it each part that had not ended: "
        "save-endpoint"
    )


def test_a_plain_task_is_dropped_when_a_record_it_does_not_name_is_damaged(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path)
    made(where, "lone-task", status="queued", after=("other-task",))
    made(where, "other-task", status="building")
    made(where, "unrelated-task", status="building")
    (where.state / "tasks" / "unrelated-task" / "task.json").write_text("{broken")
    found = drop_feature.feature_dropped(where, "lone-task", WHY)
    assert found == table.Moved(slug="lone-task", was="queued", status="dropped")


def test_a_damaged_record_the_dropped_task_names_refuses_its_drop(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path)
    made(where, "lone-task", status="queued", after=("other-task",))
    made(where, "other-task", status="building")
    (where.state / "tasks" / "other-task" / "task.json").write_text("{broken")
    with pytest.raises(Refusal) as refused:
        drop_feature.feature_dropped(where, "lone-task", WHY)
    assert refused.value.code == "unread-task-record"
    assert read(where, "lone-task").task.status == "queued"


def merged_into(where: Workspace, slug: str, base: str) -> LocalForge:
    """The task `slug` with pull request 7, its landing started on `base`, and a forge that
    merged that pull request into `base`."""
    started = Started(round=1, branch=f"feat/{slug}", base_ref=base, at=MOMENT)
    pull = LandingPull(number=7, url=PULL, title="t")
    tasks.update(
        where.state,
        slug,
        lambda one: replace(one, landing=Landing(pull=pull, started=started)),
        read(where, slug).revision,
    )
    shown = Pull(
        number=7,
        url=PULL,
        title="t",
        state="merged",
        head="a" * 40,
        head_ref=f"feat/{slug}",
        base=base,
    )
    return LocalForge(remote=ModelGit(checkout=where.checkout), pulls={7: shown})


def test_a_feature_the_forge_merged_is_refused_before_any_part_is_dropped(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path)
    made(where, FEATURE, status="landing", branch=BRANCH, after=("save-endpoint",))
    made(where, "save-endpoint", status="queued", part_of=FEATURE)
    forge = merged_into(where, FEATURE, "main")
    given = fake_ports(ModelGit(checkout=where.checkout), forge)
    with pytest.raises(Refusal) as refused:
        drop_feature.feature_dropped(where, FEATURE, WHY, given)
    assert refused.value.code == "merged"
    assert read(where, "save-endpoint").task.status == "queued"


def test_a_parts_refusal_names_the_feature_the_parts_dropped_and_the_drop_again(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path)
    after = ("save-endpoint", "ios-save-button")
    made(where, FEATURE, status="queued", branch=BRANCH, after=after)
    made(where, "save-endpoint", status="queued", part_of=FEATURE)
    made(where, "ios-save-button", status="open", part_of=FEATURE)
    forge = merged_into(where, "ios-save-button", BRANCH)
    given = fake_ports(ModelGit(checkout=where.checkout), forge)
    with pytest.raises(Refusal) as refused:
        drop_feature.feature_dropped(where, FEATURE, WHY, given)
    assert refused.value.code == "merged"
    assert refused.value.why.startswith(
        f"the drop of the feature {FEATURE} stopped at its part ios-save-button: "
    )
    assert refused.value.why.endswith(
        f"The parts dropped before it stay dropped (save-endpoint), and {FEATURE} is not "
        "dropped"
    )
    assert refused.value.fix == (
        "lem land merged ios-save-button; then /lem drop save-items again, which goes on "
        "from ios-save-button"
    )
    statuses = [read(where, slug).task.status for slug in (FEATURE, *after)]
    assert statuses == ["queued", "dropped", "open"]
    # the part lands, and the drop run again goes on from there
    tasks.update(
        where.state,
        "ios-save-button",
        lambda one: replace(one, task=replace(one.task, status="landed")),
        read(where, "ios-save-button").revision,
    )
    found = drop_feature.feature_dropped(where, FEATURE, WHY, given)
    assert isinstance(found, Envelope)
    assert read(where, FEATURE).task.status == "dropped"
