"""`lem issue tick NAME`: the parts comment of a feature on its issue. Its text from the records
(no part landed, one, all, a dropped part), the rule that finds and edits it (absent: post; the
same text: nothing; another text: edit), the step over the in-memory issues of
`fakes/issues.py`, and its refusals. What gh is asked is `tests/contract/test_tracker.py`'s."""

from typing import TYPE_CHECKING

import msgspec
import pytest
from msgspec.structs import replace

from fakes.records import MOMENT, record
from lem.adapters.tracker_gh_facts import Comment
from lem.app.tasks.issues import tick, tick_due
from lem.kernel.envelope import Envelope
from lem.kernel.errors import Fault, Refusal
from lem.model.task import feature_parts, parts_comment
from lem.ports.faults import Unanswered
from lem.store import tasks
from unit.task.issues_world import World, world
from unit.task.spaces import made, read

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.task import Task

FEATURE = "save-items"
PARTS = (
    ("save-endpoint", "the server saves an item and returns it"),
    ("ios-save-button", "the iOS app saves the item it shows"),
    ("android-saved-list", "the Android app lists the saved items"),
)
MARKER = f"lem: {FEATURE} parts"
LINEAR = '[branch]\nbase = "main"\n[tracker]\nkind = "linear"\n'


def feature_task() -> Task:
    after = tuple(slug for slug, _ in PARTS)
    return record(FEATURE, ask="save items", after=after).task


def parts(*statuses: str) -> tuple[Task, ...]:
    """The three parts of the feature in the statuses given, in a shuffled order."""
    made_parts = [
        record(slug, ask=ask, status=status, part_of=FEATURE).task
        for (slug, ask), status in zip(PARTS, statuses, strict=True)
    ]
    return tuple(reversed(made_parts))


def text_of(*statuses: str) -> str:
    feature = feature_task()
    return parts_comment.text(
        feature, feature_parts.parts_of(feature, parts(*statuses))
    )


# The comment's text from the records


def test_no_part_landed_gives_three_empty_boxes_in_the_order_of_the_features_after() -> (
    None
):
    assert text_of("shaping", "queued", "queued") == (
        "- [ ] save-endpoint: the server saves an item and returns it\n"
        "- [ ] ios-save-button: the iOS app saves the item it shows\n"
        "- [ ] android-saved-list: the Android app lists the saved items\n"
        "\n"
        f"{MARKER}\n"
    )


def test_one_part_landed_sets_its_box_alone() -> None:
    lines = text_of("landed", "building", "queued").splitlines()
    assert lines[:3] == [
        "- [x] save-endpoint: the server saves an item and returns it",
        "- [ ] ios-save-button: the iOS app saves the item it shows",
        "- [ ] android-saved-list: the Android app lists the saved items",
    ]
    assert lines[-1] == MARKER


def test_every_part_landed_sets_every_box() -> None:
    lines = text_of("landed", "landed", "landed").splitlines()
    assert [line[:6] for line in lines[:3]] == ["- [x] "] * 3


def test_a_dropped_part_keeps_an_empty_box_and_says_it_was_dropped() -> None:
    lines = text_of("landed", "dropped", "ready").splitlines()
    assert lines[1] == (
        "- [ ] ios-save-button: the iOS app saves the item it shows (dropped)"
    )
    assert lines[2].endswith("the Android app lists the saved items")


def test_the_same_records_give_the_same_text() -> None:
    assert text_of("landed", "queued", "queued") == text_of(
        "landed", "queued", "queued"
    )


def test_a_part_out_of_the_features_after_comes_last_and_an_ask_gives_its_first_line() -> (
    None
):
    feature = feature_task()
    resumed = record(
        "save-endpoint-again",
        ask="\n  the server   saves an item\nand more words\n",
        status="shaping",
        part_of=FEATURE,
        opened=MOMENT,
    ).task
    other = record("not-a-part", ask="other work").task
    found = feature_parts.parts_of(
        feature, (resumed, other, *parts("landed", "dropped", "queued"))
    )
    assert [part.slug for part in found] == [
        "save-endpoint",
        "ios-save-button",
        "android-saved-list",
        "save-endpoint-again",
    ]
    assert parts_comment.line_of(resumed) == (
        "- [ ] save-endpoint-again: the server saves an item"
    )


# The rule that finds and edits it


def comment(text: str, number: int = 1) -> Comment:
    return Comment(id=number, author="octo-cat", text=text)


def test_with_no_parts_comment_the_tick_posts_one() -> None:
    body = text_of("queued", "queued", "queued")
    found = (comment("Same here.", 1), comment("Done.\n\nlem: save-items landed\n", 2))
    assert tick_due.due(found, body, MARKER) == tick_due.Due(act="post")


def test_a_parts_comment_of_the_same_text_is_not_edited() -> None:
    body = text_of("landed", "queued", "queued")
    as_github_keeps_it = body.replace("\n", "\r\n").rstrip()
    found = (comment("Same here.", 1), comment(as_github_keeps_it, 2))
    assert tick_due.due(found, body, MARKER) == tick_due.Due(act="none")


def test_a_parts_comment_of_another_text_is_edited_the_first_one() -> None:
    before = text_of("queued", "queued", "queued")
    body = text_of("landed", "queued", "queued")
    found = (comment(before, 7), comment(before, 9))
    assert tick_due.due(found, body, MARKER) == tick_due.Due(act="edit", comment=7)


def test_a_parts_comment_with_no_id_is_a_fault() -> None:
    found = (Comment(text=text_of("queued", "queued", "queued")),)
    with pytest.raises(Fault):
        tick_due.due(found, text_of("landed", "queued", "queued"), MARKER)


# The step on the issue


def featured(w: World, *statuses: str) -> None:
    """The feature with issue 42 queued after its three parts, in the statuses given."""
    after = tuple(slug for slug, _ in PARTS)
    w.task("queued", FEATURE, after=after)
    for (slug, ask), status in zip(PARTS, statuses, strict=True):
        made(w.where, slug, ask=ask, status=status, part_of=FEATURE)


def ticked(w: World, slug: str = FEATURE) -> tuple[dict[str, object], str | None]:
    found = tick.tick(w.ports, w.where, slug)
    assert isinstance(found, Envelope)
    return msgspec.json.decode(found.outcome or b"{}"), found.say


def land(w: World, slug: str) -> None:
    before = read(w.where, slug)
    tasks.update(
        w.where.state,
        slug,
        lambda found: replace(found, task=replace(found.task, status="landed")),
        before.revision,
    )


def test_the_tick_posts_at_the_split_edits_after_a_land_and_writes_nothing_again(
    tmp_path: Path,
) -> None:
    w = world(tmp_path)
    featured(w, "shaping", "queued", "queued")
    done, say = ticked(w)
    assert done["did"] == ["posted the parts comment"]
    assert done["wrote"] == []
    assert (
        say == "posted the parts comment on issue #42 of acme/shop: 0 of 3 parts landed"
    )
    assert w.thread()[-1] == text_of("shaping", "queued", "queued")
    assert w.steps(FEATURE) == []

    done, say = ticked(w)
    assert done["did"] == []
    assert say == (
        "the parts comment on issue #42 of acme/shop says it already: 0 of 3 parts landed"
    )
    land(w, "save-endpoint")
    done, say = ticked(w)
    assert done["did"] == ["edited the parts comment"]
    assert w.thread()[-1] == text_of("landed", "queued", "queued")
    assert len(w.thread()) == 2
    assert [call[0] for call in w.fake.writes()] == ["comment", "edit_comment"]
    assert w.steps(FEATURE) == []


def test_a_tick_cut_off_after_its_edit_edits_nothing_when_run_again(
    tmp_path: Path,
) -> None:
    w = world(tmp_path)
    featured(w, "landed", "building", "queued")
    w.fake.threads[42].append(comment(text_of("queued", "queued", "queued"), 42002))
    w.fake.cut_after_edit = True
    with pytest.raises(Unanswered, match="cut off after the edit"):
        tick.tick(w.ports, w.where, FEATURE)
    w.fake.cut_after_edit = False
    done, _ = ticked(w)
    assert done["did"] == []
    assert [call[0] for call in w.fake.writes()] == ["edit_comment"]
    assert w.thread()[-1] == text_of("landed", "building", "queued")


def refused(w: World, slug: str) -> Refusal:
    with pytest.raises(Refusal) as caught:
        tick.tick(w.ports, w.where, slug)
    return caught.value


def test_a_part_and_a_task_with_no_parts_are_refused_and_nothing_is_asked(
    tmp_path: Path,
) -> None:
    w = world(tmp_path)
    featured(w, "shaping", "queued", "queued")
    w.task("building", "lone-task")
    part = refused(w, "save-endpoint")
    assert (part.code, part.fix) == ("not-a-feature", f"lem issue tick {FEATURE}")
    lone = refused(w, "lone-task")
    assert lone.code == "not-a-feature"
    assert "no task names it with --part-of" in lone.why
    assert w.fake.calls == []


def test_a_feature_with_no_ticket_and_a_linear_project_are_refused(
    tmp_path: Path,
) -> None:
    w = world(tmp_path)
    made(w.where, FEATURE, after=("save-endpoint",))
    made(w.where, "save-endpoint", ask="a part", part_of=FEATURE, status="shaping")
    assert refused(w, FEATURE).code == "no-ticket"
    linear = world(tmp_path / "linear", LINEAR)
    featured(linear, "shaping", "queued", "queued")
    found = refused(linear, FEATURE)
    assert found.code == "not-github-tracker"
    assert "lem-linear" in found.fix
