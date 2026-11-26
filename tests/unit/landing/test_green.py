"""Green: each of the seven conditions, the reason each unmet one gives in the words of today's
pull request (`main:tests/unit/test_land_text.py`), and the careful call that makes a fast task
a person's to read."""

from msgspec.structs import replace

from lem.model.landing import careful, green, green_owner, propose_careful
from lem.model.landing.propose_facts import Facts, Settings
from lem.records.approvals import Silent
from lem.records.landing.checks import CriterionCheck, Lowered, Outcome
from lem.records.landing.review import Counts
from lem.records.task import Shape
from lem.records.work import Plan
from unit.landing.proposals import (
    FACTS,
    LATER,
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
from unit.landing.worlds import CHECKED, MOMENT, REVIEWED


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
    both = replace(other, task=replace(other.task, mode="alone"))
    assert green.reasons(both, ())[0].endswith("while the task ran without the owner")
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
    left = replace(REVIEWED, findings=(), counts=Counts(must_fix=1), to_file=())
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


def test_two_silent_attempts_after_a_review_of_another_tip_are_not_green() -> None:
    older = replace(REVIEWED, tip="9" * 40)
    silent = replace(REVIEWED, attempt=2, answered=())
    record = with_landing(small(), reviews=(older, silent, replace(silent, attempt=3)))
    assert green.reasons(record, ()) == (
        "not reviewed: the review was started twice and no source answered",
    )


def test_a_lowered_bar_with_no_reason_names_that_gap() -> None:
    lowered = Lowered(path="tests/t.py", how="a test removed")
    record = with_landing(small(), checked=replace(CHECKED, lowered=(lowered,)))
    assert green.reasons(record, ()) == (
        (
            "the bar is lower in `tests/t.py` (a test removed). The builder: no reason given. "
            "No review said anything of it."
        ),
    )


def test_branch_provided_checks_name_every_regular_command_in_order() -> None:
    run = Outcome(
        command="ruff check", exit=0, last="ok", output="checks/1.log", passed=True
    )
    serial = replace(run, command="make e2e", serial=True)
    two = replace(run, command="pytest")
    checked = replace(CHECKED, own_checks=True, outcomes=(run, serial, two))
    found = green.reasons(with_landing(small(), checked=checked), ())
    assert found == (
        (
            "the checks came with this change: the main checkout's settings name no command "
            "of the checks, and the branch's .lem/settings.toml brings `ruff check`, `pytest`. "
            "Read the checks once: every later task is checked by them"
        ),
    )


def test_the_criteria_check_must_show_both_a_red_base_and_a_green_tip() -> None:
    for red, passed in ((True, False), (False, True), (False, False)):
        tried = CriterionCheck(criterion=1, red_on_base=red, green_on_tip=passed)
        record = with_landing(full(), checked=replace(CHECKED, criteria=(tried,)))
        assert green.reasons(record, ()) == (
            "criterion 1's test was not seen to fail on the base and pass on the tip",
        )


def test_a_newer_silent_persona_read_is_the_one_named_in_the_pull_request() -> None:
    record = full()
    sources = (
        Silent(name="merchant", why="no answer"),
        Silent(name="owner", why="seat unavailable"),
    )
    latest = replace(QUIET, silent=sources)
    criteria = replace(record.task.criteria, reads=(QUIET, QUIET, latest))
    record = replace(record, task=replace(record.task, criteria=criteria))
    assert green.reasons(record, ())[0] == (
        "the criteria were not read: the personas' read was started twice and nobody "
        "answered; no answer from merchant (no answer); no answer from owner (seat unavailable)"
    )


def test_a_later_owner_approval_replaces_the_approval_taken_without_the_owner() -> None:
    record = full()
    kept = replace(
        record.task.criteria, approvals=(approval("alone"), approval(number=2))
    )
    record = replace(record, task=replace(record.task, criteria=kept))
    assert green.reasons(record, ()) == ()


def test_a_criterion_uses_its_own_decision_to_explain_the_change() -> None:
    before = taken(1, "An unrelated choice", "use y", "lead")
    chosen = taken(2, "The model", "use Model X", "personas")
    choice = changed(3, "changed", 1, "Use Model X.", was="y", now="x", decision=2)
    record = full(decisions=(before, chosen, choice))
    assert green.reasons(record, ()) == (
        (
            "criterion 1 changed during the build: Use Model X, after decision 2 (The model), "
            'where the personas took "use Model X"'
        ),
    )


def test_a_resolution_does_not_count_as_the_second_round_of_the_change() -> None:
    prior = replace(REVIEWED, of="resolution")
    left = replace(REVIEWED, attempt=2, counts=Counts(must_fix=1))
    assert green.reasons(with_landing(small(), reviews=(prior, left)), ()) == (
        "the review left 1 must-fix",
    )


def test_the_last_approval_names_its_day_and_how_it_came_without_the_owner() -> None:
    record = full()
    approvals = (approval(at=MOMENT), approval("alone", number=2, at=LATER))
    criteria = replace(record.task.criteria, approvals=approvals)
    task = replace(record.task, criteria=criteria, shape=None)
    assert green_owner.approval(task) == (
        (
            f"the owner did not approve the criteria: they were approved on {LATER.date()} "
            "while the task ran without the owner"
        ),
    )


def test_a_shape_is_optional_when_the_settings_make_the_change_careful() -> None:
    record = full()
    no_shape = replace(record, task=replace(record.task, shape=None))
    malformed = careful.Seen(touched=True, base="", tip="[branch")
    local = careful.Seen(touched=True, base=None, tip="")
    assert careful.reasons(
        no_shape, careful.Edits(settings=malformed, local=local)
    ) == (
        (
            "the change leaves .lem/settings.toml in a form that does not read as TOML, so "
            "what it says is careful cannot be told"
        ),
        (
            "the change adds .lem/settings.local.toml, one machine's own settings, which git "
            "does not track: tracked, that machine's seats, naps and days the state keeps "
            "become every machine's"
        ),
    )
