"""The task that adds the project's first commands brings those commands for its own run."""

import tomllib
from typing import TYPE_CHECKING

import msgspec
from msgspec.structs import replace

from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from pathlib import Path

    from lem.model.landing.world import World
    from lem.ports.git import Git

SETTINGS = ".lem/settings.toml"


class Own(msgspec.Struct, frozen=True, kw_only=True):
    """The commands a branch names."""

    commands: tuple[str, ...] = ()


class Branched(msgspec.Struct, frozen=True, kw_only=True):
    """The table read from a branch when it supplies the first commands."""

    checks: Own = Own()


def commands(git: Git, where: Path, tip: str) -> tuple[str, ...]:
    """The commands of the settings at a commit, or none when it has no settings."""
    found = git.show(where, tip, SETTINGS)
    if found is None:
        return ()
    try:
        parsed = msgspec.convert(tomllib.loads(found.decode()), Branched)
    except (
        tomllib.TOMLDecodeError,
        UnicodeDecodeError,
        msgspec.ValidationError,
    ) as error:
        raise Refusal(
            "settings",
            f"the checks in {SETTINGS} at {tip} cannot be read: {error}",
            "the builder corrects the settings and commits the fix, then runs the step again",
        ) from error
    return parsed.checks.commands


def gathered(git: Git, where: Path, world: World) -> World:
    """Use branch commands only when the checkout and the base both name no commands."""
    if world.rules.commands or world.tip is None:
        return world
    own = commands(git, where, world.tip)
    if not own or commands(git, where, world.base):
        return world
    return replace(world, rules=replace(world.rules, commands=own, own_checks=True))
