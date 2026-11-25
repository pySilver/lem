"""`lem issue`: each step on a task's issue and each refusal, on a workspace whose tracker is
GitHub's, over the in-memory issues of `issues_world.py`. What gh is asked, and the commands
themselves, are `tests/contract/test_tracker.py`'s."""

from typing import TYPE_CHECKING

import msgspec
import pytest

from fakes.records import MOMENT
from lem.adapters.tracker_gh_facts import Comment
from lem.app.tasks.issues import ends, land, reading, start
from lem.kernel.envelope import Envelope
from lem.kernel.errors import Refusal
from lem.model.task import tickets
from lem.records.holds import Parked
from lem.records.landing.propose import Proposed
from lem.records.landing.record import Landing, Pull
from lem.records.work import Investigation
from lem.store import tasks
from unit.task.issues_world import (
    REPO,
    SLUG,
    World,
    gift_note,
    world,
)
from unit.task.spaces import read

if TYPE_CHECKING:
    from pathlib import Path

TIP = "c" * 40
BASE = "a" * 40
LINEAR = '[branch]\nbase = "main"\n[tracker]\nkind = "linear"\n'


def said(outcome: object) -> tuple[dict[str, object], str | None]:
    """A step's result as JSON reads it, and its line for the owner."""
    if isinstance(outcome, Envelope):
        found = msgspec.json.decode(outcome.outcome or b"{}")
        return found, outcome.say
    return msgspec.json.decode(msgspec.json.encode(outcome)), None


def started(w: World, slug: str = SLUG) -> tuple[dict[str, object], str | None]:
    return said(start.start(w.ports, w.where, slug))


def ended(
    w: World, step: str, slug: str = SLUG
) -> tuple[dict[str, object], str | None]:
    if step == "land":
        return said(land.land(w.ports, w.where, slug))
    return said(
        ends.ended(w.ports, w.where, slug, "drop" if step == "drop" else "answer")
    )


def refused(call: object) -> Refusal:
    assert callable(call)
    with pytest.raises(Refusal) as caught:
        call()
    return caught.value


# Read


@pytest.mark.parametrize(
    "given",
    [
        "42",
        "#42",
        "https://github.com/acme/shop/issues/42",
        "https://github.com/ACME/shop/issues/42#issuecomment-5",
    ],
)
def test_an_issue_reads_by_number_and_address_with_its_comments_apart_and_writes_nothing(
    tmp_path: Path, given: str
) -> None:
    w = world(tmp_path)
    found = msgspec.json.decode(
        msgspec.json.encode(reading.read(w.ports, w.where, given))
    )
    assert (found["id"], found["repository"], found["url"]) == (
        "#42",
        REPO,
        "https://github.com/acme/shop/issues/42",
    )
    assert (found["title"], found["text"], found["state"], found["labels"]) == (
        "The export drops the gift note",
        "Each export drops the gift note.\n\nSee order 7.",
        "open",
        ["bug"],
    )
    assert found["author"] == "ann"
    assert [(c["author"], c["text"]) for c in found["comments"]] == [
        ("bob", "Same here, on order 9.")
    ]
    # only the text is the ask, never a comment; and what `lem task open` takes
    assert (found["ask"], found["ask_is"]) == (
        "Each export drops the gift note.\n\nSee order 7.",
        "text",
    )
    assert found["task_open"] == ["--ticket", "#42", "--ticket-repo", REPO]
    assert w.fake.writes() == []
    assert all(REPO in call for call in w.fake.calls)


def test_an_issue_with_no_text_has_its_title_as_the_ask_and_a_closed_one_says_so(
    tmp_path: Path,
) -> None:
    w = world(tmp_path)
    w.fake.issues[42] = gift_note(body="", state="closed", state_reason="completed")
    found = msgspec.json.decode(
        msgspec.json.encode(reading.read(w.ports, w.where, "42"))
    )
    assert (found["ask"], found["ask_is"], found["state"], found["state_reason"]) == (
        "The export drops the gift note",
        "title",
        "closed",
        "completed",
    )


def test_the_address_of_another_repository_is_refused_with_origin_named_before_gh_is_asked(
    tmp_path: Path,
) -> None:
    w = world(tmp_path)
    refusal = refused(
        lambda: reading.read(
            w.ports, w.where, "https://github.com/upstream/shop/issues/42"
        )
    )
    assert (
        "names an issue of upstream/shop, and Lem reads the issues of origin, which is "
        "acme/shop" in refusal.why
    )
    assert w.fake.calls == []


def test_an_issue_moved_to_another_repository_is_refused(tmp_path: Path) -> None:
    w = world(tmp_path)
    w.fake.issues[42] = gift_note(url="https://github.com/other/place/issues/3")
    refusal = refused(lambda: reading.read(w.ports, w.where, "42"))
    assert (
        "an issue of another repository, and Lem reads the issues of origin, which is "
        "acme/shop" in refusal.why
    )


def test_the_number_of_a_pull_request_is_refused(tmp_path: Path) -> None:
    w = world(tmp_path)
    w.fake.issues[42] = gift_note(url="https://github.com/acme/shop/pull/42")
    refusal = refused(lambda: reading.read(w.ports, w.where, "42"))
    assert (
        "#42 of acme/shop is a pull request (https://github.com/acme/shop/pull/42), not "
        "an issue" in refusal.why
    )


def test_a_word_that_is_no_issue_issue_zero_and_another_tracker_are_refused(
    tmp_path: Path,
) -> None:
    w = world(tmp_path)
    assert "is no issue's number or address" in (
        refused(lambda: reading.read(w.ports, w.where, "MBZ-12")).why
    )
    assert "issue 0 is no issue" in (
        refused(lambda: reading.read(w.ports, w.where, "#0")).why
    )
    linear = world(tmp_path / "linear", LINEAR)
    refusal = refused(lambda: reading.read(linear.ports, linear.where, "42"))
    assert "the project's tracker is linear" in refusal.why
    assert "lem-linear" in refusal.fix
    assert w.fake.calls == []


# Start


def test_an_issue_with_no_assignee_gets_the_person_signed_in_and_a_second_start_writes_nothing(
    tmp_path: Path,
) -> None:
    w = world(tmp_path)
    w.task("building")
    found, say = started(w)
    assert w.issue().assignees == ("octo-cat",)
    assert w.steps() == ["assigned octo-cat", "started"]
    assert (found["did"], found["wrote"], say) == (
        ["added the assignee octo-cat"],
        ["assigned octo-cat", "started"],
        None,
    )
    calls = len(w.fake.calls)
    again, _ = started(w)
    assert (again["did"], again["wrote"]) == ([], [])
    assert len(w.fake.calls) == calls


def test_an_issue_with_another_assignee_keeps_it_and_the_owner_is_told_who(
    tmp_path: Path,
) -> None:
    w = world(tmp_path)
    w.fake.issues[42] = gift_note(assignees=("dana",))
    w.task("planned")
    _, say = started(w)
    assert w.issue().assignees == ("dana",)
    assert say == (
        "issue #42 of acme/shop is assigned to dana: Lem added nobody, and the build goes on"
    )
    assert w.steps() == ["started"]
    assert w.fake.writes() == []


def test_an_issue_the_person_signed_in_holds_already_is_left_with_no_line(
    tmp_path: Path,
) -> None:
    w = world(tmp_path)
    w.fake.issues[42] = gift_note(assignees=("Octo-Cat",))
    w.task("building")
    _, say = started(w)
    assert (say, w.steps(), w.fake.writes()) == (None, ["started"], [])


def test_when_gh_cannot_assign_the_owner_is_told_why_and_the_step_is_undone(
    tmp_path: Path,
) -> None:
    w = world(tmp_path)
    w.fake.refuse_add = (
        "GraphQL: octo-cat cannot be assigned to this issue (addAssigneesToAssignable)"
    )
    w.task("building")
    _, say = started(w)
    assert say is not None
    assert (
        "gh could not make octo-cat the assignee of issue #42 of acme/shop (GraphQL: "
        "octo-cat cannot be assigned" in say
    )
    assert w.steps() == ["assigned octo-cat", "unassigned", "started"]


def test_a_start_cut_off_after_its_record_adds_the_login_only_while_the_issue_has_nobody(
    tmp_path: Path,
) -> None:
    w = world(tmp_path)
    w.task("building", steps=("assigned octo-cat",))
    started(w)
    assert w.issue().assignees == ("octo-cat",)
    w.fake.issues[43] = gift_note(
        number=43, url=f"https://github.com/{REPO}/issues/43", assignees=("dana",)
    )
    w.task("building", "gift-note-two", ticket="#43", steps=("assigned octo-cat",))
    started(w, "gift-note-two")
    assert w.issue(43).assignees == ("dana",)


def test_gh_signed_out_is_refused_with_the_fix_and_nothing_is_written(
    tmp_path: Path,
) -> None:
    w = world(tmp_path)
    w.fake.login = None
    w.task("building")
    refusal = refused(lambda: start.start(w.ports, w.where, SLUG))
    assert "gh auth login" in refusal.fix
    assert w.steps() == []


def test_a_resumed_task_takes_over_the_assignee_its_dropped_task_added(
    tmp_path: Path,
) -> None:
    w = world(tmp_path)
    w.task("dropped", "gift-note", steps=("assigned octo-cat", "started"))
    w.task("building", "gift-note-2", resumed_from="gift-note")
    w.fake.issues[42] = gift_note(assignees=("octo-cat",))
    found, _ = started(w, "gift-note-2")
    assert (found["wrote"], w.fake.writes()) == (["assigned octo-cat", "started"], [])


# The guards of every step


def test_each_step_refuses_a_status_it_does_not_belong_to(tmp_path: Path) -> None:
    w = world(tmp_path)
    w.task("building")
    for step, wants in (
        ("land", "landed"),
        ("drop", "dropped"),
        ("answer", "answered"),
    ):
        refusal = refused(lambda step=step: ended(w, step))
        assert (
            f"is building, and `lem issue {step}` belongs to a task that is {wants}"
            in refusal.why
        )
    for status in ("landed", "dropped", "answered"):
        w.task(status, f"gift-note-{status}")
        refusal = refused(lambda status=status: started(w, f"gift-note-{status}"))
        assert f"is {status}: the start belongs to a task whose build starts" in (
            refusal.why
        )
    w.task("building", "gift-note-parked", hold=Parked(since=MOMENT))
    refusal = refused(lambda: started(w, "gift-note-parked"))
    assert "is parked: the start belongs to a task whose build starts" in refusal.why
    assert w.fake.calls == []


def test_another_repository_in_origin_is_refused_with_both_named_and_the_fix(
    tmp_path: Path,
) -> None:
    w = world(tmp_path)
    w.task("dropped", steps=("assigned octo-cat", "started"))
    w.fake.repo = "acme/fork"
    refusal = refused(lambda: ended(w, "drop"))
    assert (
        f"origin names acme/fork, and the task {SLUG} came from issue #42 of acme/shop"
        in refusal.why
    )
    assert "git remote set-url origin https://github.com/acme/shop.git" in refusal.fix
    assert "the owner writes to issue #42 of acme/shop by hand" in refusal.fix
    assert w.fake.calls == []


def test_a_task_a_resume_went_on_from_owes_nothing_and_each_write_names_the_holder(
    tmp_path: Path,
) -> None:
    w = world(tmp_path)
    w.task("dropped", "gift-note", steps=("assigned octo-cat", "started"))
    w.task("building", "gift-note-2", resumed_from="gift-note")
    refusal = refused(lambda: ended(w, "drop", "gift-note"))
    assert (
        "issue #42 is held by the task gift-note-2 now, which went on from gift-note"
        in refusal.why
    )
    assert "lem issue STEP gift-note-2" in refusal.fix
    assert w.fake.calls == []


def test_a_task_of_no_issue_and_a_task_that_is_not_there_are_refused(
    tmp_path: Path,
) -> None:
    w = world(tmp_path)
    assert refused(lambda: started(w, "gone")).code == "no-task"
    w.task("building", "from-words")
    record = read(w.where, "from-words")
    tasks.update(
        w.where.state,
        "from-words",
        lambda before: msgspec.structs.replace(
            before, task=msgspec.structs.replace(before.task, ticket=None)
        ),
        record.revision,
    )
    assert "came from no ticket" in refused(lambda: started(w, "from-words")).why


def test_a_task_two_releases_back_stops_its_start_and_its_end_goes_on(
    tmp_path: Path,
) -> None:
    w = world(tmp_path)
    w.task("building", "gift-note-old")
    w.task("dropped", steps=("started",))
    for slug in ("gift-note-old", SLUG):
        record = read(w.where, slug)
        path = w.where.state / "tasks" / slug / "task.json"
        old = msgspec.structs.replace(record, release="0.1.0")
        path.write_bytes(msgspec.json.encode(old))
    assert refused(lambda: started(w, "gift-note-old")).code == "release"
    ended(w, "drop")
    assert w.steps()[-1] == "dropped"


# Land


def landed(w: World, *, green: bool = True, steps: tuple[str, ...] = ()) -> None:
    pull = Pull(number=57, url="https://github.com/acme/shop/pull/57", title="Gift")
    proposed = Proposed(tip=TIP, base=BASE, green=green, who_acts="owner", at=MOMENT)
    landing = Landing(phase="ended", pull=pull, proposed=proposed)
    w.task(
        "landed",
        line="main a1b2..c3d4",
        steps=steps or ("assigned octo-cat", "started"),
    )
    record = read(w.where, SLUG)
    path = w.where.state / "tasks" / SLUG / "task.json"
    path.write_bytes(
        msgspec.json.encode(msgspec.structs.replace(record, landing=landing))
    )


def test_the_landing_comments_what_changed_the_pull_request_and_green_then_closes(
    tmp_path: Path,
) -> None:
    w = world(tmp_path)
    landed(w)
    w.fake.issues[42] = gift_note(assignees=("octo-cat",))
    found, _ = ended(w, "land")
    assert w.thread()[-1] == (
        "Lem landed the work of this issue: The export keeps the gift note of each "
        "order, as the shop shows it.\n\n"
        "The pull request: https://github.com/acme/shop/pull/57, green when it was "
        f"proposed.\n\nlem: {SLUG} landed\n"
    )
    assert (w.issue().state, w.issue().state_reason) == ("closed", "completed")
    assert w.steps() == ["assigned octo-cat", "started", "commented", "landed"]
    assert found["did"] == ["posted the comment", "closed the issue as completed"]
    calls = len(w.fake.calls)
    assert ended(w, "land")[0]["did"] == []
    assert len(w.fake.calls) == calls
    # the landed task's issue keeps the assignee Lem added
    assert w.issue().assignees == ("octo-cat",)
    task = read(w.where, SLUG).task
    assert tickets.owed(task, None) == ()


def test_not_green_is_said_and_a_closed_issue_stays_as_it_is(tmp_path: Path) -> None:
    w = world(tmp_path)
    landed(w, green=False)
    w.fake.issues[42] = gift_note(state="closed", state_reason="not_planned")
    ended(w, "land")
    assert "pull/57, not green when it was proposed." in w.thread()[-1]
    assert w.issue().state_reason == "not_planned"
    assert not [call for call in w.fake.calls if call[0] == "close"]


def test_a_landing_cut_off_after_the_comment_posts_no_second_one_and_goes_on_to_the_close(
    tmp_path: Path,
) -> None:
    w = world(tmp_path)
    landed(w)
    w.fake.threads[42] = [
        Comment(author="bob", text="one"),
        Comment(author="carl", text="two"),
        Comment(
            author="octo-cat",
            text=f"Lem landed the work of this issue: x.\n\nlem: {SLUG} landed\n",
        ),
    ]
    found, _ = ended(w, "land")
    assert len(w.thread()) == 3
    assert found["did"] == ["closed the issue as completed"]
    assert w.steps()[-2:] == ["commented", "landed"]


def test_a_comment_of_another_task_does_not_count(tmp_path: Path) -> None:
    w = world(tmp_path)
    landed(w)
    w.fake.threads[42] = [Comment(author="octo-cat", text="lem: gift-note-old dropped")]
    ended(w, "land")
    assert len(w.thread()) == 2


def test_a_landing_with_no_pull_request_on_record_says_the_state(
    tmp_path: Path,
) -> None:
    w = world(tmp_path)
    w.task("landed", line="landed on main by hand", steps=("started",))
    ended(w, "land")
    assert (
        "No pull request is on record; the task's state says: landed on main by hand."
        in w.thread()[-1]
    )


# Drop and answer


def test_a_drop_comments_why_removes_the_assignee_lem_added_and_keeps_the_others(
    tmp_path: Path,
) -> None:
    w = world(tmp_path)
    w.task(
        "dropped",
        line="the owner dropped it: the shop drops gift notes",
        steps=("assigned octo-cat", "started"),
    )
    w.fake.issues[42] = gift_note(assignees=("octo-cat", "dana"))
    _, say = ended(w, "drop")
    assert w.thread()[-1] == (
        "Lem dropped its task for this issue: the owner dropped it: the shop drops gift "
        f"notes.\n\nlem: {SLUG} dropped\n"
    )
    assert (w.issue().assignees, w.issue().state) == (("dana",), "open")
    assert (
        say
        == "issue #42 of acme/shop stays open: whether it closes is the owner's call"
    )
    assert w.steps()[-2:] == ["dropped", "unassigned"]
    assert tickets.owed(read(w.where, SLUG).task, None) == ()
    assert ended(w, "drop")[0]["did"] == []


def test_the_login_the_record_names_goes_whoever_is_signed_in_now(
    tmp_path: Path,
) -> None:
    w = world(tmp_path)
    w.task(
        "dropped", line="the owner dropped it", steps=("assigned octo-cat", "started")
    )
    w.fake.issues[42] = gift_note(assignees=("octo-cat",))
    w.fake.login = "someone-else"
    ended(w, "drop")
    assert w.issue().assignees == ()


def test_an_assignee_lem_never_added_stays_and_a_removed_one_is_written_down_all_the_same(
    tmp_path: Path,
) -> None:
    w = world(tmp_path)
    w.task("dropped", line="the owner dropped it", steps=("started",))
    w.fake.issues[42] = gift_note(assignees=("octo-cat",))
    ended(w, "drop")
    assert w.issue().assignees == ("octo-cat",)
    w.fake.issues[43] = gift_note(number=43, url=f"https://github.com/{REPO}/issues/43")
    w.task(
        "dropped",
        "gift-note-two",
        ticket="#43",
        line="x",
        steps=("assigned octo-cat", "started"),
    )
    ended(w, "drop", "gift-note-two")
    assert w.steps("gift-note-two")[-1] == "unassigned"
    assert not [call for call in w.fake.calls if call[0] == "unassign"]


def answered(w: World, *, report: bool) -> None:
    found = Investigation(
        kind="fix",
        call="not-a-bug",
        line="the export keeps the note in its last column",
        where="export.py:rows",
        report="investigation.md" if report else None,
    )
    w.task(
        "answered",
        line="not a bug: the export keeps the note",
        steps=("assigned octo-cat", "started"),
        investigation=found,
    )
    if report:
        folder = w.where.state / "tasks" / SLUG
        (folder / "investigation.md").write_text("# Investigation\n", encoding="utf-8")
    w.fake.issues[42] = gift_note(assignees=("octo-cat",))


def test_an_answer_comments_the_answer_and_where_and_the_report_stays_home(
    tmp_path: Path,
) -> None:
    w = world(tmp_path)
    answered(w, report=True)
    _, say = ended(w, "answer")
    assert w.thread()[-1] == (
        "Lem's investigation answered this issue: the export keeps the note in its last "
        "column (export.py:rows).\n\n"
        "The report is in the task's directory on the owner's machine, not on this "
        f"issue.\n\nlem: {SLUG} answered\n"
    )
    assert (w.issue().assignees, w.issue().state) == ((), "open")
    assert say is not None
    assert "stays open" in say


def test_an_answer_owed_after_the_prune_removed_the_report_names_no_report(
    tmp_path: Path,
) -> None:
    w = world(tmp_path)
    answered(w, report=False)
    ended(w, "answer")
    assert w.thread()[-1] == (
        "Lem's investigation answered this issue: the export keeps the note in its last "
        f"column (export.py:rows).\n\nlem: {SLUG} answered\n"
    )


def test_a_drop_cut_off_after_the_comment_posts_none_and_removes_the_assignee(
    tmp_path: Path,
) -> None:
    w = world(tmp_path)
    w.task(
        "dropped", line="the owner dropped it", steps=("assigned octo-cat", "started")
    )
    w.fake.issues[42] = gift_note(assignees=("octo-cat",))
    w.fake.threads[42] = [
        Comment(author="octo-cat", text=f"Lem dropped ...\n\nlem: {SLUG} dropped")
    ]
    found, _ = ended(w, "drop")
    assert (len(w.thread()), w.issue().assignees) == (1, ())
    assert found["did"] == ["removed the assignee octo-cat"]


def test_a_closed_issue_at_a_drop_is_said_to_be_closed_by_someone_else(
    tmp_path: Path,
) -> None:
    w = world(tmp_path)
    w.task("dropped", line="the owner dropped it", steps=("started",))
    w.fake.issues[42] = gift_note(state="closed")
    _, say = ended(w, "drop")
    assert say == "issue #42 of acme/shop is closed already, by someone else than Lem"
