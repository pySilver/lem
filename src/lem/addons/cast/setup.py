"""Copy a starting cast, and make a scratch folder for each panel."""

import shutil
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from lem.addons.cast import project, refs, source
from lem.kernel.errors import Refusal
from lem.kernel.paths import root
from lem.store.guard import writable
from lem.store.places import STATE, checkout_of, task_folder


def init(folder: Path) -> dict[str, str]:
    """Copy the built-in templates for the owner to edit."""
    git, state = project.project(folder)
    target = git.path / source.CAST
    if occupied(target):
        raise Refusal(
            "cast-exists", f"the owner's cast path {target} is in use", "edit it there"
        )
    if project.cast_at(git, state, refs.refs(git)) is not None:
        raise Refusal(
            "cast-exists", "the default branch has the owner's cast", "use that cast"
        )
    shipped = root() / "skills" / "lem-panel" / "cast"
    if not source.paths_of(shipped):
        raise Refusal("cast-missing", "Lem has no cast templates", "install Lem again")
    copy_cast(shipped, target)
    return {"dir": str(target), "source": str(shipped)}


def copy_cast(shipped: Path, target: Path) -> None:
    """Publish the whole cast after the copy is ready."""
    target.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=target.parent, prefix=".cast-") as temporary:
        ready = Path(temporary) / "cast"
        shutil.copytree(shipped, ready)
        try:
            ready.rename(target)
        except OSError as error:
            if not occupied(target):
                raise
            raise Refusal(
                "cast-exists",
                f"the owner's cast path {target} is in use",
                "edit it there",
            ) from error


def occupied(target: Path) -> bool:
    """A file or a nonempty directory already belongs to the owner."""
    if target.is_dir():
        return next(target.iterdir(), None) is not None
    return target.exists()


def run_dir(folder: Path, slug: str) -> str:
    """Make the dated directory in the main checkout's untracked state."""
    state = checkout_of(folder) / STATE
    task_folder(state, slug)
    writable(state)
    day = datetime.now().astimezone().date()
    target = state / "panels" / f"{day}-{slug}"
    try:
        target.mkdir(parents=True)
    except FileExistsError as error:
        raise Refusal(
            "panel-exists",
            f"the owner's panel folder {target} exists",
            "add a suffix to the slug",
        ) from error
    return str(target)
