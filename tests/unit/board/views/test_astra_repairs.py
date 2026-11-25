"""The board's offers and documents at the seams with the task and the landing."""

from dataclasses import replace as change
from typing import TYPE_CHECKING

import pytest
from msgspec.structs import replace

from fakes.records import MOMENT
from lem.board.views import branch, folder, owed
from lem.board.views.activity import tell_landing, tell_merge
from lem.board.views.artifacts.tab import artifacts
from lem.board.views.checks import reviews
from lem.board.views.checks.tab import checks
from lem.board.views.criteria.approve import card
from lem.board.views.criteria.tab import criteria
from lem.board.views.facts import Commit
from lem.board.views.panel.confirm import Asked
from lem.board.views.panel.opened import Opened
from lem.board.views.panel.panel import panel
from lem.board.views.timeline.view import timeline
from lem.board.views.waits.acts import acts
from lem.kernel import clock
from lem.model.criteria import digest, waits
from lem.model.decisions import breaker
from lem.model.landing import merge, mergeread
from lem.model.owner.looks import Row
from lem.model.task import holds
from lem.records.decisions import Breaker
from lem.records.journal.landing import ReviewRound
from lem.records.journal.merge import ReadNoted
from lem.records.landing.record import Landing
from lem.records.landing.review import Named, Reviewed
from lem.records.task import Shape
from unit.board.views.afternoon import AfternoonGit
from unit.board.views.small import PLACE, VIEWER, task, world
from unit.board.views.test_cases_merge import BASE, NEXT, PROPOSED, SLUG, TIP, opened
from unit.board.views.test_panel_pruned import INVOICE, summarized

if TYPE_CHECKING:
    from pathlib import Path

    from lem.board.inputs.task.overview import Went
    from lem.board.views.world import Seen, World

OLD = "Show the old total.\r\n"
NEW = "Show the total with tax.\n"
PR_TEXT = "pr-1-confirmed.md"
PR_WAIT = "pr-1-pending.md"
ITEM = "docs/backlog/broken-head.md"


def awaiting(text: str, mark: str | None) -> Seen:
    """A criteria wait with a separately read file and question."""
    seen = task(status="shaping")
    held = waits.asked(seen.record.task, MOMENT, "The criteria wait", mark)
    return replace(
        seen, record=replace(seen.record, task=held), prose=(("criteria.md", text),)
    )


@pytest.mark.parametrize(
    "mark", (None, digest.shown(OLD.encode()), digest.shown(NEW.encode()))
)
def test_approval_submits_only_the_digest_of_the_text_shown(mark: str | None) -> None:
    seen = awaiting(OLD, mark)
    shown = card(world(seen), seen)
    assert shown.criteria and shown.criteria.text == OLD
    if mark == digest.shown(NEW.encode()):
        assert shown.answer is None
    else:
        assert shown.answer and shown.plain == OLD
        fields = {field.name: field.shown for field in shown.answer.fields}
        assert fields["digest"] == digest.shown(OLD.encode())


@pytest.mark.parametrize("topic", ("plan", "breaker"))
def test_fresh_hold_has_actions_and_accepts_its_confirmation_key(topic: str) -> None:
    if topic == "plan":
        seen = task(status="planned")
        record = holds.waiting(
            seen.record, on="plan", line="The plan waits", now=MOMENT
        )
        key = f"plan:{SLUG}:{clock.compact(MOMENT)}"
        choices = ("build", "drop")
    else:
        seen = task(status="building")
        stopped = Breaker(
            id=1,
            what="Change the export",
            cause="criteria",
            at=MOMENT,
            document="breaker.md",
            handoff="handoff.md",
        )
        record = breaker.tripped(
            seen.record, breaker=stopped, why="The criterion changed", now=MOMENT
        )
        key = f"breaker:{SLUG}:1:{clock.compact(MOMENT)}"
        choices = ("help", "park", "drop")
    seen = replace(seen, record=record)
    found = world(seen)
    row = next(row for row in owed.rows(found) if row.kind == topic)
    actions = acts(found, seen, row)
    assert actions and actions.answer
    assert tuple(choice.option for choice in actions.answer.choices) == choices
    assert any(
        field.name == "key" and field.shown == key for field in actions.answer.fields
    )
    assert panel(found, SLUG, "drop", opened=Opened(asked=Asked(key=key))).drop
    if topic == "breaker":
        assert panel(found, SLUG, "park", opened=Opened(asked=Asked(key=key))).park


def test_a_moved_tip_has_no_merge_offer_and_names_the_new_round() -> None:
    seen = opened(proposed=PROPOSED, pushed=TIP)
    seen = replace(seen, head=Commit(sha=NEXT, subject="Change the export"))
    found = world(seen)
    head = panel(found, SLUG, "overview").head
    assert head and (head.acts is None or head.acts.merge is None)
    step = panel(found, SLUG, "merge")
    assert step.merge is None and step.not_now
    assert f"lem land next {SLUG} names the new round" in step.not_now.said


def test_a_silent_review_has_no_clean_verdict_in_checks_or_activity() -> None:
    review = Reviewed(
        attempt=1,
        kind="read",
        tip=TIP,
        of="change",
        scope="whole",
        floor="read",
        at=MOMENT,
        silent=(Named(name="reviewer", why="timeout"),),
    )
    row = reviews.round_row(world(), review, 0)
    activity = tell_landing.review(ReviewRound(at=MOMENT, review=review))
    assert "not reviewed" in row.head and row.icon != "check"
    assert "not reviewed" in activity.text and activity.look != "done"


def test_a_green_careful_proposal_says_the_owner_merges() -> None:
    seen = opened(
        proposed=replace(PROPOSED, careful=True, who_acts="owner"), pushed=TIP
    )
    assert merge.careful(seen.record)
    step = panel(world(seen), SLUG, "merge").merge
    assert step and step.green and step.careful
    assert step.careful_why and "merged by a person" in step.careful_why


def test_activity_names_a_retry_then_the_owner_after_silent_merge_reads() -> None:
    brief = mergeread.Briefed(tip=TIP, base=BASE, base_tree=BASE, moved=False)
    first = mergeread.made(Landing(), brief, None, MOMENT)
    second = mergeread.made(Landing(reads=(first,)), brief, None, MOMENT)
    one = tell_merge.read(ReadNoted(at=MOMENT, read=first))
    two = tell_merge.read(ReadNoted(at=MOMENT, read=second))
    assert "another read" in one.text
    assert two.look == "you" and "no verdict" in two.text


class BrokenBacklog(AfternoonGit):
    """A branch with an added backlog item whose front matter does not read."""

    def __init__(self, header: bytes) -> None:
        self.header = header

    def changed_paths(self, where: Path, since: str, until: str) -> tuple[str, ...]:
        return (ITEM,)

    def show(self, where: Path, rev: str, path: str) -> bytes | None:
        return (
            b"---\n" + self.header + b"\n---\n# Keep the heading\n"
            if rev == TIP
            else None
        )

    def tip(self, where: Path, ref: str) -> str:
        return TIP


@pytest.mark.parametrize("header", (b"worth: [later", b"added: 2026-13-01"))
def test_a_malformed_branch_backlog_item_keeps_its_path_and_problem(
    tmp_path: Path,
    header: bytes,
) -> None:
    seen = task(branch="feat/gift-note")
    filed = branch.filed_of(BrokenBacklog(header), tmp_path, seen.record.task, PLACE)
    assert filed and filed[0].path == ITEM and filed[0].title == "Keep the heading"
    found = panel(world(replace(seen, filed=filed)), SLUG, "overview").overview
    assert found and found.building
    title, path = found.building.on_branch[0]
    assert path == ITEM and "not YAML" in title


def test_artifacts_shows_the_confirmed_pull_text_and_marks_the_pending_edit() -> None:
    seen = opened(
        proposed=replace(PROPOSED, text=PR_TEXT, text_waits=PR_WAIT), pushed=TIP
    )
    seen = replace(
        seen,
        files=(PR_TEXT, PR_WAIT),
        prose=((PR_TEXT, "Confirmed"), (PR_WAIT, "Pending")),
    )
    tab = artifacts(world(seen), seen)
    pull = next(section for section in tab.sections if section.key == "pr")
    assert [(doc.path, doc.title) for doc in pull.docs] == [
        (PR_TEXT, "Pull request text")
    ]
    assert tab.shown and tab.shown.path == PR_TEXT
    assert "newer text waits for GitHub" in tab.said


def test_fast_track_criterion_can_be_answered_inline() -> None:
    mark = digest.shown(OLD.encode())
    seen = awaiting(OLD, mark)
    shape = Shape(
        type="feat",
        why="Show the total",
        track="small",
        then="interview",
        someone_else=True,
    )
    seen = replace(
        seen, record=replace(seen.record, task=replace(seen.record.task, shape=shape))
    )
    found = change(world(seen), viewer=replace(VIEWER, view="waits"))
    row = Row(kind="criteria", key="criterion", task=SLUG, since=MOMENT)
    actions = acts(found, seen, row)
    assert actions and actions.criterion == OLD and actions.answer
    assert [(choice.option, choice.label) for choice in actions.answer.choices] == [
        ("yes", "Yes"),
        ("no", "No"),
    ]
    assert any(
        field.name == "digest" and field.shown == mark
        for field in actions.answer.fields
    )


def test_tasks_reads_artifact_metadata_without_preview_bodies(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from unit.board.views.afternoon import world as afternoon

    original = folder.text_of
    names: list[str] = []

    def read(where: Path, name: str) -> str | None:
        names.append(name)
        return original(where, name)

    monkeypatch.setattr(folder, "text_of", read)
    found = afternoon(tmp_path, VIEWER)
    assert any("merge-review.md" in seen.files for seen in found.tasks)
    assert names == []


def test_pruned_tabs_share_the_overview_notice(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from lem.board.views.panel import pruned
    from unit.board.views.afternoon import world as afternoon

    found = summarized(afternoon(tmp_path))
    seen = owed.seen(found, INVOICE)
    original = pruned.went
    tabs: list[str] = []

    def went(found: World, seen: Seen, tab: str) -> Went:
        tabs.append(tab)
        return original(found, seen, tab)

    monkeypatch.setattr(pruned, "went", went)
    assert criteria(found, seen).went
    assert checks(found, seen).went
    assert timeline(found, seen.record.task.slug).went
    assert tabs == ["criteria", "checks", "timeline"]
