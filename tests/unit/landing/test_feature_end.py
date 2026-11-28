"""The end of a feature (`model/landing/feature.py`, and where `start`, `base`, `polish`, `merge`
and `merge_call` read it): its start waits for its parts, its base is a merge, it has no polish
pass, its merge is the owner's alone, always a squash that lists the parts, and not while a pull
request goes into its branch. A task that no part names keeps every rule as it was: the world
with no `feature` is the world of every other case of `tests/unit/landing/`."""

from typing import TYPE_CHECKING

import pytest
from inline_snapshot import snapshot
from msgspec.structs import replace

from lem.kernel.errors import Refusal
from lem.model.landing import (
    base,
    checks,
    feature,
    feature_said,
    merge,
    merge_call,
    merge_lines,
    start,
    start_said,
)
from lem.model.landing.feature_seen import Feature, PartSeen, Targeting
from lem.model.landing.world import Due, Held, Rules
from lem.model.owner.looks import Look, MergeBasis
from lem.model.owner.merging import owner_reason
from lem.records.landing.record import Pull
from lem.records.landing.review import Counts
from lem.records.task import Shape
from unit.landing.merges import BY_MERGER, BY_OWNER, SUBJECT, code_of, facing, opened
from unit.landing.worlds import BASE, BRANCH, REVIEWED, TREE, task, world

if TYPE_CHECKING:
    from lem.records.record import Record

PART = PartSeen(
    slug="save-endpoint",
    status="landed",
    pull=Pull(number=3, url="https://github.com/o/p/pull/3", title="feat: save"),
    green=True,
    review=replace(REVIEWED, kind="round", counts=Counts(should=1)),
)
DROPPED = PartSeen(slug="android-list", status="dropped")
FEATURE = Feature(parts=(PART, DROPPED))
KEEP = Rules(base="main", history="keep", commands=("true",))
INTO = Targeting(number=7, url="https://github.com/o/p/pull/7", head="docs/teammate")


def refused(found: object) -> tuple[str, str, str]:
    """The refusal's code, why and fix; a case fails on anything else."""
    assert isinstance(found, Refusal), found
    return found.code, found.why, found.fix


def full() -> Record:
    """A task of the standard track, landing."""
    made = task("landing")
    shape = Shape(type="feat", why="a feature", track="full")
    return replace(made, task=replace(made.task, shape=shape))


def test_a_feature_starts_only_once_each_of_its_parts_ended() -> None:
    ready = task("ready")
    building = replace(PART, slug="ios-button", status="building")
    open_world = world(feature=Feature(parts=(PART, building, DROPPED)))
    assert refused(
        start.decide(ready, open_world, start.Facts(), conflicting=False)
    ) == (
        snapshot(
            (
                "parts-open",
                (
                    "the feature fix-the-login lands once each of its parts ended, and "
                    "ios-button (building) has not"
                ),
                (
                    "each part lands, or the owner drops it (/lem drop PART); then lem land "
                    "start fix-the-login runs again"
                ),
            )
        )
    )
    unread = world(feature=replace(FEATURE, unread=("broken",)))
    found = start.decide(ready, unread, start.Facts(), conflicting=False)
    assert code_of(found) == "parts-open"
    assert "broken (its record does not read)" in refused(found)[1]
    ended = start.decide(
        ready, world(feature=FEATURE), start.Facts(), conflicting=False
    )
    assert not isinstance(ended, Refusal)
    assert ended.base_ref == "main"


def test_a_task_with_no_parts_starts_as_before() -> None:
    made = start.decide(task("ready"), world(), start.Facts(), conflicting=False)
    assert not isinstance(made, Refusal)
    assert (made.round, made.branch, made.base_ref) == (1, BRANCH, "main")
    assert feature.parts_open(task("ready"), world()) is None


def test_a_feature_takes_in_the_base_by_a_merge_and_a_task_by_a_rebase() -> None:
    record = task("landing")
    facts = base.Facts(ahead=2)
    behind = {"base_in_tip": False}
    assert base.decide(record, world(**behind, feature=FEATURE), facts, "w") == "merge"
    assert base.decide(record, world(**behind), facts, "w") == "rebase"
    assert base.decide(record, world(feature=FEATURE), facts, "w") == "onto"
    assert base.decide(record, world(), facts, "w") == "onto"


def test_a_feature_has_no_polish_pass_and_a_standard_task_has_one() -> None:
    record = full()
    found = checks.polished(record, world(feature=FEATURE))
    assert found == Held(why=feature.NO_POLISH)
    due = checks.polished(record, world())
    assert isinstance(due, Due)
    assert due.step == "polish"
    assert refused(feature.polish_refusal(record, world(feature=FEATURE))) == (
        "feature",
        "a feature has no polish pass: each of its parts had its own",
        "`lem land checks fix-the-login` is the next step",
    )
    assert feature.polish_refusal(record, world()) is None


def test_only_the_owner_merges_a_feature_and_the_merge_agent_merges_a_task() -> None:
    record = opened()
    assert merge.authority(record, facing()) is None
    assert merge.authority(record, facing(feature=FEATURE)) == feature.OWNER
    assert merge.authority(record, verdict=False, land="agent") is None
    assert merge.authority(record, verdict=False, is_feature=True) == feature.OWNER
    found = merge.decide(record, facing(feature=FEATURE), BY_MERGER, TREE)
    assert refused(found)[:2] == (
        "merger-rule",
        f"the merge agent may not merge: {feature.OWNER}",
    )
    assert merge.due(record, facing(feature=FEATURE)).by == "owner"
    assert merge.who(facing(feature=FEATURE), ()) == "owner"
    assert merge.who(facing(), ()) == "merger"


def test_the_owner_list_gives_a_features_merge_to_the_owner() -> None:
    record = opened()
    plain = Look(record=record, basis=MergeBasis(tree=TREE, land="agent", base=BASE))
    assert owner_reason(plain) is None
    named = replace(plain, basis=replace(plain.basis, feature=True))
    assert owner_reason(named) == feature.OWNER


def test_a_feature_is_one_squash_that_lists_its_parts_whatever_the_history() -> None:
    made = merge.decide(opened(), facing(rules=KEEP, feature=FEATURE), BY_OWNER, TREE)
    assert isinstance(made, merge_call.Merging)
    assert (made.method, made.subject) == ("squash", SUBJECT)
    assert made.body == snapshot(
        """\
Parts:
- save-endpoint: #3 (https://github.com/o/p/pull/3), landed, review round: 0 must-fix, 1 should, 0 nit, not careful, green
- android-list: no pull request, dropped

Lem task: fix-the-login"""
    )
    plain = merge.decide(opened(), facing(), BY_OWNER, TREE)
    assert isinstance(plain, merge_call.Merging)
    assert (plain.method, plain.body) == ("squash", "Lem task: fix-the-login")
    keep = merge.decide(
        opened(), facing(rules=KEEP), replace(BY_OWNER, subject=None), TREE
    )
    assert isinstance(keep, merge_call.Merging)
    assert keep.method == "rebase"


def test_a_features_squash_needs_its_subject_where_the_history_keeps_commits() -> None:
    bare = replace(BY_OWNER, subject=None)
    assert refused(
        merge.decide(opened(), facing(rules=KEEP, feature=FEATURE), bare, TREE)
    ) == (
        "message",
        "the request is a feature: its branch lands as one commit, with a subject",
        "pass --message with the commit subject of the feature",
    )
    assert feature.squashes(world(rules=KEEP, feature=FEATURE))
    assert not feature.squashes(world(rules=KEEP))
    assert feature.squashes(world())


def test_the_merge_is_refused_while_a_pull_request_goes_into_the_features_branch() -> (
    None
):
    other = Targeting(number=8, url="https://github.com/o/p/pull/8", head="docs/other")
    into = replace(FEATURE, targeting=(INTO, other))
    found = merge.decide(opened(), facing(feature=into), BY_OWNER, TREE)
    assert refused(found) == snapshot(
        (
            "pulls-into-feature",
            (
                "2 open pull request(s) go into docs/fix-the-login: #7 from docs/teammate "
                "(https://github.com/o/p/pull/7), #8 from docs/other "
                "(https://github.com/o/p/pull/8). Once the feature merges, docs/fix-the-login "
                "goes, and GitHub moves each of them onto main"
            ),
            (
                "each of them merges into docs/fix-the-login first, or its author closes it or "
                "moves it to another base; then the owner merges fix-the-login"
            ),
        )
    )
    assert feature.targeting(opened(), facing()) is None


def test_a_part_without_a_review_is_listed_by_its_pull_request_alone() -> None:
    assert PART.review is not None
    careful = replace(PART, review=replace(PART.review, careful=True), green=False)
    assert feature_said.part_line(careful).endswith(", careful, not green")
    assert feature_said.part_line(DROPPED) == "- android-list: no pull request, dropped"
    assert feature_said.lines(world()) == ()


def test_the_squash_body_of_a_task_with_no_parts_is_as_before() -> None:
    moved = "The checks ran on main"
    assert merge_lines.squash_body("x", moved, "## Decisions") == (
        "## Decisions\n\nThe checks ran on main\n\nLem task: x"
    )
    assert merge_lines.squash_body("x", None, parts=("- a: #1",)) == (
        "Parts:\n- a: #1\n\nLem task: x"
    )


@pytest.mark.parametrize("status", ["queued", "building", "ready", "landing", "open"])
def test_each_status_a_part_has_not_ended_in_holds_the_start(status: str) -> None:
    left = Feature(parts=(replace(PART, status=status),))
    assert feature.unended(left) == (f"save-endpoint ({status})",)


def test_a_merge_conflict_of_the_feature_names_the_commit_that_ends_it() -> None:
    record = task("landing")
    assert refused(
        feature_said.merge_conflict(record, world(feature=FEATURE), ("a.py",), "/w t")
    ) == snapshot(
        (
            "conflict",
            (
                "the merge of origin/main into docs/fix-the-login stopped on these file(s): "
                "a.py; the merge stays in the worktree, and nothing was pushed"
            ),
            (
                "a builder resolves each file in the worktree and commits the merge (`git -C "
                "'/w t' commit --no-edit`), then lem land base fix-the-login runs again"
            ),
        )
    )
    assert (
        refused(feature_said.merge_refused(record, world(), "locked"))[0]
        == "git-refused"
    )


def test_a_merge_in_progress_is_the_builders_and_base_names_it() -> None:
    record = task("landing")
    stopped = world(merging=True, clean=False)
    assert start_said.unready(record, stopped) is None
    assert start_said.unready(record, world(clean=False)) is not None
    found = base.holds(record, stopped)
    assert found == Due(step="base", why="a merge is in progress in the worktree")
    assert refused(base.decide(record, stopped, base.Facts(ahead=1), "/w t")) == (
        "merge-in-progress",
        (
            "a merge is in progress in the worktree of fix-the-login, a builder's "
            "resolution: base starts no merge over it and aborts none"
        ),
        (
            "the builder commits the resolution (`git -C '/w t' commit --no-edit`), then "
            "lem land base fix-the-login runs again"
        ),
    )
