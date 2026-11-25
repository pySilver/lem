"""What the stage texts of a task's shape hand to its commands."""

from lem.kernel import paths

NEW = paths.root() / "skills" / "lem" / "stages" / "new.md"


def test_a_plan_asked_for_opens_with_plan_only() -> None:
    lines = NEW.read_text(encoding="utf-8").splitlines()
    opens = [line.strip() for line in lines if line.strip().startswith("lem task open")]
    assert any("/lem plan" in line and "--plan-only" in line for line in opens)
