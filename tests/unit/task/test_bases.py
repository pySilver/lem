"""The base of a task (`app/tasks/bases.py`): the recorded base once a round started, else the
feature's branch for a part, else the settings' base; a part whose feature does not read, has
ended or has no branch on origin is refused. And `Task.part_of`, a key Lem 0.4.2 reads past."""

from typing import TYPE_CHECKING, Literal
from unittest.mock import Mock

import msgspec
import pytest
from msgspec.structs import replace

from fakes.records import MOMENT, record
from lem.app.landing import world as landing_world
from lem.app.tasks import bases
from lem.kernel.errors import Refusal
from lem.records.base import Day, Frozen, Moment, Slug
from lem.records.criteria import Criteria
from lem.records.decisions import Decision
from lem.records.holds import Hold
from lem.records.landing.record import Landing
from lem.records.questions import Question
from lem.records.record import Record
from lem.records.task import Shape, Status
from lem.records.tickets import Ticket
from lem.records.work import Investigation, Plan, Span, StandIn, Talk
from unit.landing.merges import opened
from unit.landing.worlds import BASE, TREE
from unit.task.spaces import made, workspace

if TYPE_CHECKING:
    from pathlib import Path

    from lem.store.places import Workspace

FEATURE = "save-items"
FEATURE_BRANCH = f"feature/{FEATURE}"
PART = "save-endpoint"
STABLE = '[branch]\nbase = "stable"\n'


class OldTask(Frozen, frozen=True, kw_only=True):
    """`Task` of Lem 0.4.2 (`src/lem/records/task.py` at `f8e4a91b`), copied: every key it
    reads, and none it does not."""

    slug: Slug
    ask: str
    opened: Moment
    status: Status
    since: Moment
    hold: Hold | None = None
    branch: str | None = None
    backlog_item: str | None = None
    resumed_from: Slug | None = None
    ticket: Ticket | None = None
    night: Day | None = None
    plan_only: bool = False
    after: tuple[Slug, ...] = ()
    order: str | None = None
    mode: Literal["with-owner", "alone"] = "with-owner"
    mode_since: Moment | None = None
    shape: Shape | None = None
    owner_careful: Moment | None = None
    lead: Literal["builder", "session", "small"] | None = None
    plan: Plan | None = None
    investigation: Investigation | None = None
    talk: Talk | None = None
    spans: tuple[Span, ...] = ()
    stand_ins: tuple[StandIn, ...] = ()
    criteria: Criteria = Criteria()
    decisions: tuple[Decision, ...] = ()
    questions: tuple[Question, ...] = ()


class OldRecord(Frozen, frozen=True, kw_only=True, omit_defaults=False):
    """`Record` of Lem 0.4.2, around its `Task`."""

    schema: int = 1
    release: str
    revision: int = 0
    task: OldTask
    landing: Landing | None = None
    journal: tuple[object, ...] = ()


OLD = OldRecord(
    release="0.4.2",
    revision=3,
    task=OldTask(
        slug=FEATURE,
        ask="save the items",
        opened=MOMENT,
        status="queued",
        since=MOMENT,
        branch=FEATURE_BRANCH,
        after=("save-endpoint", "ios-save-button"),
        order="after save-endpoint",
        shape=Shape(type="feat", why="a new ability", track="full", then="lead"),
        lead="session",
    ),
)


def test_a_task_record_of_lem_0_4_2_reads_as_no_part_and_is_written_back_the_same() -> (
    None
):
    body = msgspec.json.encode(OLD)
    read = msgspec.json.decode(body, type=Record)
    assert read.task.part_of is None
    assert msgspec.json.decode(msgspec.json.encode(read)) == msgspec.json.decode(body)


def test_a_part_written_now_keeps_every_key_lem_0_4_2_reads() -> None:
    old = msgspec.json.decode(msgspec.json.encode(OLD), type=Record)
    part = replace(old, task=replace(old.task, slug=PART, part_of=FEATURE))
    written = msgspec.json.decode(msgspec.json.encode(part))
    before = msgspec.json.decode(msgspec.json.encode(OLD))["task"]
    assert written["task"].pop("part_of") == FEATURE
    assert written["task"] == {**before, "slug": PART}
    read_by_old = msgspec.json.decode(msgspec.json.encode(part), type=OldRecord)
    assert read_by_old.task == replace(OLD.task, slug=PART)


def on_origin(*branches: str) -> Mock:
    """A git whose origin has `branches`, each at `BASE`."""
    git = Mock()
    git.remote_head.side_effect = lambda _where, branch: (
        BASE if branch in branches else None
    )
    return git


def feature(where: Workspace, **fields: object) -> None:
    """The feature's record: queued on its branch, with `fields` over it."""
    made(where, FEATURE, **{"branch": FEATURE_BRANCH, **fields})


def part(**fields: object) -> Record:
    return record(PART, status="building", part_of=FEATURE, **fields)


def refused(where: Workspace, chosen: Record, git: Mock | None = None) -> Refusal:
    with pytest.raises(Refusal) as error:
        bases.chosen(git or on_origin(FEATURE_BRANCH), where, chosen)
    assert error.value.code == "part-of"
    return error.value


def test_a_task_with_no_landing_and_no_feature_takes_the_settings_base(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path, STABLE)
    git = on_origin()
    assert bases.chosen(git, where, record(status="building")) == "stable"
    git.remote_head.assert_not_called()


def test_a_part_takes_its_features_branch_on_origin(tmp_path: Path) -> None:
    where = workspace(tmp_path, STABLE)
    feature(where)
    git = on_origin(FEATURE_BRANCH)
    assert bases.chosen(git, where, part()) == FEATURE_BRANCH
    git.remote_head.assert_called_once_with(where.checkout, FEATURE_BRANCH)


def test_a_recorded_base_stands_for_a_part_whose_feature_is_gone(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path, STABLE)
    started = opened()
    started = replace(started, task=replace(started.task, part_of="gone"))
    git = on_origin()
    assert bases.chosen(git, where, started) == "main"
    git.remote_head.assert_not_called()


def test_a_part_whose_feature_is_not_there_is_refused(tmp_path: Path) -> None:
    where = workspace(tmp_path, STABLE)
    found = refused(where, part())
    assert found.why.startswith(f"{PART} is a part of {FEATURE}, and the record of")
    assert f"no task {FEATURE} here" in found.why
    assert found.fix.endswith(f"the owner drops {PART} with /lem drop {PART}")


def test_a_part_whose_feature_record_does_not_read_is_refused(tmp_path: Path) -> None:
    where = workspace(tmp_path, STABLE)
    feature(where)
    (where.state / "tasks" / FEATURE / "task.json").write_text("{")
    found = refused(where, part())
    assert "is no task record" in found.why
    assert found.fix.startswith(f"lem task show {FEATURE} names what is wrong")


@pytest.mark.parametrize("ended", ["landed", "dropped", "answered"])
def test_a_part_whose_feature_ended_is_refused(tmp_path: Path, ended: str) -> None:
    where = workspace(tmp_path, STABLE)
    feature(where, status=ended)
    found = refused(where, part())
    assert found.why == (
        f"{PART} is a part of {FEATURE}, which is {ended}, so nothing lands on its "
        "branch any more"
    )


def test_a_part_whose_feature_has_no_branch_on_origin_is_refused(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path, STABLE)
    feature(where)
    found = refused(where, part(), on_origin())
    assert (
        found.why
        == f"{PART} is a part of {FEATURE}, and origin has no branch {FEATURE_BRANCH}"
    )
    assert found.fix.startswith(f"push {FEATURE_BRANCH} to origin, then run the step")


def test_a_part_whose_feature_has_no_branch_yet_is_refused(tmp_path: Path) -> None:
    where = workspace(tmp_path, STABLE)
    feature(where, branch=None)
    found = refused(where, part())
    assert (
        found.why == f"{PART} is a part of {FEATURE}, and {FEATURE} has no branch yet"
    )


def test_the_world_of_a_part_reads_origin_at_its_features_branch(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path, STABLE)
    feature(where)
    ports = Mock()
    ports.git = on_origin(FEATURE_BRANCH)
    ports.git.tree.return_value = TREE
    found = landing_world.origin(ports, where, part(branch=f"feat/{PART}"), MOMENT)
    assert (found.rules.base, found.base, found.base_tree) == (
        FEATURE_BRANCH,
        BASE,
        TREE,
    )
