"""The maintaining session's choices that span the stages and the command tree."""

from lem.settings.machine import Load
from unit.cli import reading, shapes
from unit.guides.test_rulings_held import flat, text


def test_a_stop_in_the_build_needs_a_breaker_and_the_pull_request_needs_no_new_yes() -> (
    None
):
    stage = flat("skills/lem/stages/breaker.md")
    assert "Two causes, and no others" in stage
    assert "**`irreversible`**" in stage
    assert "**`criteria`**" in stage
    assert "An overrun stops nothing" in stage
    skill = flat("skills/lem/SKILL.md")
    assert "The pull request is no step to ask about." in skill
    assert "you run it without a question" in skill


def test_lem_uses_the_same_landing_on_its_own_tasks() -> None:
    assert (
        "Lem's own tasks take the same landing steps as any other project's tasks."
        in flat("AGENTS.md")
    )
    stage = flat("skills/lem/stages/land.md")
    assert (
        reading.verdict(
            reading.Line("landing", 1, "lem land propose SLUG", span=True),
            shapes.tree(),
        )
        == []
    )
    assert "**`propose`**, with `--title` and `--notes`" in stage


def test_a_lesson_about_an_installed_stage_goes_in_the_projects_lessons() -> None:
    learn = flat("skills/lem/stages/learn.md")
    assert "one line in the project's lessons file (`lem path lessons`)" in learn
    assert "opens with the stage's or the skill's name" in learn
    assert "Never the installed skill's own file" in learn
    session = flat("skills/lem/prompts/session.md")
    assert "the project's lessons file" in session
    assert "opens with a stage's name" in session


def test_the_two_reviews_leave_one_load_number_and_no_extra_command_or_guard() -> None:
    assert Load.__struct_fields__ == ("start",)
    commands = shapes.tree()["subcommands"]
    assert isinstance(commands, dict)
    assert {"dnd", "parity"}.isdisjoint(commands)
    assert "Never the whole suite" in flat("agents/lem-builder.md")
    assert "its verdict on its first line" in text("src/lem/cli/land/merge_review.py")
    assert "Start a task opens its own session" in text(
        "src/lem/board/views/backlog/holds.py"
    )
