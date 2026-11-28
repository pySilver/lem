"""The texts of a feature in parts (`docs/plans/2026-11-27-a-feature-in-parts.md`, step 36g, and
section 9, "The cost on a small task"): `stages/feature.md` is read only through one line of
each of the four texts every task reads, and `prompts/feature-review.md` only through
`stages/feature.md`, so that a task with no parts reads neither.

Whether each `lem` line parses is `tests/unit/cli/test_lines.py`'s; a real task is what tests how
an agent follows a text.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SKILL = ROOT / "skills/lem"
# The four texts that name the feature's stage, one line each.
NAMING = (
    "stages/new.md",
    "stages/interview.md",
    "stages/land.md",
    "prompts/session.md",
)
STAGE = "stages/feature.md"
REVIEW = "prompts/feature-review.md"


def texts() -> dict[str, str]:
    """Every text a session of Lem reads: the skills, the agents and the commands this
    repository ships, by their path from the repository's root."""
    folders = ("skills", "agents", "commands")
    found = (
        path
        for folder in folders
        if (ROOT / folder).is_dir()
        for path in (ROOT / folder).rglob("*.md")
    )
    return {
        str(path.relative_to(ROOT)): path.read_text(encoding="utf-8") for path in found
    }


def test_the_feature_stage_is_named_by_one_line_of_each_of_the_four_texts_alone() -> (
    None
):
    naming = {
        name: sum(STAGE in line for line in text.splitlines())
        for name, text in texts().items()
        if STAGE in text
    }
    assert naming == {f"skills/lem/{name}": 1 for name in NAMING}


def test_the_feature_review_is_named_by_the_feature_stage_alone() -> None:
    naming = {
        name
        for name, text in texts().items()
        if REVIEW in text and name != f"skills/lem/{REVIEW}"
    }
    assert naming == {f"skills/lem/{STAGE}"}


def test_each_line_that_names_the_feature_stage_is_a_condition_of_a_feature() -> None:
    marks = ("feature", "part_of", "sync")
    for name in NAMING:
        text = (SKILL / name).read_text(encoding="utf-8")
        paragraph = next(block for block in text.split("\n\n") if STAGE in block)
        sentence = next(
            one for one in " ".join(paragraph.split()).split(". ") if STAGE in one
        )
        condition = sentence.replace(STAGE, "")
        assert any(mark in condition for mark in marks), (name, sentence)
