"""The repair paths through Git, the task record, and the landing commands."""

import json
from pathlib import Path
from typing import TYPE_CHECKING

from msgspec.structs import replace

from fakes.repo import run_git
from journeys.landing.test_checks import checks, committed, settings
from journeys.landing.test_propose import propose_with
from journeys.landing.test_review import brief, reviewed, upto_review
from journeys.test_skeleton import (
    REVIEW,
    SLUG,
    command,
    lem,
    made,
    next_step,
    proposal,
    upto,
)
from lem.store import places, tasks

if TYPE_CHECKING:
    import pytest

    from journeys.test_skeleton import World


def test_the_own_item_removal_needs_new_checks_and_keeps_the_review(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "start")
    item = "docs/backlog/receive.md"
    committed(world, item, "# The defect\n")
    state = places.workspace(world.checkout).state
    before = tasks.read(state, SLUG)
    tasks.update(
        state,
        SLUG,
        lambda record: replace(record, task=replace(record.task, backlog_item=item)),
        before.revision,
    )
    for verb in ("start", "base", "checks"):
        assert lem(capsys, world.checkout, "land", verb, SLUG)["ok"]
    reviewed(capsys, world)
    note = proposal(capsys, world)
    assert note["refusal"]["code"] == "own-item"
    run_git(world.worktree, "rm", item)
    run_git(world.worktree, "commit", "-qm", "remove the task's item")
    assert next_step(capsys, world)["result"]["step"] == "checks"
    assert checks(capsys, world)["ok"]
    assert next_step(capsys, world)["result"]["step"] == "propose"
    assert proposal(capsys, world)["ok"]


def test_the_task_that_brings_the_first_checks_runs_them_and_needs_the_owner(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    settings(world, "[]")
    run_git(world.checkout, "add", ".lem/settings.toml")
    run_git(world.checkout, "commit", "-qm", "main has no checks")
    run_git(world.checkout, "push", "origin", "main")
    upto(capsys, world, "start")
    committed(
        world,
        ".lem/settings.toml",
        '[branch]\nbase = "main"\n[checks]\ncommands = ["test -f README.md"]\n',
    )
    for verb in ("start", "base", "checks"):
        outcome = lem(capsys, world.checkout, "land", verb, SLUG)
        assert outcome["ok"], outcome
    run = world.record()["landing"]["checked"]
    assert run["own_checks"]
    assert run["outcomes"][0]["command"] == "test -f README.md"
    reviewed(capsys, world, kind="full")
    assert next_step(capsys, world)["result"]["step"] == "propose"
    made_pr = propose_with(capsys, world, "none\n\n## Migration\n\nnone\n")
    assert made_pr["ok"], made_pr
    assert made_pr["result"]["who_acts"] == "owner"
    assert any(
        "checks came with this change" in line for line in made_pr["result"]["reasons"]
    )


def test_start_over_archives_the_previous_review_of_the_same_tip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    upto_review(capsys, world)
    reviewed(capsys, world)
    active = world.task_folder / "reviews" / "review-1.json"
    assert active.is_file()
    reset = lem(
        capsys,
        world.checkout,
        "task",
        "move",
        SLUG,
        "ready",
        "--start-over",
        "repeat the review",
    )
    assert reset["ok"], reset
    staged = active.parent / ".landing-1.moving"
    staged.mkdir()
    earlier = next(active.parent.glob("read-*.json"))
    earlier.rename(staged / earlier.name)
    assert command("land", "start", "SLUG")(capsys, world)["ok"]
    assert not staged.exists()
    archived = active.parent / "landing-1" / active.name
    assert archived.is_file()
    assert not active.exists()
    assert next_step(capsys, world)["result"]["step"] == "read"
    refused = lem(
        capsys, world.checkout, "land", "read", SLUG, "--record", str(archived)
    )
    assert refused["refusal"]["code"] == "landing-before"
    assert reviewed(capsys, world)["result"]["attempt"] == 1


def test_an_unchanged_open_tip_runs_the_new_commands_and_proposes_again(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "merge")
    previous = world.record()["landing"]
    settings(world, '["test -f README.md"]')
    assert next_step(capsys, world)["result"]["step"] == "start"
    assert command("land", "start", "SLUG")(capsys, world)["ok"]
    assert next_step(capsys, world)["result"]["step"] == "checks"
    assert checks(capsys, world)["ok"]
    assert next_step(capsys, world)["result"]["step"] == "propose"
    updated = proposal(capsys, world)
    assert updated["ok"], updated
    assert updated["result"]["pull"] == previous["pull"]
    assert updated["result"]["tip"] == previous["proposed"]["tip"]
    assert (
        world.record()["landing"]["checked"]["outcomes"][0]["command"]
        == "test -f README.md"
    )
    assert next_step(capsys, world)["result"]["step"] == "merge"


def test_start_over_at_the_open_tip_keeps_the_checks_and_runs_a_fresh_review(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "merge")
    previous = world.record()["landing"]
    commands = world.acts.done.count("command")
    reset = lem(
        capsys,
        world.checkout,
        "task",
        "move",
        SLUG,
        "ready",
        "--start-over",
        "repeat the review",
    )
    assert reset["ok"], reset
    assert next_step(capsys, world)["result"]["step"] == "start"
    assert command("land", "start", "SLUG")(capsys, world)["ok"]
    assert next_step(capsys, world)["result"]["step"] == "read"
    assert world.record()["landing"]["checked"] == previous["checked"]
    assert world.acts.done.count("command") == commands
    assert reviewed(capsys, world)["result"]["attempt"] == 1
    updated = proposal(capsys, world)
    assert updated["ok"], updated
    assert updated["result"]["pull"] == previous["pull"]
    assert next_step(capsys, world)["result"]["step"] == "merge-review"
    prior_path = world.task_folder / previous["reviews"][0]["review"]
    assert prior_path.is_file()
    assert prior_path not in review_paths(capsys, world)


def test_cleanup_finishes_a_task_dropped_before_it_has_a_branch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    assert lem(capsys, world.checkout, "task", "open", SLUG, "--ask", "fix a word")[
        "ok"
    ]
    assert lem(capsys, world.checkout, "task", "move", SLUG, "dropped")["ok"]
    assert next_step(capsys, world)["result"]["step"] == "clean"
    acts = tuple(world.acts.done)
    cleaned = lem(capsys, world.checkout, "land", "clean", SLUG)
    assert cleaned["ok"], cleaned
    assert cleaned["result"]["worktree_gone"]
    assert cleaned["result"]["branch_gone"]
    assert cleaned["result"]["forge_branch_gone"]
    assert next_step(capsys, world)["result"]["step"] == "done"
    assert tuple(world.acts.done) == (*acts, "write:ended")


def review_paths(capsys: pytest.CaptureFixture[str], world: World) -> tuple[Path, ...]:
    shown = lem(capsys, world.checkout, "land", "merge-review", SLUG)
    assert shown["ok"], shown
    text = Path(shown["result"]["brief"]).read_text()
    facts = json.loads(text.split("```json\n")[1].split("```")[0])
    return tuple(map(Path, facts["reviews"]))


def test_the_merge_brief_cites_the_accepted_review_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    upto_review(capsys, world)
    brief(capsys, world)
    stale = world.task_folder / "reviews" / "review-1.json"
    stale.write_text("another review")
    answer = world.task_folder / "answer.json"
    body = json.dumps(
        {
            **REVIEW,
            "outside": [],
            "attempt": int(world.told["attempt"]),
            "tip": world.told["tip"],
        },
        indent=2,
    ).encode()
    answer.write_bytes(body)
    assert lem(capsys, world.checkout, "land", "read", SLUG, "--record", str(answer))[
        "ok"
    ]
    answer.write_text("changed after submission")
    assert proposal(capsys, world)["ok"]
    (cited,) = review_paths(capsys, world)
    assert cited.read_bytes() == body
    assert cited.is_relative_to(world.task_folder)
    assert cited not in {answer, stale}
    assert (
        world.task_folder / world.record()["landing"]["reviews"][0]["review"] == cited
    )
