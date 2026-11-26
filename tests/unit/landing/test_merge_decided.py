"""The task's decisions in the body of the one commit a squash makes (`model/landing/
merge_decided.py`, amendment A2 of the rebuild's roadmap): each decision of the record on a line
of its own before the line that names the task, so that the base's history keeps them after the
prune folds the task's record."""

from msgspec.structs import replace

from lem.model.landing import merge, merge_call, merge_decided
from lem.records.decisions import Breaker, CriterionChanged, Taken
from unit.landing.merges import BY_OWNER, facing, opened
from unit.landing.worlds import MOMENT, TREE

LEAD = Taken(
    id=1,
    at=MOMENT,
    what="where the login's error shows",
    chose="under the form",
    why="The form is where the eye is.",
    by="lead",
)
CHANGED = CriterionChanged(
    id=2,
    at=MOMENT,
    how="changed",
    criterion=1,
    why="The owner's note asked for the exact words",
    approval=1,
    was="The login works.",
    now="The login works with a wrong password shown.",
    by="lead",
)
STOPPED = Breaker(
    id=3,
    at=MOMENT,
    cause="irreversible",
    what="the next step drops a column.",
    document="breaker-3.md",
    handoff="handoff.md",
)


def test_the_squash_lists_each_decision_before_the_line_that_names_the_task() -> None:
    record = opened()
    record = replace(record, task=replace(record.task, decisions=(LEAD, CHANGED)))
    made = merge.decide(record, facing(), BY_OWNER, TREE)
    assert isinstance(made, merge_call.Merging)
    assert made.body == (
        "Decisions of the task:\n"
        '- where the login\'s error shows: "under the form", by the lead. The form is '
        "where the eye is.\n"
        '- criterion 1 changed: "The login works." is now "The login works with a wrong '
        "password shown.\". The owner's note asked for the exact words.\n\n"
        "Lem task: fix-the-login"
    )


def test_a_task_with_no_decision_adds_no_lines() -> None:
    assert merge_decided.block(()) is None
    made = merge.decide(opened(), facing(), BY_OWNER, TREE)
    assert isinstance(made, merge_call.Merging)
    assert made.body == "Lem task: fix-the-login"


def test_a_criterion_change_keeps_the_exact_words_on_one_line() -> None:
    choice = replace(
        CHANGED,
        was='The exact label ends with "Wait..."',
        now="First line.\nCafé\u0085Wait\u2028Here\u2029again.",
    )
    assert merge_decided.texts_of(choice) == (
        r'"The exact label ends with \"Wait...\"" is now "First line.\nCafé\u0085Wait\u2028Here\u2029again."'
    )


def test_the_squash_names_an_unsettled_lead_pick() -> None:
    picked = replace(LEAD, unsettled=True)
    assert merge_decided.line(picked) == (
        "- where the login's error shows: \"under the form\", the lead's unsettled pick. "
        "The form is where the eye is."
    )


def test_an_added_or_removed_criterion_and_a_stop_at_the_breaker_are_one_line_each() -> (
    None
):
    added = replace(CHANGED, how="added", was=None)
    removed = replace(CHANGED, how="removed", now=None)
    assert [merge_decided.line(one) for one in (added, removed, STOPPED)] == [
        (
            '- criterion 1 added: "The login works with a wrong password shown.". The '
            "owner's note asked for the exact words."
        ),
        (
            '- criterion 1 removed: "The login works.". The owner\'s note asked for the '
            "exact words."
        ),
        "- the build stopped at breaker 3: the next step drops a column.",
    ]


def test_an_absent_criterion_text_has_empty_quotes() -> None:
    assert merge_decided.quoted(None) == '""'
