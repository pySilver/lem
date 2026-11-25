"""Where a check of the criteria runs, and the facts of git it starts from: its two worktrees
beside the task's own, the lock that lets one check of a task run at a time, a stop of the run,
the base it is measured against, and the files it lays over the base (`criteria.remove`,
`onto_of` and `cmd_red` on `main`).

A worktree of the check is `SLUG.red-tip` or `SLUG.red-base` beside the task's worktree; a slug
holds no dot, so `SLUG.red-*` is this task's alone. Each is removed before the run, whatever a
dead run left, and after it, however it ended. The lock is the kernel's, so it goes with its
process: whoever holds it knows that a worktree it finds is a dead run's.
"""

import os
import shutil
from contextlib import contextmanager
from typing import TYPE_CHECKING

from lem.app.landing import checks_git
from lem.app.tasks import where
from lem.kernel import errors, locks
from lem.store import places

if TYPE_CHECKING:
    from collections.abc import Generator, Iterable, Sequence
    from pathlib import Path

    from lem.records.red import RedTest

LOCK = "red.lock"
CODE = "criteria"
BLOB = "blob"
WORKTREE = "worktree"
STOPPED = "the check was stopped, and its commands are ended"
REMOVED = "its worktrees are removed"
JOIN = "; "
STUCK = (
    "{place} could not be removed; remove it yourself: git -C {checkout} worktree remove "
    "--force --force {place}"
)
GIT_FIX = (
    "the owner reads git's words, puts the repository right, and runs the check again"
)


def said(where: Path, *args: str) -> str:
    """What a git that runs no hook answers; a failure is refused in git's words."""
    ran = checks_git.raw(where, *args)
    if ran.returncode:
        words = ran.stderr.decode(errors="replace").strip()
        named = " ".join(args[:2])
        raise errors.Refusal(CODE, f"git {named} failed: {words}", GIT_FIX)
    return ran.stdout.decode(errors="replace").strip()


def onto_of(checkout: Path, base: str) -> str:
    """What the branch is measured against: origin's base branch, or the base branch itself in
    a repository with no origin."""
    ran = checks_git.raw(checkout, "remote", "get-url", "origin")
    return base if ran.returncode else f"origin/{base}"


def laid(worktree: Path, tip: str, tests: Sequence[RedTest]) -> tuple[str, ...]:
    """The files laid over the base, each file a test names; one that is a folder or no file
    on the branch is refused, since a folder would lay the change itself over the base."""
    named = [(test.criterion, name) for test in tests for name in test.files]
    for number, name in named:
        kind = checks_git.kind_at(worktree, tip, name)
        if kind != BLOB:
            kind = "a folder" if kind == "tree" else "not a file"
            raise errors.Refusal(
                CODE,
                f"criterion {number}: {name!r} is {kind} on the branch",
                "name each file that holds the test, one by one and relative to the root: a "
                "folder would lay the change itself over the base commit",
            )
    return tuple(sorted({each for _, each in named}))


def removed(checkout: Path, found: Iterable[Path]) -> tuple[str, ...]:
    """Remove each worktree of the check, a locked one too, and say each that stays. Twice
    `--force`: a worktree with changes, and one that a command locked."""
    gone = sorted(found)
    for doomed in gone:
        checks_git.raw(checkout, WORKTREE, "unlock", str(doomed))
        checks_git.raw(checkout, WORKTREE, "remove", "--force", "--force", str(doomed))
        shutil.rmtree(doomed, ignore_errors=True)
    checks_git.raw(checkout, WORKTREE, "prune")
    entries = checks_git.raw(checkout, WORKTREE, "list", "--porcelain", "-z").stdout
    listed = {
        os.fsdecode(entry).removeprefix("worktree ") for entry in entries.split(b"\0")
    }
    listed.update(str(path) for path in gone if path.exists())
    return tuple(
        STUCK.format(place=path, checkout=checkout)
        for path in gone
        if str(path) in listed
    )


@contextmanager
def kept(checkout: Path, found: tuple[Path, Path], slug: str) -> Generator[None]:
    """Remove both worktrees however the run ends. A worktree that stays is said whatever else
    went wrong: the first failure does not hide it."""
    again = f"lem criteria red {slug} runs the check again"
    try:
        yield
    except errors.Refusal as failure:
        left = JOIN.join(removed(checkout, found)) or REMOVED
        raise errors.Refusal(CODE, f"{failure.why}; {left}", failure.fix) from None
    except InterruptedError:
        left = JOIN.join(removed(checkout, found)) or REMOVED
        raise errors.Refusal(CODE, f"{STOPPED}; {left}", again) from None
    finally:
        stuck = removed(checkout, found)
    if stuck:
        raise errors.Refusal(CODE, JOIN.join(stuck), again)


@contextmanager
def ready(workspace: places.Workspace, slug: str) -> Generator[tuple[Path, Path]]:
    """Hold the task's check lock, remove what a dead run left, and give the two worktrees'
    places, the branch's first, which `kept` removes after the run."""
    parent = where.worktree(workspace, slug).parent
    found = (parent / f"{slug}.red-tip", parent / f"{slug}.red-base")
    with locks.tried(places.task_folder(workspace.state, slug) / LOCK) as stream:
        if stream is None:
            raise errors.Refusal(
                CODE,
                "another check of this task's criteria runs now",
                f"wait for it to end, then run lem criteria red {slug} again",
            )
        old = {*found, *parent.glob(f"{slug}.red-*")}
        stuck = removed(workspace.checkout, old)
        if stuck:
            raise errors.Refusal(
                CODE, JOIN.join(stuck), f"lem criteria red {slug} runs it again"
            )
        with kept(workspace.checkout, found, slug):
            yield found


@contextmanager
def stopped(slug: str) -> Generator[None]:
    """A stop of the run while it is held is refused in the words of a stop: by then what it
    started is ended, and its worktrees are removed (`kept`)."""
    try:
        yield
    except InterruptedError:
        again = f"lem criteria red {slug} runs the check again"
        raise errors.Refusal(CODE, STOPPED, again) from None
