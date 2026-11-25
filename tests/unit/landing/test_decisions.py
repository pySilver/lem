"""What each stage of the plain landing decides from the record and the world, and what it refuses
(`landing.md` F), with the code of the step that builds what the plain path leaves out."""

from msgspec.structs import replace

from lem.kernel.errors import Refusal
from lem.model.landing import checks, invariants, phases
from lem.model.landing.world import Rules
from unit.landing.worlds import CHECKED, PREPARED, RULES, task, world


def code_of(found: object) -> str:
    """The code of a refusal; a case fails on anything else."""
    assert isinstance(found, Refusal), found
    return found.code


def test_checks_refuse_serial_commands_and_a_red_tip_as_later_steps() -> None:
    assert checks.decide(task(**PREPARED), world()) is None
    serial = world(rules=Rules(base="main", commands=("true",), serial=("e2e",)))
    assert code_of(checks.decide(task(**PREPARED), serial)) == "not-built"
    red = task(**{**PREPARED, "checked": replace(CHECKED, outcome="red")})
    assert code_of(checks.decide(red, world())) == "not-built"
    assert checks.left(clean=True) is None
    assert code_of(checks.left(clean=False)) == "not-built"
    assert checks.inputs(RULES) != checks.inputs(Rules(base="main", commands=("make",)))


def test_nothing_is_pushed_to_merged_from_or_deleted_on_a_protected_branch() -> None:
    rules = Rules(base="main", protected=("release",))
    assert invariants.protected("docs/x", rules, "pushes") is None
    assert invariants.protected("main", rules, "merges") is None
    assert code_of(invariants.protected("main", rules, "pushes")) == "protected"
    assert code_of(invariants.protected("release", rules, "deletes")) == "protected"


def test_a_branch_reset_under_its_recorded_base_makes_the_base_due_again() -> None:
    assert phases.due(task(**PREPARED), world(base_in_tip=False)).step == "base"
