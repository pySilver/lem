"""The main checkout `lem init` sets Lem up in: the repository the call's folder is in, where Lem
need not be set up yet (`store.places.workspace` refuses that, which every other command wants).
"""

import fcntl
import os
from contextlib import ExitStack, contextmanager
from typing import TYPE_CHECKING

from lem.kernel import folders
from lem.kernel.errors import Refusal
from lem.store import places

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path


def main_checkout(folder: Path) -> Path:
    """The main checkout of the repository `folder` is in; refused outside one."""
    start = folder.resolve()
    marks = (one / ".git" for one in (start, *start.parents))
    found = next((mark for mark in marks if mark.exists()), None)
    if found is None:
        raise Refusal(
            "no-repository",
            f"{start} is in no git repository",
            "run it inside a repository's checkout, or name one with lem --repo PATH",
        )
    checkout = places.common_dir(found).parent
    folders.inside_test_root(checkout)
    return checkout


@contextmanager
def locked(checkout: Path) -> Iterator[None]:
    """Serialize init calls on the git directory, which exists before any Lem file."""
    descriptor = os.open(checkout / ".git", os.O_RDONLY)
    with ExitStack() as cleanup:
        cleanup.callback(os.close, descriptor)
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        yield
