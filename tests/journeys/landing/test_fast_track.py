"""A fast-track repair with a criterion's test, with or without a builder's backlog item."""

import shlex
from importlib.util import find_spec
from typing import TYPE_CHECKING

import pytest

from fakes.repo import run_git, write
from journeys.landing.test_review import brief as review_brief
from journeys.landing.test_review import recorded
from journeys.test_skeleton import (
    SETTINGS,
    SLUG,
    lem,
    made,
    reply,
    upto,
)
from journeys.test_skeleton import (
    brief as merge_brief,
)
from lem.app.landing import checks_run

if TYPE_CHECKING:
    from pathlib import Path

    from journeys.test_skeleton import World
    from lem.app.landing.frame import Context

TITLE = "fix(report): the date column never wraps"
CRITERION = "The date column of the report never wraps: 2026-11-17 stays on one line."
TEST = "tests/date-nowrap.sh"
ITEM_TITLE = "a range over two months repeats the year"
ITEM = "docs/backlog/a-range-over-two-months-repeats-the-year.md"
ITEM_BODY = (
    "---\nworth: later\nwhere: report.css\nadded: 2026-11-17\n---\n"
    f"# {ITEM_TITLE}\n\n"
    'The range 28 Feb to 3 Mar 2026 reads "28 Feb 2026 - 3 Mar 2026"; '
    "a noqa in a note is no mark.\n\n"
    f"Seen outside the change by the builder of task {SLUG} (2026-11-17); "
    "the base commit has it.\n"
).encode()


def test_checks_say_how_the_run_ended_in_the_command_that_ran_them(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "checks")
    checked = lem(capsys, world.checkout, "land", "checks", SLUG)
    assert checked["result"]["outcome"] == "passed"
    end = next(
        mark for mark in world.record()["journal"] if mark["kind"] == "check-end"
    )
    assert end["say"]
    assert checked["say"] == end["say"]


def call(
    capsys: pytest.CaptureFixture[str], world: World, noun: str, verb: str, *words: str
) -> dict:
    envelope = lem(capsys, world.checkout, noun, verb, SLUG, *words)
    assert envelope["ok"] is True, envelope
    return envelope["result"]


def commit(world: World, subject: str, files: dict[str, bytes | None]) -> None:
    write(world.worktree, files)
    run_git(world.worktree, "add", "--all")
    run_git(world.worktree, "commit", "--quiet", "--message", subject)


def built(
    capsys: pytest.CaptureFixture[str], world: World, runs: Path, *, with_item: bool
) -> None:
    settings = SETTINGS.replace(
        b'["grep -q receive README.md", "test -f README.md"]', b'["true"]'
    )
    world.repo.outside_commit("main", {".lem/settings.toml": settings})
    run_git(world.checkout, "pull", "--quiet", "--ff-only", "origin", "main")
    call(
        capsys,
        world,
        "task",
        "open",
        "--ask",
        "The date column of the report must never wrap.",
    )
    call(
        capsys,
        world,
        "task",
        "read",
        "--type",
        "fix",
        "--why",
        "the date wraps",
        "--track",
        "small",
        "--then",
        "fast",
    )
    criteria = world.task_folder / "criteria.md"
    text = f"## Acceptance criteria\n\nSize: small, because the ask is one sentence.\n\n1. {CRITERION}\n"
    criteria.write_text(text)
    call(capsys, world, "criteria", "approve", "--small")
    call(capsys, world, "task", "worktree")
    call(capsys, world, "task", "move", "building", "--line", "one builder")
    script = (
        f"if test -f {shlex.quote(ITEM)}; then echo 'ran with item'; else echo ran; fi"
        f" >> {shlex.quote(str(runs))}\ngrep -q nowrap report.css\n"
    )
    commit(
        world,
        TITLE,
        {"report.css": b"td { white-space: nowrap; }\n", TEST: script.encode()},
    )
    criteria.write_text(f"{text}   - test: `sh {TEST}` in `{TEST}`\n")
    call(capsys, world, "criteria", "record")
    if with_item:
        commit(
            world,
            "docs(backlog): what the builder saw outside the change",
            {ITEM: ITEM_BODY},
        )
    call(capsys, world, "task", "move", "ready", "--line", "built")


def span_marks(world: World) -> list[tuple[str, str]]:
    return [
        (entry["name"], entry["edge"])
        for entry in world.record()["journal"]
        if entry["kind"] == "span"
    ]


@pytest.mark.skipif(
    find_spec("lem.app.landing.checks_record") is None,
    reason="the land-checks step supplies the criterion run, check spans, and polish refusal",
)
@pytest.mark.parametrize("with_item", [False, True], ids=["clean", "with-item"])
def test_the_fast_track_checks_its_criterion_once_and_lands(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    *,
    with_item: bool,
) -> None:
    world = made(tmp_path, monkeypatch)
    runs = tmp_path / "criterion-runs"
    built(capsys, world, runs, with_item=with_item)
    call(capsys, world, "land", "start")
    call(capsys, world, "land", "base")
    assert call(capsys, world, "land", "next")["step"] == "checks"
    refused = lem(capsys, world.checkout, "land", "polish", SLUG)["refusal"]
    assert refused["code"] == "not-due"
    assert f"lem land checks {SLUG}" in refused["fix"]

    ran = checks_run.output_of

    def with_start(context: Context, command: str) -> tuple[int, bytes]:
        assert span_marks(world) == [("checks", "start")]
        return ran(context, command)

    monkeypatch.setattr(checks_run, "output_of", with_start)
    checked = call(capsys, world, "land", "checks")
    assert checked["outcome"] == "passed"
    assert checked["tip"] == run_git(world.worktree, "rev-parse", "HEAD")
    assert [line["command"] for line in checked["outcomes"]] == ["true"]
    assert [
        (one["red_on_base"], one["green_on_tip"]) for one in checked["criteria"]
    ] == [(True, True)]
    red = world.record()["task"]["criteria"]["red"]
    assert red["run_without"] == ([ITEM, "report.css"] if with_item else ["report.css"])

    for _ in range(2):
        read = review_brief(capsys, world)["result"]
        assert (read["attempt"], read["floor"], read["tip"]) == (
            1,
            "read",
            checked["tip"],
        )
        assert [
            mark["job"]
            for mark in world.record()["journal"]
            if mark["kind"] == "span"
            and (mark["name"], mark["edge"]) == ("review", "start")
        ] == ["attempt 1"]
    assert recorded(capsys, world)["ok"] is True
    assert span_marks(world) == [
        ("checks", "start"),
        ("checks", "end"),
        ("review", "start"),
        ("review", "end"),
    ]

    notes = world.written("notes.md", "none\n")
    proposed = call(
        capsys, world, "land", "propose", "--title", TITLE, "--notes", notes
    )
    assert proposed["green"] is True
    pull = proposed["pull"]
    assert pull["url"] == world.forge.url(pull["number"])
    body = world.forge.bodies[pull["number"]].splitlines()
    if with_item:
        heading = body.index("## Filed in the backlog")
        assert body[heading + 2] == f"- `{ITEM}`: {ITEM_TITLE}"
    else:
        assert (
            len(body) <= 20
        )  # The clean task's limit in main:tests/lem-land-small.sh.
    assert f"1. {CRITERION}" in body
    assert f"   - `sh {TEST}`: passes on the branch, fails on the base commit" in body
    assert not any("polish" in line for line in body)

    assert merge_brief(capsys, world)["ok"] is True
    assert reply(capsys, world)["ok"] is True
    call(capsys, world, "land", "merge", "--by", "merger", "--message", TITLE)
    call(capsys, world, "land", "merged")
    assert world.record()["task"]["status"] == "landed"
    assert world.forge.merge_calls == [(pull["number"], checked["tip"])]
    if with_item:
        assert (
            run_git(world.repo.origin, "show", f"main:{ITEM}")
            == ITEM_BODY.decode().rstrip()
        )
    assert not (world.worktree / "docs/plans").exists()
    assert runs.read_text().splitlines() == [
        "ran with item" if with_item else "ran",
        "ran",
    ]  # A single trial on each side.
