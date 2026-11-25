"""The rules of `main`'s `tests/unit/test_board_model.py` that the rebuild holds in the list of what
waits for the owner and in where a task stands, case by case (`AfterDropped`, `Blocked`, `Cards`,
`InterviewRead`, `InterviewTurns`, `NewTask`, `Sessions`, `Summary`): each test names the old case
it stands for."""

from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING, NamedTuple

from msgspec.structs import replace

from fakes.records import MOMENT
from lem.board.views import owed, standing, tasks, telling
from lem.board.views.frame import counted
from lem.board.views.panel import heads, now, opening
from lem.board.views.panel import waiting as panel_waiting
from lem.board.views.panel.answer import answer
from lem.board.views.waits import view as waits_view
from lem.board.views.where import where
from lem.model.owner import verbs, waiting
from lem.model.owner.looks import Look
from lem.records.approvals import PersonaRead, Silent
from lem.records.criteria import Criteria
from lem.records.holds import Blocked, BreakerHold, OwnerHold
from lem.records.journal.task import StateNoted, Summary
from lem.records.questions import Question
from lem.records.work import Span
from unit.board.views.small import NOW, gone, task, world

if TYPE_CHECKING:
    from lem.board.inputs.task.now import Now
    from lem.board.views.panel.waiting import Waiting
    from lem.board.views.standing import Standing
    from lem.board.views.world import Seen, World
    from lem.model.owner.looks import Rows

GIFT = "gift-note-in-export"
ORDER = "export-notes-in-order"
INTERVIEW = "the interview waits for the owner"
ASKING = OwnerHold(on="interview", line=INTERVIEW, since=MOMENT)


def at(minutes: float) -> datetime:
    """A moment `minutes` after the records' moment."""
    return MOMENT + timedelta(minutes=minutes)


class Told(NamedTuple):
    """What the board says of one task: its rows, where it stands, its card's line, its large
    card, and what it waits for."""

    rows: Rows
    standing: Standing
    line: str
    now: Now
    waits: Waiting | None


def told(seen: World, slug: str) -> Told:
    """What the board of `seen` says of the task `slug`."""
    found = owed.seen(seen, slug)
    rows = owed.of_task(seen, slug)
    where_it_stands = standing.standing(found, rows)
    title = tasks.TITLES[where_it_stands.column]
    return Told(
        rows=rows,
        standing=where_it_stands,
        line=telling.line(found.record, where_it_stands, title),
        now=now.now(seen, found, rows, where_it_stands),
        waits=panel_waiting.waits_for(found, rows),
    )


def keys(rows: Rows) -> list[tuple[str, str]]:
    """Each row's kind and key."""
    return [(row.kind, row.key) for row in rows]


def queued_after(**fields: object) -> Seen:
    """The task queued after `gift-note-in-export`, with no session on record."""
    named: dict[str, object] = {"status": "queued", "after": (GIFT,)} | fields
    made = task(ORDER, None, **named)
    return replace(made, session=None)


def test_a_need_after_a_dropped_task_gets_the_same_row() -> None:
    """`main`'s AfterDropped.test_a_need_gets_the_same_row: a task that waits for another's
    result (`after` with no order of his) is the same row with his two words."""
    seen = world(task(GIFT, status="dropped", since=at(30)), queued_after())
    rows = owed.rows(seen)
    assert keys(rows) == [("after_dropped", f"after_dropped:{ORDER}")]
    said = where(owed.seen(seen, ORDER), rows[0])
    assert f"Type “start {ORDER} now”" in said
    assert f"or /lem drop {ORDER} to end it" in said


def test_a_breaker_with_no_session_says_first_to_open_one_then_where_its_task_is_answered() -> (
    None
):
    """`main`'s AfterDropped.test_a_row_of_another_kind_leaves_where_he_answers_to_the_task_
    state: the session's row does not take the breaker's words away, and says first that a
    session is to be opened."""
    stopped = task(status="building", hold=BreakerHold(number=1, since=MOMENT))
    seen = world(replace(stopped, session=gone()))
    shown = told(seen, "gift-note")
    assert [row.kind for row in shown.rows] == ["session", "breaker"]
    found = owed.seen(seen, "gift-note")
    assert shown.waits is not None
    assert (
        shown.waits.where
        == f"{where(found, shown.rows[0])} {answer(found.record.task)}"
    )
    assert "/lem park gift-note" in shown.waits.where


def test_no_row_behind_a_task_that_runs_or_ended_with_its_result() -> None:
    """`main`'s AfterDropped.test_no_row_behind_a_task_that_runs_or_ended_with_its_result."""
    for status in ("building", "landed", "answered"):
        seen = world(task(GIFT, status=status), queued_after())
        assert owed.of_task(seen, ORDER) == (), status


def test_the_row_after_a_dropped_task_is_gone_after_his_word() -> None:
    """`main`'s AfterDropped.test_the_row_is_gone_after_his_word: his "start it" (the task
    queued with no task before it, or building), or his drop."""
    dropped = task(GIFT, status="dropped", since=at(30))
    for word in (
        queued_after(after=()),
        queued_after(status="building"),
        queued_after(status="dropped", since=at(40)),
    ):
        seen = world(dropped, word)
        kinds = [row.kind for row in owed.of_task(seen, ORDER)]
        assert "after_dropped" not in kinds, word.record.task.status


def test_a_task_after_a_dropped_one_waits_for_him_on_every_view_but_one_behind_a_running_task() -> (
    None
):
    """`main`'s AfterDropped.test_the_task_waits_for_him_on_every_view_of_the_board and the
    rest of AfterDropped.test_a_task_queued_after_a_dropped_task_is_one_row_with_his_two_words:
    the row's facts and words, the kanban's column, the count, the large card's eyebrow, head
    and where he answers; behind a task that still runs, Lem holds it."""
    seen = world(task(GIFT, status="dropped", since=at(30)), queued_after())
    shown = told(seen, ORDER)
    (row,) = shown.rows
    assert (row.kind, row.after, row.since) == ("after_dropped", GIFT, at(30))
    verb = verbs.verb(row, owed.seen(seen, ORDER).record.task, None)
    assert verb == f"{GIFT} was dropped: your word starts or ends this task"
    said = where(owed.seen(seen, ORDER), row)
    assert said == (
        f"It waited for {GIFT}, which was dropped, so the result it waited for never "
        f"came. Type “start {ORDER} now” to start it without that result, or /lem drop "
        f"{ORDER} to end it, in any Lem session of this repository."
    )
    assert shown.standing.column == "you"
    assert [stack[0].task for stack in counted.counted(seen).stacks] == [ORDER]
    assert (shown.now.who, shown.now.head, shown.now.where) == ("You act", verb, said)
    assert shown.waits is not None
    assert shown.waits.where == said
    runs = told(world(task(GIFT, status="building"), queued_after()), ORDER)
    assert (runs.standing.column, runs.now.who, runs.now.head) == (
        "build",
        "Lem acts",
        "Waits for another task",
    )


def test_a_blocked_task_is_a_row_of_his_with_its_line_and_a_block_on_the_base_is_none() -> (
    None
):
    """`main`'s Blocked.test_a_blocked_task_is_a_row_of_his_with_its_own_line_and_the_base_
    red_is_none, changed: a block on the base is a hold over the landing, which keeps the
    column of its status (the checks), where `main` put it among the builds."""
    why = "a builder ended two times with no report"
    hold = Blocked(why=why, fix="tell it what to do", since=at(5))
    seen = world(task(status="building", hold=hold))
    shown = told(seen, "gift-note")
    assert keys(shown.rows) == [("blocked", "blocked:gift-note")]
    found = owed.seen(seen, "gift-note")
    assert verbs.verb(shown.rows[0], found.record.task, None) == (
        "Its session stopped: tell it what to do"
    )
    assert why in where(found, shown.rows[0])
    assert (shown.standing.column, shown.standing.look) == ("you", "you")
    assert shown.now.head == "Its session stopped: it waits for your word"
    red = replace(hold, why="the base is red", after="fix-the-base")
    base = told(world(task(status="landing", hold=red)), "gift-note")
    assert (base.rows, base.standing.column) == ((), "checks")
    assert "waits for the base" in base.now.head


def test_the_where_of_a_blocked_task_says_to_tell_its_session_what_to_do() -> None:
    """`main`'s Blocked.test_the_where_of_a_blocked_task_says_to_tell_its_session_what_to_do:
    the row, the header's Waits for and the large card say the same."""
    hold = Blocked(why="the migration needs the owner", fix="x", since=at(5))
    seen = world(task(status="building", hold=hold))
    shown = told(seen, "gift-note")
    said = where(owed.seen(seen, "gift-note"), shown.rows[0])
    assert shown.waits is not None
    assert shown.waits.where == said == shown.now.where
    assert "“the migration needs the owner”" in said
    assert "to build it" not in said


def test_an_open_card_of_the_live_session_is_a_row_with_its_question_answered_on_the_board() -> (
    None
):
    """`main`'s Cards.test_an_open_card_of_the_live_session_is_a_row_with_its_question_whose_
    verb_opens_the_card: its key, its question as the verb, the card's own page, and where
    he answers it; the board takes the answer, so the verb jumps to no session."""
    card = Question(
        id="P-1",
        topic="card",
        question="keep the empty cell?",
        options=("yes", "no"),
        asked=MOMENT,
    )
    seen = world(task("export-notes", status="building", questions=(card,)))
    (stack,) = waits_view.waits(seen).stacks
    (row,) = stack.waits
    assert (row.id, row.kind, row.verb) == (
        "wait-P-1",
        "card",
        "Keep the empty cell?",
    )
    assert owed.rows(seen)[0].key == "card:export-notes:P-1"
    assert row.href.endswith("/tasks/export-notes/card/P-1?in=waits")
    assert row.jump is None
    assert "never a conversation" in row.where


def reading(*reads: PersonaRead, slug: str = "gift-note") -> Seen:
    """A task whose interview ended at minute 5, with the personas' reads `reads`."""
    ended = Span(name="interview", start=at(1), end=at(5))
    return task(
        slug,
        INTERVIEW,
        status="shaping",
        hold=ASKING,
        spans=(ended,),
        criteria=Criteria(reads=reads),
    )


def test_a_read_nobody_answered_and_started_once_more_hides_the_row_again() -> None:
    """`main`'s InterviewRead.test_a_read_nobody_answered_and_started_once_more_hides_the_row_
    again."""
    silent = PersonaRead(
        by="lem",
        started=at(10),
        ended=at(14),
        silent=(Silent(name="Ania, opus", why="no answer"),),
    )
    again = PersonaRead(by="lem", started=at(15))
    shown = told(world(reading(silent, again)), "gift-note")
    assert (shown.rows, shown.standing.column) == ((), "build")


def test_a_read_that_started_before_the_newest_hold_does_not_hide_it() -> None:
    """`main`'s InterviewRead.test_a_read_that_started_before_the_newest_block_does_not_hide_it:
    a start with no end before the interview's hold (one a resumed task carried over) is no
    read of these criteria."""
    stale = PersonaRead(by="lem", started=MOMENT - timedelta(minutes=1))
    asking = task(
        "gift-note",
        INTERVIEW,
        status="shaping",
        hold=ASKING,
        criteria=Criteria(reads=(stale,)),
    )
    assert keys(owed.rows(world(asking))) == [("held", "held:gift-note")]


def test_a_session_gone_in_the_read_is_still_a_row() -> None:
    """`main`'s InterviewRead.test_a_session_gone_in_the_read_is_still_a_row."""
    seen = replace(reading(PersonaRead(by="lem", started=at(10))), session=gone())
    assert keys(owed.rows(world(seen))) == [("session", "session:gift-note")]


def test_the_list_counts_only_the_interview_that_asks_him() -> None:
    """`main`'s InterviewRead.test_lem_project_waiting_counts_only_the_interview_that_asks_him:
    two interviews, and the personas read the criteria of the first; the list (which `lem
    waiting` and the board's Waits for you both read) counts one."""
    first = reading(
        PersonaRead(by="lem", started=at(10)), slug="landing-in-the-background"
    )
    second = task(
        "interview-in-a-companion",
        INTERVIEW,
        status="shaping",
        hold=ASKING,
        spans=(Span(name="interview", start=at(3)),),
    )
    seen = world(first, second)
    assert keys(owed.rows(seen)) == [("held", "held:interview-in-a-companion")]
    assert counted.counted(seen).waits == 1


def test_the_row_leaves_while_the_personas_read_and_comes_back_when_his_yes_is_missing() -> (
    None
):
    """`main`'s InterviewRead.test_the_row_leaves_while_the_
    personas_read_and_comes_back_when_his_yes_is_what_is_missing: the row, the column, the
    state's words, the card's line and the large card's head."""
    asking = told(
        world(
            task(
                "gift-note",
                INTERVIEW,
                status="shaping",
                hold=ASKING,
                spans=(Span(name="interview", start=at(1)),),
            )
        ),
        "gift-note",
    )
    assert keys(asking.rows) == [("held", "held:gift-note")]
    assert (asking.standing.column, asking.now.head) == (
        "you",
        "The interview waits for you",
    )
    runs = told(world(reading(PersonaRead(by="lem", started=at(10)))), "gift-note")
    assert runs.rows == ()
    assert (runs.standing.column, runs.standing.look, runs.now.who) == (
        "build",
        "quiet",
        "Lem acts",
    )
    assert (runs.standing.label, runs.now.head) == (
        "The personas read the criteria",
        "The personas read the criteria",
    )
    assert runs.line == (
        "The personas read the criteria: nothing waits for you until their read is in"
    )
    done = PersonaRead(by="lem", started=at(10), ended=at(14), answered=3, asked=3)
    read_in = told(world(reading(done)), "gift-note")
    assert keys(read_in.rows) == [("criteria", "held:gift-note")]
    assert (read_in.standing.column, read_in.now.head) == (
        "you",
        "The criteria wait for your yes",
    )


def test_the_scouts_read_keeps_the_row_since_the_interview_may_still_ask_him() -> None:
    """`main`'s InterviewRead.test_the_scouts_read_keeps_the_row_since_the_interview_may_still_
    ask_him: an interview whose span has no end yet is his."""
    asking = task(
        "gift-note",
        INTERVIEW,
        status="shaping",
        hold=ASKING,
        spans=(Span(name="scout", start=at(0.5)), Span(name="interview", start=at(1))),
    )
    assert keys(owed.rows(world(asking))) == [("held", "held:gift-note")]


def test_while_he_is_away_a_breaker_an_order_and_one_more_fact_stay_his() -> None:
    """The model's part of `main`'s InterviewTurns.test_criterion_3_while_he_is_away_lem_goes_
    on_and_only_a_breaker_and_an_order_stay_his: the interview goes on without him; a breaker,
    an order that names no task, and an investigation's wait for one more fact stay his; at
    his back the interview's row comes back."""
    order = OwnerHold(on="order", line="the order waits for the owner", since=MOMENT)
    fact = OwnerHold(
        on="fact", line="the investigation waits for one more fact", since=MOMENT
    )
    looks = (
        Look(
            record=task(
                "gift-note",
                status="shaping",
                hold=ASKING,
                spans=(Span(name="interview", start=at(1)),),
            ).record
        ),
        Look(record=task(ORDER, status="queued", hold=order).record),
        Look(
            record=task(
                "stopped-build",
                status="building",
                hold=BreakerHold(number=1, since=MOMENT),
            ).record
        ),
        Look(record=task("zero-after-refund", status="building", hold=fact).record),
    )
    away = sorted(row.key for row in waiting.rows(looks, away=True, now=NOW))
    assert away == [
        "breaker:stopped-build:1",
        f"held:{ORDER}",
        "held:zero-after-refund",
    ]
    back = [row.key for row in waiting.rows(looks, away=False, now=NOW)]
    assert "held:gift-note" in back


def test_a_nights_interview_and_criteria_go_on_without_him() -> None:
    """The night's part of `main`'s InterviewTurns.test_criterion_3_a_nights_task_and_the_
    requests_one_answer_go_on_without_him: a task the night opened answers its interview and
    settles its criteria without him; the large card says so."""
    night = date(2026, 11, 19)
    interview = task("gift-note", status="shaping", hold=ASKING, night=night)
    criteria = OwnerHold(on="criteria", line="the criteria wait", since=MOMENT)
    settles = task("settles", status="shaping", hold=criteria, night=night)
    seen = world(interview, settles)
    assert owed.rows(seen) == ()
    found = owed.seen(seen, "gift-note")
    assert heads.now_head(found, alone=True) == "Lem goes on without you"


def test_the_interview_is_yours_and_lems_writing_runs_to_the_read_the_skip_or_an_approval() -> (
    None
):
    """`main`'s InterviewTurns.test_criterion_4_the_interview_ends_with_its_questions_and_lems_
    writing_runs_to_the_read: the interview's stretch is yours from its start to its end, and
    Lem writes the criteria from that end to the personas' read; the skip question and his
    approval end Lem's writing too."""
    from lem.board.views.timeline import criteria, frame, worked
    from lem.board.views.timeline.shapes import Held
    from lem.records.approvals import Approval

    ended = Span(name="interview", start=at(60), end=at(65))
    read = PersonaRead(by="lem", started=at(72))
    made = task(
        "gift-note",
        status="shaping",
        hold=ASKING,
        spans=(ended,),
        criteria=Criteria(reads=(read,)),
    ).record
    drawn = frame.frame_of(made, NOW + timedelta(hours=1))
    spans = [
        (one.lane, one.start, one.end, one.head)
        for one in worked.worked(made.task, drawn)
        if isinstance(one, Held)
    ]
    writes = [
        (one.lane, one.start, one.end, one.head)
        for one in criteria.written(made, drawn)
        if isinstance(one, Held)
    ]
    assert spans == [("you", at(60), at(65), "The interview")]
    assert writes == [("lem", at(65), at(72), "Lem writes the criteria")]
    approval = Approval(
        number=1, at=at(70), by="owner", size="full", why="w", digest="d", criteria=()
    )
    for ends in (
        Criteria(skip="asked", skip_at=at(70)),
        Criteria(approvals=(approval,)),
    ):
        other = replace(made, task=replace(made.task, criteria=ends))
        found = [
            (one.start, one.end)
            for one in criteria.written(other, drawn)
            if isinstance(one, Held)
        ]
        assert found == [(at(65), at(70))]


def test_a_task_whose_session_opened_on_its_request_starts_and_lacks_no_session_until_it_is_gone() -> (
    None
):
    """`main`'s NewTask.test_a_session_open_with_no_block_is_a_task_that_starts, changed: the
    task is `shaping` from its open (the record exists before its session), so it says
    "Shaping" where `main` said "Starting"; it reads its request, waits for nobody while its
    session lives, and is a row with "Open a session" once its session is gone."""
    starts = task("gift-note", status="shaping")
    shown = told(world(starts), "gift-note")
    assert (shown.rows, shown.standing.column, shown.standing.label) == (
        (),
        "build",
        "Shaping",
    )
    assert shown.now.head == "Its session opened: it reads the request"
    lacking = world(replace(starts, session=gone()))
    assert keys(owed.rows(lacking)) == [("session", "session:gift-note")]
    assert opening.opens(lacking, owed.seen(lacking, "gift-note"))


def test_an_ended_tasks_card_and_its_followers_read_the_same_after_its_journal_became_a_summary() -> (
    None
):
    """The view's part of `main`'s Summary.test_an_old_ended_tasks_card_and_its_followers_
    read_the_same_after_its_events_became_one_summary, changed: the prune makes a task's
    journal one `Summary` entry and keeps its record (status, since, pull request); the card
    and the tasks queued after it read the same."""
    entries = (
        StateNoted(at=at(1), status="building", line="lead: builder"),
        StateNoted(at=at(15), status="landed", line="main: pull request 12 is merged"),
    )
    whole = task("report-dates", status="landed", since=at(15))
    whole = replace(whole, record=replace(whole.record, journal=entries))
    past = Summary(
        at=at(40),
        statuses=("building", "landed"),
        last_state=entries[-1],
        first=at(1),
        last=at(15),
        entries=2,
        pull=12,
    )
    pruned = replace(whole, record=replace(whole.record, journal=(past,)))
    starts = task("report-dates-in-export", status="queued", after=("report-dates",))
    waits = task("card-foot-after", status="queued", after=("card-foot",))
    dropped = task("card-foot", status="dropped")
    said = []
    for ended in (whole, pruned):
        seen = world(ended, starts, waits, dropped)
        shown = told(seen, "report-dates")
        said.append(
            (
                shown.standing,
                shown.line,
                keys(owed.of_task(seen, "card-foot-after")),
                told(seen, "report-dates-in-export").now.head,
            )
        )
    assert said[0] == said[1]
    assert said[0][1] == "Landed: main: pull request 12 is merged"
    assert said[0][2] == [("after_dropped", "after_dropped:card-foot-after")]


def test_a_merged_or_closed_task_lacks_its_session_only_while_its_worktree_stays() -> (
    None
):
    """`main`'s Sessions.test_a_merged_task_has_a_row_only_while_its_worktree_stays and
    Sessions.test_a_task_dropped_by_a_close_on_github_has_a_row_only_while_its_worktree_stays:
    the row says which cleanup lacks its session and since when; with no worktree, no row and
    no "Open a session"."""
    for status, verb, note in (
        ("landed", "No session cleans the merged task", "since it was merged"),
        ("dropped", "No session cleans the dropped task", "since it was dropped"),
    ):
        ended = replace(task("gift-note", status=status), session=gone())
        seen = world(replace(ended, worktree=True))
        (stack,) = waits_view.waits(seen).stacks
        (row,) = stack.waits
        assert (row.id, row.verb, row.since.title) == (
            "wait-session-gift-note",
            verb,
            note,
        )
        assert opening.opens(seen, owed.seen(seen, "gift-note"))
        bare = world(ended)
        assert owed.rows(bare) == ()
        assert not opening.opens(bare, owed.seen(bare, "gift-note"))


def test_a_parked_task_and_one_queued_behind_an_open_task_lack_no_session() -> None:
    """`main`'s Sessions.test_a_parked_task_and_one_queued_behind_an_open_task_have_none."""
    from lem.records.holds import Parked

    parked = replace(
        task("aside", status="planned", hold=Parked(since=MOMENT)), session=gone()
    )
    behind = replace(
        task("gift-note", status="queued", after=("coupon",)), session=gone()
    )
    seen = world(parked, behind, task("coupon", status="open"))
    assert [row.task for row in owed.rows(seen) if row.kind == "session"] == []
    assert not opening.opens(seen, owed.seen(seen, "gift-note"))


def test_a_task_with_a_second_row_beside_no_session_is_answered_where_that_row_says() -> (
    None
):
    """`main`'s Sessions.test_a_task_with_a_second_row_beside_no_session_is_answered_where_
    that_row_says: a held and a planned task whose session is gone; the open comes first,
    and the second row's words follow for the session he opens."""
    held = OwnerHold(on="step", line="the migration needs the owner", since=at(5))
    plan = OwnerHold(on="plan", line="plan written, the owner reads it", since=at(5))
    for status, hold, second in (
        ("building", held, "held"),
        ("planned", plan, "plan"),
    ):
        seen = world(replace(task(status=status, hold=hold), session=gone()))
        shown = told(seen, "gift-note")
        assert [row.kind for row in shown.rows] == ["session", second]
        found = owed.seen(seen, "gift-note")
        first = where(found, shown.rows[0])
        assert shown.waits is not None
        assert shown.waits.where == f"{first} {answer(found.record.task)}"
        assert first.startswith("Open a session here or on the task’s header")


def test_a_wake_nobody_took_is_a_row_of_its_own() -> None:
    """`main`'s Sessions.test_a_wake_nobody_took_is_a_row_of_its_own: an open pull request's
    session that lives and left a wake-up unanswered."""
    from lem.model.owner.looks import Session

    deaf = Session(live=True, since=MOMENT, unanswered=True)
    seen = world(replace(task("gift-note", status="open"), session=deaf))
    rows = [row for row in owed.rows(seen) if row.kind == "session"]
    assert [row.key for row in rows] == ["deaf:gift-note"]
    found = owed.seen(seen, "gift-note")
    assert verbs.verb(rows[0], found.record.task, None) == "Its session does not answer"


def test_nothing_is_said_while_the_sessions_are_not_known_or_the_session_is_young() -> (
    None
):
    """`main`'s Sessions.test_nothing_is_said_while_the_server_has_not_asked_or_the_session_
    is_young: no session facts (the terminal was not asked), and a session two minutes young."""
    unknown = replace(task(status="building"), session=None)
    assert owed.rows(world(unknown)) == ()
    young = replace(task(status="shaping", hold=ASKING), session=gone())
    early = world(young, now=MOMENT + timedelta(seconds=119))
    assert [row.kind for row in owed.rows(early)] == ["held"]


def test_the_where_of_a_task_whose_session_is_gone_says_what_its_row_says() -> None:
    """`main`'s Sessions.test_the_where_of_a_task_whose_session_is_gone_says_what_its_row_
    says."""
    seen = world(replace(task(status="building"), session=gone()))
    shown = told(seen, "gift-note")
    assert [row.kind for row in shown.rows] == ["session"]
    assert verbs.verb(
        shown.rows[0], owed.seen(seen, "gift-note").record.task, None
    ) == ("No session runs this task")
    assert shown.waits is not None
    said = shown.waits.where or ""
    assert "Open a session here or on the task’s header" in said
    assert "/lem drop gift-note" in said
    assert "Tell the task’s session" not in said


def test_criterion_1_after_the_last_answer_lem_writes_the_criteria_and_nothing_waits_for_him() -> (
    None
):
    """`main`'s InterviewTurns.test_criterion_1_after_the_last_answer_lem_writes_the_criteria_
    and_nothing_waits_for_him: the scout's read in or not, the card says Lem's turn and no
    scout."""
    for spans in (
        (Span(name="interview", start=at(1), end=at(5)),),
        (
            Span(name="interview", start=at(1), end=at(5)),
            Span(name="scout", start=at(0.5), end=at(6)),
        ),
    ):
        seen = world(
            task("gift-note", INTERVIEW, status="shaping", hold=ASKING, spans=spans)
        )
        shown = told(seen, "gift-note")
        assert (shown.rows, shown.standing.column, counted.counted(seen).waits) == (
            (),
            "build",
            0,
        )
        assert shown.line == "Lem writes the criteria; then they come to you."
        assert "scout" not in shown.line.lower()
        assert (shown.now.who, shown.now.head, shown.standing.look) == (
            "Lem acts",
            "Lem writes the criteria",
            "lem",
        )
        assert shown.waits is None


def test_criterion_2_the_skip_question_is_his_row_answered_on_it_and_his_no_starts_the_read() -> (
    None
):
    """`main`'s InterviewTurns.test_criterion_2_the_skip_question_is_his_row_and_his_no_
    starts_the_read, changed: the skip's row is his wait's (`held:SLUG`), where `main` named it
    by its held block; its verb and the board's Yes and No are the skip question's. His no
    starts the read and nothing waits for him; with the read in, or with his yes, the
    criteria wait for his yes."""
    from lem.model.criteria import skip, waits
    from lem.records.questions import Question

    ended = Span(name="interview", start=at(1), end=at(5))
    asked = Question(
        id="skip:gift-note:1",
        topic="skip",
        question="Skip the personas' read?",
        options=("yes", "no"),
        asked=at(12),
    )
    hold = OwnerHold(on="skip-read", line=skip.ASKED, since=MOMENT)
    seen = world(
        task(
            "gift-note",
            skip.ASKED,
            status="shaping",
            hold=hold,
            spans=(ended,),
            questions=(asked,),
        )
    )
    (stack,) = waits_view.waits(seen).stacks
    (row,) = stack.waits
    assert (row.id, row.kind, row.verb) == (
        "wait-held-gift-note",
        "held",
        "Lem asks whether to skip the personas' read of the criteria",
    )
    assert row.acts is not None
    assert row.acts.answer is not None
    assert [one.option for one in row.acts.answer.choices] == ["yes", "no"]
    assert row.where.startswith("Lem asks whether to skip")
    assert "y or n" in (told(seen, "gift-note").now.where or "")
    said_no = reading(PersonaRead(by="lem", started=at(13)))
    assert owed.rows(world(said_no)) == ()
    read_in = PersonaRead(by="lem", started=at(13), ended=at(18), asked=3, answered=3)
    assert keys(owed.rows(world(reading(read_in)))) == [("criteria", "held:gift-note")]
    criterion = Question(
        id="criterion-1",
        topic=waits.TOPIC,
        question=waits.QUESTION,
        options=waits.OPTIONS,
        asked=at(14),
    )
    said_yes = task(
        "gift-note",
        INTERVIEW,
        status="shaping",
        hold=ASKING,
        spans=(ended,),
        criteria=Criteria(skip="yes", skip_at=at(13)),
        questions=(criterion,),
    )
    yes = told(world(said_yes), "gift-note")
    assert keys(yes.rows) == [("criteria", "held:gift-note")]
    assert yes.now.head == "The criteria wait for your yes"


def test_criterion_3_while_he_is_away_the_interview_goes_on_without_him_on_the_board() -> (
    None
):
    """The board's part of `main`'s InterviewTurns.test_criterion_3_while_he_is_away_lem_goes_
    on_and_only_a_breaker_and_an_order_stay_his: the task is Lem's, its state and its large
    card say that Lem goes on without him and its card's line how; the rows are
    `test_while_he_is_away_a_breaker_an_order_and_one_more_fact_stay_his`."""
    import dataclasses

    from lem.records.owner import Presence

    asking = task(
        "gift-note",
        INTERVIEW,
        status="shaping",
        hold=ASKING,
        spans=(Span(name="interview", start=at(1)),),
    )
    away = Presence(away=True, since=MOMENT, words="/lem im-away")
    seen = dataclasses.replace(world(replace(asking, alone=True)), presence=away)
    shown = told(seen, "gift-note")
    assert (shown.rows, shown.standing.column, shown.standing.label) == (
        (),
        "build",
        "Lem goes on without you",
    )
    assert (shown.now.head, shown.now.who) == ("Lem goes on without you", "Lem acts")
    assert shown.line.startswith("Lem goes on without you: ")
    assert "each in the task's decisions for the pull request" in shown.line
    assert counted.counted(seen).waits == 0
    back = told(world(asking), "gift-note")
    assert (keys(back.rows), back.now.head) == (
        [("held", "held:gift-note")],
        "The interview waits for you",
    )
