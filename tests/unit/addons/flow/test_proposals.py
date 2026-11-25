"""The records of the night's and the retro's proposals, the reviewer's verdicts and items, and
the owner's drop of an item (`main`: tests/unit/test_proposals.py, `project.cmd_proposals_*`)."""

import datetime as dt
import json
from typing import TYPE_CHECKING

import msgspec
import pytest

from fakes.command import lem
from lem.addons.proposals import days, heads, item_files, listing
from lem.app.tasks import opening
from lem.kernel import locks
from lem.kernel.errors import Refusal
from lem.store import places
from lem.store import workspace as claims
from unit.addons.flow.runs import (
    DAY,
    MORNING,
    TODAY,
    add,
    eleven,
    judge,
    proposal,
    record,
)
from unit.task.spaces import made, refusal, result, workspace

if TYPE_CHECKING:
    from pathlib import Path

LATER = MORNING + dt.timedelta(hours=3)


def state_of(tmp_path: Path) -> Path:
    return workspace(tmp_path).state


def test_a_retro_with_no_proposal_writes_its_days_file_with_what_it_read(
    tmp_path: Path,
) -> None:
    state = state_of(tmp_path)
    added = add(state, "retro", [], day=TODAY)
    assert (added.numbers, added.names) == ((), ())
    found = record(state, "retro", TODAY)
    assert [run.read for run in found.runs] == ["the tasks since the last retro"]
    assert found.proposals == ()
    body = json.loads((state / "retros" / "2026-11-25.json").read_text())
    assert set(body) == {"date", "kind", "runs", "proposals", "refuted", "passed"} | {
        "dropped"
    }
    assert body["runs"][0]["at"] == "2026-11-23T06:55:00Z"


def test_a_second_retro_of_the_day_adds_after_the_first_and_keeps_its_verdicts(
    tmp_path: Path,
) -> None:
    state = state_of(tmp_path)
    add(state, "retro", [proposal("lessons", "One"), proposal("lessons", "Two")])
    judge(state, [{"proposal": "retro of 2026-11-24 #1", "refuted": "already held"}])
    second = add(state, "retro", [proposal("board", "Three")], now=LATER)
    assert second.names == ("retro of 2026-11-24 #3",)
    found = record(state, "retro")
    assert [one.number for one in found.proposals] == [1, 2, 3]
    assert [run.proposals for run in found.runs] == [(1, 2), (3,)]
    assert [entry.number for entry in found.refuted] == [1]


def test_a_run_that_is_not_in_the_form_is_refused_and_writes_nothing(
    tmp_path: Path,
) -> None:
    workspace(tmp_path)
    good = {"area": "lessons", "move": "A", "body": "B", "source": "C", "where": "D"}
    runs = (
        "not json",
        json.dumps({"read": "the tasks", "proposals": [], "extra": 1}),
        json.dumps({"read": "  ", "proposals": []}),
        json.dumps({"read": "x", "proposals": [{**good, "move": "two\nlines"}]}),
        json.dumps({"read": "x", "proposals": [{**good, "area": "Two Words"}]}),
        json.dumps({"read": "x", "proposals": [{**good, "body": ""}]}),
    )
    codes = [
        refusal(
            lem(
                "proposals",
                "add",
                "--kind",
                "retro",
                "--file",
                "-",
                stdin=run,
                cwd=tmp_path,
            )
        )
        for run in runs
    ]
    assert [code["code"] for code in codes] == [
        "form",
        "form",
        "run-read",
        "run-proposal",
        "form",
        "run-proposal",
    ]
    assert not (tmp_path / ".lem" / "state" / "retros").exists()
    wrong_day = lem(
        "proposals",
        "add",
        "--kind",
        "night",
        "--date",
        "24-11",
        "--file",
        "-",
        cwd=tmp_path,
    )
    assert refusal(wrong_day)["code"] == "date"


def test_a_record_that_does_not_read_is_refused_with_the_form(tmp_path: Path) -> None:
    state = state_of(tmp_path)
    add(state, "retro", [proposal("lessons", "One")])
    path = days.path_of(state, "retro", DAY)
    body = json.loads(path.read_text())
    body["proposals"][0]["number"] = 2
    path.write_text(json.dumps(body))
    with pytest.raises(Refusal) as caught:
        listing.listed(state)
    assert "the numbers go 1, 2, 3 in order" in caught.value.why
    assert "`refuted` (`number`, `reason`, `day`)" in caught.value.fix
    path.write_text("{")
    assert refusal(lem("proposals", "list", cwd=tmp_path))["code"] == "proposals-record"


def test_a_retro_file_in_the_form_of_the_question_page_is_refused_with_the_form(
    tmp_path: Path,
) -> None:
    state = state_of(tmp_path)
    (state / "retros").mkdir()
    page = {"prompt": "the retro of 2026-11-24", "questions": [{"id": "q1"}]}
    (state / "retros" / "2026-11-24.json").write_text(json.dumps(page))
    with pytest.raises(Refusal) as caught:
        listing.listed(state)
    assert "it does not read" in caught.value.why
    assert "only lem proposals writes one" in caught.value.fix


def test_a_morning_whose_reviewer_did_not_finish_is_read_on_the_next(
    tmp_path: Path,
) -> None:
    state = state_of(tmp_path)
    eleven(state)
    judge(state, [{"proposal": "retro of 2026-11-24 #1", "refuted": "held already"}])
    add(state, "retro", [proposal("lessons", "Next")], day=TODAY, now=LATER)
    found = listing.listed(state)
    assert [one.name for one in found.undecided] == [
        "night of 2026-11-24 #1",
        *(f"retro of 2026-11-24 #{n}" for n in range(2, 11)),
        "retro of 2026-11-25 #1",
    ]
    assert found.newest["retro"] is not None
    assert found.newest["retro"].date == TODAY
    assert found.newest["night"] is not None
    assert found.newest["night"].at == MORNING


def test_the_list_gives_every_refuted_one_of_every_day_with_its_day(
    tmp_path: Path,
) -> None:
    state = state_of(tmp_path)
    eleven(state)
    judge(state, [{"proposal": "retro of 2026-11-24 #2", "refuted": "no source"}])
    add(state, "night", [proposal("board", "Later")], day=TODAY, now=LATER)
    later = TODAY + dt.timedelta(days=1)
    judge(state, [{"proposal": "night of 2026-11-25 #1", "refuted": "no"}], today=later)
    found = msgspec.to_builtins(listing.listed(state))
    assert [(one["name"], one["day"]) for one in found["refuted"]] == [
        ("retro of 2026-11-24 #2", "2026-11-25"),
        ("night of 2026-11-25 #1", "2026-11-26"),
    ]
    assert found["refuted"][0]["reason"] == "no source"


def test_the_passed_ones_become_one_item_for_each_area_and_the_refuted_ones_their_own(
    tmp_path: Path,
) -> None:
    state = state_of(tmp_path)
    eleven(state)
    passed = [
        {"proposal": f"retro of 2026-11-24 #{n}", "passed": "lessons"}
        for n in range(1, 6)
    ]
    passed += [
        {"proposal": f"retro of 2026-11-24 #{n}", "passed": "board"} for n in (7, 8, 9)
    ]
    passed += [{"proposal": "night of 2026-11-24 #1", "passed": "tests"}]
    refuted = [
        {"proposal": "retro of 2026-11-24 #6", "refuted": "a lesson already holds it"},
        {"proposal": "retro of 2026-11-24 #10", "refuted": "the board shows it"},
    ]
    titles = {"lessons": "Lessons", "board": "The board", "tests": "The tests"}
    judged = judge(state, [*passed, *refuted], titles)
    assert [(made.area, len(made.proposals)) for made in judged.items_made] == [
        ("lessons", 5),
        ("board", 3),
        ("tests", 1),
    ]
    assert judged.refuted == ("retro of 2026-11-24 #6", "retro of 2026-11-24 #10")
    lessons = item_files.file_of(state, judged.items_made[0].path)
    text = lessons.read_text()
    assert judged.items_made[0].path == ".lem/state/backlog/lessons.md"
    assert text.startswith("---\nworth: later\nwhere: skills/lem/stages/learn.md\n")
    assert "The reviewer passed 5 proposals about lessons on 2026-11-25:" in text
    assert "## Lesson 3" in text
    assert heads.head_of(text).proposals[:2] == (
        "retro of 2026-11-24 #1",
        "retro of 2026-11-24 #2",
    )
    found = record(state, "retro")
    assert {entry.number for entry in found.passed} == {1, 2, 3, 4, 5, 7, 8, 9}
    assert {entry.number: entry.reason for entry in found.refuted} == {
        6: "a lesson already holds it",
        10: "the board shows it",
    }
    assert listing.listed(state).undecided == ()


def test_no_item_of_an_area_on_a_morning_where_nothing_passed(tmp_path: Path) -> None:
    state = state_of(tmp_path)
    add(state, "retro", [proposal("lessons", "One")])
    judged = judge(state, [{"proposal": "retro of 2026-11-24 #1", "refuted": "no"}])
    assert judged.items_made == ()
    backlog = sorted(path.name for path in (state / "backlog").iterdir())
    assert backlog == ["one.md"]
    assert heads.head_of((state / "backlog" / "one.md").read_text()).worth == "no"


def test_an_item_name_that_is_taken_gets_the_next_number(tmp_path: Path) -> None:
    state = state_of(tmp_path)
    (state / "backlog").mkdir()
    (state / "backlog" / "lessons.md").write_text("---\nworth: later\n---\n# Lessons\n")
    add(state, "retro", [proposal("lessons", "One")])
    judged = judge(
        state,
        [{"proposal": "retro of 2026-11-24 #1", "passed": "lessons"}],
        {"lessons": "Lessons"},
    )
    assert judged.items_made[0].path == ".lem/state/backlog/lessons-2.md"


def test_a_proposal_judged_once_is_not_judged_again_and_a_wrong_verdict_writes_nothing(
    tmp_path: Path,
) -> None:
    state = state_of(tmp_path)
    eleven(state)
    judge(state, [{"proposal": "retro of 2026-11-24 #1", "refuted": "no"}])
    before = record(state, "retro")
    wrong = (
        [{"proposal": "retro of 2026-11-24 #1", "refuted": "again"}],
        [{"proposal": "retro of 2026-11-24 #2", "passed": "lessons"}],
        [{"proposal": "retro of 2026-11-24 #99", "refuted": "no"}],
        [{"proposal": "retro of 2026-11-30 #1", "refuted": "no"}],
        [{"proposal": "the second one", "refuted": "no"}],
        [{"proposal": "retro of 2026-11-24 #2"}],
        [
            {"proposal": "retro of 2026-11-24 #2", "refuted": "no"},
            {"proposal": "retro of 2026-11-24 #2", "refuted": "no"},
        ],
        [],
    )
    codes = []
    for given in wrong:
        with pytest.raises(Refusal) as caught:
            judge(state, given)
        codes.append(caught.value.code)
    assert codes == [
        "verdict-again",
        "verdict-titles",
        "verdict-number",
        "verdict-record",
        "verdict-name",
        "verdict-form",
        "verdict-twice",
        "verdict-none",
    ]
    assert record(state, "retro") == before
    assert [path.name for path in (state / "backlog").iterdir()] == ["lesson-1.md"]


def test_criterion_3_a_refuted_proposal_is_a_worth_no_item_that_holds_its_reason(
    tmp_path: Path,
) -> None:
    state = state_of(tmp_path)
    eleven(state)
    judged = judge(
        state, [{"proposal": "retro of 2026-11-24 #6", "refuted": "rule 4 holds it"}]
    )
    (against,) = judged.decided_against
    assert against.proposal == "retro of 2026-11-24 #6"
    text = item_files.file_of(state, against.path).read_text()
    head = heads.head_of(text)
    assert (head.worth, head.proposals) == ("no", ("retro of 2026-11-24 #6",))
    assert "# Lesson 6\n" in text
    assert "The reviewer refuted retro of 2026-11-24 #6 on 2026-11-25." in text
    assert "From the retro of 2026-11-24, proposal 6." in text
    assert text.rstrip().endswith("Decided against: rule 4 holds it")


def test_a_verdict_cut_off_before_its_record_finds_its_item_again_and_writes_it_in_place(
    tmp_path: Path,
) -> None:
    state = state_of(tmp_path)
    add(state, "retro", [proposal("lessons", "One")])
    path = days.path_of(state, "retro", DAY)
    before = path.read_bytes()
    judge(state, [{"proposal": "retro of 2026-11-24 #1", "refuted": "first reason"}])
    path.write_bytes(before)
    judge(state, [{"proposal": "retro of 2026-11-24 #1", "refuted": "second reason"}])
    assert [path.name for path in (state / "backlog").iterdir()] == ["one.md"]
    text = (state / "backlog" / "one.md").read_text()
    assert text.rstrip().endswith("Decided against: second reason")


def test_a_retry_that_passes_a_proposal_whose_refute_was_cut_off_removes_the_refuted_item(
    tmp_path: Path,
) -> None:
    state = state_of(tmp_path)
    add(state, "retro", [proposal("lessons", "One")])
    path = days.path_of(state, "retro", DAY)
    before = path.read_bytes()
    judge(state, [{"proposal": "retro of 2026-11-24 #1", "refuted": "no"}])
    path.write_bytes(before)
    judge(
        state,
        [{"proposal": "retro of 2026-11-24 #1", "passed": "lessons"}],
        {"lessons": "Lessons"},
    )
    assert [path.name for path in (state / "backlog").iterdir()] == ["lessons.md"]


def test_a_record_with_a_refuted_entry_and_no_item_still_reads_and_takes_verdicts(
    tmp_path: Path,
) -> None:
    state = state_of(tmp_path)
    add(state, "retro", [proposal("lessons", "One"), proposal("lessons", "Two")])
    judge(state, [{"proposal": "retro of 2026-11-24 #1", "refuted": "no"}])
    (state / "backlog" / "one.md").unlink()
    judge(state, [{"proposal": "retro of 2026-11-24 #2", "refuted": "no"}])
    found = listing.listed(state)
    assert [one.name for one in found.refuted] == [
        "retro of 2026-11-24 #1",
        "retro of 2026-11-24 #2",
    ]


def passed_item(state: Path) -> str:
    """A retro whose two lessons passed into one item; the item's path."""
    add(state, "retro", [proposal("lessons", "One"), proposal("lessons", "Two")])
    judged = judge(
        state,
        [
            {"proposal": "retro of 2026-11-24 #1", "passed": "lessons"},
            {"proposal": "retro of 2026-11-24 #2", "passed": "lessons"},
        ],
        {"lessons": "Lessons"},
    )
    return judged.items_made[0].path


def test_a_drop_removes_the_file_at_once_and_keeps_the_drop_in_the_retros_record(
    tmp_path: Path,
) -> None:
    state = state_of(tmp_path)
    path = passed_item(state)
    dropped = result(lem("proposals", "drop", path, cwd=tmp_path))
    assert dropped["item"] == path
    assert dropped["proposals"] == ["retro of 2026-11-24 #1", "retro of 2026-11-24 #2"]
    assert not item_files.file_of(state, path).exists()
    found = record(state, "retro")
    assert [(one.number, one.said, one.item_path) for one in found.dropped] == [
        (1, "the owner dropped it", path),
        (2, "the owner dropped it", path),
    ]
    listed = listing.listed(state)
    assert [one.name for one in listed.dropped] == list(dropped["proposals"])
    gone = refusal(lem("proposals", "drop", path, cwd=tmp_path))
    assert gone["code"] == "item-gone"


def test_a_drop_is_refused_while_a_task_that_has_not_ended_holds_the_item(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path)
    path = passed_item(where.state)
    made(where, "do-the-lessons", backlog_item=path)
    held = refusal(lem("proposals", "drop", path, cwd=tmp_path))
    assert held["code"] == "item-held"
    assert "do-the-lessons (queued)" in held["why"]
    assert item_files.file_of(where.state, path).is_file()


def test_a_task_with_no_state_yet_holds_the_item_and_one_that_ended_does_not(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path)
    path = passed_item(where.state)
    made(where, "shapes-it", backlog_item=path, status="shaping")
    assert refusal(lem("proposals", "drop", path, cwd=tmp_path))["code"] == "item-held"
    (where.state / "tasks" / "shapes-it" / "task.json").unlink()
    made(where, "dropped-it", backlog_item=path, status="dropped")
    assert result(lem("proposals", "drop", path, cwd=tmp_path))["item"] == path


def test_a_path_outside_the_state_folders_backlog_is_refused(tmp_path: Path) -> None:
    workspace(tmp_path)
    for given in ("docs/backlog/x.md", ".lem/state/backlog/.md", "", "../a.md"):
        refused = refusal(lem("proposals", "drop", given, cwd=tmp_path))
        assert refused["code"] == "not-reviewer-item", given


def test_the_reviewers_item_is_its_path_from_the_checkout_or_whole_under_it(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path)
    path = passed_item(where.state)
    whole = f"{tmp_path.resolve()}/{path}"
    dropped = result(lem("proposals", "drop", f"  {whole}\n", cwd=tmp_path))
    assert dropped["item"] == path
    outside = refusal(lem("proposals", "drop", f"/elsewhere/{path}", cwd=tmp_path))
    assert outside["code"] == "not-reviewer-item"


def test_a_drop_of_a_refuted_item_is_refused_as_decided_against_already(
    tmp_path: Path,
) -> None:
    state = state_of(tmp_path)
    add(state, "retro", [proposal("lessons", "One")])
    judged = judge(state, [{"proposal": "retro of 2026-11-24 #1", "refuted": "no"}])
    path = judged.decided_against[0].path
    assert refusal(lem("proposals", "drop", path, cwd=tmp_path))["code"] == (
        "decided-against"
    )
    (state / "backlog" / "hand.md").write_text("# By hand\n")
    unnamed = refusal(
        lem("proposals", "drop", ".lem/state/backlog/hand.md", cwd=tmp_path)
    )
    assert unnamed["code"] == "item-unnamed"


def test_task_open_refuses_the_path_of_an_item_the_owner_dropped(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path)
    path = passed_item(where.state)
    result(lem("proposals", "drop", path, cwd=tmp_path))
    asked = opening.Asked(slug="do-the-lessons", ask=path)
    with pytest.raises(Refusal) as caught:
        opening.item_of(where, asked)
    assert caught.value.code == "item-gone"


def test_the_drop_takes_the_proposals_lock_and_never_the_workspace_lock(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path)
    path = passed_item(where.state)
    with locks.held(places.locks_folder(where.state) / claims.LOCK):
        dropped = lem("proposals", "drop", path, cwd=tmp_path)
    assert result(dropped)["item"] == path
    assert (where.state / days.LOCK).is_file()


def test_the_whole_round_runs_from_the_command_line(tmp_path: Path) -> None:
    workspace(tmp_path)
    run = {
        "read": "the tasks since the last retro",
        "proposals": [
            {
                "area": "lessons",
                "move": "Ask first",
                "body": "Why",
                "source": "S",
                "where": "W",
            }
        ],
    }
    spec = tmp_path / "run.json"
    spec.write_text(json.dumps(run))
    added = result(
        lem(
            "proposals",
            "add",
            "--kind",
            "retro",
            "--date",
            "2026-11-24",
            "--file",
            str(spec),
            cwd=tmp_path,
        )
    )
    assert added["names"] == ["retro of 2026-11-24 #1"]
    listed = result(lem("proposals", "list", cwd=tmp_path))
    assert [one["name"] for one in listed["undecided"]] == ["retro of 2026-11-24 #1"]
    verdict = {
        "verdicts": [{"proposal": "retro of 2026-11-24 #1", "passed": "lessons"}],
        "titles": {"lessons": "Lessons"},
    }
    judged = result(
        lem(
            "proposals",
            "verdict",
            "--file",
            "-",
            stdin=json.dumps(verdict),
            cwd=tmp_path,
        )
    )
    assert judged["items"][0]["path"] == ".lem/state/backlog/lessons.md"
    assert result(lem("proposals", "list", cwd=tmp_path))["passed"][0]["there"] is True
