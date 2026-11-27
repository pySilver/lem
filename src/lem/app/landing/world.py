"""`gather`: the world a landing step reads, fresh from git, the forge and the settings
(`landing.md` C).

Origin is fetched first, from the main checkout, so origin's base and the task's branch there
are as they are now. The pull request is the one on record, by its number, else every open one
on the task's branch (a run cut off after the forge made it wrote none down).
"""

from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.app.landing import (
    branch_checks,
    item_carry,
    pull_identity,
    review_item,
)
from lem.app.tasks import bases, where
from lem.model.landing import destination
from lem.model.landing import world as facts
from lem.settings import load as settings_load

if TYPE_CHECKING:
    from pathlib import Path

    from lem.app.wiring import Ports
    from lem.records.base import Moment
    from lem.records.record import Record
    from lem.store.places import Workspace


def rules(workspace: Workspace) -> facts.Rules:
    """The settings a landing reads, from the main checkout."""
    team = settings_load.team_of(workspace.checkout)
    return facts.Rules(
        base=settings_load.base_of(team),
        land=team.branch.land,
        history=team.branch.history,
        protected=team.branch.protected,
        commands=team.checks.commands,
        serial=team.checks.serial,
        setup=team.checks.setup,
    )


def origin(
    ports: Ports, workspace: Workspace, record: Record, now: Moment
) -> facts.World:
    """The world of origin's base, before the worktree and the branches are read: the base
    the landing recorded, else a part's feature branch, else the settings' (`bases.chosen`)."""
    git = ports.git
    found = replace(rules(workspace), base=bases.chosen(git, workspace, record))
    base = git.remote_head(workspace.checkout, found.base)
    if base is None:
        raise destination.missing(found.base)
    return facts.World(
        rules=found,
        branch=where.branch(record),
        base=base,
        base_tree=git.tree(workspace.checkout, base),
        now=now,
    )


def empty_cleanup(
    workspace: Workspace, record: Record, now: Moment
) -> facts.World | None:
    """An ended task whose worktree and branch were never made needs no look at origin."""
    task = record.task
    if task.branch is not None or record.landing is not None:
        return None
    path = workspace.lem / where.WORKTREES / task.slug
    if path.exists() or path.is_symlink():
        return None
    return facts.World(
        rules=facts.Rules(base=""), branch="", base="", base_tree="", now=now
    )


def in_worktree(ports: Ports, path: Path, world: facts.World) -> facts.World:
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


def branches(ports: Ports, checkout: Path, world: facts.World) -> facts.World:
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


def gather(
    ports: Ports, workspace: Workspace, record: Record, now: Moment, *, fetch: bool
) -> facts.World:
    """The world now, for the task of `record`; with `fetch`, after a fetch of origin."""
    if fetch:
        ports.git.fetch(workspace.checkout)
    world = origin(ports, workspace, record, now)
    path = where.worktree(workspace, record.task.slug)
    world = in_worktree(ports, path, world)
    world = branch_checks.gathered(ports.git, path, world)
    checked = record.landing.checked if record.landing else None
    world = item_carry.gathered(ports.git, path, checked, world)
    world = review_item.gathered(ports.git, path, record, world)
    world = branches(ports, workspace.checkout, world)
    return pull_identity.in_world(ports.forge, record, world)
