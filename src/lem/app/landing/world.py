"""`gather`: the world a landing step reads, fresh from git, the forge and the settings
(`landing.md` C).

Origin is fetched first, from the main checkout, so origin's base and the task's branch there
are as they are now. The pull request is the one on record, by its number, else every open one
on the task's branch (a run cut off after the forge made it wrote none down).
"""

from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.app.tasks import where
from lem.kernel.errors import Refusal
from lem.model.landing.world import PullSeen, Rules, World
from lem.settings.load import base_of, team_of

if TYPE_CHECKING:
    from pathlib import Path

    from lem.app.wiring import Ports
    from lem.ports.forge_facts import Pull
    from lem.records.base import Moment
    from lem.records.record import Record
    from lem.store.places import Workspace


def rules(workspace: Workspace) -> Rules:
    """The settings a landing reads, from the main checkout."""
    team = team_of(workspace.checkout)
    return Rules(
        base=base_of(team),
        land=team.branch.land,
        history=team.branch.history,
        protected=team.branch.protected,
        commands=team.checks.commands,
        serial=team.checks.serial,
    )


def origin(ports: Ports, workspace: Workspace, record: Record, now: Moment) -> World:
    """The world of origin's base, before the worktree and the branches are read."""
    found = rules(workspace)
    git = ports.git
    base = git.remote_head(workspace.checkout, found.base)
    if base is None:
        raise Refusal(
            "no-base",
            f"origin has no branch {found.base}, the base of .lem/settings.toml",
            f"push {found.base} to origin, then run the step again",
        )
    return World(
        rules=found,
        branch=where.branch(record),
        base=base,
        base_tree=git.tree(workspace.checkout, base),
        now=now,
    )


def in_worktree(ports: Ports, path: Path, world: World) -> World:
    """The worktree's facts: its tip and tree, clean, a rebase, and whether it holds origin's
    base. A worktree that is not there leaves them unset."""
    git = ports.git
    tip = git.tip(path, "HEAD") if path.is_dir() else None
    if tip is None:
        return world
    return replace(
        world,
        tip=tip,
        tree=git.tree(path, tip),
        clean=git.clean(path),
        rebasing=git.rebase_state(path) is not None,
        base_in_tip=git.is_ancestor(path, world.base, tip),
    )


def branches(ports: Ports, checkout: Path, world: World) -> World:
    """Origin's task branch and the local one, and what holds each."""
    git = ports.git
    remote = git.remote_head(checkout, world.branch)
    local = git.tip(checkout, f"refs/heads/{world.branch}")
    tip = world.tip
    return replace(
        world,
        remote=remote,
        remote_in_tip=bool(remote and tip and git.is_ancestor(checkout, remote, tip)),
        local=local,
        local_in_base=bool(local and git.is_ancestor(checkout, local, world.base)),
    )


def seen(pull: Pull) -> PullSeen:
    """A pull request as the landing reads it."""
    return PullSeen(
        number=pull.number,
        url=pull.url,
        title=pull.title,
        body=pull.body,
        state=pull.state,
        head=pull.head,
        base=pull.base,
        queued=pull.queued,
        merge_commit=pull.merge_commit,
        merged_head=pull.merged_head,
        base_parent=pull.base_parent,
    )


def pulls_of(ports: Ports, record: Record, world: World) -> World:
    """The pull request on record, by its number; with none on record, every open one on the
    task's branch, which `propose` judges (`model/landing/propose.adopted`)."""
    landing = record.landing
    if landing is not None and landing.pull is not None:
        return replace(world, pull=seen(ports.forge.pull(landing.pull.number)))
    found = ports.forge.find_pulls(world.branch, world.rules.base)
    candidates = tuple(seen(pull) for pull in found if pull.state == "open")
    return replace(world, candidates=candidates)


def gather(
    ports: Ports, workspace: Workspace, record: Record, now: Moment, *, fetch: bool
) -> World:
    """The world now, for the task of `record`; with `fetch`, after a fetch of origin."""
    if fetch:
        ports.git.fetch(workspace.checkout)
    world = origin(ports, workspace, record, now)
    path = where.worktree(workspace, record.task.slug)
    world = in_worktree(ports, path, world)
    world = branches(ports, workspace.checkout, world)
    return pulls_of(ports, record, world)
