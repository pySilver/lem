"""Where the owner answers each row of what waits for him (`main`'s `board_model.wait_say`, its
`where`, and `answer_of`)."""

from typing import TYPE_CHECKING

import msgspec

from fakes.records import MOMENT, record
from fixtures.board import waiting
from lem.board.views import owed
from lem.board.views.panel.answer import answer
from lem.board.views.where import where
from lem.board.views.world import Seen
from lem.model.owner.looks import Row
from lem.records.holds import Blocked, OwnerHold
from lem.records.landing.merge import Refused
from lem.records.landing.propose import Proposed
from lem.records.landing.record import Landing
from unit.board.views.afternoon import world

if TYPE_CHECKING:
    from pathlib import Path

    from lem.model.owner.looks import Kind

TIP = "a" * 40


def row(kind: Kind, slug: str = "fix-the-login", **facts: object) -> Row:
    """A row of `kind` of the task `slug`."""
    made = Row(kind=kind, key=f"{kind}:{slug}", task=slug, since=MOMENT)
    return msgspec.structs.replace(made, **facts)


def test_each_row_of_the_afternoon_says_where_the_owner_answers(
    tmp_path: Path,
) -> None:
    afternoon = world(tmp_path)
    said = [where(owed.seen(afternoon, one.task), one) for one in owed.rows(afternoon)]
    assert said == [
        waiting.BREAKER.where,
        waiting.NO_SESSION.where,
        waiting.ASKED.where,
        waiting.CRITERIA.where,
        waiting.REVIEW.where,
        waiting.MERGE.where,
    ]


def refused(source: str) -> Seen:
    """An open task whose merge of the proposed tip `source` refused."""
    landing = Landing(
        phase="open",
        proposed=Proposed(tip=TIP, base=TIP, green=True, who_acts="owner", at=MOMENT),
        refused=Refused(
            tip=TIP,
            source="lem" if source == "lem" else "github",
            kind="rule",
            line="Required status check is expected",
            by="merger",
            at=MOMENT,
        ),
    )
    made = msgspec.structs.replace(record(status="open"), landing=landing)
    return Seen(record=made)


def test_a_merge_github_refused_says_its_line() -> None:
    """`main`'s `test_board_model.py` Merge.test_a_merge_github_refused_says_its_line: the
    row of a merge GitHub refused says GitHub's line, and Lem's refusal says Lem's."""
    github = where(refused("github"), row("merge"))
    assert github.startswith("GitHub said: Required status check is expected.")
    lem = where(refused("lem"), row("merge"))
    assert lem.startswith("Lem said: Required status check is expected.")
    conflict = where(Seen(record=record(status="open")), row("merge", conflict=True))
    assert conflict.startswith("Nothing to do now")


def test_a_session_the_task_lacks_or_one_that_stopped_says_what_a_fresh_one_does() -> (
    None
):
    seen = Seen(record=record(status="building"))
    assert where(seen, row("session")).endswith("goes on from there.")
    assert where(seen, row("session", deaf=True)).startswith("A wake-up has waited")
    dropped = Seen(record=record(status="dropped"))
    assert "the branch keeps its commits" in where(dropped, row("session"))
    assert "after 45 minutes" in where(seen, row("stopped", unread=True))
    assert "already stopped once" in where(seen, row("stopped", restarted=False))
    assert "neither did the fresh session" in where(seen, row("stopped"))


def test_a_review_row_drops_the_verdict_the_row_says_already() -> None:
    seen = Seen(record=record(status="open"))
    said = where(seen, row("review", why="Verdict: call. it is careful"))
    assert said.endswith("Overview. It is careful.")
    bare = where(seen, row("review"))
    assert bare.endswith("Overview. The merge agent calls you.")


def test_a_task_after_a_dropped_one_a_block_and_a_wait_say_where_each_is_answered() -> (
    None
):
    queued = Seen(record=record(status="queued"))
    assert "in any Lem session" in where(queued, row("after_dropped", after="old-task"))
    block = Blocked(why="the seat failed", fix="lem doctor", since=MOMENT)
    blocked = Seen(record=record(status="building", hold=block))
    assert "“the seat failed”" in where(blocked, row("blocked"))
    hold = OwnerHold(on="skip-read", line="skip?", since=MOMENT)
    skip = Seen(record=record(status="shaping", hold=hold))
    assert where(skip, row("held")).startswith("Lem asks whether to skip")
    asking = msgspec.structs.replace(hold, on="interview")
    interview = Seen(record=record(status="shaping", hold=asking))
    assert answer(interview.record.task).startswith("The interview runs")


def test_a_plan_and_a_held_step_are_answered_in_the_session_or_on_the_board() -> None:
    plan = OwnerHold(on="plan", line="the plan waits", since=MOMENT)
    planned = Seen(record=record(status="planned", hold=plan))
    assert answer(planned.record.task).startswith("Read the plan")
    step = OwnerHold(on="fact", line="which date counts", since=MOMENT)
    held = Seen(record=record(status="building", hold=step))
    assert answer(held.record.task) == (
        "It waits on what its state says: “which date counts”. "
        "The task’s session says what to do."
    )
