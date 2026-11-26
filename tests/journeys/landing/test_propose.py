"""`lem land propose` end to end, on a real repository and `LocalForge`, with the commands an
agent runs, through the tree in this process (the skeleton's world, `journeys.test_skeleton`).

The hard path of `landing.md` E that this step proves, "Push recorded first": the push is kept
before the forge's call, and a run cut off after any of its effects (the text published, the
push, its record, the pull request opened or edited) proposes again with each effect once. Then
the pull request's text as the owner reads it, a new round that edits the one pull request, a
closed one, an origin that is not on GitHub, and a forge that fails before its pull request.
"""

import dataclasses
from typing import TYPE_CHECKING

import pytest
from msgspec.structs import replace

from fakes.outside import FakeJudge
from fakes.repo import git_env, run_git
from journeys.test_skeleton import (
    JOURNEY,
    MERGE,
    REVIEW,
    SLUG,
    SUBJECT,
    Killed,
    World,
    brief,
    built,
    command,
    due,
    lem,
    made,
    next_step,
    proposal,
    reply,
    review,
    upto,
)
from lem.adapters import forge_gh
from lem.app import wiring
from lem.ports.faults import Unanswered
from lem.ports.place import Place
from lem.records.landing.review import Filed, Finding
from lem.store import tasks

if TYPE_CHECKING:
    from pathlib import Path

    from lem.ports.judge import Defect, NotAsked, Score
    from lem.records.record import Record

PROPOSE = ("land", "propose", "SLUG", "--title", SUBJECT, "--notes")


def propose_with(capsys: pytest.CaptureFixture[str], world: World, notes: str) -> dict:
    """`lem land propose` with the notes `notes`."""
    path = world.written("notes.md", notes)
    return command(*PROPOSE, path)(capsys, world)


def text_of(world: World) -> str:
    """The pull request's text the record cites."""
    named = world.record()["landing"]["proposed"]["text"]
    return (world.task_folder / named).read_text()


def test_the_proposal_gives_the_pull_request_and_its_text_says_what_the_owner_reads(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "propose")
    envelope = proposal(capsys, world)
    assert envelope["ok"] is True, envelope
    found = envelope["result"]
    url = world.forge.url(1)
    assert found["pull"] == {"number": 1, "url": url, "title": SUBJECT}
    assert (found["green"], found["reasons"], found["who_acts"]) == (True, [], "merger")
    assert envelope["say"] == f"pull request {url}: green"
    text = text_of(world)
    assert text == world.forge.bodies[1]
    assert found["text"].startswith("pr-1-")
    lines = text.splitlines()
    assert lines[0].startswith("**Green.**")
    assert "> the README says recieve; fix it" in lines
    assert "## The acceptance criterion" in lines
    assert "- check, `grep -q receive README.md`: exit 0" in lines
    assert (
        "- careful: no; the review says no: one word of the README reaches nothing that "
        "must never go wrong"
    ) in lines
    assert world.record()["task"]["status"] == "open"


def test_a_cut_after_the_push_proposes_with_the_push_on_record_and_one_pull_request(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "propose")
    tip = world.told["tip"]
    world.acts.cut = ("write:pushed", 1)
    with pytest.raises(Killed):
        proposal(capsys, world)
    capsys.readouterr()
    assert world.record()["landing"]["pushed"] == tip
    assert "proposed" not in world.record()["landing"]
    assert due(capsys, world) == "propose"
    assert proposal(capsys, world)["ok"] is True
    counted = world.acts.counted()
    assert (counted["push"], counted["open_pull"], counted["update_pull"]) == (1, 1, 0)


def test_a_cut_after_the_pull_request_was_opened_adopts_it_and_edits_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "propose")
    world.acts.cut = ("open_pull", 1)
    with pytest.raises(Killed):
        proposal(capsys, world)
    capsys.readouterr()
    assert "pull" not in world.record()["landing"]
    assert proposal(capsys, world)["ok"] is True
    counted = world.acts.counted()
    assert (counted["open_pull"], counted["update_pull"]) == (1, 0)
    assert world.record()["landing"]["pull"]["number"] == 1


def test_a_forge_that_fails_before_its_pull_request_keeps_the_task_in_landing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "propose")
    opened, failures = world.forge.open_pull, [True]

    def failing(head: str, base: str, title: str, body: str) -> object:
        if failures:
            failures.pop()
            raise Unanswered("gh", "HTTP 502: Server Error")
        return opened(head, base, title, body)

    monkeypatch.setattr(world.forge, "open_pull", failing)
    faulted = proposal(capsys, world)
    assert (faulted["code"], faulted["ok"]) == (3, False)
    record = world.record()
    assert record["task"]["status"] == "landing"
    assert "proposed" not in record["landing"]
    assert record["landing"]["pushed"] == world.told["tip"]
    assert proposal(capsys, world)["ok"] is True
    assert len(world.forge.pulls) == 1


def test_an_origin_that_is_not_on_github_is_refused_before_anything_is_written_or_pushed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "propose")
    place = Place(checkout=world.checkout, home=tmp_path, environ=git_env())
    ports = wiring.bound(place)
    real = forge_gh.bind(place)
    swapped = dataclasses.replace(ports, forge=real)
    monkeypatch.setattr(wiring, "bound", lambda place: swapped)
    before = world.record()
    refused = proposal(capsys, world)
    assert refused["refusal"]["code"] == "not-github"
    assert world.record() == before
    assert world.repo.head_of(f"docs/{SLUG}") is None
    assert not list(world.task_folder.glob("pr-*.md"))


def again(record: Record) -> Record:
    """The record of a new round, as `lem land start` from `open` writes it (the step
    `land-base`'s): round 2, its start, the phase `preparing`, the task `landing`."""
    landing = record.landing
    assert landing is not None and landing.started is not None
    started = replace(landing.started, round=2)
    landing = replace(landing, round=2, relands=1, phase="preparing", started=started)
    task = replace(record.task, status="landing")
    return replace(record, landing=landing, task=task)


def new_round(
    capsys: pytest.CaptureFixture[str],
    world: World,
    *,
    keep_pull: bool = True,
    teammate: bool = False,
) -> None:
    """A builder's fix after the proposal, and the round's steps up to `propose`; with
    `teammate`, a teammate's commit on the task's branch on origin, which the builder brings
    in first."""
    if teammate:
        world.repo.outside_commit(f"docs/{SLUG}", {"NOTE.md": b"a teammate's line\n"})
        run_git(world.worktree, "fetch", "--quiet", "origin")
        run_git(world.worktree, "merge", "--quiet", "--ff-only", f"origin/docs/{SLUG}")
    (world.worktree / "README.md").write_text("The README says receive, twice.\n")
    run_git(world.worktree, "commit", "--quiet", "--all", "--message", "docs: twice")
    state = world.checkout / ".lem" / "state"
    found = tasks.read(state, SLUG)
    changed = again(found)
    if not keep_pull and changed.landing is not None:
        changed = replace(changed, landing=replace(changed.landing, pull=None))
    tasks.update(state, SLUG, lambda record: changed, found.revision)
    for verb, step in JOURNEY:
        if verb in {"checks", "read", "file"}:
            envelope = step(capsys, world)
            assert envelope["ok"] is True, envelope


@pytest.mark.parametrize("pull", ["on-record", "record-lost"])
def test_a_new_round_edits_the_one_pull_request_and_opens_no_second(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    pull: str,
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "merge-review")
    first = world.forge.bodies[1]
    new_round(capsys, world, keep_pull=pull == "on-record")
    assert due(capsys, world) == "propose"
    world.acts.cut = ("update_pull", 1)
    notes = "- `README.md`: says it twice now; under: one reader reads one line\n"
    with pytest.raises(Killed):
        propose_with(capsys, world, notes)
    capsys.readouterr()
    assert propose_with(capsys, world, notes)["ok"] is True
    counted = world.acts.counted()
    assert (counted["open_pull"], counted["update_pull"], counted["push"]) == (1, 1, 2)
    assert len(world.forge.pulls) == 1
    assert world.forge.bodies[1] != first
    assert "says it twice now" in world.forge.bodies[1]
    assert world.record()["landing"]["proposed"]["text"].startswith("pr-2-")
    assert world.forge.pull(1).head == world.record()["landing"]["pushed"]


def test_a_pull_request_closed_on_the_forge_is_refused_and_named_for_merged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "merge-review")
    world.forge.close(1)
    new_round(capsys, world)
    refused = propose_with(capsys, world, "none\n")
    assert refused["refusal"]["code"] == "closed"
    assert refused["refusal"]["fix"].startswith(
        f"lem land merged {SLUG} writes it dropped"
    )
    assert world.acts.counted()["push"] == 1


def test_notes_with_a_finding_and_no_bar_call_are_refused_before_any_push(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "propose")
    refused = propose_with(capsys, world, "- `README.md`: the second line is long\n")
    assert refused["refusal"]["code"] == "no-bar-call"
    assert world.acts.counted()["push"] == 0
    assert next_step(capsys, world)["result"]["step"] == "propose"
    title = lem(
        capsys,
        world.checkout,
        "land",
        "propose",
        SLUG,
        "--title",
        " ",
        "--notes",
        world.written("notes.md", "none\n"),
    )
    assert title["refusal"]["code"] == "title"


# ---- the review of 2026-11-25 ----

NOTES_OK = "- `README.md`: says it twice now; under: one reader reads one line\n"


def test_a_teammate_commit_the_branch_brought_in_and_the_checks_covered_is_pushed_over(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "merge-review")
    new_round(capsys, world, teammate=True)
    envelope = propose_with(capsys, world, NOTES_OK)
    assert envelope["ok"] is True, envelope
    pushed = world.record()["landing"]["pushed"]
    assert world.repo.head_of(f"docs/{SLUG}") == pushed
    assert world.forge.pull(1).head == pushed
    assert "a teammate's line" in run_git(
        world.repo.origin, "show", f"{pushed}:NOTE.md"
    )


def test_a_finding_whose_item_left_the_tip_is_refused_before_any_push(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "propose")
    state = world.checkout / ".lem" / "state"
    found = tasks.read(state, SLUG)
    landing = found.landing
    assert landing is not None
    review = landing.reviews[-1]
    over = Finding(
        id=f"r{review.attempt}.9",
        level="nit",
        where="README.md",
        title="the README has no license line",
        what="README.md names no license",
        against="over",
    )
    review = replace(
        review,
        findings=(*review.findings, over),
        counts=replace(review.counts, outside=review.counts.outside + 1),
        to_file=(*review.to_file, over.id),
    )
    held = Filed(finding=over.id, disposition="same", path="docs/backlog/no-license.md")
    changed = replace(
        found,
        landing=replace(
            landing,
            reviews=(*landing.reviews[:-1], review),
            filed=(*landing.filed, held),
        ),
    )
    tasks.update(state, SLUG, lambda record: changed, found.revision)
    refused = proposal(capsys, world)
    assert refused["refusal"]["code"] == "item-gone"
    assert world.acts.counted()["push"] == 0
    assert world.forge.pulls == {}


def test_jev_stops_the_proposal_once_for_a_finding_it_reads_over_the_bar(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "propose")
    judge = wiring.bound(
        Place(checkout=world.checkout, home=tmp_path, environ={})
    ).judge
    assert isinstance(judge, FakeJudge)
    line = "- `README.md`: the second line is long; under: one reader reads one line"
    judge.over["`README.md`: the second line is long"] = 0.85
    refused = propose_with(capsys, world, f"{line}\n")
    assert refused["refusal"]["code"] == "jev-over"
    assert "Jev: 0.85" in refused["refusal"]["why"]
    [verdict] = world.record()["landing"]["jev"]
    assert verdict["score"] == 0.85
    assert "path" not in verdict
    assert world.acts.counted()["push"] == 0
    line = line.replace("one reader reads one line", "the reader has no width limit")
    envelope = propose_with(capsys, world, f"{line}\n")
    assert envelope["ok"] is True, envelope
    assert len(judge.asked) == 1
    assert f"{line}; Jev: 0.85" in world.forge.bodies[1].splitlines()


def test_propose_sends_nothing_to_jev_when_the_team_disables_findings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "propose")
    settings = world.checkout / ".lem" / "settings.toml"
    settings.write_text(settings.read_text() + "\n[jev]\nfindings = false\n")
    judge = wiring.bound(
        Place(checkout=world.checkout, home=tmp_path, environ={})
    ).judge
    assert isinstance(judge, FakeJudge)
    notes = "- The README has one long line; under: it fits on the page\n"
    assert propose_with(capsys, world, notes)["ok"]
    assert judge.asked == []
    assert "Jev: not asked (off in the settings)" in world.forge.bodies[1]


def test_propose_keeps_the_first_jev_answer_if_the_second_call_stops(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "propose")
    judge = wiring.bound(
        Place(checkout=world.checkout, home=tmp_path, environ={})
    ).judge
    assert isinstance(judge, FakeJudge)
    first, second = "The README has one long line", "The README has no title"
    notes = (
        f"- {first}; under: it fits on the page\n- {second}; under: it is one line\n"
    )
    judge.over[first] = 0.85
    ask = judge.over_bar

    def interrupted(defect: Defect) -> Score | NotAsked:
        if defect.title == second:
            raise Killed("Jev's second call")
        return ask(defect)

    with monkeypatch.context() as patch:
        patch.setattr(judge, "over_bar", interrupted)
        with pytest.raises(Killed):
            propose_with(capsys, world, notes)
    capsys.readouterr()
    assert [read["score"] for read in world.record()["landing"].get("jev", [])] == [
        0.85
    ]
    assert world.acts.counted()["push"] == 0
    assert propose_with(capsys, world, notes)["refusal"]["code"] == "jev-over"
    assert propose_with(capsys, world, notes)["ok"]
    assert [defect.title for defect in judge.asked] == [first, second]


@pytest.mark.parametrize(
    ("key", "ending"),
    [(False, "not asked (no key for Jev)"), (True, "0.25")],
    ids=["no-key", "below-bar"],
)
def test_a_cut_does_not_ask_jev_again_for_a_nonblocking_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    *,
    key: bool,
    ending: str,
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "propose")
    judge = wiring.bound(
        Place(checkout=world.checkout, home=tmp_path, environ={})
    ).judge
    assert isinstance(judge, FakeJudge)
    title = "The README has one long line"
    judge.key = key
    judge.over[title] = 0.25
    notes = f"- {title}; under: it fits on the page\n"
    world.acts.cut = ("write:pushed", 1)
    with pytest.raises(Killed):
        propose_with(capsys, world, notes)
    capsys.readouterr()
    [before] = world.record()["landing"]["jev"]

    judge.key = True
    judge.over[title] = 0.85
    assert propose_with(capsys, world, notes)["ok"]
    assert world.record()["landing"]["jev"] == [before]
    assert len(judge.asked) == int(key)
    assert f"Jev: {ending}" in world.forge.bodies[1]


def careful_built(capsys: pytest.CaptureFixture[str], world: World) -> dict:
    """The builder's change, which edits Lem's own settings beside the README."""
    (world.worktree / "README.md").write_text("The README says receive.\n")
    settings = world.worktree / ".lem" / "settings.toml"
    settings.write_text(settings.read_text() + "# the checks of the README\n")
    run_git(world.worktree, "commit", "--quiet", "--all", "--message", "docs: receive")
    with (world.task_folder / "criteria.md").open("a") as found:
        found.write("   - no test: the change keeps behavior; the suite holds it\n")
    return {"ok": True}


def test_an_edit_of_lems_settings_needs_the_full_set_and_the_owner_merges_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    for _verb, step in JOURNEY:
        if step is review:
            break
        envelope = (careful_built if step is built else step)(capsys, world)
        assert envelope["ok"] is True, envelope
    # the review's floor knows the edit of Lem's settings (`land-review`): a read is refused,
    # and the full set is taken
    assert review(capsys, world)["refusal"]["code"] == "under-floor"
    full = {**REVIEW, "kind": "full", "left_out": []}
    said = {**full, "attempt": int(world.told["attempt"]), "tip": world.told["tip"]}
    record = world.written("review.json", said)
    taken = command("land", "read", "SLUG", "--record", record)(capsys, world)
    assert taken["ok"] is True, taken
    assert command("land", "file", "SLUG")(capsys, world)["ok"] is True
    notes = "none\n\n## Migration\n\nnone\n"
    envelope = propose_with(capsys, world, notes)
    assert envelope["ok"] is True, envelope
    found = envelope["result"]
    assert (found["careful"], found["who_acts"], found["green"]) == (
        True,
        "owner",
        False,
    )
    assert found["reasons"][0].startswith("careful on the fast track (the change edits")
    assert brief(capsys, world)["ok"] is True
    assert reply(capsys, world)["result"]["verdict"] == "merge"
    assert MERGE(capsys, world)["refusal"]["code"] == "merger-rule"
    assert world.record()["task"]["status"] == "open"
    assert world.forge.pull(found["pull"]["number"]).state == "open"
    assert world.forge.merge_calls == []
