"""`lem task open --part-of NAME`: refused when NAME is not a queued task with its branch on
origin, is a part itself, or with `--ticket`; else the part opens and NAME waits for it, once,
also after a run cut off between the two writes."""

from typing import TYPE_CHECKING

import msgspec
import pytest

from fakes.command import lem
from fakes.repo import RealRepo, run_git
from lem.app.tasks import open as opening
from lem.app.tasks.opening import Asked
from lem.kernel.errors import Refusal
from unit.task.spaces import SETTINGS, made, read, refusal, result, workspace

if TYPE_CHECKING:
    from pathlib import Path

    from lem.store.places import Workspace

FEATURE = "save-items"
FEATURE_BRANCH = f"feature/{FEATURE}"
PART = "save-endpoint"
ASK = "the server saves an item and returns it"


def opened(where: Workspace, **words: str) -> opening.Opened:
    """Open the part with `words` over its plain ask."""
    asked = msgspec.convert(
        {"slug": PART, "ask": ASK, "part_of": FEATURE, **words}, Asked
    )
    return opening.opened(where.checkout, asked)


def refused(where: Workspace, **words: str) -> Refusal:
    with pytest.raises(Refusal) as error:
        opened(where, **words)
    assert not (where.state / "tasks" / PART).exists()
    return error.value


def real(tmp_path: Path) -> Workspace:
    """A workspace over a real repository whose origin has the feature's branch, and the
    feature queued on it."""
    repo = RealRepo.init(tmp_path / "repo", {"README.md": b"one\n"})
    repo.outside_commit(FEATURE_BRANCH, {"FEATURE.md": b"the feature\n"})
    where = workspace(repo.checkout)
    made(where, FEATURE, branch=FEATURE_BRANCH)
    return where


def test_a_part_opens_and_its_feature_waits_for_it_once(tmp_path: Path) -> None:
    where = real(tmp_path)
    first = opened(where)
    again = opened(where)
    assert (first.status, first.made, again.made) == ("shaping", True, False)
    assert read(where, PART).task.part_of == FEATURE
    assert read(where, FEATURE).task.after == (PART,)


def test_a_retry_after_a_cut_between_the_writes_puts_the_part_into_its_feature(
    tmp_path: Path,
) -> None:
    where = real(tmp_path)
    # the run that was cut off fetched origin before it wrote the part's record
    run_git(where.checkout, "fetch", "--quiet", "origin")
    made(where, PART, ask=ASK, status="shaping", part_of=FEATURE)
    assert opened(where).made is False
    assert read(where, FEATURE).task.after == (PART,)


def test_the_same_slug_with_another_feature_is_another_request(tmp_path: Path) -> None:
    where = real(tmp_path)
    made(where, PART, ask=ASK, status="shaping")
    with pytest.raises(Refusal) as error:
        opened(where)
    assert error.value.code == "task-exists"
    assert error.value.why.startswith(f"the task {PART} is no part of a feature")
    assert read(where, FEATURE).task.after == ()


def test_a_part_with_a_ticket_is_refused_before_any_look(tmp_path: Path) -> None:
    where = workspace(tmp_path, f'{SETTINGS}[tracker]\nkind = "linear"\n')
    found = refused(where, ticket="ABC-12")
    assert (found.code, found.fix) == (
        "part-of",
        "leave out --ticket: the feature's ticket stands for each of its parts",
    )


def test_a_feature_that_is_not_there_is_refused(tmp_path: Path) -> None:
    found = refused(workspace(tmp_path))
    assert (found.code, found.why) == (
        "part-of",
        f"no task {FEATURE} here, so {PART} cannot be a part of it",
    )


@pytest.mark.parametrize("status", ["shaping", "building", "landed"])
def test_a_feature_that_is_not_queued_is_refused(tmp_path: Path, status: str) -> None:
    where = workspace(tmp_path)
    made(where, FEATURE, status=status, branch=FEATURE_BRANCH)
    found = refused(where)
    assert found.why == (
        f"{FEATURE} is {status}, and a part joins only a feature that is queued and "
        "waits for its parts"
    )
    assert read(where, FEATURE).task.after == ()


def test_a_part_of_a_part_is_refused(tmp_path: Path) -> None:
    where = workspace(tmp_path)
    made(where, FEATURE, branch=FEATURE_BRANCH, part_of="whole-thing")
    found = refused(where)
    assert found.why == (
        f"{FEATURE} is a part of whole-thing, and a part has no parts of its own"
    )
    assert found.fix == (
        f"open {PART} with --part-of whole-thing, or as a task of its own"
    )


def test_a_feature_with_no_branch_on_origin_is_refused(tmp_path: Path) -> None:
    repo = RealRepo.init(tmp_path / "repo", {"README.md": b"one\n"})
    where = workspace(repo.checkout)
    made(where, FEATURE, branch=FEATURE_BRANCH)
    found = refused(where)
    assert found.why == (
        f"{PART} is a part of {FEATURE}, and origin has no branch {FEATURE_BRANCH}"
    )
    assert read(where, FEATURE).task.after == ()


def test_the_command_takes_part_of_and_its_help_says_the_owner(tmp_path: Path) -> None:
    where = real(tmp_path)
    ran = lem(
        "task", "open", PART, "--ask", ASK, "--part-of", FEATURE, cwd=where.checkout
    )
    assert result(ran)["slug"] == PART
    assert read(where, FEATURE).task.after == (PART,)
    ticketed = lem(
        "task",
        "open",
        "other-part",
        "--ask",
        ASK,
        "--part-of",
        FEATURE,
        "--ticket",
        "42",
        cwd=where.checkout,
    )
    assert refusal(ticketed)["code"] == "part-of"
    helped = lem("task", "open", "--help", cwd=where.checkout)
    assert "--part-of" in helped.stdout
    assert "the owner gives no --ticket" in " ".join(helped.stdout.split())
