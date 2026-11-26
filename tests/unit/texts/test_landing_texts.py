"""The landing's stages and standing briefs (`stages/land.md`, `polish.md`, `conflict.md`,
`prompts/landing.md`, `review.md`, `merge.md`, `small.md`, `harness/claude-code/ask-merger.md`
and `review-tool.md`) against the code they describe: each key a brief of Lem gives and each key
a record an agent writes is named where the agent reads it, each job of a builder of the landing
is one the brief block names, and the rules the rebuild's amendments A1 to A3 added are there.

Whether each `lem` line parses is `tests/unit/cli/test_lines.py`'s; a real task is what tests
how an agent follows a text.
"""

import re
import shlex
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


def test_the_landing_stage_limits_repair_to_two_builders_on_the_same_failure() -> None:
    said = text("stages/land.md")
    _, _, repair = said.partition("A check that fails is work")
    decision, _, _ = repair.partition("`spawn-builder`")
    assert "Before you start another builder for the same failure" in decision
    assert "If two builders worked on it, start no third builder" in decision
    assert "take the ladder when an approval stands through the recheck" in decision
    assert (
        "Ask the owner only if a criterion must change or the breaker applies"
        in decision
    )
    assert "In other landings, run `lem land checks SLUG --repair-limit`" in decision


def test_the_landing_stage_tells_the_owner_after_the_repair_session_is_gone_twice() -> (
    None
):
    said = text("stages/land.md")
    _, _, repair = said.partition(
        "`lem session wait REPAIR --until landed,dropped,answered`"
    )
    lost, _, ended = repair.partition("When the repair lands")
    assert lost.count("`lem session open REPAIR --why dead`") == 1
    assert (
        "If the second session is gone, tell the owner in one line that the repair "
        "session is gone again. Keep the hold and wait for his word." in lost
    )
    assert (
        "If the repair is dropped or answered, tell the owner in one line and wait "
        "for his word before you lift the hold." in ended
    )


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


def test_a_session_merge_names_the_tip_the_owner_saw_and_the_squash_subject() -> None:
    said = text("stages/land.md")
    assert "`lem land merge SLUG --by owner --tip TIP`" in said
    assert "`TIP` is the whole commit the owner saw" in said
    assert "Add `--message` with the report's commit subject for a squash" in said


def test_the_conflict_wake_starts_a_round_before_it_asks_for_the_due_step() -> None:
    said = text("stages/conflict.md")
    assert "Run `lem land start SLUG --conflicting` first." in said
    assert "Then use `lem land next SLUG` to find each step that is due." in said


@pytest.mark.parametrize("stage", ["land", "conflict"])
def test_propose_takes_the_quoted_full_path_to_the_tasks_notes(stage: str) -> None:
    assert '--notes "TASK_DIR/notes.md"' in text(f"stages/{stage}.md")


def test_the_merger_judges_items_from_both_backlog_headings() -> None:
    said = text("prompts/merge.md")
    read = said.split("## Read ", 1)[1].split("## A moved base", 1)[0]
    decide = said.split("## Decide ", 1)[1]
    assert "Open each item the branch adds (`filed`)" in read
    assert "both `## Filed in the backlog` and `## Filed as not worth it`" in read
    assert "any new item under either backlog heading" in decide


def test_the_merge_prompt_gives_no_credit_to_silent_review_attempts() -> None:
    said = text("prompts/merge.md")
    assert "its checks passed and a review read the diff" not in said
    assert "the review read every line" not in said
    assert "If a recorded review answered, open its files in `reviews`" in said
    assert "tell the owner that neither attempt got an answer" in said


def test_a_must_fix_starts_a_builder_before_the_due_filing_step() -> None:
    said = text("stages/land.md")
    assert "before a fix builder starts too" not in said
    assert (
        "When `next` names `file`, file the recorded defects outside the change" in said
    )
    assert said.index("- *a must-fix*") < said.index("- *defects outside the change*")


def test_an_interrupted_merge_reuses_its_arguments_and_a_squash_retry_takes_a_subject() -> (
    None
):
    said = text("stages/land.md")
    assert "Run the original `lem land merge` command with the same arguments" in said
    assert (
        '`lem land merge SLUG --by owner --tip TIP --checked MOMENT --message "SUBJECT"`'
        in said
    )
    assert "Omit `--message` when `branch.history` is `keep`" in said


def test_the_repair_builder_ends_the_job_that_it_started() -> None:
    said = text("stages/land.md")
    assert '`lem task span SLUG builder end --job "JOB"` with the same job' in said


def test_the_stage_reads_the_completion_line_of_its_checks_run() -> None:
    said = text("stages/land.md")
    assert "Say the command's top-level `say`" in said
    assert "`result.ended.say` from `lem land checks SLUG --status`" in said


@pytest.mark.parametrize(
    "name", ["stages/land.md", "harness/claude-code/ask-merger.md"]
)
def test_the_merge_reply_command_accepts_an_answer_path_with_spaces(name: str) -> None:
    found = re.search(r"`(lem land merge-review SLUG --file [^`]+)`", text(name))
    assert found is not None
    path = "/Client Work/answer.md"
    words = shlex.split(found[1].replace("ANSWER", path))
    assert words[words.index("--file") + 1] == path


def test_the_merger_opens_pictures_from_the_task_directory_and_links_them_relatively() -> (
    None
):
    said = text("prompts/merge.md")
    assert "Open each picture under `task_directory`" in said
    assert "use its relative `media/NAME` path" in said


def test_a_review_agent_that_chose_its_own_read_skips_the_tool_round() -> None:
    said = text("prompts/review.md")
    assert "4. Run the tool only if you chose it." in said
    assert "If you chose your own read, do it and go to step 5." in said
    assert "for each lens you run and each you leave out" in said


def test_the_merge_line_ruling_records_the_owners_whole_choice() -> None:
    rulings = (ROOT / "docs/rulings/rulings.md").read_text(encoding="utf-8")
    bullet = next(
        part
        for part in rulings.split("\n- ")
        if part.startswith("**The board's button says Approve")
    )
    said = " ".join(bullet.split("\n\n")[0].split())
    for clause in (
        "approval stands through a moved base and a conflict",
        "checks run on the task rebased onto that base",
        "leaves the line and comes back after a builder's fix",
        "calls the owner only when the fix needs a criterion to change or a breaker applies",
        "checks ran on the current base merges first",
        "server records how many approved tasks wait at each merge",
    ):
        assert clause in said
    assert said.endswith("(2026-11-25)")


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
