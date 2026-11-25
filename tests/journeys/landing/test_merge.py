"""The merge's end of the landing on a real repository and `LocalForge`, one journey for each
hard path of `landing.md` E whose proof owner is the step `land-merge`: the commands an agent and
the board's server run, each through the tree in this process, as in
`tests/journeys/test_skeleton.py`, whose world this module takes.

Each journey counts the forge's merge calls (as trial R5 does), and the journey of a moved base
is cut off after each of its effects (`Killed`), before its record: `lem land next` names the
cut step again or the one after it, the cut command runs again, and nothing is done twice.
"""

import json
from functools import partial
from typing import TYPE_CHECKING

import pytest
from msgspec.structs import replace

from fakes.repo import run_git
from journeys.test_skeleton import (
    BRANCH,
    JOURNEY,
    MERGE,
    SLUG,
    SUBJECT,
    Killed,
    World,
    brief,
    command,
    made,
    next_step,
    parses,
    proposal,
    upto,
)
from lem.app.landing import changes
from lem.cli import lazy
from lem.kernel import clock
from lem.ports.faults import Unanswered
from lem.store import places, tasks

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from journeys.test_skeleton import Envelope
    from lem.ports.forge_facts import MergeMethod, MergeText, Pull
    from lem.records.landing.record import Landing
    from lem.records.record import Record
    from lem.records.task import Status
    from lem.store.tasks import Change

type Capsys = pytest.CaptureFixture[str]
MERGED = command("land", "merged", "SLUG")
CLEAN = command("land", "clean", "SLUG")
SERVER = command(
    "land",
    "merge",
    "SLUG",
    "--by",
    "owner",
    "--via",
    "server",
    "--standing",
    "--message",
    SUBJECT,
)
SAFE = "Verdict: merge.\nBase: safe. Only NOTES.md moved, and the change reads none of it.\n"
ROUND = "Verdict: merge.\nBase: another round, the moved base renamed what the change reads.\n"


def owner(capsys: Capsys, world: World, *words: str) -> Envelope:
    """The owner's merge of the tip he saw, from the board."""
    tip = world.record()["landing"]["proposed"]["tip"]
    argv = (
        "land",
        "merge",
        "SLUG",
        "--by",
        "owner",
        "--tip",
        tip,
        "--message",
        SUBJECT,
    )
    return command(*argv, *words)(capsys, world)


def answered(capsys: Capsys, world: World, said: str | None) -> Envelope:
    """The merge agent's reply to the brief `lem land merge-review` printed last, or its end
    with no answer."""
    pinned = ("--tip", world.told["tip"], "--base", world.told["base"])
    if said is None:
        return command("land", "merge-review", "SLUG", "--no-answer", *pinned)(
            capsys, world
        )
    reply = world.written("reply.md", said)
    return command("land", "merge-review", "SLUG", "--file", reply, *pinned)(
        capsys, world
    )


def read(capsys: Capsys, world: World, said: str | None) -> Envelope:
    """A brief, and the merge agent's reply to it."""
    briefed = brief(capsys, world)
    assert briefed["ok"] is True, briefed
    return answered(capsys, world, said)


def moved(world: World, name: str = "NOTES.md") -> str:
    """A teammate's commit on origin's base after the checks."""
    return world.repo.outside_commit("main", {name: b"a teammate's later note\n"})


def due(capsys: Capsys, world: World) -> dict[str, str]:
    """What `lem land next` says is due, its next line parsed against the tree."""
    envelope = next_step(capsys, world)
    parses(envelope)
    return {**envelope["result"], "do": envelope["next"]["do"]}


def landing(world: World) -> Envelope:
    return world.record()["landing"]


def calls(world: World) -> int:
    return len(world.forge.merge_calls)


def landed(capsys: Capsys, world: World) -> None:
    """`merged` and `clean` run, and the task landed with its landing ended."""
    for step in (MERGED, CLEAN):
        envelope = step(capsys, world)
        assert envelope["ok"] is True, envelope
    assert world.record()["task"]["status"] == "landed"
    assert landing(world)["phase"] == "ended"


def text_of(world: World) -> str:
    return world.forge.bodies[1]


# ---- the merge read: a moved base, its safe read, another round, answers it cannot record ----


def test_a_moved_base_is_refused_read_with_what_moved_and_merged_on_a_safe_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "merge")
    moved(world)
    assert due(capsys, world)["step"] == "merge-review"
    assert MERGE(capsys, world)["refusal"]["code"] == "not-due"
    assert calls(world) == 0
    assert "refused" not in landing(world)
    media = world.task_folder / "media"
    media.mkdir()
    (media / "detail").mkdir()
    for name in ("after.png", "detail/phone.WEBP", ".hidden.png", "notes.txt"):
        (media / name).write_bytes(b"an artifact")
    briefed = brief(capsys, world)
    facts = (tmp_path / briefed["result"]["brief"]).read_text()
    shown = json.loads(facts.split("```json\n", 1)[1].split("\n```", 1)[0])
    assert shown["task_directory"] == str(world.task_folder)
    assert shown["pictures"] == ["media/after.png", "media/detail/phone.WEBP"]
    assert '"checkout": "gh pr checkout 1"' in facts
    assert facts.startswith("Read `skills/lem/prompts/merge.md`")
    assert "https://github.com/owner/project/pull/1" in facts
    assert '"files": [\n      "NOTES.md"\n    ]' in facts
    assert '"overlap": []' in facts
    assert briefed["next"]["do"] == "spawn"
    assert (
        f"--tip {world.told['tip']} --base {world.told['base']}"
        in briefed["next"]["command"]
    )
    safe = answered(capsys, world, SAFE)
    assert safe["result"]["base_call"] == "safe"
    assert MERGE(capsys, world)["ok"] is True
    assert calls(world) == 1
    body = run_git(world.repo.origin, "log", "-1", "--format=%B", "main")
    assert "it merged on main at" in body
    assert "Only NOTES.md moved" in body
    assert body.rstrip().endswith(f"Lem task: {SLUG}")
    landed(capsys, world)
    assert "after the merge agent's read of what moved: Only NOTES.md moved" in text_of(
        world
    )
    assert landing(world)["merged"].get("text_updated", True) is True
    assert landing(world)["proposed"]["text"].startswith("pr-1-")


def test_a_safe_read_covers_its_base_and_no_later_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "merge")
    moved(world)
    assert read(capsys, world, SAFE)["ok"] is True
    moved(world, "LATER.md")
    assert due(capsys, world)["step"] == "merge-review"
    assert MERGE(capsys, world)["refusal"]["code"] == "not-due"
    assert read(capsys, world, SAFE)["ok"] is True
    assert MERGE(capsys, world)["ok"] is True
    assert calls(world) == 1


def test_a_read_that_says_another_round_makes_a_new_round_and_no_new_brief(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "merge")
    moved(world)
    said = read(capsys, world, ROUND)
    assert said["result"]["base_call"] == "another round"
    assert due(capsys, world)["step"] == "start"
    assert (
        command("land", "merge-review", "SLUG")(capsys, world)["refusal"]["code"]
        == "not-due"
    )
    assert calls(world) == 0


def test_two_unusable_answers_on_an_unmoved_base_call_the_owner_and_no_read_is_due(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "merge-review")
    first = read(capsys, world, "It looks fine to me.\n")
    assert first["refusal"]["code"] == "no-verdict"
    assert due(capsys, world)["step"] == "merge-review"
    second = read(capsys, world, "Looks good.\nVerdict: merge.\n")
    assert second["ok"] is True
    assert second["result"].get("verdict") is None
    assert "`Verdict: merge.`" in second["result"]["why"]
    now = due(capsys, world)
    assert (now["step"], now["by"], now["do"]) == ("merge", "owner", "wait")
    assert MERGE(capsys, world)["refusal"]["code"] == "merger-rule"
    assert calls(world) == 0
    briefs = sorted((world.task_folder).glob("merge-brief-*.md"))
    assert len(briefs) == 1


def test_no_answer_twice_is_an_unusable_answer_twice(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "merge-review")
    assert read(capsys, world, None)["refusal"]["code"] == "no-verdict"
    second = answered(capsys, world, None)
    assert second["result"]["why"].endswith("its last try ended with no answer")
    assert due(capsys, world)["by"] == "owner"


def test_two_unusable_answers_on_a_moved_base_are_another_round(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "merge")
    moved(world)
    assert read(capsys, world, "Verdict: merge.\n")["refusal"]["code"] == "no-verdict"
    second = answered(capsys, world, None)
    assert second["result"]["base_call"] == "another round"
    assert "could not be recorded twice" in second["result"]["why"]
    review = (world.task_folder / "merge-review.md").read_text()
    assert review.startswith(
        "No answer of the merge agent: the merge agent's answer could"
    )
    assert due(capsys, world)["step"] == "start"
    assert calls(world) == 0


# ---- the owner's word: a stale tap, his merge refused for the base, GitHub's refusal ----


def test_a_stale_tap_merges_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "merge")
    old = "0" * 40
    argv = (
        "land",
        "merge",
        "SLUG",
        "--by",
        "owner",
        "--tip",
        old,
        "--message",
        SUBJECT,
    )
    refused = command(*argv)(capsys, world)["refusal"]
    assert refused["code"] == "tip"
    assert calls(world) == 0
    assert "intent" not in landing(world)


def test_the_owners_merge_refused_for_the_base_stands_and_the_server_merges_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "merge")
    moved(world)
    assert owner(capsys, world)["refusal"]["code"] == "base"
    kept = landing(world)
    assert (kept["refused"]["by"], kept["standing"]["by_act"]) == ("owner", "session")
    assert due(capsys, world)["step"] == "start"
    for verb in ("start", "base", "checks"):
        assert command("land", verb, "SLUG")(capsys, world)["ok"] is True
    assert proposal(capsys, world)["ok"] is True
    assert due(capsys, world)["step"] == "merge"
    assert SERVER(capsys, world)["ok"] is True
    assert calls(world) == 1
    assert landing(world)["merged"]["by"] == "owner"


def test_after_githubs_refusal_the_owners_word_lands_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "merge")
    world.forge.refuse = "Required status check is expected"
    assert MERGE(capsys, world)["refusal"]["code"] == "github"
    assert MERGE(capsys, world)["refusal"]["code"] == "github"
    assert calls(world) == 1
    world.forge.refuse = None
    assert owner(capsys, world)["ok"] is True
    assert calls(world) == 2
    landed(capsys, world)


# ---- a stop, a lost reply and a fault around the merge call ----


def test_a_transport_fault_before_the_call_keeps_nothing_and_the_next_try_lands(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "merge")
    pull, faults = world.forge.pull, [True]

    def flaky(number: int) -> object:
        if faults:
            faults.pop()
            raise Unanswered("gh", "error connecting to api.github.com")
        return pull(number)

    monkeypatch.setattr(world.forge, "pull", flaky)
    before = world.record()
    assert MERGE(capsys, world)["code"] == 3
    assert world.record() == before
    assert calls(world) == 0
    assert MERGE(capsys, world)["ok"] is True
    assert calls(world) == 1


def lose(monkeypatch: pytest.MonkeyPatch, world: World) -> None:
    """The forge's merge call fails once before it reaches GitHub."""
    merge, lost = world.forge.merge, [True]

    def call(number: int, head: str, method: MergeMethod, text: MergeText) -> object:
        if lost:
            lost.pop()
            raise Unanswered("gh", "error connecting to api.github.com")
        return merge(number, head, method, text)

    monkeypatch.setattr(world.forge, "merge", call)


def test_with_only_an_open_pull_request_a_new_call_goes_on_the_owners_word_alone(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "merge")
    lose(monkeypatch, world)
    assert MERGE(capsys, world)["code"] == 3
    assert landing(world)["intent"]["by"] == "merger"
    for again in (
        MERGE,
        command(
            "land", "merge", "SLUG", "--by", "owner", "--via", "server", "--standing"
        ),
    ):
        assert again(capsys, world)["refusal"]["code"] in {"intent", "tip"}
    refused = MERGE(capsys, world)["refusal"]
    assert refused["fix"].startswith(
        "the owner checks https://github.com/owner/project/pull/1"
    )
    assert calls(world) == 0
    assert owner(capsys, world)["refusal"]["code"] == "intent"
    assert owner(capsys, world, *checked(refused))["ok"] is True
    assert calls(world) == 1
    acts = [
        entry for entry in world.record()["journal"] if entry["kind"] == "owner-act"
    ]
    assert acts[-1]["option"].startswith("open at ")
    landed(capsys, world)


def checked(refused: Envelope) -> tuple[str, str]:
    """The owner's word after his check, as the refusal that asked him for it names it."""
    return ("--checked", refused["fix"].rsplit("--checked ", 1)[1])


def test_a_replay_of_the_owners_own_command_after_a_lost_reply_sends_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "merge")
    lose(monkeypatch, world)
    assert owner(capsys, world)["code"] == 3
    assert landing(world)["intent"]["by"] == "owner"
    refused = owner(capsys, world)["refusal"]
    assert refused["code"] == "intent"
    assert calls(world) == 0
    stale = owner(capsys, world, "--checked", "20200101T000000Z")["refusal"]
    assert stale["code"] == "intent"
    assert calls(world) == 0
    assert owner(capsys, world, *checked(refused))["ok"] is True
    assert calls(world) == 1


def test_the_owners_checked_word_with_no_call_on_record_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "merge")
    refused = owner(capsys, world, "--checked", "20261125T100000Z")["refusal"]
    assert refused["code"] == "checked"
    assert calls(world) == 0


def test_a_merge_lock_that_cannot_be_opened_is_a_refusal_that_keeps_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "merge")
    (world.checkout / ".lem" / "state" / "locks" / "merge.lock").mkdir(parents=True)
    before = world.record()
    envelope = MERGE(capsys, world)
    assert envelope["code"] == 1
    assert envelope["refusal"]["code"] == "merge-lock"
    assert world.record() == before
    assert calls(world) == 0


# ---- the forge's answers: a queue, a text edit that fails, a retarget, a merge between ----


def test_a_queue_that_took_the_call_is_written_and_merged_handles_its_end(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "merge")
    world.forge.queue = True
    assert MERGE(capsys, world)["result"]["queued"] == "the merge queue"
    assert due(capsys, world)["step"] == "merged"
    assert MERGED(capsys, world)["refusal"]["code"] == "queued"
    world.forge.settle(1)
    landed(capsys, world)
    assert calls(world) == 1


def test_a_queue_that_ends_with_no_merge_keeps_githubs_words(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "merge")
    world.forge.queue = True
    assert MERGE(capsys, world)["ok"] is True
    world.forge.dequeue(1, "a required check failed in the queue")
    refused = MERGED(capsys, world)["refusal"]
    assert (
        refused["code"],
        refused["why"].endswith("a required check failed in the queue"),
    ) == (
        "github",
        True,
    )
    assert "accepted" not in landing(world)
    now = due(capsys, world)
    assert (now["step"], now["by"]) == ("merge", "owner")


def test_a_failed_edit_of_the_text_leaves_it_waiting_and_merged_tries_again(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "merge")
    moved(world)
    assert read(capsys, world, SAFE)["ok"] is True
    assert MERGE(capsys, world)["ok"] is True
    world.forge.fail_edits = True
    failed = MERGED(capsys, world)
    assert (failed["code"], failed["refusal"]["code"]) == (1, "text")
    kept = landing(world)
    assert kept["merged"]["text_updated"] is False
    assert kept["proposed"]["text_waits"].startswith("pr-1-")
    assert world.record()["task"]["status"] == "open"
    assert due(capsys, world)["step"] == "merged"
    world.forge.fail_edits = False
    landed(capsys, world)
    assert text_of(world).count("Only NOTES.md moved") == 1
    assert "text_waits" not in landing(world)["proposed"]


def test_a_retarget_before_the_merge_is_refused_with_the_edit_that_puts_it_back(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "merge")
    world.forge.retarget(1, "release")
    refused = MERGE(capsys, world)["refusal"]
    assert (refused["code"], refused["fix"]) == (
        "target",
        f"gh pr edit 1 --base main, then lem land merge {SLUG} again",
    )
    assert calls(world) == 0


def test_a_retarget_after_the_locked_read_is_no_landing_and_cleans_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "merge")
    world.repo.outside_commit("release", {"RELEASE.md": b"a release\n"})
    merge = world.forge.merge

    def retargeted(
        number: int, head: str, method: MergeMethod, text: MergeText
    ) -> object:
        world.forge.retarget(number, "release")
        return merge(number, head, method, text)

    monkeypatch.setattr(world.forge, "merge", retargeted)
    refused = MERGE(capsys, world)["refusal"]
    assert refused["code"] == "target"
    kept = landing(world)
    assert (kept["refused"]["kind"], kept["phase"]) == ("target", "open")
    assert world.record()["task"]["status"] == "open"
    now = due(capsys, world)
    assert (now["step"], now["do"]) == ("wait", "wait")
    assert CLEAN(capsys, world)["refusal"]["code"] == "not-due"
    assert world.worktree.is_dir()
    assert calls(world) == 1


def test_a_merge_on_github_between_the_look_and_the_call_lands_uncovered(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "merge")
    merge = world.forge.merge

    def between(number: int, head: str, method: MergeMethod, text: MergeText) -> object:
        moved(world, "BETWEEN.md")
        return merge(number, head, method, text)

    monkeypatch.setattr(world.forge, "merge", between)
    made_merge = MERGE(capsys, world)
    assert made_merge["ok"] is True, made_merge
    uncovered = landing(world)["merged"]["uncovered"]
    assert "which no read of the merge agent covered" in uncovered
    landed(capsys, world)
    assert uncovered in text_of(world)
    states = [entry for entry in world.record()["journal"] if entry["kind"] == "state"]
    assert uncovered in states[-1]["line"]


def test_a_merge_that_keeps_the_branchs_commits_rebases_and_its_parent_is_the_old_base(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    settings = world.checkout / ".lem" / "settings.toml"
    settings.write_text(settings.read_text().replace('"squash"', '"keep"'))
    run_git(world.checkout, "commit", "--quiet", "--all", "--message", "keep history")
    run_git(world.checkout, "push", "--quiet", "origin", "main")
    upto(capsys, world, "merge")
    before = world.repo.head_of("main")
    keep = command("land", "merge", "SLUG", "--by", "merger")
    assert (
        command("land", "merge", "SLUG", "--by", "merger", "--message", SUBJECT)(
            capsys, world
        )["refusal"]["code"]
        == "message"
    )
    assert keep(capsys, world)["ok"] is True
    merged = landing(world)["merged"]
    assert (merged["parent"], merged["base_merged"]) == (before, before)
    assert (
        run_git(world.repo.origin, "log", "-1", "--format=%s", "main")
        == "docs: receive"
    )
    landed(capsys, world)


def test_a_main_checkout_that_cannot_follow_is_left_with_gits_words(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "merge")
    (world.checkout / "LOCAL.md").write_text("a commit of the owner's own\n")
    run_git(world.checkout, "add", "LOCAL.md")
    run_git(world.checkout, "commit", "--quiet", "--message", "the owner's own")
    assert MERGE(capsys, world)["ok"] is True
    landed(capsys, world)
    left = landing(world)["merged"]["left_behind"]
    assert (
        "did not follow origin/main, and nothing in it was changed; git said:" in left
    )


# ---- the end: a request closed on GitHub, and every case of the cleanup ----


@pytest.mark.parametrize("end", ["lem", "github", "closed"])
def test_a_reviewers_item_leaves_when_its_task_lands(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys, end: str
) -> None:
    world = made(tmp_path, monkeypatch)
    places.state_of(world.checkout)
    path = ".lem/state/backlog/lessons.md"
    item = world.checkout / path
    item.parent.mkdir(parents=True)
    item.write_text("# Fix the spelling in the README\n")
    opened = command("task", "open", "SLUG", "--ask", path, "--item", path)
    claim = opened(capsys, world)
    assert claim["ok"] is True, claim
    for verb, step in JOURNEY[1:]:
        if verb == "merge":
            break
        completed = step(capsys, world)
        assert completed["ok"] is True, completed
    if end == "lem":
        assert MERGE(capsys, world)["ok"] is True
    elif end == "github":
        world.forge.outside_merge(1)
    else:
        world.forge.close(1)
    assert item.is_file()
    assert MERGED(capsys, world)["ok"] is True
    assert item.is_file() is (end == "closed")
    assert world.record()["task"]["status"] == (
        "dropped" if end == "closed" else "landed"
    )


def test_a_request_closed_on_github_drops_the_task_and_keeps_its_commits(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "merge")
    world.forge.close(1)
    assert due(capsys, world)["step"] == "merged"
    assert MERGED(capsys, world)["ok"] is True
    record = world.record()
    assert record["task"]["status"] == "dropped"
    assert record["journal"][-1]["line"].startswith(
        "the pull request was closed on the forge"
    )
    assert due(capsys, world)["step"] == "clean"
    cleaned = CLEAN(capsys, world)["result"]
    assert "the dropped task's commits" in cleaned["branch_left"]
    assert not world.worktree.exists()
    assert run_git(world.checkout, "branch", "--list", BRANCH) != ""
    assert world.repo.head_of(BRANCH) is not None
    assert due(capsys, world)["step"] == "done"
    assert calls(world) == 0


def merged_and_noted(capsys: Capsys, world: World) -> None:
    """The merge and its bookkeeping, before the cleanup."""
    for step in (MERGE, MERGED):
        assert step(capsys, world)["ok"] is True


def test_a_branch_rebased_after_its_push_goes_when_it_holds_the_same_change(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "merge")
    merged_and_noted(capsys, world)
    run_git(
        world.worktree,
        "commit",
        "--quiet",
        "--amend",
        "--message",
        "docs: receive, again",
    )
    cleaned = CLEAN(capsys, world)["result"]
    assert cleaned["branch_gone"] is True
    assert cleaned["rebased"] is True
    assert run_git(world.checkout, "branch", "--list", BRANCH) == ""


def test_a_branch_changed_after_its_push_stays_with_the_commands_that_show_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "merge")
    merged_and_noted(capsys, world)
    (world.worktree / "README.md").write_text("The README says receive, twice.\n")
    run_git(
        world.worktree, "commit", "--quiet", "--all", "--amend", "--message", "other"
    )
    cleaned = CLEAN(capsys, world)["result"]
    assert cleaned["branch_gone"] is False
    assert "`git range-diff" in cleaned["branch_left"]
    assert cleaned["forge_branch_gone"] is True
    assert world.repo.head_of(BRANCH) is None


def test_a_commit_after_the_merged_head_keeps_the_branch_and_its_copy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "merge")
    merged_and_noted(capsys, world)
    (world.worktree / "MORE.md").write_text("one more\n")
    run_git(world.worktree, "add", "MORE.md")
    run_git(world.worktree, "commit", "--quiet", "--message", "one more")
    refused = CLEAN(capsys, world)["refusal"]
    assert refused["code"] == "unmerged"
    assert "commits after the head the forge merged" in refused["why"]
    assert world.worktree.is_dir()
    assert world.repo.head_of(BRANCH) is not None


def test_the_forges_copy_goes_only_at_the_merged_head_and_a_failed_deletion_is_due_again(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "merge")
    merged_and_noted(capsys, world)
    delete, fails = world.forge.delete_ref, [True]

    def once(name: str, expect: str) -> bool:
        if fails:
            fails.pop()
            return False
        return delete(name, expect)

    monkeypatch.setattr(world.forge, "delete_ref", once)
    assert CLEAN(capsys, world)["refusal"]["code"] == "not-deleted"
    assert due(capsys, world)["step"] == "clean"
    assert CLEAN(capsys, world)["ok"] is True
    assert world.repo.head_of(BRANCH) is None


def test_a_forge_copy_someone_pushed_to_after_the_merge_stays(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "merge")
    merged_and_noted(capsys, world)
    pushed = world.repo.outside_commit(BRANCH, {"LATE.md": b"late\n"})
    cleaned = CLEAN(capsys, world)["result"]
    assert (cleaned["branch_gone"], cleaned["forge_branch_gone"]) == (True, False)
    assert world.repo.head_of(BRANCH) == pushed


def test_a_dirty_worktree_is_not_cleaned(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "merge")
    merged_and_noted(capsys, world)
    (world.worktree / "mine.txt").write_text("the owner's own file\n")
    assert CLEAN(capsys, world)["refusal"]["code"] == "dirty"
    assert (world.worktree / "mine.txt").is_file()


def ended_as(state: Path, status: Status) -> None:
    """The task moved to `status` as a drop or an answer writes it."""
    record = tasks.read(state, SLUG)
    change = partial(changes.moved, status=status, line=status, now=clock.now())
    tasks.update(state, SLUG, change, record.revision)


ENDS: tuple[Status, ...] = ("dropped", "answered")


@pytest.mark.parametrize("status", ENDS)
def test_a_dropped_or_answered_tasks_branch_stays_with_its_commits(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys, status: Status
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "start")
    ended_as(world.checkout / ".lem" / "state", status)
    assert due(capsys, world)["step"] == "clean"
    cleaned = CLEAN(capsys, world)["result"]
    assert cleaned["branch_gone"] is False
    assert f"git branch -D {BRANCH}" in cleaned["branch_left"]
    assert not world.worktree.exists()
    assert due(capsys, world)["step"] == "done"


# ---- the journey of a moved base, cut off after each of its effects ----


def observed(monkeypatch: pytest.MonkeyPatch, world: World) -> None:
    """Count, and let a test cut after, the writes of the merge's end that the skeleton does
    not name: a read, a refusal kept, the text confirmed, the task landed."""
    update = tasks.update

    def written(state: Path, slug: str, change: Change, expect: int) -> Record:
        before = tasks.read(state, slug)
        after = update(state, slug, change, expect)
        for name in news(before, after):
            world.acts.after(f"write:{name}")
        return after

    monkeypatch.setattr(tasks, "update", written)


def news(before: Record, after: Record) -> list[str]:
    """What a write newly holds: a read, a refusal, the merge's text, the task landed."""
    was: Landing | None = before.landing
    now: Landing | None = after.landing
    if now is None:
        return []
    reads = len(was.reads) if was else 0
    texted = bool(was and was.merged and was.merged.text_updated)
    found = [
        ("read", len(now.reads) > reads),
        ("refused", now.refused is not None and (was is None or was.refused is None)),
        ("text", bool(now.merged and now.merged.text_updated) and not texted),
        ("landed", after.task.status == "landed" != before.task.status),
    ]
    return [name for name, new in found if new]


def merged_on_the_recheck(capsys: Capsys, world: World) -> Envelope:
    """The standing merge; after a stop between the intent and the call, the owner's
    word after his check of GitHub, as the refusal names it."""
    found = SERVER(capsys, world)
    if found.get("refusal", {}).get("code") == "intent":
        return owner(capsys, world, *checked(found["refusal"]))
    return found


def tapped(capsys: Capsys, world: World) -> Envelope:
    """The owner's merge of the tip he saw, on a base that moved: refused for the base."""
    return owner(capsys, world)


# The steps after origin's base moved, each with the step `lem land next` names before it and
# the refusal it ends with, if any.
FLOW: tuple[tuple[str, Callable[[Capsys, World], Envelope], str | None], ...] = (
    ("merge", tapped, "base"),
    ("start", command("land", "start", "SLUG"), None),
    ("base", command("land", "base", "SLUG"), None),
    ("checks", command("land", "checks", "SLUG"), None),
    ("propose", proposal, None),
    ("merge", merged_on_the_recheck, None),
    ("merged", MERGED, None),
    ("clean", CLEAN, None),
)
CUTS = (
    ("write:refused", 1),
    ("rebase", 2),
    ("write:read", 2),
    ("write:intent", 1),
    ("merge", 1),
    ("write:merged", 1),
    ("publish:pr", 2),
    ("update_pull", 1),
    ("write:text", 1),
    ("fast_forward", 1),
    ("write:landed", 1),
    ("worktree_remove", 1),
    ("branch_delete", 1),
    ("delete_ref", 1),
    ("write:ended", 1),
)


def ended(capsys: Capsys, world: World, at: int) -> bool:
    """After a kill in the step at `at`: whether that step is due again; else the write it
    was killed after ended it, and the next one is due."""
    verb = FLOW[at][0]
    found = due(capsys, world)["step"]
    if found == verb:
        return False
    later = [name for name, _, _ in FLOW[at + 1 :] if name != verb]
    assert found == (later[0] if later else "done"), (verb, found)
    return True


def flowed(capsys: Capsys, world: World) -> list[str]:
    """The steps after the move; a cut step runs again when it is due again. Gives the cut
    steps."""
    cut: list[str] = []
    for at, (verb, step, code) in enumerate(FLOW):
        try:
            envelope = step(capsys, world)
        except Killed:
            capsys.readouterr()
            cut.append(verb)
            if ended(capsys, world, at):
                continue
            envelope = step(capsys, world)
        if code is None:
            assert envelope["ok"] is True, envelope
        else:
            assert envelope["refusal"]["code"] == code, envelope
        parses(envelope)
    return cut


@pytest.mark.parametrize("cut", CUTS, ids=[f"{name}-{count}" for name, count in CUTS])
def test_a_cut_after_an_effect_of_a_merge_on_a_moved_base_does_nothing_twice(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: Capsys,
    cut: tuple[str, int],
) -> None:
    world = made(tmp_path, monkeypatch)
    observed(monkeypatch, world)
    upto(capsys, world, "merge")
    moved(world)
    world.acts.cut = cut
    assert len(flowed(capsys, world)) == 1
    assert world.acts.cut is None
    assert world.record()["task"]["status"] == "landed"
    assert landing(world)["phase"] == "ended"
    counted = world.acts.counted()
    assert calls(world) == 1
    for act in (
        "merge",
        "update_pull",
        "fast_forward",
        "worktree_remove",
        "delete_ref",
    ):
        assert counted[act] == 1, act
    assert (
        landing(world)["merged"]["base_checked"]
        == landing(world)["merged"]["base_merged"]
    )
    assert world.repo.head_of(BRANCH) is None
    proposed = landing(world)["proposed"]
    assert "text_waits" not in proposed
    cited = (world.task_folder / proposed["text"]).read_text()
    assert cited == text_of(world)


@pytest.mark.parametrize(
    "words",
    [
        ("merge-review", "SLUG", "--file", "reply.md", "--no-answer"),
        ("merge-review", "SLUG", "--tip", "0" * 40),
        ("merge", "SLUG", "--by", "merger", "--standing"),
    ],
    ids=["an answer and none", "a tip with no answer", "the merger's standing merge"],
)
def test_a_wrong_call_of_the_merges_words_is_exit_2_before_any_look(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: Capsys,
    words: tuple[str, ...],
) -> None:
    world = made(tmp_path, monkeypatch)
    argv = [
        "--repo",
        str(world.checkout),
        "land",
        *(SLUG if w == "SLUG" else w for w in words),
    ]
    assert lazy.main(argv) == 2
    capsys.readouterr()
    assert world.acts.done == []


def again(state: Path) -> None:
    """A new round begun, as `lem land start` of an open task writes it (the step
    `land-base` builds that start): the task landing, its landing preparing round 2."""
    record = tasks.read(state, SLUG)

    def begun(before: Record) -> Record:
        moved = changes.moved(before, "landing", "a new round", clock.now())
        return changes.landing(moved, phase="preparing", round=2, relands=1)

    tasks.update(state, SLUG, begun, record.revision)


def test_a_merge_on_github_while_a_new_round_runs_is_written_down_and_lands(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "merge")
    (world.worktree / "MORE.md").write_text("one more\n")
    run_git(world.worktree, "add", "MORE.md")
    run_git(world.worktree, "commit", "--quiet", "--message", "one more")
    assert due(capsys, world)["step"] == "start"
    again(world.checkout / ".lem" / "state")
    world.forge.outside_merge(1)
    assert due(capsys, world)["step"] == "merged"
    bookkept = MERGED(capsys, world)
    assert bookkept["ok"] is True, bookkept
    assert world.record()["task"]["status"] == "landed"
    assert landing(world)["merged"]["via"] == "github"


def test_a_linked_worktree_that_holds_the_base_follows_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "merge")
    run_git(world.checkout, "switch", "--quiet", "-c", "elsewhere")
    holder = tmp_path / "base-checkout"
    run_git(world.checkout, "worktree", "add", "--quiet", str(holder), "main")
    assert MERGE(capsys, world)["ok"] is True
    assert MERGED(capsys, world)["ok"] is True
    assert "left_behind" not in landing(world)["merged"]
    assert run_git(holder, "rev-parse", "HEAD") == world.repo.head_of("main")


def test_a_request_closed_on_github_while_a_new_round_runs_is_dropped_by_merged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "merge")
    again(world.checkout / ".lem" / "state")
    world.forge.close(1)
    assert due(capsys, world)["step"] != "merged"
    assert MERGED(capsys, world)["ok"] is True
    assert world.record()["task"]["status"] == "dropped"


@pytest.mark.parametrize("state", ["closed", "merged", "reply", "drop"])
def test_a_foreign_pull_at_the_recorded_number_cannot_end_the_task(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys, state: str
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "merge")
    if state == "closed":
        world.forge.close(1)
    elif state != "reply":
        world.forge.outside_merge(1)
    pull = world.forge.pull

    def foreign(number: int) -> Pull:
        shown = pull(number)
        if state == "reply" and shown.state == "open":
            return shown
        return replace(shown, url="https://github.com/other/project/pull/1")

    monkeypatch.setattr(world.forge, "pull", foreign)
    drop = command("task", "move", "SLUG", "dropped", "--line", "the owner drops it")
    step = {"reply": MERGE, "drop": drop}.get(state, MERGED)
    envelope = step(capsys, world)
    assert envelope.get("refusal", {}).get("code") == "no-pull", envelope
    assert world.record()["task"]["status"] == "open"
    assert landing(world)["phase"] == "open"


def test_drop_recovers_a_matching_merge_after_the_pull_number_was_lost(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "propose")
    world.acts.cut = ("open_pull", 1)
    with pytest.raises(Killed):
        proposal(capsys, world)
    capsys.readouterr()
    assert "pull" not in landing(world)
    assert landing(world)["pushed"] == world.forge.pull(1).head
    world.forge.outside_merge(1)

    drop = command("task", "move", "SLUG", "dropped", "--line", "the owner drops it")
    envelope = drop(capsys, world)
    assert envelope.get("refusal", {}).get("code") == "merged", envelope
    assert landing(world)["pull"]["number"] == 1
    assert MERGED(capsys, world)["ok"] is True
    assert world.record()["task"]["status"] == "landed"
