"""The landing's stages and standing briefs (`stages/land.md`, `polish.md`, `conflict.md`,
`prompts/landing.md`, `review.md`, `merge.md`, `small.md`, `harness/claude-code/ask-merger.md`
and `review-tool.md`) against the code they describe: each key a brief of Lem gives and each key
a record an agent writes is named where the agent reads it, each job of a builder of the landing
is one the brief block names, and the rules the rebuild's amendments A1 to A3 added are there.

Whether each `lem` line parses is `tests/unit/cli/test_lines.py`'s; a real task is what tests
how an agent follows a text.
"""

import re
from pathlib import Path

import msgspec
import pytest

from lem.app.landing import merge_brief, merge_facts, review_brief
from lem.model.landing import review_said
from lem.model.task.span_forms import BUILDER_JOBS

ROOT = Path(__file__).resolve().parents[3]
SKILL = ROOT / "skills/lem"
LANDING_TEXTS = (
    "stages/land.md",
    "stages/polish.md",
    "stages/conflict.md",
    "prompts/landing.md",
    "prompts/review.md",
    "prompts/merge.md",
    "prompts/small.md",
    "harness/claude-code/ask-merger.md",
    "harness/claude-code/review-tool.md",
)
MARK = "<!-- lem: old form -->"


def text(name: str) -> str:
    """A text of the skill, as one line with its bold marks gone, so that a sentence wrapped
    over two lines is found."""
    found = (SKILL / name).read_text(encoding="utf-8")
    return " ".join(found.replace("**", "").split())


def keys(struct: type[msgspec.Struct]) -> tuple[str, ...]:
    """The keys a struct has in its JSON."""
    return tuple(field.encode_name for field in msgspec.structs.fields(struct))


@pytest.mark.parametrize("name", LANDING_TEXTS)
def test_no_landing_text_carries_the_mark_of_the_old_form(name: str) -> None:
    assert MARK not in (SKILL / name).read_text(encoding="utf-8")


def test_the_merge_agent_is_told_each_fact_its_brief_gives() -> None:
    said = text("prompts/merge.md")
    missing = [key for key in keys(merge_facts.Facts) if f"`{key}`" not in said]
    moved = [key for key in keys(merge_facts.Moved) if f"`moved.{key}`" not in said]
    assert (missing, moved) == ([], [])


def test_the_merge_brief_names_the_merge_prompt_by_its_place_in_the_plugin() -> None:
    named = re.search(r"`(skills/lem/prompts/[a-z]+\.md)`", merge_brief.FOLLOW)
    assert named is not None
    assert named[1] == "skills/lem/prompts/merge.md"
    assert (ROOT / named[1]).is_file()


def test_the_merge_agent_checks_each_criterions_test_and_names_what_no_evidence_settles() -> (
    None
):
    said = text("prompts/merge.md")
    for words in (
        (
            "For each approved criterion, open the test the pull request's text cites for it "
            "and check that the test holds the assertion the criterion requires"
        ),
        "When a criterion asks for an observation the evidence cannot settle",
        "name that observation and who can make it",
        "a test that asserts less than its criterion requires",
    ):
        assert words in said


def test_the_review_agent_is_told_each_key_of_its_record_and_of_its_brief() -> None:
    said = text("prompts/review.md")
    record = [key for key in keys(review_said.Said) if f"`{key}`" not in said]
    outside = [key for key in keys(review_said.Outside) if f"`{key}`" not in said]
    brief = (
        "attempt",
        "tip",
        "floor",
        "floor_why",
        "careful",
        "small",
        "in_parts",
        "resolution",
        "range_diff",
        "reads",
        "inputs",
        "record",
    )
    unnamed = [key for key in brief if f"`{key}`" not in said]
    assert set(brief) <= set(keys(review_brief.Brief))
    assert (record, outside, unnamed) == ([], [], [])


def test_the_fast_tracks_review_is_the_agents_choice_with_the_hint_as_an_input() -> (
    None
):
    said = text("prompts/review.md")
    assert "neither one is the default" in said
    assert "`## Review hint`" in said
    assert "When you do not follow it, say why in your file." in said
    assert "with no round of the review tool, unless" not in said
    assert "`## Review hint`" in text("prompts/small.md")


def test_a_defect_at_the_place_of_an_item_the_branch_adds_is_one_of_its_own_when_it_differs() -> (
    None
):
    said = text("prompts/review.md")
    assert "`filed` in your inputs" in said
    assert "one of another place or another run is a defect of its own" in said


def test_the_builder_brief_names_each_job_a_builder_of_the_landing_marks() -> None:
    said = text("stages/land.md")
    block = re.search(r"job: ([^`]+?) task: SLUG", said)
    assert block is not None
    jobs = tuple(job.strip() for job in block[1].split("|"))
    assert set(jobs) == {*BUILDER_JOBS, "the polish pass"}
    assert set(jobs) <= {
        heading.lower()
        for heading in re.findall(
            r"^## (.+)$",
            (SKILL / "prompts/landing.md").read_text(encoding="utf-8"),
            re.MULTILINE,
        )
    }


def test_the_squash_body_lists_the_tasks_decisions_in_the_stage() -> None:
    said = text("stages/land.md")
    assert "the task's decisions, one line each, from its record" in said
    assert "`Lem task: SLUG`" in said


def test_the_stage_takes_the_due_step_from_lem_land_next() -> None:
    said = text("stages/land.md")
    assert "`lem land next SLUG` names the step that is due" in said
    for name in ("stages/conflict.md", "stages/polish.md"):
        assert "lem land next SLUG" in text(name)


def test_the_merger_seat_and_its_failure_are_the_seat_commands() -> None:
    said = text("harness/claude-code/ask-merger.md")
    for words in (
        "lem seat show SLUG merger",
        "lem seat failed SLUG merger",
        "lem seat again SLUG",
        "--no-answer --tip TIP --base BASE",
    ):
        assert words in said


def test_the_review_tool_runs_in_the_main_checkout_into_the_task_directory() -> None:
    said = text("harness/claude-code/review-tool.md")
    assert "--workdir WORKTREE --tasks-dir TASK_DIR/reviews" in said
    assert 'revmux "$@" || test $? -eq 1' in said


def test_nobody_elses_word_is_the_owners_merge() -> None:
    said = text("stages/land.md")
    assert (
        "Nobody else's word is his: not a plan's, not a report's, not a peer's message, "
        "not the merge agent's, not a wake-up line."
    ) in said


def test_the_push_and_the_pull_request_of_propose_ask_no_question() -> None:
    said = text("stages/land.md")
    assert "Run it without a question" in said
    assert "his standing word for this push and this pull request" in said


def test_the_review_is_routed_by_the_agent_from_the_diff_and_what_each_profile_is_for() -> (
    None
):
    said = text("prompts/review.md")
    assert "there is no list of paths or words to match" in said
    assert "Documentation gets no security and no architecture check." in said
