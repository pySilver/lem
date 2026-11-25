"""The invariants checked before an effect (`model/landing/invariants.py`, `landing.md` H):
nothing is pushed to, merged into or deleted from a protected branch (4); a pull request that
goes into another branch is not the task's (2); no status leaves an ended state, and after the
end only the cleanup runs (6); and a merge names a tip that a passed run covers with the checks
as now (1, by the checks' own rule)."""

import pytest
from msgspec.structs import replace

from lem.model.landing import invariants, merge_evidence
from lem.model.landing.world import Rules
from unit.landing.merges import code_of, facing, opened
from unit.landing.worlds import CHECKED, OTHER, TIP

RULES = Rules(base="main", protected=("release",))


def test_nothing_is_pushed_to_merged_from_or_deleted_on_a_protected_branch() -> None:
    assert invariants.protected("docs/x", RULES, "pushes") is None
    assert invariants.protected("main", RULES, "merges") is None
    assert code_of(invariants.protected("main", RULES, "pushes")) == "protected"
    assert code_of(invariants.protected("main", RULES, "deletes")) == "protected"
    assert code_of(invariants.protected("release", RULES, "merges")) == "protected"


def test_a_pull_request_into_another_branch_is_not_the_tasks() -> None:
    assert invariants.target("main", RULES, "https://github.com/o/p/pull/1") is None
    found = invariants.target("release", RULES, "https://github.com/o/p/pull/1")
    assert code_of(found) == "target"


@pytest.mark.parametrize(
    ("status", "step", "outcome"),
    [
        ("landed", "clean", "runs"),
        ("landed", "merged", "runs"),
        ("landed", "merge", "refused"),
        ("dropped", "start", "refused"),
        ("answered", "propose", "refused"),
        ("dropped", "clean", "runs"),
        ("open", "merge", "runs"),
    ],
)
def test_after_the_end_only_the_cleanup_runs(
    status: str, step: str, outcome: str
) -> None:
    found = invariants.ended("fix-the-login", status, step)
    assert ("runs" if found is None else "refused") == outcome


def test_a_merge_names_a_tip_a_passed_run_covers_with_the_checks_as_now() -> None:
    assert merge_evidence.covered(opened(), facing(), TIP) is None
    red = opened(checked=replace(CHECKED, outcome="red"))
    assert code_of(merge_evidence.covered(red, facing(), TIP)) == "checks-changed"
    assert (
        code_of(merge_evidence.covered(opened(), facing(), OTHER)) == "checks-changed"
    )
    changed = facing(rules=Rules(base="main", commands=("make",)))
    assert code_of(merge_evidence.covered(opened(), changed, TIP)) == "checks-changed"
