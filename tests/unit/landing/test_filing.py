"""The filing of what a review saw outside the change (`model/landing/filing*.py`, `items.py`,
`item_names.py`, `alike.py`, `jev_bar.py`) and Jev's adapter (`adapters/judge_jev*.py`): each
defect's place by the review's call, the item `file` writes, the words `--same`, `--new` and
`--again`, the items Jev names, and the requests it gets (`landing.md` D filing, F `file`;
`land.cmd_file`, `land.item_body`, `land.alike_named`, `land.ask_jev` on `main`)."""

import itertools
import json
import time
from pathlib import Path
from typing import TYPE_CHECKING

import httpx
import msgspec
import pytest
from msgspec.structs import replace

from lem.adapters import judge_jev, judge_jev_ask, judge_jev_wire
from lem.kernel.errors import Refusal
from lem.model.landing import (
    alike,
    filing,
    filing_flags,
    filing_place,
    item_names,
    items,
    jev_bar,
    phases,
)
from lem.model.landing.filing_place import Shelf
from lem.ports.judge import Candidate, Defect, NotAsked, Score
from lem.ports.place import Place
from lem.records.landing.record import Landing
from lem.records.landing.review import Filed, Finding, Reviewed
from unit.landing.worlds import MOMENT, PREPARED, REVIEWED, task, world

if TYPE_CHECKING:
    from collections.abc import Iterator

    from lem.records.record import Record

FOLDER = "docs/backlog"
PADS = items.Defect(
    where="shop/dates.py:format_day",
    title="format_day pads the day with a space",
    what='format_day of 3 May gives " 3 May"; the rest of the shop gives "03 May".',
)
WHY = "no user is confused, no contract breaks"
SEEN = "Seen outside the change by review round 1 of task export-notes (2026-11-23); the base commit has it."
ROOT = Path(__file__).resolve().parents[3]


def refused_of(found: object) -> Refusal:
    """The refusal; a case fails on anything else."""
    assert isinstance(found, Refusal), found
    return found


def finding(number: str = "r1.1", against: str = "over", **fields: object) -> Finding:
    made = Finding(
        id=number,
        level="nit",
        where=PADS.where,
        title=PADS.title,
        what=PADS.what,
        against="over",
    )
    return replace(made, against=against, **fields)


def reviewed(*found: Finding) -> Reviewed:
    return replace(REVIEWED, findings=found, to_file=tuple(one.id for one in found))


def record_of(*found: Finding, filed: tuple[Filed, ...] = ()) -> Record:
    return task(**{**PREPARED, "reviews": (reviewed(*found),), "filed": filed})


def shelf(*texts: tuple[str, str]) -> Shelf:
    read = tuple(
        found for found in (items.read(path, text) for path, text in texts) if found
    )
    return Shelf(
        folder=FOLDER, paths=frozenset(path for path, _ in texts), shelved=read
    )


def written(
    defect: items.Defect, worth: str, why: str | None = None, cites: str | None = None
) -> str:
    return item_names.body(
        defect,
        item_names.Written(
            worth=worth, added="2026-11-23", seen=SEEN, why=why, cites=cites
        ),
    )


# The item `file` writes for a defect.


def test_an_under_defect_is_a_worth_no_item_that_ends_with_its_reason() -> None:
    text = written(PADS, "no", WHY)
    front, lines = items.front_of(text)
    assert front == {
        "worth": "no",
        "where": "shop/dates.py:format_day",
        "added": "2026-11-23",
    }
    assert lines[0] == f"# {PADS.title}"
    assert lines[-1] == f"Decided against: {WHY}"
    assert SEEN in lines


def test_an_over_defect_is_a_worth_later_item_with_no_reason_line() -> None:
    text = written(PADS, "later", WHY)
    assert items.front_of(text)[0]["worth"] == "later"
    assert "Decided against" not in text
    assert text.endswith(f"{SEEN}\n")


def test_the_file_is_still_the_defect_with_its_reason_in_it_and_another_run_is_another() -> (
    None
):
    found = items.read("docs/backlog/x.md", written(PADS, "no", WHY))
    assert found is not None and found.reason
    assert items.holds(found, PADS)
    assert not items.holds(found, replace(PADS, what="format_day of 4 May gives 4 May"))
    assert not items.holds(found, replace(PADS, where="shop/dates.py"))
    assert items.read("x.md", "no heading here\n") is None


def test_an_item_is_named_by_its_title_then_its_place_then_a_number() -> None:
    names = list(itertools.islice(item_names.names_for(PADS), 4))
    slug = "format-day-pads-the-day-with-a-space"
    assert names == [
        f"{slug}.md",
        f"{slug}-dates-format-day.md",
        f"{slug}-dates-format-day-2.md",
        f"{slug}-dates-format-day-3.md",
    ]
    assert item_names.slug_of("!!") == ""
    assert len(item_names.slug_of("word " * 40)) <= item_names.SLUG_AT


def test_filing_indexes_the_shelf_once_across_name_collisions() -> None:
    scans: list[None] = []

    class Counted(tuple[items.BacklogItem, ...]):
        __slots__ = ()

        def __iter__(self) -> Iterator[items.BacklogItem]:
            scans.append(None)
            return super().__iter__()

    first, second, third = (
        f"{FOLDER}/{name}" for name in itertools.islice(item_names.names_for(PADS), 3)
    )
    other = written(replace(PADS, what="a different run"), "later")
    found = shelf((first, other), (second, other))
    indexed = replace(found, shelved=Counted(found.shelved))
    assert filing_place.named(indexed, PADS, None) == (third, False)
    assert len(scans) == 1


# Each defect's place.


def test_a_review_judges_each_defect_outside_the_change_by_the_bar() -> None:
    record = record_of(
        finding("r1.1", "over"),
        finding("r1.2", "under", why=WHY, what="other run"),
        finding("r1.3", "cheap", why="a comment"),
    )
    placed = filing.decide(record, world(), shelf(), filing_flags.Flags())
    assert not isinstance(placed, Refusal)
    assert [(one.finding, one.disposition, one.worth) for one in placed.filed] == [
        ("r1.1", "item", "later"),
        ("r1.2", "item", "no"),
        ("r1.3", "seen", None),
    ]
    assert placed.filed[2].line == f"`{PADS.where}`: {PADS.title}; cheap: a comment"
    assert [write.path for write in placed.writes] == [
        f"{FOLDER}/format-day-pads-the-day-with-a-space.md",
        f"{FOLDER}/format-day-pads-the-day-with-a-space-dates-format-day.md",
    ]
    assert placed.writes[1].text.rstrip().endswith(f"Decided against: {WHY}")
    assert [one.id for one in placed.asks] == ["r1.1", "r1.2"]


def test_a_defect_an_open_item_holds_gets_no_second_file() -> None:
    held = f"{FOLDER}/held.md"
    record = record_of(finding("r1.1", "under", why=WHY, open=held))
    placed = filing.decide(
        record, world(), shelf((held, written(PADS, "later"))), filing_flags.Flags()
    )
    assert not isinstance(placed, Refusal)
    assert [(one.disposition, one.path) for one in placed.filed] == [("same", held)]
    assert placed.filed[0].line is not None and placed.filed[0].line.endswith(
        f"an open item holds it, `{held}`"
    )
    assert placed.writes == ()
    gone = filing.decide(record, world(), shelf(), filing_flags.Flags())
    assert not isinstance(gone, Refusal) and gone.filed[0].disposition == "item"


def test_an_over_defect_whose_open_item_says_worth_no_gets_a_new_item_that_names_it() -> (
    None
):
    held = f"{FOLDER}/held.md"
    over = record_of(finding("r1.1", "over", open=held))
    placed = filing.decide(
        over, world(), shelf((held, written(PADS, "no", WHY))), filing_flags.Flags()
    )
    assert not isinstance(placed, Refusal)
    assert (
        placed.filed[0].disposition,
        placed.filed[0].worth,
        placed.filed[0].cites,
    ) == ("item", "later", held)
    assert placed.writes[0].path != held
    assert item_names.NOW_OVER.format(held) in placed.writes[0].text
    assert placed.asks == ()
    new = items.read(placed.writes[0].path, placed.writes[0].text)
    assert items.holds(new, PADS)
    under = record_of(finding("r1.1", "under", why=WHY, open=held))
    settled = filing.decide(
        under, world(), shelf((held, written(PADS, "no", WHY))), filing_flags.Flags()
    )
    assert not isinstance(settled, Refusal) and settled.filed[0].disposition == "same"


def test_a_defect_two_rounds_saw_word_for_word_is_one_item_and_two_runs_are_two() -> (
    None
):
    path = f"{FOLDER}/format-day-pads-the-day-with-a-space.md"
    there = shelf((path, written(PADS, "later")))
    placed = filing.decide(record_of(finding()), world(), there, filing_flags.Flags())
    assert not isinstance(placed, Refusal)
    assert (placed.filed[0].path, placed.writes) == (path, ())
    other = finding(what="format_day of 4 May gives 4 May")
    second = filing.decide(record_of(other), world(), there, filing_flags.Flags())
    assert not isinstance(second, Refusal)
    assert (
        second.writes[0].path
        == f"{FOLDER}/format-day-pads-the-day-with-a-space-dates-format-day.md"
    )


def test_every_defect_has_its_place_before_propose() -> None:
    record = record_of(finding())
    assert phases.due(record, world()).step == "file"
    done = record_of(
        finding(),
        filed=(
            Filed(
                finding="r1.1",
                disposition="item",
                path="docs/backlog/x.md",
                worth="later",
            ),
        ),
    )
    assert filing.holds(done, world()).why.startswith("every defect")
    assert phases.due(done, world()).step == "propose"
    nothing = record_of()
    assert phases.due(nothing, world()).step == "propose"
    silent = task(
        **{
            **PREPARED,
            "reviews": (replace(reviewed(finding()), answered=()),),
            "filed": (),
        }
    )
    assert filing.waiting(silent.landing or Landing()) == ()


# The words `--same`, `--new` and `--again`.


def test_file_refuses_a_defect_named_by_both_same_and_new_and_a_number_of_no_waiting_defect() -> (
    None
):
    held = f"{FOLDER}/held.md"
    there = shelf((held, written(PADS, "later")))
    record = record_of(finding())
    both = filing_flags.Flags(same=(f"r1.1={held}",), new=("r1.1",))
    assert refused_of(filing.decide(record, world(), there, both)).code == "same-new"
    stray = refused_of(
        filing.decide(record, world(), there, filing_flags.Flags(new=("r1.9",)))
    )
    assert stray.code == "same-new" and "the ones here are r1.1" in stray.why
    for word in ("r1=docs/backlog/held.md", "r1.1=docs/backlog/gone.md", "r1.1"):
        flags = filing_flags.Flags(same=(word,))
        assert refused_of(filing.decide(record, world(), there, flags)).code == "same"
    same = filing.decide(
        record, world(), there, filing_flags.Flags(same=(f"r1.1={held}",))
    )
    assert not isinstance(same, Refusal)
    assert (same.filed[0].disposition, same.filed[0].path, same.asks) == (
        "same",
        held,
        (),
    )
    new = filing.decide(record, world(), there, filing_flags.Flags(new=("r1.1",)))
    assert not isinstance(new, Refusal) and new.writes and new.asks == ()


def test_an_item_that_was_filed_and_then_removed_stops_file_and_again_puts_it_back() -> (
    None
):
    path = f"{FOLDER}/format-day-pads-the-day-with-a-space.md"
    filed = Filed(finding="r1.1", disposition="item", path=path, worth="later")
    record = record_of(finding(), filed=(filed,))
    stopped = refused_of(filing.decide(record, world(), shelf(), filing_flags.Flags()))
    assert (
        stopped.code == "item-gone" and path in stopped.why and "--again" in stopped.fix
    )
    again = filing.decide(record, world(), shelf(), filing_flags.Flags(again=True))
    assert not isinstance(again, Refusal)
    assert [write.path for write in again.writes] == [path]


# The items Jev names.


def test_the_three_highest_at_or_over_same_at_are_named_the_highest_first() -> None:
    shelved = tuple(
        items.BacklogItem(path=f"{FOLDER}/{name}.md", title=name, worth="later")
        for name in "abcde"
    )
    scores = {
        f"{FOLDER}/a.md": 0.4,
        f"{FOLDER}/b.md": 0.5,
        f"{FOLDER}/c.md": 0.9,
        f"{FOLDER}/d.md": 0.7,
        f"{FOLDER}/e.md": 0.6,
    }
    named = alike.named(scores, shelved)
    assert [(one.path, one.jev) for one in named] == [
        (f"{FOLDER}/c.md", "Jev: 0.90"),
        (f"{FOLDER}/d.md", "Jev: 0.70"),
        (f"{FOLDER}/e.md", "Jev: 0.60"),
    ]
    assert alike.named({}, shelved) == ()


def test_a_finding_is_kept_by_its_place_title_and_run_and_a_new_reason_leaves_it_the_same() -> (
    None
):
    assert alike.key_of(PADS) == alike.key_of(replace(PADS, what=f"  {PADS.what}  "))
    assert alike.key_of(PADS) != alike.key_of(replace(PADS, what="another run"))
    assert len(alike.key_of(PADS)) == alike.KEY_LENGTH


def test_file_stops_with_each_defect_jev_names_and_the_two_ways_on() -> None:
    one = alike.Alike(
        path=f"{FOLDER}/x.md", title="x", worth="no", score=0.8, jev="Jev: 0.80"
    )
    line = alike.line_of("r1.1", "a title", (one,))
    assert line == f'r1.1 "a title": `{FOLDER}/x.md` "x" (Jev: 0.80, worth: no)'
    refused = alike.refused((line,), "r1.1", "export-notes")
    assert refused is not None and refused.code == "jev-same"
    assert "Nothing is written" in refused.why
    assert "--same r1.1=PATH" in refused.fix and "--new r1.1" in refused.fix
    assert alike.refused((), "", "export-notes") is None


# The bar Jev reads.


def test_the_condition_of_lem_s_own_rule_6() -> None:
    text = (ROOT / jev_bar.LEMS).read_text(encoding="utf-8")
    assert jev_bar.condition(text) == (
        "it confuses a user, breaks a contract, damages data or costs money, and it happens "
        "today; or the owner said it is worth an item"
    )


def test_the_sentence_counts_only_in_rule_6() -> None:
    assert (
        jev_bar.condition(
            "5. An item is filed only for a defect over the bar: it is red.\n6. **Defects.** List them.\n7. Ask nobody.\n"
        )
        is None
    )
    split = "6. **Defects.** An item is filed only for a defect\nover the bar: it is red\nand loud. Then stop.\n"
    assert jev_bar.condition(split) == "it is red and loud"


def test_lem_s_own_bar_file_when_the_project_has_none_and_the_project_s_own_by_its_path(
    tmp_path: Path,
) -> None:
    assert judge_jev.bar_of(tmp_path)[1] == "agents/lem-builder.md"
    assert judge_jev.bar_of(tmp_path)[0] is not None
    own = tmp_path / ".claude" / "agents" / "lem-builder.md"
    own.parent.mkdir(parents=True)
    own.write_text(
        "5. **Commit.**\n6. **A defect.** File it when it hurts someone.\n7. Ask.\n"
    )
    assert judge_jev.bar_of(tmp_path) == (None, ".claude/agents/lem-builder.md")
    place = Place(
        checkout=tmp_path, home=tmp_path, environ={"JEV_API_KEY": "not-a-real-key"}
    )
    judge = judge_jev.bind(
        place, transport=httpx.MockTransport(lambda request: pytest.fail("sent"))
    )
    assert judge.over_bar(Defect(where="a.py", title="T", what="r")) == NotAsked(
        why="no bar in .claude/agents/lem-builder.md"
    )


# Jev's adapter, on a stand-in transport: nothing leaves the machine.

DEFECT = Defect(where="a.py:f", title="T", what="f(1) gives 2.")


def answering(
    score: object, sent: list[dict], status: int = 200
) -> httpx.MockTransport:
    """A stand-in for Jev that keeps each request and answers each question with `score`."""

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        sent.append({"body": body, "key": request.headers.get("authorization")})
        answers = {name: {"type": "noul", "noul": score} for name in body["questions"]}
        return httpx.Response(status, json={"model": "stand-in", "answers": answers})

    return httpx.MockTransport(handler)


def bound(
    tmp_path: Path, transport: httpx.BaseTransport, key: str | None = "not-a-real-key"
) -> judge_jev.JevJudge:
    environ = {"JEV_API_KEY": key} if key else {}
    return judge_jev.bind(
        Place(checkout=tmp_path, home=tmp_path, environ=environ), transport=transport
    )


def test_a_score_comes_back_and_the_request_is_sent_whole(tmp_path: Path) -> None:
    sent: list[dict] = []
    judge = bound(tmp_path, answering(0.82, sent))
    assert judge.over_bar(DEFECT) == Score(score=0.82)
    body = sent[0]["body"]
    assert body["state"] == {"where": "a.py:f", "title": "T", "run": "f(1) gives 2."}
    assert body["model"] == judge_jev.MODEL
    question = body["questions"][judge_jev_wire.OVER]
    assert question["type"] == "noul"
    assert question["criteria"]["true"].startswith(
        "The finding meets the bar: it confuses a user"
    )
    assert sent[0]["key"] == "Bearer not-a-real-key"


def test_no_key_starts_nothing(tmp_path: Path) -> None:
    sent: list[dict] = []
    judge = bound(tmp_path, answering(0.82, sent), key=None)
    assert judge.over_bar(DEFECT) == NotAsked(why="no key")
    held = Candidate(path="a.md", title="an item")
    assert judge.same_items(DEFECT, (held,)) == NotAsked(why="no key")
    assert sent == []


def test_a_failed_request_a_reply_that_does_not_read_and_a_request_over_the_limit(
    tmp_path: Path,
) -> None:
    sent: list[dict] = []
    for transport in (
        answering(0.5, sent, status=502),
        answering(1.5, sent),
        httpx.MockTransport(lambda request: httpx.Response(200, content=b"not json")),
    ):
        assert bound(tmp_path, transport).over_bar(DEFECT) == NotAsked(why="no answer")
    long = replace(DEFECT, what="x" * (judge_jev_wire.LIMIT_BYTES + 1))
    assert bound(tmp_path, answering(0.5, sent)).over_bar(long) == NotAsked(
        why="too long"
    )


def test_a_request_past_its_seconds_is_no_answer(tmp_path: Path) -> None:
    def slow(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out", request=request)

    assert bound(tmp_path, httpx.MockTransport(slow)).over_bar(DEFECT) == NotAsked(
        why="no answer"
    )
    assert judge_jev_ask.SECONDS < 120


def test_every_item_is_asked_in_requests_each_under_the_limit_and_comes_back_by_its_path(
    tmp_path: Path,
) -> None:
    candidates = tuple(
        Candidate(
            path=f"docs/backlog/item-{number}.md",
            title=f"title {number} {'w ' * 800}",
            where="a.py",
            first="first line",
        )
        for number in range(30)
    )
    sent: list[dict] = []
    found = bound(tmp_path, answering(0.6, sent)).same_items(DEFECT, candidates)
    assert not isinstance(found, NotAsked)
    assert sorted(str(score.path) for score in found) == sorted(
        one.path for one in candidates
    )
    assert len(sent) > 1
    sizes = [
        len(msgspec.json.encode(one["body"]["state"]))
        + len(msgspec.json.encode(one["body"]["questions"]))
        for one in sent
    ]
    assert max(sizes) <= judge_jev_wire.LIMIT_BYTES
    question = sent[0]["body"]["questions"]["i0"]["instructions"]
    assert (
        "title: title 0" in question
        and "where: a.py" in question
        and "the first line of its body: first line" in question
    )


def test_a_state_that_does_not_fit_with_one_question_is_too_long(
    tmp_path: Path,
) -> None:
    held = Candidate(path="docs/backlog/item.md", title="an item")
    long = replace(DEFECT, what="x" * judge_jev_wire.LIMIT_BYTES)
    assert bound(tmp_path, answering(0.5, [])).same_items(long, (held,)) == NotAsked(
        why="too long"
    )


def test_the_request_and_reply_are_jev_s_own_form() -> None:
    asked = judge_jev_wire.Request(
        model="m",
        state={"run": "r"},
        questions={"over": judge_jev_wire.question("Over?", "y", "n")},
    )
    assert json.loads(msgspec.json.encode(asked))["questions"]["over"] == {
        "instructions": "Over?",
        "criteria": {"true": "y", "false": "n"},
        "type": "noul",
    }
    assert judge_jev_wire.scores_of(b'{"answers": {"over": {"noul": 0.3}}}', asked) == {
        "over": 0.3
    }
    assert judge_jev_wire.scores_of(b'{"answers": {}}', asked) is None


def test_an_item_and_the_moment_of_the_review_name_where_it_was_seen() -> None:
    record = record_of(finding())
    placed = filing.decide(record, world(now=MOMENT), shelf(), filing_flags.Flags())
    assert not isinstance(placed, Refusal)
    text = placed.writes[0].text
    assert "added: 2026-11-25" in text
    assert (
        "Seen outside the change by review round 1 of task fix-the-login (2026-11-25)"
        in text
    )


# The cases of the review round of 2026-11-25 (Astra's findings, each failed before its fix).


def test_a_file_git_does_not_track_settles_no_defect_and_only_takes_its_name() -> None:
    private = f"{FOLDER}/private-note.md"
    name = f"{FOLDER}/format-day-pads-the-day-with-a-space.md"
    there = Shelf(folder=FOLDER, paths=frozenset(), taken=frozenset({private, name}))
    record = record_of(finding())
    same = filing.decide(
        record, world(), there, filing_flags.Flags(same=(f"r1.1={private}",))
    )
    assert refused_of(same).code == "same"
    opened = record_of(finding(open=private))
    placed = filing.decide(opened, world(), there, filing_flags.Flags())
    assert not isinstance(placed, Refusal)
    assert placed.filed[0].disposition == "item"
    assert (
        placed.writes[0].path
        == f"{FOLDER}/format-day-pads-the-day-with-a-space-dates-format-day.md"
    )


def test_a_defect_whose_open_item_left_the_tip_waits_for_its_place_again() -> None:
    held = f"{FOLDER}/held.md"
    filed = Filed(finding="r1.1", disposition="same", path=held, line="seen")
    record = record_of(finding(open=held), filed=(filed,))
    placed = filing.decide(record, world(), shelf(), filing_flags.Flags())
    assert not isinstance(placed, Refusal)
    assert [(one.finding, one.disposition) for one in placed.filed] == [
        ("r1.1", "item")
    ]
    assert len(placed.writes) == 1
    still = filing.decide(
        record, world(), shelf((held, written(PADS, "later"))), filing_flags.Flags()
    )
    assert not isinstance(still, Refusal) and still.filed == ()


def test_an_item_found_by_its_defect_keeps_the_worth_its_file_says() -> None:
    path = f"{FOLDER}/format-day-pads-the-day-with-a-space.md"
    owners = shelf((path, written(PADS, "no", "the owner: nobody reads the day")))
    placed = filing.decide(
        record_of(finding(against="over")), world(), owners, filing_flags.Flags()
    )
    assert not isinstance(placed, Refusal)
    assert (placed.filed[0].path, placed.filed[0].worth, placed.writes) == (
        path,
        "no",
        (),
    )


def test_a_reply_that_trickles_past_the_whole_request_s_seconds_is_no_answer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(judge_jev_ask, "SECONDS", 0.3)
    seen: list[dict] = []

    class Trickle(httpx.SyncByteStream):
        def __iter__(self):  # noqa: ANN204 - httpx's own protocol
            for _ in range(8):
                time.sleep(0.1)
                yield b" "

    def slow(request: httpx.Request) -> httpx.Response:
        seen.append(request.extensions["timeout"])
        return httpx.Response(200, stream=Trickle())

    started = time.monotonic()
    assert bound(tmp_path, httpx.MockTransport(slow)).over_bar(DEFECT) == NotAsked(
        why="no answer"
    )
    assert time.monotonic() - started < 0.7
    assert seen[0]["read"] <= 0.3


def test_the_request_is_json_and_an_answer_of_another_type_is_no_answer(
    tmp_path: Path,
) -> None:
    sent: list[httpx.Request] = []

    def choice(request: httpx.Request) -> httpx.Response:
        sent.append(request)
        body = {"answers": {"over": {"type": "choice", "noul": 0.9}}}
        return httpx.Response(200, json=body)

    assert bound(tmp_path, httpx.MockTransport(choice)).over_bar(DEFECT) == NotAsked(
        why="no answer"
    )
    assert sent[0].headers["content-type"] == "application/json"


def test_again_files_an_over_defect_whose_open_item_now_says_worth_no() -> None:
    held = f"{FOLDER}/held.md"
    filed = Filed(finding="r1.1", disposition="same", path=held, line="seen")
    record = record_of(finding(open=held), filed=(filed,))
    owners = shelf((held, written(PADS, "no", WHY)))
    plain = filing.decide(record, world(), owners, filing_flags.Flags())
    assert not isinstance(plain, Refusal) and plain.filed == ()
    again = filing.decide(record, world(), owners, filing_flags.Flags(again=True))
    assert not isinstance(again, Refusal)
    assert [(one.disposition, one.cites) for one in again.filed] == [("item", held)]


def test_the_alike_scores_keep_a_file_of_their_own_beside_proposes_jev_words() -> None:
    from lem.app.landing import jev_kept, propose_jev

    assert jev_kept.NAME != propose_jev.KEPT
