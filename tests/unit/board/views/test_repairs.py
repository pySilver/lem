"""What a stale board page must not offer, and the facts a fresh page must show."""

from typing import TYPE_CHECKING

import pytest
from msgspec.structs import replace

from fakes.records import MOMENT
from fixtures.board.beside import write
from fixtures.board.receipt import RECEIPT
from lem.board.views import owed, telling
from lem.board.views.artifacts.tab import artifacts
from lem.board.views.ask import Ask
from lem.board.views.criteria.tab import criteria
from lem.board.views.gather import gather
from lem.board.views.panel.confirm import Asked
from lem.board.views.panel.opened import Opened
from lem.board.views.panel.panel import panel
from lem.model.landing.merge_said import ROUND
from lem.records.holds import OwnerHold, ReleaseHold
from lem.records.journal.landing import CheckWait
from lem.records.journal.merge import LandAgain
from lem.records.journal.task import SpanMark
from lem.records.landing.merge import MergeIntent
from lem.records.questions import Question
from unit.board.views.afternoon import world as afternoon
from unit.board.views.small import gone, task, world
from unit.board.views.test_artifacts_tab import opened as artifacts_opened
from unit.board.views.test_cases_merge import (
    PROPOSED,
    PULL,
    SLUG,
    TIP,
    at,
    opened,
    read,
    waits,
)
from unit.board.views.test_criteria_tab_cases import GIFT, INVOICE, with_task

if TYPE_CHECKING:
    from pathlib import Path

    from lem.board.views.world import World


def gathered(folder: Path, found: World) -> World:
    """Read the same showcase checkout after the case changes one file."""
    ask = Ask(
        viewer=found.viewer,
        clock=found.clock,
        version=found.version,
        place=found.place,
        home=folder / "home",
    )
    return gather(folder / "shop", ask)


@pytest.mark.parametrize("change", ("command", "digest", "missing-run", "files"))
def test_polish_credit_needs_current_test_evidence(tmp_path: Path, change: str) -> None:
    found = afternoon(tmp_path)
    seen = owed.seen(found, INVOICE)
    landing = seen.record.landing
    assert landing and landing.checked and landing.checked.criteria
    check = replace(landing.checked.criteria[0], taken_at=TIP)
    checked = replace(landing.checked, criteria=(check,))
    seen = replace(
        seen, record=replace(seen.record, landing=replace(landing, checked=checked))
    )
    recorded = seen.record.task.criteria
    first = recorded.criteria[0]
    test = first.tests[0]
    if change == "command":
        test = replace(test, command="sh tests/new.sh")
    if change == "files":
        test = replace(test, files=("tests/new.sh",))
    changed = replace(first, tests=(test,))
    recorded = replace(
        recorded,
        criteria=(changed,),
        digest="new-digest" if change == "digest" else recorded.digest,
        red=None if change == "missing-run" else recorded.red,
    )
    seen = with_task(seen, status="landing", criteria=recorded)
    shown = criteria(found, seen).criteria[0]
    assert shown.tests == ((test.command, "not checked yet"),)
    assert shown.label is None


@pytest.mark.parametrize("state", ("dropped", "other-hold", "new-hold"))
def test_old_plan_question_has_no_answer_or_drop_form(state: str) -> None:
    question = Question(
        id=f"plan:{SLUG}:old",
        topic="plan",
        question="Build the plan?",
        options=("build", "drop"),
        asked=MOMENT,
    )
    hold = OwnerHold(on="plan", line="The plan waits", since=MOMENT)
    status = "planned"
    if state == "dropped":
        status = "dropped"
    if state == "other-hold":
        hold = replace(hold, on="step")
    if state == "new-hold":
        hold = replace(hold, since=at(1))
    found = world(task(status=status, hold=hold, questions=(question,)))
    overview = panel(found, SLUG, "overview").overview
    assert overview and overview.now.answer is None
    drop = panel(found, SLUG, "drop", opened=Opened(asked=Asked(key=question.id)))
    assert drop.drop is None and drop.not_now is not None


def test_merge_confirm_names_the_effective_history(tmp_path: Path) -> None:
    found = afternoon(tmp_path)
    path = tmp_path / "shop" / ".lem" / "settings.toml"
    for history, expected in (
        ("squash", "one commit:"),
        ("keep", "the branch’s own commits"),
    ):
        write(path, f'[branch]\nbase = "main"\nhistory = "{history}"\n')
        merge = panel(gathered(tmp_path, found), RECEIPT.task.slug, "merge").merge
        assert merge and merge.confirm.form
        method = next(fact.text for fact in merge.facts if fact.key == "as")
        assert method and method.startswith(expected)


def test_lost_merge_reply_leaves_only_the_github_check() -> None:
    intent = MergeIntent(tip=TIP, by="owner", via="board", at=MOMENT)
    seen = opened(proposed=PROPOSED, reads=(read("call"),), intent=intent)
    found = world(seen)
    (row,) = waits(seen)
    assert row.verb == "Check the pull request on GitHub"
    assert row.acts is None
    assert row.where and PULL.url in row.where
    assert "still open" in row.where
    overview = panel(found, SLUG, "overview")
    assert overview.head and overview.head.acts is None
    assert overview.overview and overview.overview.now.where
    assert overview.overview.now.head == "Check the pull request on GitHub"
    assert PULL.url in overview.overview.now.where
    confirm = panel(found, SLUG, "merge")
    assert confirm.merge is None
    assert confirm.not_now and PULL.url in confirm.not_now.said


def test_merge_review_card_says_another_round() -> None:
    seen = opened(proposed=PROPOSED, reads=(read("call", base_call=ROUND),))
    seen = replace(seen, prose=(("merge-review.md", "The base needs more checks."),))
    overview = panel(world(seen), SLUG, "overview").overview
    assert overview and overview.review and "another round" in overview.review.head


@pytest.mark.parametrize("ends", ("checks-start", "new-round"))
def test_checks_wait_ends_at_its_start_or_a_new_round(ends: str) -> None:
    seen = task(status="landing")
    waited = CheckWait(at=MOMENT, reason="behind", behind="receipt")
    boundary = (
        SpanMark(at=MOMENT, name="checks", edge="start")
        if ends == "checks-start"
        else LandAgain(at=MOMENT, round=2, relands=1)
    )
    record = replace(seen.record, journal=(waited, boundary))
    assert telling.waiting(record) is None
    assert telling.waiting(replace(record, journal=(waited, boundary, waited)))


@pytest.mark.parametrize("filename", ("review.out", "script.py", "plan"))
def test_artifacts_preview_the_file_from_its_own_folder(
    tmp_path: Path, filename: str
) -> None:
    found = afternoon(tmp_path)
    slug = RECEIPT.task.slug
    checkout = tmp_path / "shop"
    plan = RECEIPT.task.plan
    assert plan
    worktree = checkout / ".lem" / "worktrees" / slug
    if filename == "plan":
        filename = plan.path
        write(worktree / ".git", "gitdir: elsewhere\n")
        write(worktree / filename, "# The worktree plan\n")
        write(checkout / filename, "# The plan in the main checkout\n")
    else:
        write(checkout / ".lem" / "state" / "tasks" / slug / filename, "One line\n")
    found = artifacts_opened(gathered(tmp_path, found), filename)
    shown = artifacts(found, owed.seen(found, slug))
    assert shown and shown.chosen and shown.shown
    body = shown.shown.body
    if filename == plan.path:
        assert body.document and body.document.text == "# The worktree plan\n"
    elif filename == "script.py":
        assert body.text == "One line\n"
    else:
        assert body.lines == ("One line",)


def test_session_offer_checks_every_prerequisite() -> None:
    queued = task(status="queued", after=("receipt", "coupon"))
    queued = replace(queued, session=gone())
    receipt = task("receipt", status="landed")
    for status in ("open", "dropped", "answered"):
        coupon = task("coupon", status=status)
        head = panel(world(queued, receipt, coupon), SLUG, "overview").head
        assert head
        offered = head.acts is not None and head.acts.session is not None
        assert offered == (status == "answered"), status


def test_release_stop_suspends_a_breaker(tmp_path: Path) -> None:
    found = afternoon(tmp_path)
    seen = owed.seen(found, GIFT)
    hold = ReleaseHold(began="v1", running="v3", say="Old release", since=MOMENT)
    row = criteria(found, with_task(seen, hold=hold)).decisions[0]
    assert row.look == "quiet"
    assert "release" in row.who
    assert all(part.label != "Where you answer" for part in row.parts)


def test_dropped_status_takes_priority_over_a_retained_release_stop() -> None:
    hold = ReleaseHold(began="v1", running="v3", say="Old release", since=MOMENT)
    seen = task(status="dropped", hold=hold)
    overview = panel(world(seen), SLUG, "overview").overview
    assert overview and overview.now.head == "Dropped"
