"""Green: each of the seven conditions, the reason each unmet one gives in the words of today's
pull request (`main:tests/unit/test_land_text.py`), and the careful call that makes a fast task
a person's to read."""

from msgspec.structs import replace

from lem.model.landing import green, propose_careful
from lem.model.landing.propose_facts import Facts, Settings
from lem.records.landing.checks import Lowered
from lem.records.landing.review import Finding
from lem.records.task import Shape
from lem.records.work import Plan
from unit.landing.proposals import (
    FACTS,
    QUIET,
    approval,
    breaker,
    changed,
    full,
    picked,
    read,
    small,
    taken,
    with_landing,
)
from unit.landing.worlds import CHECKED, REVIEWED

MUST = Finding(
    id="r1.c1", level="must-fix", where="a", title="t", what="w", against="over"
)


def test_a_task_that_meets_the_seven_is_green_on_either_track() -> None:
    assert green.reasons(full(), ()) == ()
    assert green.reasons(small(), ()) == ()


def test_a_pick_of_the_dialectic_is_not_green_and_the_gate_and_the_personas_are() -> (
    None
):
    where = picked(1, "Where the word goes", "the first line")
    assert green.reasons(full(decisions=(where,)), ()) == (
        (
            'decision 1 was taken without the owner (Where the word goes): "the first line", '
            "by the dialectic"
        ),
    )
    votes = (
        ("the merchant, opus", "the first line"),
        ("the accountant, sol", "the first line"),
    )
    settled = (
        taken(1, "Where", "the first line", "gate"),
        taken(2, "Which", "the first line", "personas", votes=votes),
    )
    assert green.reasons(full(decisions=settled), ()) == ()


def test_one_expert_alone_is_named_as_one_and_two_as_the_experts() -> None:
    one = taken(1, "The word's case", "upper case", "experts", advisers=("fable",))
    [line] = green.reasons(full(decisions=(one,)), ())
    assert line.startswith("decision 1 was taken without the owner (The word's case)")
    assert line.endswith(", by one expert")
    two = taken(1, "Where", "b", "experts", advisers=("fable", "astra"))
    assert green.reasons(full(decisions=(two,)), ())[0].endswith(", by the experts")


def test_an_unsettled_pick_of_the_lead_is_not_green() -> None:
    pick = taken(1, "Where", "b", "lead", unsettled=True)
    assert green.reasons(full(decisions=(pick,)), ())[0].endswith(
        "the lead's pick, which no level of the ladder settled"
    )


def test_his_help_on_a_breaker_is_no_cause_nor_a_criterion_it_changed() -> None:
    lines = (
        breaker(1, "irreversible", irreversible="person"),
        taken(
            2,
            "Email the merchants",
            "send nothing",
            "owner",
            breaker=1,
            words="no email",
        ),
        changed(
            3, "removed", 2, "A second line holds the date now.", was="x", decision=2
        ),
    )
    assert green.reasons(full(decisions=lines), ()) == ()


def test_a_criterion_the_build_changed_is_not_green_with_its_reason() -> None:
    moved = changed(
        1,
        "changed",
        1,
        "y is taken by another file.",
        was="The file holds the word y.",
        now="The file holds the word the owner asked for.",
        by="personas",
        said="Both personas picked x.",
    )
    [reason] = green.reasons(full(decisions=(moved,)), ())
    assert reason == "criterion 1 changed during the build: y is taken by another file."


def test_one_removed_after_a_pick_and_one_added_by_the_lead() -> None:
    pick = picked(1, "The one-line rule", "no such rule")
    removed = changed(
        2, "removed", 2, "A second line holds the date now.", was="x", decision=1
    )
    added = changed(
        3, "added", 2, "The importer reads whole lines only.", now="y", by="lead"
    )
    found = green.reasons(full(decisions=(pick, removed, added)), ())
    assert found[0] == (
        "criterion 2 was removed during the build: A second line holds the date now, "
        'after decision 1 (The one-line rule), where the dialectic took "no such rule"'
    )
    assert found[1].startswith("criterion 2 was added during the build: The importer")
    assert found[2].startswith("decision 1 was taken without the owner")


def test_a_change_his_later_approval_took_over_is_his() -> None:
    moved = changed(1, "changed", 1, "y is taken.", was="y", now="z", by="lead")
    record = full(decisions=(moved,))
    criteria = replace(record.task.criteria, approvals=(approval(), approval(number=2)))
    record = replace(record, task=replace(record.task, criteria=criteria))
    assert green.reasons(record, ()) == ()


def test_criteria_approved_without_him_say_how() -> None:
    record = full()
    alone = replace(record.task.criteria, approvals=(approval("alone"),))
    away = replace(record, task=replace(record.task, criteria=alone, mode="alone"))
    assert green.reasons(away, ()) == (
        (
            "the owner did not approve the criteria: they were approved on 2026-11-25 while "
            "the task ran without the owner"
        ),
    )
    shape = Shape(type="feat", why="a word", track="full", someone_else=True)
    other = replace(record, task=replace(record.task, criteria=alone, shape=shape))
    assert green.reasons(other, ())[0].endswith(
        "without the owner, since someone else wrote the request"
    )
    none = replace(record.task.criteria, approvals=())
    bare = replace(record, task=replace(record.task, criteria=none))
    assert green.reasons(bare, ()) == ("nobody approved the criteria",)


def test_two_reads_nobody_answered_are_not_green_with_that_reason_first() -> None:
    record = full()
    quiet = replace(record.task.criteria, reads=(QUIET, QUIET))
    record = replace(record, task=replace(record.task, criteria=quiet))
    pick = picked(1, "Where", "a")
    record = replace(record, task=replace(record.task, decisions=(pick,)))
    found = green.reasons(record, ())
    assert found[0] == (
        "the criteria were not read: the personas' read was started twice and nobody "
        "answered; no answer from the buyer, opus (the model was at capacity)"
    )
    once = replace(record.task.criteria, reads=(read(), QUIET))
    assert not green.reasons(
        replace(record, task=replace(record.task, criteria=once)), ()
    )[0].startswith("the criteria were not read")


def test_checks_the_branch_brought_a_lowered_bar_and_a_red_run_are_not_green() -> None:
    lowered = Lowered(
        path="tests/t.py", how="a test removed", reason="it tested a dead flag."
    )
    checked = replace(CHECKED, own_checks=True, lowered=(lowered,))
    found = green.reasons(with_landing(small(), checked=checked), ())
    assert found == (
        (
            "the checks came with this change: the main checkout's settings name no command "
            "of the checks, and the branch's .lem/settings.toml brings . Read the checks once: "
            "every later task is checked by them"
        ),
        (
            "the bar is lower in `tests/t.py` (a test removed). The builder: it tested a dead "
            "flag. No review said anything of it."
        ),
    )
    answered = replace(lowered, reviewer="the flag is gone; fine.")
    said = green.reasons(
        with_landing(small(), checked=replace(CHECKED, lowered=(answered,))), ()
    )
    assert said[0].endswith("The review: the flag is gone; fine.")
    red = green.reasons(
        with_landing(small(), checked=replace(CHECKED, outcome="red")), ()
    )
    assert red == ("the checks did not pass",)


def test_a_review_that_left_a_must_fix_or_that_nobody_answered_is_not_green() -> None:
    left = replace(REVIEWED, findings=(MUST,))
    assert green.reasons(with_landing(small(), reviews=(left,)), ()) == (
        "the review left 1 must-fix",
    )
    two = (left, replace(left, attempt=2))
    assert green.reasons(with_landing(small(), reviews=two), ()) == (
        "two rounds reviewed it: the last one left 1 must-fix",
    )
    silent = replace(REVIEWED, answered=())
    assert green.reasons(with_landing(small(), reviews=(silent, silent)), ()) == (
        "not reviewed: the review was started twice and no source answered",
    )
    assert green.reasons(with_landing(small(), reviews=()), ()) == (
        "no review read the change",
    )


def test_a_criterion_whose_test_nobody_saw_fail_on_the_base_is_not_green() -> None:
    record = with_landing(full(), checked=CHECKED)
    assert green.reasons(record, ()) == (
        "criterion 1's test was not seen to fail on the base and pass on the tip",
    )


def test_a_careful_task_on_the_fast_track_is_not_green_and_on_the_standard_track_is() -> (
    None
):
    shape = Shape(type="docs", why="a word", track="small", careful=("money",))
    record = small(shape=shape)
    careful = propose_careful.why(record, FACTS)
    assert careful == ("money",)
    assert green.reasons(record, careful) == (
        (
            "careful on the fast track (money): it took the fast track, with no interview, no "
            "personas' read of its criterion and no plan, so a person reads it"
        ),
    )
    assert green.reasons(full(), ("money",)) == ()


def test_the_careful_call_names_the_shape_the_plan_the_settings_and_the_review() -> (
    None
):
    plan = Plan(path="docs/plans/p.md", careful="a charge")
    called = replace(REVIEWED, careful=True, careful_why="it charges a card.")
    record = with_landing(full(plan=plan), reviews=(called,))
    team = Settings(
        before='[branch]\nbase = "main"\n', after='[branch]\nbase = "dev"\n'
    )
    facts = Facts(changed=(".lem/settings.toml",), settings=team)
    assert propose_careful.why(record, facts) == (
        "the plan says so",
        (
            "the change edits [branch] of .lem/settings.toml, Lem's own settings, which say "
            "for every later task what is careful, what the checks run, who merges and where "
            "a task lands"
        ),
        "the review says so: it charges a card",
    )
    gone = Facts(changed=(".lem/settings.toml",), settings=Settings(before="x = 1\n"))
    assert propose_careful.why(full(), gone)[0].startswith(
        "the change removes .lem/settings.toml"
    )
    local = Facts(
        changed=(".lem/settings.local.toml",), settings=Settings(local=(False, True))
    )
    assert propose_careful.why(full(), local)[0].startswith(
        "the change adds .lem/settings.local.toml, one machine's own settings"
    )
    broken = Facts(changed=(".lem/settings.toml",), settings=Settings(after="[x\n"))
    assert "does not read as TOML" in propose_careful.why(full(), broken)[0]
