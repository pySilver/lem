"""The refusal of a checkout whose origin is not a repository on GitHub, with the command that
points it there, its path quoted for the shell."""

import shlex
from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from pathlib import Path


def not_github(checkout: Path) -> Refusal:
    """A task ends as a GitHub pull request, the one way Lem lands: origin must be there."""
    where = shlex.quote(str(checkout))
    return Refusal(
        "not-github",
        f"origin of {checkout} is not a repository on GitHub, or there is none: a task ends "
        "as a GitHub pull request, the one way Lem lands",
        f"point origin at the repository on GitHub (git -C {where} remote set-url origin "
        "git@github.com:OWNER/REPO.git), push the base there, then run the step again",
    )
