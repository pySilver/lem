"""The review and the filing on a real repository and `LocalForge` (`landing.md` C rows 5 and
6, D filing, E "Fast track turns careful", F `read --record` and `file`), with the commands an
agent runs, through the tree in this process, as the walking skeleton runs them
(`tests/journeys/test_skeleton.py`, whose world and journey this reuses).

Jev is the `FakeJudge` of the skeleton's ports: nothing is sent, and no key of the environment
is read.
"""

import json
from typing import TYPE_CHECKING, Any, cast

import pytest

from fakes.repo import run_git
from journeys.test_skeleton import (
    JOURNEY,
    REVIEW,
    SLUG,
    SUBJECT,
    Killed,
    World,
    command,
    lem,
    made,
    next_step,
    parses,
    proposal,
)
from lem.app import wiring
from lem.ports.judge import Score
from lem.ports.place import Place

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from fakes.outside import FakeJudge

type Envelope = dict[str, Any]
OVER = {
    "where": "README.md",
    "title": "the README names no licence",
    "what": "README.md ends after one sentence; a reader finds no licence",
    "bar": "over",
}
UNDER = {
    "where": "NOTES.md",
    "title": "the notes have no date",
    "what": "NOTES.md says a teammate's note with no day",
    "bar": "under",
    "why": "nobody reads the notes by their day",
}
CHEAP = {
    "where": "README.md",
    "title": "the README has no heading",
    "what": "README.md starts with a sentence",
    "bar": "cheap",
    "why": "a heading changes nothing a reader of one line needs",
}
HELD = "docs/backlog/the-readme-names-no-licence.md"
HELD_TEXT = (
    "---\nworth: later\nwhere: README.md\nadded: 2026-11-20\n---\n"
    "# the README names no licence\n\nREADME.md ends after one sentence; a reader finds no "
    "licence\n"
)


def judge_of(world: World) -> FakeJudge:
    """The Jev of the test's ports."""
    place = Place(checkout=world.checkout, home=world.folder / "home", environ={})
    return cast("FakeJudge", wiring.bound(place).judge)


def upto_review(
    capsys: pytest.CaptureFixture[str], world: World, *, base: dict | None = None
) -> None:
    """The skeleton's journey up to the review, with `base` committed on origin's base by a
    teammate (the landing rebases onto it)."""
    for verb, step in JOURNEY:
        if verb == "read":
            return
        envelope = step(capsys, world)
        if verb is None and base and step.__name__ == "teammate":
            world.repo.outside_commit(
                "main", {path: text.encode() for path, text in base.items()}
            )
        assert envelope["ok"] is True, envelope


def brief(capsys: pytest.CaptureFixture[str], world: World) -> Envelope:
    """`lem land read SLUG`: the brief; its attempt and tip go to the record."""
    envelope = lem(capsys, world.checkout, "land", "read", SLUG)
    assert envelope["ok"] is True, envelope
    world.told.update(
        tip=envelope["result"]["tip"], attempt=str(envelope["result"]["attempt"])
    )
    return envelope


def recorded(
    capsys: pytest.CaptureFixture[str], world: World, **fields: object
) -> Envelope:
    """The review agent's record of the attempt and tip the brief named, with `fields` over
    the skeleton's, written in the task's folder as `prompts/review.md` says, and taken by its
    path there."""
    said = {
        **REVIEW,
        "outside": [],
        "attempt": int(world.told["attempt"]),
        "tip": world.told["tip"],
        **fields,
    }
    name = f"reviews/review-{world.told['attempt']}.json"
    (world.task_folder / name).parent.mkdir(exist_ok=True)
    (world.task_folder / name).write_text(json.dumps(said))
    return lem(capsys, world.checkout, "land", "read", SLUG, "--record", name)


def reviewed(
    capsys: pytest.CaptureFixture[str], world: World, **fields: object
) -> Envelope:
    brief(capsys, world)
    envelope = recorded(capsys, world, **fields)
    assert envelope["ok"] is True, envelope
    return envelope


def landed_from_propose(capsys: pytest.CaptureFixture[str], world: World) -> None:
    """The rest of the skeleton's journey, from the proposal to the cleanup."""
    rest = [
        step
        for verb, step in JOURNEY
        if verb in {"propose", "merge-review", "merge", "merged", "clean"}
    ]
    for step in rest:
        envelope = step(capsys, world)
        assert envelope["ok"] is True, envelope
    assert world.record()["task"]["status"] == "landed"


def file_step(*words: str) -> Callable[[pytest.CaptureFixture[str], World], Envelope]:
    return command("land", "file", "SLUG", *words)


def commits_of(world: World) -> list[str]:
    """The subjects of the commits after the tip the review read."""
    since = f"{world.told['tip']}..HEAD"
    return run_git(world.worktree, "log", "--format=%s", since).splitlines()


def test_the_brief_names_the_record_s_command_next_and_says_what_the_file_holds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    upto_review(capsys, world)
    envelope = brief(capsys, world)
    parses(envelope)
    following = envelope["next"]
    assert (following["do"], following["job"]) == ("spawn", "review")
    assert following["command"] == f"lem land read {SLUG} --record FILE"
    assert "reviews/review-1.json in the task's folder" in following["why"]
    told = json.loads((world.task_folder / envelope["result"]["path"]).read_text())
    assert (told["attempt"], told["tip"], told["floor"]["kind"]) == (
        1,
        envelope["result"]["tip"],
        "read",
    )
    assert told["inputs"]["range"].endswith(f"..{told['tip']}")
    assert told["inputs"]["worktree"] == str(world.worktree)
    assert told["small"] is True
    spans = world.record()["task"]["spans"]
    assert [(span["name"], span["job"]) for span in spans] == [("review", "attempt 1")]
    again = next_step(capsys, world)
    assert (again["result"]["step"], again["next"]["command"]) == (
        "read",
        f"lem land read {SLUG}",
    )
    assert brief(capsys, world)["result"]["path"] == envelope["result"]["path"]


def test_with_no_defect_outside_the_change_file_is_not_due_and_next_names_propose(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    upto_review(capsys, world)
    envelope = reviewed(capsys, world)
    assert envelope["next"]["command"].startswith(f"lem land propose {SLUG} ")
    assert next_step(capsys, world)["result"]["step"] == "propose"
    refused = file_step()(capsys, world)["refusal"]
    assert (refused["code"], refused["fix"]) == (
        "not-due",
        f"lem land propose {SLUG} is the step that is due",
    )
    assert world.record()["task"]["spans"][0]["end"] is not None


def test_defects_over_and_under_the_bar_are_items_in_one_commit_and_the_request_lands(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    upto_review(capsys, world)
    envelope = reviewed(capsys, world, outside=[OVER, UNDER, CHEAP])
    assert envelope["result"]["to_file"] == ["r1.1", "r1.2", "r1.3"]
    assert next_step(capsys, world)["result"]["step"] == "file"
    filed = file_step()(capsys, world)
    assert filed["ok"] is True, filed
    assert [
        (one["finding"], one["disposition"], one.get("worth"))
        for one in filed["result"]
    ] == [
        ("r1.1", "item", "later"),
        ("r1.2", "item", "no"),
        ("r1.3", "seen", None),
    ]
    assert (
        commits_of(world)[0] == f"docs(backlog): what review round 1 saw outside {SLUG}"
    )
    under = (world.worktree / "docs/backlog/the-notes-have-no-date.md").read_text()
    assert under.startswith("---\nworth: no\nwhere: NOTES.md\n")
    assert under.rstrip().endswith(
        "Decided against: nobody reads the notes by their day"
    )
    landing = world.record()["landing"]
    assert landing["checked"]["items_after"] == [
        HELD,
        "docs/backlog/the-notes-have-no-date.md",
    ]
    assert next_step(capsys, world)["result"]["step"] == "propose"
    assert file_step()(capsys, world)["refusal"]["code"] == "not-due"
    landed_from_propose(capsys, world)
    assert run_git(world.repo.origin, "show", f"main:{HELD}").startswith(
        "---\nworth: later"
    )
    assert world.acts.counted()["commit"] == 1


def test_a_cut_after_the_items_commit_finds_them_again_and_commits_nothing_twice(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    upto_review(capsys, world)
    reviewed(capsys, world, outside=[OVER])
    world.acts.cut = ("commit", 1)
    with pytest.raises(Killed):
        file_step()(capsys, world)
    capsys.readouterr()
    # The commit is there and its record is not: the checks take the new tip, the review is
    # read again, and `file` finds the item by its defect.
    assert next_step(capsys, world)["result"]["step"] == "checks"
    assert command("land", "checks", "SLUG")(capsys, world)["ok"] is True
    reviewed(capsys, world, outside=[OVER])
    again = file_step()(capsys, world)
    assert again["ok"] is True, again
    assert {one["path"] for one in again["result"]} == {HELD}
    assert world.acts.counted()["commit"] == 1
    assert next_step(capsys, world)["result"]["step"] == "propose"


def test_jev_names_an_item_and_file_writes_nothing_until_same_or_new(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    old = "docs/backlog/no-licence-file.md"
    text = "---\nworth: no\nwhere: LICENSE\n---\n# no licence file\n\nThere is no LICENSE.\n"
    upto_review(capsys, world, base={old: text})
    judge = judge_of(world)
    judge.same[OVER["title"]] = (Score(score=0.8, path=str(world.worktree / old)),)
    reviewed(capsys, world, outside=[OVER])
    refused = file_step()(capsys, world)["refusal"]
    assert refused["code"] == "jev-same"
    assert (
        f'r1.1 "{OVER["title"]}": `{old}` "no licence file" (Jev: 0.80, worth: no)'
        in refused["why"]
    )
    assert not (world.worktree / HELD).exists()
    assert commits_of(world) == []
    asked = len(judge.asked)
    both = file_step("--same", f"r1.1={old}", "--new", "r1.1")(capsys, world)["refusal"]
    assert both["code"] == "same-new"
    assert file_step("--new", "r1.9")(capsys, world)["refusal"]["code"] == "same-new"
    same = file_step("--same", f"r1.1={old}")(capsys, world)
    assert same["ok"] is True, same
    # The item Jev named says `worth: no`, and the defect is over the bar: a new item names
    # it, and the old one stays as it is.
    [placed] = same["result"]
    assert (placed["disposition"], placed["path"], placed["cites"]) == (
        "item",
        HELD,
        old,
    )
    assert (
        f"The same defect as `{old}`, now over the bar."
        in (world.worktree / HELD).read_text()
    )
    assert len(judge.asked) == asked
    assert len(commits_of(world)) == 1


def test_new_files_the_defect_as_its_own_item_and_leaves_the_one_jev_named(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    old = "docs/backlog/no-licence-file.md"
    text = "---\nworth: no\nwhere: LICENSE\n---\n# no licence file\n\nThere is no LICENSE.\n"
    upto_review(capsys, world, base={old: text})
    judge_of(world).same[OVER["title"]] = (
        Score(score=0.8, path=str(world.worktree / old)),
    )
    reviewed(capsys, world, outside=[OVER])
    assert file_step()(capsys, world)["refusal"]["code"] == "jev-same"
    new = file_step("--new", "r1.1")(capsys, world)
    assert new["ok"] is True, new
    assert (world.worktree / HELD).is_file()
    assert (world.worktree / old).read_text() == text


def test_alike_names_the_items_jev_reads_as_the_same_and_with_jev_not_asked_lists_every_item(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    upto_review(capsys, world, base={HELD: HELD_TEXT})
    what = tmp_path / "run.txt"
    what.write_text(OVER["what"])
    words = (
        "land",
        "alike",
        SLUG,
        "--where",
        "README.md",
        "--title",
        "no licence",
        "--what",
        str(what),
    )
    judge = judge_of(world)
    judge.same["no licence"] = (Score(score=0.9, path=str(world.worktree / HELD)),)
    answered = lem(capsys, world.checkout, *words)
    assert answered["ok"] is True, answered
    named = answered["result"]
    assert named["items"] == 1
    assert [(one["path"], one["jev"]) for one in named["alike"]] == [
        (HELD, "Jev: 0.90")
    ]
    judge.key = False
    unasked = lem(capsys, world.checkout, *words)["result"]
    assert unasked["jev"] == "Jev: not asked (no key for Jev)"
    assert unasked["read"] == [
        {
            "path": HELD,
            "title": "the README names no licence",
            "where": "README.md",
            "worth": "later",
        }
    ]
    assert unasked["alike"] == []
    what.write_text("")
    assert lem(capsys, world.checkout, *words)["refusal"]["code"] == "what"
    bad = (
        "land",
        "alike",
        SLUG,
        "--where",
        "README.md",
        "--title",
        "!!",
        "--what",
        str(what),
    )
    assert lem(capsys, world.checkout, *bad)["refusal"]["code"] == "title"


def test_a_review_that_calls_the_fast_track_careful_gets_the_full_set_and_a_person_s_merge(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    upto_review(capsys, world)
    brief(capsys, world)
    why = "README.md is the page a customer reads before paying"
    refused = recorded(capsys, world, careful=True, careful_why=why)["refusal"]
    assert refused["code"] == "careful-not-full"
    full = {"kind": "full", "careful": True, "careful_why": why, "left_out": []}
    assert recorded(capsys, world, **full)["ok"] is True
    journal = world.record()["journal"]
    assert [entry["why"] for entry in journal if entry["kind"] == "careful-missed"] == [
        why
    ]
    proposed = proposal(capsys, world)
    assert proposed["result"]["green"] is False
    assert f"the change is careful: {why}" in proposed["result"]["reasons"]
    assert world.record()["landing"]["proposed"]["who_acts"] == "owner"
    merge = command("land", "merge", "SLUG", "--by", "merger", "--message", SUBJECT)
    assert merge(capsys, world)["ok"] is False
    assert world.forge.merge_calls == []


def test_a_review_nobody_answered_is_started_once_more_then_the_request_goes_on(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    upto_review(capsys, world)
    quiet = {
        "answered": [],
        "silent": [{"name": "the review agent", "why": "it ended with no files"}],
        "ran": [],
        "careful": None,
        "careful_why": None,
    }
    for attempt in (1, 2):
        assert next_step(capsys, world)["result"]["step"] == "read"
        envelope = reviewed(capsys, world, **quiet)
        assert envelope["result"]["attempt"] == attempt
    assert next_step(capsys, world)["result"]["step"] == "propose"


def test_an_edit_of_lem_s_own_settings_gets_the_full_set_whatever_the_shape_says(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    upto_review(capsys, world)
    settings = world.worktree / ".lem" / "settings.toml"
    settings.write_text(
        settings.read_text().replace('land = "agent"', 'land = "owner"')
    )
    run_git(
        world.worktree,
        "commit",
        "--quiet",
        "--all",
        "--message",
        "chore: the owner lands",
    )
    assert command("land", "checks", "SLUG")(capsys, world)["ok"] is True
    told = brief(capsys, world)["result"]
    assert told["floor"]["kind"] == "full"
    assert "the change edits [branch] of .lem/settings.toml" in told["floor"]["why"]
    assert recorded(capsys, world)["refusal"]["code"] == "under-floor"


def test_a_commit_hook_that_refuses_the_items_is_named_and_the_next_run_finds_them(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    upto_review(capsys, world)
    hook = world.checkout / ".git" / "hooks" / "commit-msg"
    hook.write_text(
        '#!/bin/sh\ngrep -q "^backlog: " "$1" || { echo "subject must start with backlog:" >&2; exit 1; }\n'
    )
    hook.chmod(0o755)
    reviewed(capsys, world, outside=[OVER])
    refused = file_step()(capsys, world)["refusal"]
    assert refused["code"] == "commit"
    assert "subject must start with backlog:" in refused["why"]
    assert "never with --no-verify" in refused["fix"]
    assert run_git(world.worktree, "diff", "--cached", "--name-only") == HELD
    run_git(
        world.worktree, "commit", "--quiet", "--message", "backlog: what the review saw"
    )
    # A builder's commit is no commit of `file`: the checks and a read take it, and `file`
    # then finds the item by its defect and writes nothing.
    assert next_step(capsys, world)["result"]["step"] == "checks"
    assert command("land", "checks", "SLUG")(capsys, world)["ok"] is True
    reviewed(capsys, world, outside=[OVER])
    again = file_step()(capsys, world)
    assert again["ok"] is True, again
    placed = {(one["disposition"], one["path"]) for one in again["result"]}
    assert placed == {("item", HELD)}
    assert commits_of(world) == []
    assert next_step(capsys, world)["result"]["step"] == "propose"


def test_a_worktree_with_a_change_nobody_committed_takes_no_filing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    upto_review(capsys, world)
    reviewed(capsys, world, outside=[OVER])
    (world.worktree / "scratch.txt").write_text("left behind\n")
    refused = file_step()(capsys, world)["refusal"]
    assert (refused["code"], refused["fix"]) == (
        "not-due",
        f"lem land start {SLUG} is the step that is due",
    )
    assert commits_of(world) == []


def test_alike_reads_the_task_s_worktree_and_takes_its_words_one_line_each(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    what = tmp_path / "run.txt"
    what.write_text(OVER["what"])
    words = ("--where", "README.md", "--title", "no licence", "--what", str(what))
    assert JOURNEY[0][1](capsys, world)["ok"] is True
    no_tree = lem(capsys, world.checkout, "land", "alike", SLUG, *words)["refusal"]
    assert (no_tree["code"], no_tree["fix"]) == (
        "no-worktree",
        f"lem task worktree {SLUG} makes it",
    )
    two = ("--where", "README.md", "--title", "two\nlines", "--what", str(what))
    assert (
        lem(capsys, world.checkout, "land", "alike", SLUG, *two)["refusal"]["code"]
        == "line"
    )
    gone = (
        "--where",
        "README.md",
        "--title",
        "t",
        "--what",
        str(tmp_path / "gone.txt"),
    )
    assert (
        lem(capsys, world.checkout, "land", "alike", SLUG, *gone)["refusal"]["code"]
        == "what"
    )


def test_a_team_that_sends_no_finding_to_jev_asks_jev_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    upto_review(capsys, world, base={HELD: HELD_TEXT})
    settings = world.checkout / ".lem" / "settings.toml"
    settings.write_text(settings.read_text() + "\n[jev]\nfindings = false\n")
    what = tmp_path / "run.txt"
    what.write_text(OVER["what"])
    judge = judge_of(world)
    judge.same["no licence"] = (Score(score=0.9, path=str(world.worktree / HELD)),)
    words = ("--where", "README.md", "--title", "no licence", "--what", str(what))
    told = lem(capsys, world.checkout, "land", "alike", SLUG, *words)["result"]
    assert told["jev"] == "Jev: not asked (off in the settings)"
    assert judge.asked == []
