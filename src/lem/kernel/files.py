"""A file written whole, and an artifact published once.

A reader finds the old file or the new one, never a part: the text goes to a temporary file of a
unique name in the same folder, is synced, and replaces the file in one rename, after which the
folder is synced too, so that the rename outlives a cut of the power. An artifact that a record
cites by its digest is published at a path of its own before the citation, and is never written
again with other bytes: a cut-off between the two leaves an artifact that nothing cites, never a
citation of a changed file.
"""

import contextlib
import hashlib
import os
import tempfile
from pathlib import Path

from lem.kernel.errors import Fault


def write_whole(path: Path, body: bytes) -> None:
    """Write `body` as `path`, whole or not at all; the folder must exist."""
    prefix = f".{path.name}."
    with tempfile.NamedTemporaryFile(
        dir=path.parent, prefix=prefix, delete_on_close=False
    ) as stream:
        stream.write(body)
        stream.flush()
        os.fsync(stream.fileno())
        Path(stream.name).replace(path)
    sync_folder(path.parent)


def sync_folder(folder: Path) -> None:
    """Sync a folder, so that a rename or a new name in it is on the disk."""
    descriptor = os.open(folder, os.O_RDONLY)
    with contextlib.ExitStack() as stack:
        stack.callback(os.close, descriptor)
        os.fsync(descriptor)


def digest(body: bytes) -> str:
    """The sha256 of `body`, in hex: the name a record cites an artifact by."""
    return hashlib.sha256(body).hexdigest()


def publish(path: Path, body: bytes) -> str:
    """Publish `body` at `path` once, and give its digest. The same bytes again are no
    change; other bytes at a published path are a fault of the caller, which names each body
    by its round, number or digest."""
    if path.exists():
        if path.read_bytes() != body:
            raise Fault(f"{path} is published already, with other bytes")
        return digest(body)
    path.parent.mkdir(parents=True, exist_ok=True)
    write_whole(path, body)
    return digest(body)
