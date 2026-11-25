"""`lem land start`: a round of the landing begins, and the task is `landing`. It has no effect
outside the record: a task whose project names no command of the checks is blocked, and an
open task whose pull request the forge calls conflicting starts its new round with
`--conflicting` whatever step was due."""

import tomllib
from functools import partial
from typing import TYPE_CHECKING

import msgspec

from lem.app.landing import frame, say, step
from lem.kernel import clock
from lem.kernel.envelope import Envelope
from lem.kernel.errors import Refusal
from lem.model.landing import begin, start
from lem.store import places, steps, tasks

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.landing.start import Started

SETTINGS = ".lem/settings.toml"


class Own(msgspec.Struct, frozen=True, kw_only=True):
    """The checks a branch's own settings name."""

    commands: tuple[str, ...] = ()


class Branched(msgspec.Struct, frozen=True, kw_only=True):
    """The tables of a branch's own settings that `start` reads."""

    checks: Own = Own()


def own_commands(context: frame.Context) -> tuple[str, ...]:
    """The commands of the checks the branch's own settings name at its tip, read only while
    the main checkout's name none; none where the file is not there or not TOML."""
    world = context.world
    if world.rules.commands or world.tip is None:
        return ()
    found = context.ports.git.show(context.worktree, world.tip, SETTINGS)
    try:
        return msgspec.convert(
            tomllib.loads((found or b"").decode()), Branched
        ).checks.commands
    except tomllib.TOMLDecodeError, UnicodeDecodeError, msgspec.ValidationError:
        return ()


def act(context: frame.Context, *, conflicting: bool) -> Started:
    """Record the start of the round, or the block of a task with no command of the checks."""
    record, world = context.record, context.world
    facts = start.Facts(
        on_branch=world.local == world.tip, own_commands=own_commands(context)
    )
    started = start.decide(record, world, facts, conflicting=conflicting)
    if isinstance(started, Refusal):
        if started.code == "no-checks" and not begin.is_blocked(record):
            context.write(
                record, partial(begin.blocked, refusal=started, now=world.now)
            )
        raise started
    context.write(record, partial(begin.begun, started=started))
    return started


def called(context: frame.Context) -> bool:
    """Whether the forge calls the task's pull request conflicting now."""
    landing = context.record.landing
    if landing is None or landing.pull is None:
        return False
    return context.ports.forge.pull(landing.pull.number).mergeable == "conflicting"


def woken(folder: Path, slug: str) -> Envelope:
    """`lem land start SLUG --conflicting`: the start is due when the forge calls the pull
    request conflicting, else as any step is."""
    workspace = places.workspace(folder)
    tasks.read(workspace.state, slug)
    now = clock.now()
    with steps.step(workspace.state, slug, "start", now):
        context = step.opened(workspace, slug, now)
        if not called(context):
            context = step.allowed(context, "start")
        outcome = msgspec.Raw(msgspec.json.encode(act(context, conflicting=True)))
        following = say.following(slug, step.looked(context))
    return Envelope(ok=True, outcome=outcome, following=following)


def run(folder: Path, slug: str, *, conflicting: bool) -> Envelope:
    """`lem land start SLUG`."""
    if conflicting:
        return woken(folder, slug)
    return step.landed(folder, slug, "start", partial(act, conflicting=False))
