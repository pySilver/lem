"""The panel uses the project's own people and its profile."""

from pathlib import Path

from lem.addons.cast import person, refs, source
from lem.kernel.errors import Refusal
from lem.records.base import Frozen
from lem.settings.load import settings_of
from lem.store.places import STATE, checkout_of

type Finder = refs.Checkout


class Cast(Frozen, frozen=True, kw_only=True):
    """The files that describe this project and its people."""

    layer: str = "project"
    source: str
    dir: str
    index: str | None
    personas: tuple[person.Person, ...]
    profile: source.Located | None


def project(folder: Path) -> tuple[Finder, Path]:
    """Use the active worktree for prose and the main checkout for state and settings."""
    main = checkout_of(folder)
    settings_of(main)
    return refs.checkout(folder), main / STATE


def resolve(folder: Path) -> Cast:
    """Resolve the cast and profile separately, preserving worktree edits."""
    git, state = project(folder)
    branches = refs.refs(git)
    found = cast_at(git, state, branches)
    if found is None:
        raise Refusal(
            "no-personas",
            "the owner's project has no personas in .lem/personas",
            "run lem cast init and edit the files for this project",
        )
    return described(found, state, profile_at(git, state, branches))


def described(
    found: source.Located, state: Path, profile: source.Located | None
) -> Cast:
    """Include the original paths and the exact prose to read."""
    folder = Path(found.path)
    index = folder / source.INDEX
    return Cast(
        source=found.source,
        dir=found.path,
        index=str(index) if index.is_file() else None,
        personas=tuple(person.read(path, state) for path in source.paths_of(folder)),
        profile=profile,
    )


def cast_at(
    git: Finder, state: Path, branches: tuple[str, ...]
) -> source.Located | None:
    """Use the default branch when the active cast is absent or unchanged."""
    local = git.path / source.CAST
    has_local = bool(source.paths_of(local))
    for branch in branches:
        if not has_local or refs.follows(git, branch, source.CAST):
            found = source.remote_cast(git, branch, state)
            if found is not None:
                return found
    return source.Located(path=str(local), source="checkout") if has_local else None


def profile_at(
    git: Finder, state: Path, branches: tuple[str, ...]
) -> source.Located | None:
    """Apply the same selection independently to the profile."""
    local = git.path / source.PROFILE
    has_local = local.is_file()
    for branch in branches:
        if not has_local or refs.follows(git, branch, source.PROFILE):
            found = source.remote_profile(git, branch, state)
            if found is not None:
                return found
    return source.Located(path=str(local), source="checkout") if has_local else None
