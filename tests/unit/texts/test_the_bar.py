"""The bar of a backlog item, written in one place (`main:tests/unit/test_the_bar.py`).

Rule 6 of `agents/lem-builder.md` holds the bar: the sentence that says which defect outside a
task is worth an item with `worth: later`, its limit (Lem's agents only), what makes a defect
cheap, and the three outcomes of a defect no open item holds. The polish pass, the fast track's
builder, the review and the reviewer of the night's and the retro's proposals each read that file
whole, so every other file of Lem names the bar of rule 6 and copies no part of its sentence: a
copy would drift from the rule the agents read.
"""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
BUILDER = ROOT / "agents/lem-builder.md"
# The bar, word for word as rule 6 gives it.
BAR = (
    "An item with `worth: later` is filed only for a defect over the bar: "
    "it confuses a user, breaks a contract, damages data or costs money, and it "
    "happens today; or the owner said it is worth an item."
)
# The parts of the bar a copy would carry, each one rare enough in Lem's prose that it is found
# nowhere else.
PARTS = (
    "confuses a user",
    "breaks a contract",
    "damages data",
    "costs money",
    "happens today",
    "said it is worth an item",
)
# The files that send an agent to judge a defect outside a task, or say what that agent does.
NAMERS = (
    "skills/lem/prompts/landing.md",
    "skills/lem/prompts/small.md",
    "skills/lem/prompts/review.md",
    "skills/lem/prompts/merge.md",
    "skills/lem/prompts/proposals.md",
    "skills/lem/stages/polish.md",
    "skills/lem/stages/build.md",
    "skills/lem/stages/interview.md",
    "skills/lem/stages/learn.md",
    "skills/lem/SKILL.md",
)


def flat(text: str) -> str:
    """The text as one line, with its bold marks gone, so that a sentence wrapped over two
    lines is found."""
    return " ".join(text.replace("**", "").split())


def rule_6() -> str:
    """The text of rule 6 of the builder's standing rules, from its number to rule 7's."""
    text = flat(BUILDER.read_text(encoding="utf-8"))
    start = text.index("6. A defect outside your task")
    return text[start : text.index("7. You ask nobody.", start)]


def test_the_bar_is_in_rule_6_and_nowhere_else_in_the_builder() -> None:
    assert flat(BUILDER.read_text(encoding="utf-8")).count(BAR) == 1
    assert BAR in rule_6()


@pytest.mark.parametrize(
    "words",
    [
        (
            "The bar binds Lem's agents only: an item a person writes, or asks an agent to "
            "file, is filed whatever the bar."
        ),
        (
            "A defect is cheap when its fix is text that does not run (a comment, a "
            "docstring, a sentence of a document), or when a check of the project reports it "
            "and the check's rerun shows it fixed."
        ),
        "A refactor, or the removal of code that looks unused, is not cheap",
        (
            "a commit of its own whose message names it, as "
            "`fixed on the way: FILE, what was wrong`"
        ),
        "A cheap defect alone never starts a builder or a new run of the checks",
        '"Fixed on the way": the file, the commit and what was wrong',
        (
            "Look in the backlog folder of the base for an open item that names the same "
            "defect"
        ),
        (
            "One item with `worth: no`, which the pull request lists under "
            '"Filed as not worth it"'
        ),
        (
            "One item with `worth: later`, which the pull request lists under "
            '"Filed in the backlog"'
        ),
        "the optional line `Decided against: REASON`",
    ],
)
def test_rule_6_says_its_limit_what_is_cheap_and_the_three_outcomes(words: str) -> None:
    assert words in rule_6()


@pytest.mark.parametrize(
    "words",
    [
        "No file, and no `worth: no` item",
        "its fix changes no behavior and needs no new test",
        '"Seen, not filed": its place and why it is under the bar',
    ],
)
def test_rule_6_gives_a_defect_under_the_bar_a_file_and_cheap_no_room_for_code(
    words: str,
) -> None:
    # an under defect that lived only in a pull request's text was raised again by the next
    # review
    assert words not in rule_6()


def test_rule_6_keeps_a_plan_builder_to_its_list() -> None:
    assert rule_6().startswith(
        "6. A defect outside your task is listed, not fixed and not filed."
    )


@pytest.mark.parametrize("name", NAMERS)
def test_each_file_that_sends_an_agent_to_a_defect_names_the_bar_of_rule_6(
    name: str,
) -> None:
    assert "the bar of rule 6" in flat((ROOT / name).read_text(encoding="utf-8"))


def test_no_other_file_of_lem_copies_a_part_of_the_bar() -> None:
    files = sorted(
        {*(ROOT / "skills/lem").rglob("*.md"), *(ROOT / "agents").glob("*.md")}
        - {BUILDER}
    )
    assert files
    copies = [
        (str(path.relative_to(ROOT)), part)
        for path in files
        for part in PARTS
        if part in flat(path.read_text(encoding="utf-8")).lower()
    ]
    assert copies == []


def test_the_parts_are_the_bars_own() -> None:
    # a part that the bar does not hold would guard nothing
    assert [part for part in PARTS if part not in BAR.lower()] == []
