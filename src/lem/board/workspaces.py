"""The machine's list of workspaces, `workspaces.json` in Lem's home folder, and the names they
have in the board's addresses.

The list is the main checkouts the server shows, as absolute paths in the order they came. A
board command run in a workspace puts it there. A workspace's name is its folder's name in lower
case, every character but a letter, a digit, `.`, `_` and `-` made `-`; two of one name are
`NAME-2`, `NAME-3` in the order of the list, so that a name does not move while a checkout is
away.
"""

import re
from pathlib import Path

import msgspec

from lem.kernel import files, locks
from lem.kernel.errors import Refusal
from lem.store import places

WORKSPACES = "workspaces.json"
LOCK = "workspaces.lock"
# The server's own words in its addresses, which no workspace may be named.
RESERVED = ("api", "assets", "push", "manifest.webmanifest", "sw.js")
OTHER = re.compile(r"[^a-z0-9._-]+")

type Names = tuple[tuple[str, str], ...]


def listed(home: Path) -> tuple[str, ...]:
    """The main checkouts in the list, in its order; none when there is no list."""
    path = home / WORKSPACES
    try:
        return msgspec.json.decode(path.read_bytes(), type=tuple[str, ...])
    except FileNotFoundError:
        return ()
    except msgspec.DecodeError as error:
        raise Refusal(
            "workspaces",
            f"{path} is no list of workspaces: {error}",
            f"remove {path}, and run lem board in each repository",
        ) from error


def noted(home: Path, folder: Path) -> places.Workspace | None:
    """Put the main checkout of the workspace `folder` is in on the list, unless it is there;
    None when the folder is in no workspace, which a machine's server needs none of."""
    try:
        space = places.workspace(folder)
    except Refusal:
        return None
    home.mkdir(parents=True, exist_ok=True)
    path = str(space.checkout.resolve())
    with locks.held(home / LOCK):
        before = listed(home)
        if path not in before:
            after = msgspec.json.encode((*before, path))
            files.write_whole(home / WORKSPACES, after)
    return space


def word(text: str) -> str:
    """`text` as a word of an address: lower case, and `-` for every other character."""
    return OTHER.sub("-", text.lower()).strip("-")


def free(stem: str, taken: set[str]) -> str:
    """`stem`, else the first of `stem-2`, `stem-3` that is not taken."""
    number = 1
    name = stem
    while name in taken:
        number += 1
        name = f"{stem}-{number}"
    return name


def named(paths: tuple[str, ...], host: str) -> Names:
    """Each path of the list with its name, the first of a name first; the server's words
    and the machine's name are taken."""
    taken = {*RESERVED, host}
    names: list[tuple[str, str]] = []
    for path in paths:
        name = free(word(Path(path).name) or "workspace", taken)
        taken.add(name)
        names.append((name, path))
    return tuple(names)


def name_of(home: Path, host: str, checkout: Path) -> str | None:
    """The name of a listed main checkout in the board's addresses."""
    path = str(checkout.resolve())
    names = named(listed(home), host)
    return next((name for name, at in names if at == path), None)


def found(home: Path, host: str, name: str) -> places.Workspace | None:
    """The workspace of the name `name`, while its checkout still has Lem set up."""
    path = dict(named(listed(home), host)).get(name)
    if path is None or not (Path(path) / ".lem").is_dir():
        return None
    checkout = Path(path)
    return places.Workspace(
        checkout=checkout, lem=checkout / ".lem", state=checkout / places.STATE
    )
