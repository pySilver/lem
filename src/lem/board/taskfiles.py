"""A task's files as they are: an HTML page of the task's folder for the panel's sandboxed frame,
and a picture of its `media/` folder for a document that shows it (`Handler.raw` and
`Handler.media` on `main`).

A path is a file inside the task's folder with no hidden part, which resolves inside it; anything
else is not found. A page goes under a sandbox of its own, so that opened alone it runs as no
page of the board's origin; a link that opens a tab of its own may leave it. A picture is a PNG,
JPEG, GIF or WebP whose extension and first bytes are the same format (`artifacts.image_type`
on `main`): an SVG, which can carry a script, and a text with a picture's name are not found.
"""

from http import HTTPStatus
from types import MappingProxyType
from typing import TYPE_CHECKING

from starlette.responses import PlainTextResponse, Response

from lem.board.pages import place
from lem.kernel.errors import Refusal
from lem.store import places

if TYPE_CHECKING:
    from pathlib import Path

    from starlette.requests import Request

PAGES = (".html", ".htm")
IMAGES = MappingProxyType(
    {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
)
MAGIC = (
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"GIF87a", "image/gif"),
    (b"GIF89a", "image/gif"),
)
RIFF = b"RIFF"
# How many first bytes a picture's check reads, and where a WebP file names its format.
HEAD = 16
WEBP_AT = 8
WEBP = slice(WEBP_AT, WEBP_AT + len(RIFF))
SANDBOX = "sandbox allow-scripts allow-popups allow-popups-to-escape-sandbox"
NOT_FOUND = "Not found."
PICTURE = MappingProxyType(
    {
        "Cache-Control": "no-cache",
        "Content-Security-Policy": "default-src 'none'; sandbox",
    }
)


def inside(folder: Path, path: str) -> Path | None:
    """The file `path` names inside `folder`; None for a hidden part, a path out of it, or
    no such file."""
    parts = [part for part in path.split("/") if part]
    if not parts or any(part.startswith(".") for part in parts):
        return None
    found = folder.joinpath(*parts)
    within = found.resolve().is_relative_to(folder.resolve())
    return found if within and found.is_file() else None


def image_type(name: str, head: bytes) -> str | None:
    """The type of a picture the board shows, by its extension and its first bytes alike."""
    suffix = name[name.rfind(".") :].lower()
    found = format_of(head)
    return found if found is not None and found == IMAGES.get(suffix) else None


def format_of(head: bytes) -> str | None:
    """The picture format the first bytes of a file name, if any."""
    if head.startswith(RIFF) and head[WEBP] == b"WEBP":
        return "image/webp"
    return next((kind for magic, kind in MAGIC if head.startswith(magic)), None)


def task_folder(request: Request) -> Path:
    """The folder of the task of the request's address."""
    space = place.workspace(request)
    try:
        return places.task_folder(space.state, request.path_params["slug"])
    except Refusal:
        return space.state / "tasks" / "-"


async def raw(request: Request) -> Response:
    """An HTML page of the task's folder, under a sandbox of its own."""
    found = inside(task_folder(request), request.path_params["path"])
    if found is None or found.suffix.lower() not in PAGES:
        return PlainTextResponse(NOT_FOUND, status_code=HTTPStatus.NOT_FOUND)
    headers = {"Content-Security-Policy": SANDBOX, "Cache-Control": "no-store"}
    body = found.read_bytes()
    return Response(body, media_type="text/html", headers=headers)


async def media(request: Request) -> Response:
    """A picture of the task's media folder."""
    found = inside(task_folder(request) / "media", request.path_params["path"])
    body = b"" if found is None else found.read_bytes()
    name = "" if found is None else found.name
    kind = image_type(name, body[:HEAD])
    if kind is None:
        said = (
            "Not found: the board shows only a PNG, JPEG, GIF or WebP picture from a "
            "task's media folder."
        )
        return PlainTextResponse(said, status_code=HTTPStatus.NOT_FOUND)
    return Response(body, media_type=kind, headers=PICTURE)
