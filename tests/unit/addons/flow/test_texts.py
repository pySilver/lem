"""What the add-ons' texts hold for the owner's rulings of the lessons, the correction queue, the
naps, the night and the free hour: each rule is a sentence of the file an agent reads at the
step (`docs/rulings/rulings.md`; `docs/rulings/history.md`, "Kept in one place")."""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
SKILL = ROOT / "skills" / "lem"


def text(*parts: str) -> str:
    """One file of the repository, its lines joined into one, so a sentence wraps freely."""
    return " ".join(ROOT.joinpath(*parts).read_text(encoding="utf-8").split())


def test_a_nights_brake_opens_nothing_with_two_of_its_pull_requests_waiting() -> None:
    night = text("skills", "lem", "stages", "night.md")
    assert "**The brake.**" in night
    assert "whose `night` is not null. With two or more, open nothing" in night


def test_a_night_that_builds_an_item_ends_as_a_pull_request_with_criteria_approved_alone() -> (
    None
):
    night = text("skills", "lem", "stages", "night.md")
    assert "lem task open SLUG --ask PATH --item PATH --night YYYY-MM-DD" in night
    assert "--alone" in night
    assert "its pull request is not green for them" in night


def test_the_free_hour_searches_and_proposes_and_makes_no_branch() -> None:
    night = text("skills", "lem", "stages", "night.md")
    assert "no branch, no worktree and no commit for it" in night
    assert "lem proposals add --kind night" in night
    hour = text("docs", "free-hour.md")
    assert "the free hour searches and proposes, and makes no branch" in hour
    assert "the scheduled `/lem retro` takes none" in hour
    assert "`.venv/bin/python -I -B tests --level full`" in hour
    assert "the tasks' records and journals" in hour


def test_improvements_reach_a_project_only_through_the_reviewer_and_the_owners_start() -> (
    None
):
    learn = text("skills", "lem", "stages", "learn.md")
    assert "`/lem retro` changes no file and asks the owner nothing" in learn
    assert "all through `lem proposals verdict`" in learn
    reviewer = text("skills", "lem", "prompts", "proposals.md")
    assert "Nothing reaches him from the night or the retro but those items" in reviewer
    assert "Your one write is the verdict command below" in reviewer


def test_the_retro_names_the_latest_proposal_and_the_journals_landing_fields() -> None:
    learn = text("skills", "lem", "stages", "learn.md").split("## retro", 1)[1]
    for named in (
        "`landing.proposed`",
        "`green`",
        "`reasons`",
        "`review-round`",
        "`review.counts`",
        "`review.answered`",
        "`not-green`",
        "`careful-missed`",
        "`round`",
        "`why`",
    ):
        assert named in learn
    assert "`careful.missed`" not in learn


def test_lem_naps_from_a_tasks_session_and_no_page_shows_a_nap() -> None:
    nap = text("skills", "lem", "stages", "nap.md")
    assert "A task's session starts a nap by itself" in nap
    assert "lem nap may" in nap
    assert "No page shows it" in nap
    brief = text("skills", "lem", "prompts", "nap.md")
    for gone in ("state.md", "events.jsonl", "decisions.jsonl"):
        assert gone not in brief, gone
    assert "`task.json`" in brief


def test_the_correction_hook_works_only_on_the_machines_yes() -> None:
    hook = text("skills", "lem", "harness", "claude-code", "correction-hook.md")
    assert "lem settings set corrections.collect yes --machine" in hook
    assert "no file of a repository can hold it" in hook
    assert "a machine with no such line is a no too" in hook


@pytest.mark.parametrize(
    "parts",
    [
        ("stages", "night.md"),
        ("stages", "learn.md"),
        ("stages", "nap.md"),
        ("prompts", "proposals.md"),
        ("prompts", "nap.md"),
        ("harness", "claude-code", "correction-hook.md"),
        ("harness", "claude-code", "start-nap.md"),
    ],
)
def test_no_text_of_the_add_ons_is_of_the_old_form(parts: tuple[str, ...]) -> None:
    said = SKILL.joinpath(*parts).read_text(encoding="utf-8")
    assert "<!-- lem: old form -->" not in said
    assert "lem project " not in said
