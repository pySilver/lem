"""The review before a pull request (`model/landing/review*.py`, `careful.py`): the record a
review agent writes, read in the form `prompts/review.md` gives it, the floor, the careful call,
the rounds and the silent attempts, the defects outside the change, and what the review covers
(`landing.md` C row 5, D, F `read --record`; `land.cmd_read`, `land.due_of`, `land.defects_of`
on `main`)."""

import re
from pathlib import Path
from typing import TYPE_CHECKING

import msgspec
import pytest
from msgspec.structs import replace

from lem.app.landing import review_changes, review_files
from lem.kernel.errors import Refusal
from lem.model.landing import (
    careful,
    phases,
    review,
    review_due,
    review_form,
    review_said,
)
from lem.model.landing.review_said import Named, Outside, Said
from lem.model.landing.world import Due
from lem.records.journal.landing import CarefulMissed, ReviewRound
from lem.records.journal.task import SpanMark
from lem.records.landing.checks import Lowered
from lem.records.landing.record import Landing
from lem.records.landing.review import Finding
from lem.records.landing.start import Resolution
from lem.records.task import Shape
from lem.records.work import Plan
from unit.landing.worlds import (
    BASE,
    CHECKED,
    MOMENT,
    OTHER,
    PREPARED,
    REVIEWED,
    TIP,
    task,
    world,
)

if TYPE_CHECKING:
    from lem.records.record import Record

PROMPT = (
    Path(__file__).resolve().parents[3] / "skills" / "lem" / "prompts" / "review.md"
)
FACTS = review_due.Facts(at_base=frozenset({"docs/backlog/held.md"}))
OUT = Outside(
    where="a.py:f",
    title="f drops a line",
    what="f(2) gives 1",
    against="under",
    why="a reader of the code meets it",
)
DEFECT = {"where": "a.py:f", "title": "f drops a line", "what": "f(2) gives 1"}


def said(**fields: object) -> Said:
    """A record of attempt 1 for `TIP`, a read that answered and calls the change not careful,
    with `fields` over it."""
    made = Said(
        attempt=1,
        tip=TIP,
        kind="read",
        answered=("claude",),
        careful=False,
        careful_why="it reaches no topic",
    )
    return replace(made, **fields)


def decoded(body: dict) -> Said:
    """The record from its JSON, as `read --record` reads the file."""
    return msgspec.json.decode(msgspec.json.encode(body), type=Said)


def code_of(found: object) -> str:
    return refused_of(found).code


def refused_of(found: object) -> Refusal:
    """The refusal; a case fails on anything else."""
    assert isinstance(found, Refusal), found
    return found


def due_of(found: object) -> str:
    """The step a rule says is due; a case fails on anything else."""
    assert isinstance(found, Due), found
    return found.step


def fresh() -> Record:
    """A fast-track task whose checks passed on `TIP`, with no review yet."""
    return task(**{**PREPARED, "reviews": (), "filed": ()})


def careful_task(*topics: str) -> Record:
    made = fresh()
    shape = Shape(type="docs", why="a word", track="small", careful=topics)
    return replace(made, task=replace(made.task, shape=shape))


# The record's form, against the prompt that tells the agent to write it.


def test_the_record_names_each_key_the_prompt_tells_the_review_to_write() -> None:
    step = PROMPT.read_text(encoding="utf-8").split("8. **Write two files**", 1)[1]
    told = set(re.findall(r"`([a-z_]+)`", step.split("Before you reply", 1)[0]))
    keys = {field.encode_name for field in msgspec.structs.fields(Said)}
    outside = {field.encode_name for field in msgspec.structs.fields(Outside)}
    assert keys <= told | {"bar"}
    assert {
        "attempt",
        "tip",
        "kind",
        "ran",
        "left_out",
        "answered",
        "silent",
        "must_fix",
        "should",
        "nit",
        "outside",
        "careful",
        "careful_why",
        "bar",
    } == keys
    assert outside == {"where", "title", "what", "bar", "why", "open"}
    assert outside - {"bar"} <= told | {"where", "title", "what"}


def test_a_record_with_a_key_the_prompt_does_not_name_is_refused() -> None:
    form = {"attempt": 1, "tip": TIP, "kind": "read", "answered": []}
    assert decoded(form).attempt == 1
    with pytest.raises(msgspec.ValidationError, match="findings"):
        decoded({**form, "findings": []})
    with pytest.raises(msgspec.ValidationError, match="answered"):
        decoded({"attempt": 1, "tip": TIP, "kind": "read"})


@pytest.mark.parametrize(
    ("body", "names"),
    [
        ({"kind": "deep"}, "kind"),
        ({"must_fix": -1}, "must_fix"),
        ({"nit": True}, "nit"),
        ({"answered": [""]}, "answered"),
        ({"ran": [{"name": "codex"}]}, "why"),
        ({"ran": [{"name": "codex", "why": "w", "more": 1}]}, "more"),
        ({"outside": 2}, "outside"),
        ({"outside": [{"where": "app.txt"}]}, "title"),
        ({"outside": [{**DEFECT}]}, "bar"),
        ({"outside": [{**DEFECT, "bar": "low"}]}, "bar"),
        ({"outside": [{**DEFECT, "bar": "over", "item": "docs/backlog/x.md"}]}, "item"),
        ({"outside": [{**DEFECT, "bar": "under", "why": "two\nlines"}]}, "why"),
    ],
    ids=[
        "kind-another-word",
        "count-under-0",
        "count-true",
        "answered-no-name",
        "named-no-why",
        "named-own-key",
        "outside-a-count",
        "outside-place-only",
        "outside-no-bar",
        "outside-another-bar",
        "outside-own-key",
        "outside-why-two-lines",
    ],
)
def test_a_record_of_another_form_is_refused_by_the_key_that_is_wrong(
    body: dict, names: str
) -> None:
    form = {"attempt": 1, "tip": TIP, "kind": "read", "answered": ["claude"]}
    with pytest.raises(msgspec.ValidationError, match=names):
        decoded({**form, **body})


def test_zero_is_no_defect_and_each_entry_gets_its_number_and_keeps_the_call() -> None:
    assert (
        review_said.defects(
            decoded(
                {"attempt": 2, "tip": TIP, "kind": "read", "answered": [], "outside": 0}
            )
        )
        == ()
    )
    listed = [
        {**DEFECT, "bar": "over"},
        {**DEFECT, "bar": "cheap", "why": "a comment that says the opposite"},
        {**DEFECT, "bar": "over", "open": "docs/backlog/held.md"},
    ]
    record = decoded(
        {
            "attempt": 2,
            "tip": TIP,
            "kind": "read",
            "answered": ["claude"],
            "outside": listed,
        }
    )
    found = review_outside_findings(record)
    assert [(one.id, one.against, one.why, one.open) for one in found] == [
        ("r2.1", "over", None, None),
        ("r2.2", "cheap", "a comment that says the opposite", None),
        ("r2.3", "over", None, "docs/backlog/held.md"),
    ]


def review_outside_findings(record: Said) -> tuple[Finding, ...]:
    from lem.model.landing import review_outside

    return review_outside.findings(record)


def test_under_or_cheap_with_no_why_and_an_open_that_is_no_file_at_the_base_are_refused() -> (
    None
):
    from lem.model.landing import review_outside

    for call in ("under", "cheap"):
        bare = said(
            outside=(replace(OUT, against="over"), replace(OUT, against=call, why=None))
        )
        made = review_outside.refused(bare, "docs/backlog", FACTS.at_base)
        assert made is not None
        assert (
            f'the defect r1.2 outside the change ("{OUT.title}") is {call}, and has no `why`'
            in made.why
        )
    for path in (
        "docs/backlog/gone.md",
        "docs/other/held.md",
        "docs/backlog/../backlog/held.md",
    ):
        opened = said(outside=(replace(OUT, open=path),))
        made = review_outside.refused(opened, "docs/backlog", FACTS.at_base)
        assert (
            made is not None
            and "no file of the backlog folder docs/backlog at the base" in made.why
        )
    assert (
        review_outside.refused(
            said(outside=(replace(OUT, open="docs/backlog/held.md"),)),
            "docs/backlog",
            FACTS.at_base,
        )
        is None
    )
    worded = said(outside=(replace(OUT, title="!!"),))
    assert (
        code_of(review_outside.refused(worded, "docs/backlog", FACTS.at_base))
        == "outside"
    )


# The attempt and the tip.


def test_the_record_of_another_attempt_or_tip_is_refused() -> None:
    record = fresh()
    assert code_of(review.decide(record, world(), said(attempt=2), FACTS)) == "attempt"
    again = task(**{**PREPARED, "reviews": (REVIEWED,), "filed": ()})
    sent_again = review.decide(again, world(), said(attempt=1), FACTS)
    assert isinstance(sent_again, Refusal) and "written down already" in sent_again.why
    stale = review.decide(record, world(), said(tip=OTHER), FACTS)
    assert isinstance(stale, Refusal)
    assert (
        f"the record is of the review of {OTHER[:12]}, and the branch is at {TIP[:12]} now"
        in stale.why
    )
    for short in ("a" * 9, "HEAD"):
        bad = review_form.tip_refused(short, TIP, "fix-the-login")
        assert bad is not None and "40 hex digits" in bad.why
    assert review_form.tip_refused(TIP, TIP, "fix-the-login") is None


# The floor and the careful call.


def test_a_review_is_refused_under_its_floor_without_a_careful_call_or_careful_and_not_full() -> (
    None
):
    record = fresh()
    made = review.decide(record, world(), said(outside=(OUT,), nit=2), FACTS)
    assert not isinstance(made, Refusal)
    assert (made.attempt, made.tip, made.to_file, made.floor) == (
        1,
        TIP,
        ("r1.1",),
        "read",
    )
    assert [finding.id for finding in made.findings] == ["r1.c1", "r1.c2", "r1.1"]
    assert (
        code_of(review.decide(record, world(), said(careful=None), FACTS))
        == "no-careful-call"
    )
    assert (
        code_of(review.decide(record, world(), said(careful_why=None), FACTS))
        == "no-careful-call"
    )
    called = review.decide(record, world(), said(careful=True), FACTS)
    assert code_of(called) == "careful-not-full"
    careful_one = careful_task("a customer is charged")
    under = review.decide(
        careful_one,
        world(),
        said(),
        review_due.Facts(careful=careful.reasons(careful_one, careful.Edits())),
    )
    assert code_of(under) == "under-floor"
    assert (
        "the project's full set at the least (the request is careful: a customer is charged)"
        in refused_of(under).why
    )


def test_a_round_names_what_it_ran_and_a_full_set_leaves_nothing_out() -> None:
    record = fresh()
    assert code_of(review.decide(record, world(), said(kind="round"), FACTS)) == "ran"
    ran = (Named(name="security", why="the diff reads a token"),)
    assert not isinstance(
        review.decide(record, world(), said(kind="round", ran=ran), FACTS), Refusal
    )
    left = said(kind="full", ran=ran, left_out=(Named(name="docs", why="no prose"),))
    assert code_of(review.decide(record, world(), left, FACTS)) == "left-out"
    nobody = said(
        answered=(), must_fix=1, silent=(Named(name="codex", why="at capacity"),)
    )
    assert code_of(review.decide(record, world(), nobody, FACTS)) == "answered"


def test_the_floor_is_full_when_careful_a_round_for_a_large_plan_or_after_a_must_fix() -> (
    None
):
    record = fresh()
    assert review_due.floor(record, (), resolution=False).kind == "read"
    assert (
        review_due.floor(record, ("the plan says so: money",), resolution=False).kind
        == "full"
    )
    large = replace(
        record, task=replace(record.task, plan=Plan(path="plan.md", tasks=4))
    )
    floor = review_due.floor(large, (), resolution=False)
    assert (floor.kind, floor.why) == ("round", "the plan has 4 tasks, more than three")
    three = replace(
        record, task=replace(record.task, plan=Plan(path="plan.md", tasks=3))
    )
    assert review_due.floor(three, (), resolution=False).kind == "read"
    must = replace(
        REVIEWED,
        findings=(
            Finding(
                id="r1.c1",
                level="must-fix",
                where="r",
                title="t",
                what="w",
                against="over",
            ),
        ),
    )
    after = task(**{**PREPARED, "reviews": (must,), "filed": ()})
    assert review_due.floor(after, (), resolution=False).kind == "round"
    assert phases.due(after, world()).step == "read"
    assert (
        code_of(review.decide(after, world(), said(attempt=2), FACTS)) == "under-floor"
    )
    assert review_due.floor(after, (), resolution=True).kind == "read"
    assert review_due.floor(after, ("x",), resolution=True).kind == "full"


def test_each_reason_the_request_is_careful_in_main_s_order() -> None:
    made = careful_task("a customer is charged")
    planned = replace(
        made, task=replace(made.task, plan=Plan(path="p.md", careful="money moves"))
    )
    called = replace(REVIEWED, careful=True, careful_why="billing/total sets the price")
    reviewed = replace(planned, landing=replace(Landing(), reviews=(called,)))
    settings = careful.Seen(
        touched=True,
        base='[branch]\nland = "owner"\n',
        tip='[branch]\nland = "agent"\n',
    )
    found = careful.reasons(reviewed, careful.Edits(settings=settings))
    assert found == (
        "a customer is charged",
        "the plan says so: money moves",
        "the change edits [branch] of .lem/settings.toml, " + careful.GUARDS,
        "the review says so: billing/total sets the price",
    )


@pytest.mark.parametrize(
    ("seen", "says"),
    [
        (careful.Seen(), None),
        (
            careful.Seen(touched=True, base="[flow]\n", tip=None),
            "the change removes .lem/settings.toml",
        ),
        (
            careful.Seen(touched=True, base="a = 1\n", tip="a = 1 # x\n"),
            "the text of .lem/settings.toml, and no value in it",
        ),
        (careful.Seen(touched=True, base="", tip="[flow\n"), "does not read as TOML"),
        (
            careful.Seen(
                touched=True,
                base="[flow]\ntopics = []\n",
                tip='[flow]\ntopics = ["x"]\n[checks]\n',
            ),
            "[checks] and [flow] of .lem/settings.toml",
        ),
    ],
    ids=["untouched", "removed", "text-only", "not-toml", "tables"],
)
def test_every_edit_of_lem_s_own_settings_is_careful_by_this_code(
    seen: careful.Seen, says: str | None
) -> None:
    found = careful.settings_reason(seen)
    assert (found is None) if says is None else (found is not None and says in found)


def test_a_commit_of_one_machine_s_own_settings_is_careful_and_says_how() -> None:
    assert careful.local_reason(careful.Seen()) is None
    for seen, how in (
        (careful.Seen(touched=True, tip="x"), "adds"),
        (careful.Seen(touched=True, base="x"), "removes"),
        (careful.Seen(touched=True, base="x", tip="y"), "changes"),
    ):
        said_now = careful.local_reason(seen)
        assert said_now is not None and said_now.startswith(
            f"the change {how} .lem/settings.local.toml"
        )


# What the review holds: the rounds, the silent attempts, and what it covers.


def test_two_rounds_go_on_to_the_owner_with_what_they_left_open() -> None:
    must = Finding(
        id="r1.c1", level="must-fix", where="r", title="t", what="w", against="over"
    )
    first = replace(REVIEWED, findings=(must,), to_file=())
    second = replace(first, attempt=2, kind="round", floor="round")
    record = task(**{**PREPARED, "reviews": (first, second), "filed": ()})
    held = review.holds(record, world())
    assert held.why == "two rounds reviewed it: the last one left 1 must-fix"
    third = said(attempt=3, kind="round", ran=(Named(name="p", why="w"),))
    assert not isinstance(review.decide(record, world(), third, FACTS), Refusal)


def test_a_review_nobody_answered_is_started_once_more_then_the_request_goes_on() -> (
    None
):
    quiet = (Named(name="the review agent", why="it ended with no files"),)
    silent = said(answered=(), silent=quiet, careful=None, careful_why=None)
    assert review_form.silent(silent)
    assert not review_form.silent(said(answered=(), silent=()))
    assert not review_form.silent(replace(silent, must_fix=1))
    record = fresh()
    first = review.decide(record, world(), silent, FACTS)
    assert not isinstance(first, Refusal) and first.careful is None
    once = task(**{**PREPARED, "reviews": (first,), "filed": ()})
    assert due_of(review.holds(once, world())) == "read"
    second = review.decide(once, world(), replace(silent, attempt=2), FACTS)
    assert not isinstance(second, Refusal)
    twice = task(**{**PREPARED, "reviews": (first, second), "filed": ()})
    assert review.holds(twice, world()).why.startswith(
        "not reviewed: two attempts in a row"
    )
    assert phases.due(twice, world()).step == "propose"


def test_the_review_covers_its_tip_and_the_commit_file_made_after_it() -> None:
    record = task(**PREPARED)
    assert review.holds(record, world()).why.startswith("the newest review covers")
    moved = review.holds(record, world(tip=OTHER))
    assert moved.why == "nobody reviewed what changed after it"
    filed_after = replace(CHECKED, tip=OTHER, items_after=("docs/backlog/x.md",))
    after = task(**{**PREPARED, "checked": filed_after})
    assert review.holds(after, world(tip=OTHER)).why.startswith(
        "the newest review covers"
    )
    late = replace(filed_after, at=MOMENT.replace(hour=11))
    assert (
        due_of(review.holds(task(**{**PREPARED, "checked": late}), world(tip=OTHER)))
        == "read"
    )


def test_a_resolution_of_a_conflict_gets_one_read_of_what_it_changed() -> None:
    resolution = Resolution(files=("a.py",), before=OTHER, after=TIP, base=BASE)
    record = task(**{**PREPARED, "resolution": resolution})
    assert review.holds(record, world()).why.startswith("a builder resolved a conflict")
    made = review.decide(record, world(), said(attempt=2), FACTS)
    assert not isinstance(made, Refusal)
    assert (made.of, made.scope, made.floor) == ("resolution", "resolution", "read")
    changed = review_changes.recorded(record, review=made, said=said(attempt=2))
    assert changed.landing is not None and changed.landing.resolution is not None
    assert changed.landing.resolution.read == 2
    assert review.holds(changed, world()).why.startswith("the newest review covers")


# What a recorded review writes.


def test_the_brief_starts_the_review_s_span_once_and_the_record_ends_it() -> None:
    record = fresh()
    started = review_changes.started(record, attempt=1, now=MOMENT)
    assert review_changes.started(started, attempt=1, now=MOMENT) == started
    assert [(span.name, span.job, span.end) for span in started.task.spans] == [
        ("review", "attempt 1", None)
    ]
    made = review.decide(started, world(), said(), FACTS)
    assert not isinstance(made, Refusal)
    done = review_changes.recorded(started, review=made, said=said())
    assert done.task.spans[0].end == made.at
    kinds = [type(entry) for entry in done.journal]
    assert kinds == [SpanMark, ReviewRound, SpanMark]


def test_a_careful_call_the_plan_did_not_make_is_noted_once() -> None:
    record = fresh()
    full = said(
        kind="full",
        careful=True,
        careful_why="billing/total sets the price",
        ran=(Named(name="all", why="careful"),),
    )
    made = review.decide(record, world(), full, FACTS)
    assert not isinstance(made, Refusal)
    once = review_changes.recorded(record, review=made, said=full)
    missed = [entry for entry in once.journal if isinstance(entry, CarefulMissed)]
    assert [(entry.round, entry.why) for entry in missed] == [
        (1, "billing/total sets the price")
    ]
    twice = review_changes.missed(once, made)
    assert twice == once
    planned = replace(
        record, task=replace(record.task, plan=Plan(path="p.md", careful="money"))
    )
    assert not [
        entry
        for entry in review_changes.recorded(planned, review=made, said=full).journal
        if isinstance(entry, CarefulMissed)
    ]


def test_a_lowered_bar_the_record_says_nothing_of_is_refused_and_its_word_is_kept() -> (
    None
):
    lowered = replace(
        CHECKED,
        lowered=(
            Lowered(path="t.py", how="a test removed", reason="it tested nothing"),
        ),
    )
    record = task(**{**PREPARED, "reviews": (), "filed": (), "checked": lowered})
    facts = review_due.Facts(lowered=("t.py",))
    refused = review.decide(record, world(), said(), facts)
    assert code_of(refused) == "bar" and "t.py" in refused_of(refused).why
    worded = said(lowered=(Named(name="t.py", why="the reason holds"),))
    made = review.decide(record, world(), worded, facts)
    assert not isinstance(made, Refusal)
    kept = review_changes.recorded(record, review=made, said=worded)
    assert kept.landing is not None and kept.landing.checked is not None
    assert kept.landing.checked.lowered[0].reviewer == "the reason holds"


# The file `--record` names.


def test_the_record_file_is_found_from_the_working_directory_first_then_the_task_folder(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    here, folder = tmp_path / "main", tmp_path / "tasks" / "gift-note"
    (folder / "reviews").mkdir(parents=True)
    here.mkdir()
    (folder / "reviews" / "review-1.json").write_text("{}")
    monkeypatch.chdir(here)
    assert (
        review_files.task_file("reviews/review-1.json", folder)
        == folder / "reviews" / "review-1.json"
    )
    (here / "reviews").mkdir()
    (here / "reviews" / "review-1.json").write_text("{}")
    assert (
        review_files.task_file("reviews/review-1.json", folder)
        == here / "reviews" / "review-1.json"
    )
    absolute = folder / "reviews" / "review-1.json"
    assert review_files.task_file(str(absolute), folder) == absolute
    with pytest.raises(Refusal) as missing:
        review_files.task_file("notes.md", folder)
    assert (
        str(here / "notes.md") in missing.value.why
        and str(folder / "notes.md") in missing.value.why
    )
    with pytest.raises(Refusal):
        review_files.task_file(str(here / "missing.json"), folder)


def test_a_record_that_does_not_read_is_refused_with_its_form(tmp_path: Path) -> None:
    bad = tmp_path / "review-1.json"
    bad.write_text("{not json")
    with pytest.raises(Refusal) as refused:
        review_files.said(bad)
    assert refused.value.code == "review-file"
    assert "careful_why" in refused.value.fix


def test_no_change_is_proposed_without_a_review() -> None:
    record = fresh()
    assert phases.due(record, world()).step == "read"
    assert review.holds(record, world()).why == "no review read the change yet"


def test_the_review_is_not_due_before_the_checks_hold() -> None:
    unchecked = task(**{**PREPARED, "checked": None, "reviews": (), "filed": ()})
    assert phases.due(unchecked, world()).step == "checks"
    other = replace(CHECKED, inputs="another digest of the commands")
    changed = task(**{**PREPARED, "checked": other, "reviews": (), "filed": ()})
    assert phases.due(changed, world()).step == "checks"
