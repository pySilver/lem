"""The texts of the onboarding hold what the steps read in them: the stage's seven steps with its
three questions, the commands of this build, and the sections the profile and a persona fill.
"""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
STAGE = ROOT / "skills" / "lem" / "stages" / "init.md"
HARNESS = ROOT / "skills" / "lem" / "harness" / "claude-code"
TEMPLATES = ROOT / "skills" / "lem" / "templates"
TEXTS = (
    STAGE,
    HARNESS / "onboarding.md",
    HARNESS / "owner-steps.md",
    TEMPLATES / "profile.md",
    TEMPLATES / "persona.md",
)
# The command forms of the proof of concept that no text of this build names.
OLD = re.compile(r"lem project |/lem set |lem corrections collect |lem project$")


@pytest.mark.parametrize("path", TEXTS, ids=lambda path: path.name)
def test_each_text_names_no_command_of_the_lem_before(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    assert not text.startswith("<!-- lem: old form -->")
    assert OLD.search(text) is None


def test_the_onboarding_asks_three_questions_in_seven_steps() -> None:
    headings = re.findall(
        r"^## (\d)\. (.+)$", STAGE.read_text(encoding="utf-8"), re.MULTILINE
    )
    assert [number for number, _ in headings] == list("1234567")
    assert dict(headings)["3"] == "Three questions"


def test_the_stage_writes_the_settings_with_init_and_checks_the_machine_first() -> None:
    text = STAGE.read_text(encoding="utf-8")
    assert text.index("lem doctor") < text.index("lem init --base BRANCH --codex yes")
    assert "lem settings set corrections.collect yes --machine" in text


def test_the_profile_and_a_persona_have_the_sections_the_onboarding_fills() -> None:
    profile = re.findall(
        r"^## (.+)$", (TEMPLATES / "profile.md").read_text(), re.MULTILINE
    )
    assert profile == [
        "What it is",
        "Scale",
        "Rules every answer works within",
        "Tools and versions",
        "What a newcomer gets wrong",
        "Who to compare with",
    ]
    persona = (TEMPLATES / "persona.md").read_text()
    assert re.findall(r"^## (.+)$", persona, re.MULTILINE) == [
        "Who they are",
        "What they want",
        "What they notice",
        "What they never see",
    ]
    assert "A thin guess" in persona


def test_the_owner_steps_name_the_read_outside_the_working_directories() -> None:
    text = (HARNESS / "owner-steps.md").read_text(encoding="utf-8")
    steps = " ".join(
        text.split("**A read outside the working directories.**", 1)[1].split()
    )
    assert (
        "Claude Code asks for permission to read outside the working directories "
        "the first time a session reads a file of Lem's plugin or of its app" in steps
    )
    assert (
        "the allow rule that the row of `lem doctor` for this question names" in steps
    )
