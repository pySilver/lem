"""The check that each criterion's tests pass on the task's branch and fail on the base commit,
and the five inputs a run depends on (`criteria.cmd_red`, `cmd_inputs` and `inputs` on `main`).

A run that does not hold is written to the record and returned; a run that may not start, or
that was cut off, is refused, and what it started is ended and its worktrees removed first
(`checks_red_places.py`, `checks_red_run.py`). The settings are the main checkout's, so that a
branch cannot change what it is judged by.
"""

from typing import TYPE_CHECKING

import msgspec

from lem.app.landing import checks_git, checks_red_places, checks_red_run
from lem.app.tasks import where
from lem.kernel import errors, files
from lem.model.landing import checks_red
from lem.records.red import Inputs, Red
from lem.settings.load import base_of, team_of
from lem.store import places, tasks

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.base import Moment
    from lem.records.record import Record

CODE = "criteria"


def worktree_of(workspace: places.Workspace, record: Record) -> Path:
    """The task's worktree; refused before it has one, or before its criteria are on record."""
    slug = record.task.slug
    worktree = where.worktree(workspace, slug)
    if not (worktree / ".git").exists():
        raise errors.Refusal(
            CODE,
            f"the task has no worktree at {worktree}",
            f"lem task worktree {slug} makes it",
        )
    if record.task.criteria.digest is None:
        raise errors.Refusal(
            CODE,
            f"{slug} has no criteria on record",
            f"lem criteria record {slug} reads them",
        )
    return worktree


def inputs(workspace: places.Workspace, record: Record) -> Inputs:
    """The five inputs a run depends on, as they stand now: the tip, the base commit, the plan
    file, and the main checkout's `checks.setup` and `checks.serial`."""
    worktree = worktree_of(workspace, record)
    team = team_of(workspace.checkout)
    tip = checks_red_places.said(worktree, "rev-parse", "HEAD")
    onto = checks_red_places.onto_of(workspace.checkout, base_of(team))
    plan = record.task.plan
    return Inputs(
        tip=tip,
        base=checks_red_places.said(worktree, "merge-base", tip, onto),
        plan=plan.path if plan else None,
        setup=team.checks.setup,
        serial=team.checks.serial,
    )


def digest(found: Inputs) -> str:
    """The digest of a run's five inputs, which tells a run of other inputs from this one."""
    return files.digest(msgspec.json.encode(found))


def checked(workspace: places.Workspace, record: Record, found: Inputs) -> None:
    """Refuse a run that may not start (`checks_red.precondition`)."""
    worktree = worktree_of(workspace, record)
    team = team_of(workspace.checkout)
    onto = checks_red_places.onto_of(workspace.checkout, base_of(team))
    refusal = checks_red.precondition(
        record.task.criteria.criteria,
        checks_git.changed(worktree),
        found,
        onto,
        fast=record.task.plan is None,
    )
    if refusal:
        raise refusal


def prepared(workspace: places.Workspace, record: Record) -> checks_red_run.Run:
    """What the run needs, once it may start: its inputs, its tests, and the files the branch
    changed, read before any test runs."""
    found = inputs(workspace, record)
    checked(workspace, record, found)
    worktree = worktree_of(workspace, record)
    criteria = record.task.criteria
    tests = checks_red.tests_of(criteria.criteria)
    return checks_red_run.Run(
        checkout=workspace.checkout,
        found=found,
        tests=tests,
        without=checks_red.without_of(criteria.criteria),
        digest=criteria.digest or "",
        laid=checks_red_places.laid(worktree, found.tip, tests),
        changed=checks_git.listed(
            worktree, "diff", "--name-only", "--no-renames", "-z", found.base, found.tip
        ),
    )


def with_red(record: Record, *, made: Red) -> Record:
    """The record with this run as the newest of its criteria's check."""
    criteria = msgspec.structs.replace(record.task.criteria, red=made)
    task = msgspec.structs.replace(record.task, criteria=criteria)
    return msgspec.structs.replace(record, task=task)


def red(workspace: places.Workspace, record: Record, now: Moment) -> Red:
    """Run the check, write it on the task's record, and give it. A run with no test holds with
    no worktree; one with tests runs under the task's check lock."""
    slug = record.task.slug
    with checks_red_places.stopped(slug):
        run = prepared(workspace, record)
        made = run.red(now, (), ())
        if run.tests:
            with checks_red_places.ready(workspace, slug) as both:
                made = run.red(now, *run.outcomes(both))
    revision = tasks.read(workspace.state, slug).revision
    tasks.update(
        workspace.state, slug, lambda before: with_red(before, made=made), revision
    )
    return made
