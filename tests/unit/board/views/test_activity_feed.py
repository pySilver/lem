"""The feed's words of what happened to a task (`board_model.describe` and `SAYS` on `main`): each
entry of its journal, Lem's acts on its sessions, its questions and its seats, in the words
`main`'s `tests/unit/test_board_model.py` held for its events."""

from typing import TYPE_CHECKING, Literal

import msgspec

from lem.app.sessions.acts import Open, Stopped, Wake
from lem.board.views import owed, sessions
from lem.board.views.activity import happenings
from lem.records.holds import Blocked
from lem.records.journal.landing import CheckEnd, CheckWait
from lem.records.journal.merge import ReadNoted, RefusalNoted
from lem.records.journal.task import OwnerAct, SpanMark, StateNoted
from lem.records.landing.merge import Refused
from lem.records.landing.propose import MergeRead
from lem.records.questions import Question
from lem.records.work import StandIn
from unit.board.views.timed import at, seen, task, world

if TYPE_CHECKING:
    from lem.app.sessions.acts import Act
    from lem.board.views.activity.told import Told
    from lem.board.views.world import Seen
    from lem.records.journal.entry import Entry

TIP = "abc1234560" + "0" * 30
MOVED = "m2m2m2m2m" + "0" * 31
TREE = "7" * 40
LINE = (
    "the reviewer `codex/gpt-6.2-sol:high` gave an error: no tokens, and this "
    "project permits no fallback"
)
STATUS = "The board’s server asked the task’s session for its status"
STOPPED = "The task’s session stopped"


def rows_of(made: Seen) -> list[Told]:
    """The rows of a task, oldest first."""
    return [row.told for row in happenings.of(made)]


def told(*journal: Entry, acts: tuple[Act, ...] = (), **fields: object) -> list[Told]:
    """The rows of a task with `journal`, Lem's `acts` and the task's `fields`."""
    return rows_of(seen(task(*journal, **fields), *acts))


def test_the_timeline_says_both_events_of_the_interviews_end_and_the_skip() -> None:
    """`main`'s InterviewTurns.test_the_timeline_says_both_events: the end of the interview's
    questions, and Lem's question whether to skip the personas' read."""
    skip = Question(
        id="skip:gift-note:20261122T101200Z",
        topic="skip",
        question="Skip the personas’ read?",
        options=("yes", "no"),
        asked=at("10:12"),
    )
    rows = told(
        SpanMark(at=at("10:05"), name="interview", edge="end"),
        questions=(skip,),
    )
    assert [row.head for row in rows] == [
        "The interview’s questions ended",
        "Lem asked whether to skip the personas’ read",
    ]


def refused(source: Literal["github", "lem"], by: Literal["owner", "merger"]) -> str:
    """The head of a merge refused by `source`, of `by`'s merge."""
    refusal = Refused(
        tip=TIP,
        source=source,
        kind="base",
        line="origin/main moved",
        by=by,
        at=at("10:02"),
    )
    return told(RefusalNoted(at=at("10:02"), refusal=refusal))[0].head


def test_the_timeline_says_whose_merge_lem_refused() -> None:
    """`main`'s Merge.test_the_timeline_says_whose_merge_lem_refused: right after his own
    press, the owner read whose merge Lem refused (merge-button-after-failed-merge,
    2026-11-22)."""
    assert (
        refused("lem", "owner"),
        refused("lem", "merger"),
        refused("github", "owner"),
    ) == (
        "Lem refused your merge",
        "Lem refused the merge agent’s merge",
        "GitHub refused the merge",
    )


def test_the_timeline_says_each_seat_event() -> None:
    """`main`'s SeatThatFailed.test_the_timeline_says_each_seat_event: the fallback that stood
    in, a seat no fallback stood in for, and the owner's go on. The go on speaks to him (`your
    go on`), where `main` printed the script's line about him."""
    stood = StandIn(
        seat="reviewer",
        failed="codex/gpt-6.2-sol:high",
        took="claude/opus:high",
        error="tokens",
        said="no tokens left",
        at=at("10:01"),
        again=at("10:03"),
    )
    lone = StandIn(
        seat="merger", failed="codex/gpt-6.2-sol:high", error="tokens", at=at("10:02")
    )
    hold = Blocked(why=LINE, fix="the owner's go on", seat="merger", since=at("10:02"))
    rows = told(stand_ins=(stood, lone), status="building", hold=hold)
    assert [(row.head, row.text, row.sub, row.look) for row in rows] == [
        (
            "The fallback stood in for the reviewer",
            "claude/opus:high in place of codex/gpt-6.2-sol:high",
            "no tokens left",
            "lem",
        ),
        (
            "The seat of the merge agent gave an error, and no fallback stood in",
            LINE,
            "",
            "you",
        ),
        (
            "Your go on: the seat is tried again",
            "your go on: the reviewer codex/gpt-6.2-sol:high is tried again",
            "",
            "you",
        ),
    ]


def landing() -> tuple[Entry, ...]:
    """The landing of #37 up to its checks' end at 10:54 (`main`'s StoppedSession.landing)."""
    return (
        StateNoted(
            at=at("10:15"),
            status="landing",
            line="the base moved: the checks run again",
        ),
        CheckEnd(at=at("10:54"), outcome="passed", say="", seconds=2156, tip=TIP),
    )


OPENED = Open(
    at=at("01:33"), session="S1", name="gift-note", phase="land", why="handoff"
)


def guarded(*acts: Act, journal: tuple[Entry, ...] = ()) -> list[Told]:
    """The rows of the landing of #37 with Lem's `acts` and more of its journal."""
    return told(*landing(), *journal, acts=(OPENED, *acts), status="landing")


def test_the_timeline_says_an_unread_wake_and_stop_in_words_of_their_own() -> None:
    """`main`'s StoppedRow.test_the_timeline_says_an_unread_wake_and_stop_in_words_of_their_own:
    a status message and a stop Lem sent while it could not read the session say so; the
    readable ones keep their words."""
    unread = guarded(
        Wake(at=at("11:39"), session="S1", why="status", unread=True),
        Stopped(at=at("11:49"), session="S1", unread=True),
    )
    assert (unread[-2].head, unread[-2].text) == (
        STATUS,
        (
            "no event of the task for 45 minutes, and Lem cannot read its session: "
            "it says where the task stands and goes on with its next step"
        ),
    )
    assert (unread[-1].head, unread[-1].look, unread[-1].text) == (
        STOPPED,
        "bad",
        (
            "no event of the task in the 10 minutes after the status message, and "
            "Lem cannot read its session: “Open a session” on the board starts a fresh one"
        ),
    )
    readable = guarded(*restarted(), *stopped())
    wake = next(row for row in readable if row.head == STATUS)
    assert wake.text == (
        "no sign of work for 45 minutes: it says where the task stands and goes on with "
        "its next step"
    )
    assert readable[-1].text == (
        "no sign of work after the status message, nor in the fresh session: "
        "“Open a session” on the board starts another"
    )


def restarted() -> tuple[Act, ...]:
    """The status message of 11:39 and the fresh session of 11:49 (`main`'s
    StoppedSession.restarted)."""
    return (
        Wake(at=at("11:39"), session="S1", why="status"),
        Open(
            at=at("11:49"), session="S2", name="gift-note", phase="land", why="stopped"
        ),
        Wake(at=at("11:49"), session="S1", why="replaced"),
    )


def stopped() -> tuple[Act, ...]:
    """The fresh session's status message and its stop (`main`'s StoppedRow.stopped)."""
    return (
        Wake(at=at("12:34"), session="S2", why="status"),
        Stopped(at=at("12:44"), session="S2"),
    )


def test_a_readable_stop_that_no_fresh_session_preceded_says_lem_opened_none() -> None:
    """`main`'s StoppedRow.test_a_stop_over_a_standing_unread_stop_names_no_fresh_session: a
    readable stop over one that already stood names no fresh session."""
    rows = guarded(
        Wake(at=at("11:39"), session="S1", why="status", unread=True),
        Stopped(at=at("11:49"), session="S1", unread=True),
        Wake(at=at("12:45"), session="S1", why="status"),
        Stopped(at=at("12:55"), session="S1"),
    )
    assert rows[-1].text == (
        "no sign of work after the status message, and Lem opened no fresh "
        "session by itself: “Open a session” on the board starts one"
    )


def test_the_timeline_says_that_a_stop_over_new_work_leaves_nothing_waiting() -> None:
    """`main`'s StoppedRow.test_the_timeline_says_that_a_stop_over_new_work_leaves_nothing_
    waiting: work logged after the status message and before the stop overtook it, which never
    stood, and nothing waits for the owner. Work of the stop's own second counts as after it,
    as the guard's timeline orders them, so such a stop stood: the work ends it, and nothing
    waits either (`main` told the two apart by the order of one log)."""
    wake = Wake(at=at("11:39"), session="S1", why="status", unread=True)
    stop = Stopped(at=at("11:49"), session="S1", unread=True)
    moved = StateNoted(
        at=at("11:48:30"),
        status="landing",
        line="the pull request waits for its checks",
    )
    raced = guarded(wake, stop, journal=(moved,))
    overtaken = next(row for row in raced if row.head.startswith("Lem logged a stop"))
    assert (overtaken.head, overtaken.look) == (
        "Lem logged a stop of the task’s session, but the task worked",
        "quiet",
    )
    assert "so the stop does not stand and nothing waits for you" in overtaken.text
    same = StateNoted(at=at("11:49"), status="landing", line=moved.line)
    later = guarded(wake, stop, journal=(same,))
    assert [row.head for row in later].count(STOPPED) == 1
    for journal in ((moved,), (same,)):
        made = seen(task(*landing(), *journal, status="landing"), OPENED, wake, stop)
        session = sessions.from_acts(made.record, made.acts)
        assert sessions.stop_of(made.record, made.acts, session) is None
        assert owed.rows(world(made)) == ()


def read(call: Literal["safe", "another round"] | None, **fields: object) -> Told:
    """The words of the merge agent's read with `call` on the moved base."""
    given = MergeRead(
        tip=TIP,
        base=MOVED,
        base_tree=TREE,
        verdict="merge",
        base_call=call,
        why="B changed only docs/board.md, which the change does not read",
        by="claude",
        at=at("10:03"),
    )
    shown = msgspec.structs.replace(given, **fields)
    return told(ReadNoted(at=at("10:03"), read=shown))[0]


def test_the_feed_shows_the_read_of_a_moved_base_with_its_call() -> None:
    """`main`'s MovedBase.test_the_feed_shows_the_read_of_a_moved_base_with_its_call: a safe
    moved base merges, another round lands it again, an answer Lem could not record is another
    round in doubt, and a read of no moved base says its verdict and who read it."""
    safe = read("safe")
    assert (safe.head, safe.text, safe.sub) == (
        "The merge agent read the task and the moved base",
        "the moved base m2m2m2m2m is safe; it merges",
        "B changed only docs/board.md, which the change does not read",
    )
    again = read("another round")
    assert (again.look, again.text) == (
        "gate",
        "the moved base m2m2m2m2m needs another round of the checks: Lem lands it again",
    )
    why = (
        "the merge agent's answer could not be recorded twice (it ended with no answer), "
        "and in doubt the checks run again"
    )
    unread = read("another round", no_answer=True, why=why)
    assert (unread.head, unread.text, unread.sub) == (
        "The merge agent's answer could not be recorded",
        (
            "the moved base m2m2m2m2m gets another round of the checks in doubt: "
            "Lem lands it again"
        ),
        why,
    )
    plain = read(None, why=None)
    assert (plain.head, plain.text, plain.sub) == (
        "The merge agent read the task",
        "it merges",
        "by claude",
    )


def test_the_activity_says_where_he_asked_from_and_no_login() -> None:
    """`main`'s Acts.test_the_activity_says_where_he_asked_from_and_no_login: a merge from the
    board through the tailnet door names the door, never a login."""
    row = told(OwnerAct(at=at("10:00"), act="merge", via="door"), status="open")[0]
    assert (row.head, row.text) == (
        "You merged it from the board",
        "the board, through the tailnet door",
    )


def test_the_activity_names_the_answer_and_its_own_question() -> None:
    asked = Question(
        id="criterion:gift-note",
        topic="criterion",
        question="Approve the new export column?",
        options=("yes", "no"),
        asked=at("10:00"),
    )
    other = msgspec.structs.replace(
        asked, id="criterion:gift-note:later", question="Approve the next plan?"
    )
    acted = OwnerAct(
        at=at("10:05"), act="answer", via="local", option="no", question=asked.id
    )
    row = next(
        row
        for row in told(acted, questions=(asked, other))
        if "You picked No" in row.head
    )
    assert (
        row.head == "You picked No on “Approve the new export column?” from the board"
    )


def test_criterion_7_a_landing_behind_one_that_waits_longer_says_so_in_the_feed() -> (
    None
):
    """The feed's part of `main`'s WaitsBehind.test_criterion_7_a_landing_behind_one_that_waits_
    longer_says_so_on_the_card_and_in_the_feed: the checks wait behind the landing that waits
    longer; the first itself waits for the load."""
    behind = CheckWait(
        at=at("10:01"),
        reason="behind",
        load=50.0,
        start_below=40,
        behind="fast-track-checks-documents",
        why="longer",
    )
    row = told(behind, status="landing")[0]
    assert row == (
        "quiet",
        "clock",
        "The checks wait",
        "behind fast-track-checks-documents, which waits longer",
        "",
        False,
    )
    load = CheckWait(at=at("10:01"), reason="load", load=9.5, start_below=6)
    assert (
        told(load, status="landing")[0].text == "for the load: 9.5, they start below 6"
    )
