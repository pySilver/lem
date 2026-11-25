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
from msgspec.structs import replace

from fakes.records import MOMENT
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
from lem.app.landing import changes
from lem.ports.judge import Score
from lem.ports.place import Place
from lem.records.decisions import Taken
from lem.records.landing.record import Landing
from lem.records.landing.start import Resolution
from lem.store import tasks

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from fakes.outside import FakeJudge
    from lem.records.record import Record

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
    assert (told["attempt"], told["tip"], told["floor"]) == (
        1,
        envelope["result"]["tip"],
        "read",
    )
    assert told["floor_why"].startswith("nothing asks for more than one read")
    assert envelope["result"]["floor"] == "read"
    assert told["inputs"]["ask"] == "the README says recieve; fix it"
    assert (
        told["inputs"]["rules"]
        == f"lem --repo {world.worktree} rules --range {told['inputs']['range']}"
    )
    assert told["inputs"]["range"].endswith(f"..{told['tip']}")
    assert told["inputs"]["worktree"] == str(world.worktree)
    assert told["small"] is True
    spans = world.record()["task"]["spans"]
    reviews = [span for span in spans if span["name"] == "review"]
    assert [(span["name"], span["job"]) for span in reviews] == [
        ("review", "attempt 1")
    ]
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
    judge.same[OVER["title"]] = (Score(score=0.8, path=old),)
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
    judge_of(world).same[OVER["title"]] = (Score(score=0.8, path=old),)
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
    judge.same["no licence"] = (Score(score=0.9, path=HELD),)
    answered = lem(capsys, world.checkout, *words)
    assert answered["ok"] is True, answered
    named = answered["result"]
    assert named["items"] == 1
    assert [(one["path"], one["jev"]) for one in named["alike"]] == [
        (HELD, "Jev: 0.90")
    ]
    assert not (world.task_folder / "items-at-tip").exists()
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
    # a careful request's notes say whether it holds a migration
    notes = world.written("notes.md", "none\n\n## Migration\n\nnone\n")
    words = ("--title", SUBJECT, "--notes", notes)
    proposed = command("land", "propose", "SLUG", *words)(capsys, world)
    assert proposed["result"]["green"] is False
    careful_on_fast = f"careful on the fast track (the review says so: {why})"
    assert any(one.startswith(careful_on_fast) for one in proposed["result"]["reasons"])
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
    assert told["floor"] == "full"
    assert "the change edits [branch] of .lem/settings.toml" in told["floor_why"]
    assert recorded(capsys, world)["refusal"]["code"] == "under-floor"
    full = {"kind": "full", "left_out": [], "careful": False}
    assert recorded(capsys, world, **full)["ok"] is True
    assert world.record()["landing"]["reviews"][-1]["floor"] == "full"
    assert next_step(capsys, world)["result"]["step"] == "propose"


@pytest.mark.parametrize("redirect", ["", " >&2"], ids=["stdout", "stderr"])
def test_a_commit_hook_that_refuses_the_items_is_named_and_the_next_run_finds_them(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    redirect: str,
) -> None:
    world = made(tmp_path, monkeypatch)
    upto_review(capsys, world)
    hook = world.checkout / ".git" / "hooks" / "commit-msg"
    hook.write_text(
        '#!/bin/sh\ngrep -q "^backlog: " "$1" || '
        f'{{ echo "subject must start with backlog:"{redirect}; exit 1; }}\n'
    )
    hook.chmod(0o755)
    reviewed(capsys, world, outside=[OVER])
    refused = file_step()(capsys, world)["refusal"]
    assert refused["code"] == "commit"
    assert "subject must start with backlog:" in refused["why"]
    assert "never with --no-verify" in refused["fix"]
    assert f"git -C {world.worktree} commit -m MESSAGE -- {HELD}" in refused["fix"]
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
    judge.same["no licence"] = (Score(score=0.9, path=HELD),)
    words = ("--where", "README.md", "--title", "no licence", "--what", str(what))
    told = lem(capsys, world.checkout, "land", "alike", SLUG, *words)["result"]
    assert told["jev"] == "Jev: not asked (off in the settings)"
    assert judge.asked == []


# The cases of the review round of 2026-11-25 (Astra's findings, each failed before its fix).


def changed(
    capsys: pytest.CaptureFixture[str],
    world: World,
    files: dict[str, str],
    subject: str,
) -> None:
    """A builder's commit of `files` in the worktree, and the checks on it."""
    for path, text in files.items():
        target = world.worktree / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
    run_git(world.worktree, "add", "--all")
    run_git(world.worktree, "commit", "--quiet", "--message", subject)
    assert command("land", "checks", "SLUG")(capsys, world)["ok"] is True


def written_into_record(world: World, change: Callable[[Record], Record]) -> None:
    """A change of the task's record, as another step's command writes it."""
    state = world.checkout / ".lem" / "state"
    found = tasks.read(state, SLUG)
    tasks.update(state, SLUG, change, found.revision)


QUIET = {
    "answered": [],
    "silent": [{"name": "the review agent", "why": "it ended with no files"}],
    "ran": [],
    "careful": None,
    "careful_why": None,
}


def test_a_tip_that_two_silent_reads_left_unread_is_not_green_and_no_agent_merges_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    upto_review(capsys, world)
    reviewed(capsys, world)
    changed(
        capsys, world, {"README.md": "The README says receive, twice.\n"}, "docs: twice"
    )
    reviewed(capsys, world, **QUIET)
    reviewed(capsys, world, **QUIET)
    assert next_step(capsys, world)["result"]["step"] == "propose"
    proposed = proposal(capsys, world)["result"]
    assert proposed["green"] is False
    assert any(one.startswith("not reviewed") for one in proposed["reasons"])
    assert world.record()["landing"]["proposed"]["who_acts"] == "owner"


def test_a_resolution_after_a_must_fix_is_reviewed_whole(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    upto_review(capsys, world)
    reviewed(capsys, world, must_fix=1)
    before = world.told["tip"]
    changed(
        capsys, world, {"NOTES.md": "resolved\n"}, "fix: the conflict and the must-fix"
    )
    after = run_git(world.worktree, "rev-parse", "HEAD")
    resolution = Resolution(
        files=("NOTES.md",), before=before, after=after, base=before
    )
    written_into_record(
        world, lambda found: changes.landing(found, resolution=resolution)
    )
    told = brief(capsys, world)["result"]
    assert (told["floor"], told["brief"].get("resolution")) == ("round", None)


def test_a_resolution_after_a_clean_review_gets_one_read_with_its_range_diff(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    upto_review(capsys, world)
    reviewed(capsys, world)
    before = world.told["tip"]
    changed(capsys, world, {"NOTES.md": "resolved\n"}, "fix: the conflict")
    after = run_git(world.worktree, "rev-parse", "HEAD")
    resolution = Resolution(
        files=("NOTES.md",), before=before, after=after, base=before
    )
    written_into_record(
        world, lambda found: changes.landing(found, resolution=resolution)
    )
    told = brief(capsys, world)["result"]["brief"]
    assert told["resolution"]["files"] == ["NOTES.md"]
    assert told["range_diff"].startswith("git range-diff ")


def test_the_owner_s_careful_word_during_the_landing_asks_for_the_full_set(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    upto_review(capsys, world)
    reviewed(capsys, world)
    assert next_step(capsys, world)["result"]["step"] == "propose"
    said = Taken(
        id=1,
        at=MOMENT,
        what="whether the task is careful",
        chose="careful until its merge",
        why="the README is what a customer reads",
        by="owner",
    )
    written_into_record(
        world, lambda found: replace(found, task=replace(found.task, decisions=(said,)))
    )
    (world.task_folder / "brief.md").write_text("careful: the owner says so\n")
    assert next_step(capsys, world)["result"]["step"] == "read"
    told = brief(capsys, world)["result"]
    assert (told["floor"], told["brief"]["floor_why"]) == (
        "full",
        "the request is careful: the owner says so",
    )
    assert recorded(capsys, world)["refusal"]["code"] == "under-floor"


def test_a_report_of_a_landing_before_does_not_count_again_at_the_same_tip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    upto_review(capsys, world)
    reviewed(capsys, world)
    reviews = world.task_folder / "reviews"
    (reviews / "landing-1").mkdir()
    (reviews / "review-1.json").rename(reviews / "landing-1" / "review-1.json")

    def started_over(found: Record) -> Record:
        landing = found.landing or Landing()
        return changes.landing(found, reviews=(), archived=landing.reviews)

    written_into_record(world, started_over)
    assert brief(capsys, world)["result"]["attempt"] == 1
    old = lem(
        capsys,
        world.checkout,
        "land",
        "read",
        SLUG,
        "--record",
        "reviews/landing-1/review-1.json",
    )
    assert old["refusal"]["code"] == "landing-before"


def test_a_same_whose_open_item_left_the_base_is_filed_again(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    upto_review(capsys, world, base={HELD: HELD_TEXT})
    opened = {**OVER, "bar": "under", "why": "nobody reads it", "open": HELD}
    reviewed(capsys, world, outside=[opened])
    assert file_step()(capsys, world)["result"][0]["disposition"] == "same"
    changed(
        capsys, world, {"README.md": "The README says receive, again.\n"}, "docs: again"
    )
    run_git(world.worktree, "rm", "--quiet", HELD)
    run_git(world.worktree, "commit", "--quiet", "--message", "docs: the item is gone")
    assert command("land", "checks", "SLUG")(capsys, world)["ok"] is True
    reviewed(capsys, world, outside=[CHEAP])
    placed = {one["finding"]: one for one in file_step()(capsys, world)["result"]}
    assert placed["r1.1"]["disposition"] == "item"


def test_an_item_the_owner_set_to_worth_no_keeps_his_no_in_the_record(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    owners = (
        HELD_TEXT.replace("worth: later", "worth: no")
        + "\nDecided against: the owner: no licence yet\n"
    )
    upto_review(capsys, world, base={HELD: owners})
    reviewed(capsys, world, outside=[OVER])
    [placed] = file_step()(capsys, world)["result"]
    assert (placed["path"], placed["worth"]) == (HELD, "no")
    assert commits_of(world) == []


def test_an_edit_of_the_settings_file_s_mode_alone_gets_the_full_set(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    upto_review(capsys, world)
    run_git(world.worktree, "update-index", "--chmod=+x", ".lem/settings.toml")
    run_git(world.worktree, "commit", "--quiet", "--message", "chore: the settings run")
    run_git(world.worktree, "checkout", "--quiet", "--", ".lem/settings.toml")
    assert command("land", "checks", "SLUG")(capsys, world)["ok"] is True
    assert brief(capsys, world)["result"]["floor"] == "full"


def test_jev_and_the_topics_are_the_base_branch_s_when_the_main_checkout_is_on_another(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    upto_review(capsys, world, base={HELD: HELD_TEXT})
    settings = world.checkout / ".lem" / "settings.toml"
    plain = settings.read_text()
    settings.write_text(
        plain
        + '\n[flow]\ntopics = ["a customer is charged"]\n\n[jev]\nfindings = false\n'
    )
    run_git(world.checkout, "commit", "--quiet", "--all", "--message", "chore: no Jev")
    run_git(world.checkout, "checkout", "--quiet", "-b", "elsewhere")
    settings.write_text(plain)
    run_git(
        world.checkout, "commit", "--quiet", "--all", "--message", "chore: Jev again"
    )
    judge = judge_of(world)
    judge.same["no licence"] = (Score(score=0.9, path=HELD),)
    what = tmp_path / "run.txt"
    what.write_text(OVER["what"])
    words = ("--where", "README.md", "--title", "no licence", "--what", str(what))
    told = lem(capsys, world.checkout, "land", "alike", SLUG, *words)["result"]
    assert told["jev"] == "Jev: not asked (off in the settings)"
    assert judge.asked == []
    topics = brief(capsys, world)["result"]["brief"]["inputs"]["topics"]
    assert topics == ["a customer is charged"]


def test_the_review_is_told_of_each_existing_test_the_change_edits(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    upto_review(capsys, world, base={"tests/test_readme.py": "assert True\n"})
    changed(capsys, world, {"tests/test_readme.py": "assert 1\n"}, "test: one")
    told = brief(capsys, world)["result"]["brief"]["inputs"]
    assert told["edited"] == [{"path": "tests/test_readme.py", "kind": "test"}]


def test_again_runs_when_propose_names_it_for_an_open_item_the_owner_set_to_worth_no(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    upto_review(capsys, world, base={HELD: HELD_TEXT})
    reviewed(capsys, world, outside=[{**OVER, "open": HELD}])
    assert file_step()(capsys, world)["result"][0]["disposition"] == "same"
    refuted = HELD_TEXT.replace("worth: later", "worth: no")
    changed(capsys, world, {HELD: refuted}, "docs(backlog): the owner says no")
    reviewed(capsys, world)
    assert next_step(capsys, world)["result"]["step"] == "propose"
    refused = proposal(capsys, world)["refusal"]
    assert refused["code"] == "item-refuted"
    again = file_step("--again")(capsys, world)
    assert again["ok"] is True, again
    assert [(one["disposition"], one["cites"]) for one in again["result"]] == [
        ("item", HELD)
    ]
