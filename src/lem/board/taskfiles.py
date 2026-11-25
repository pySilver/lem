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
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING

from starlette.responses import PlainTextResponse, Response

from lem.board import taskfile_read
from lem.board.pages import place

if TYPE_CHECKING:
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


def read(request: Request, *, picture: bool = False) -> bytes | None:
    """Read the requested file below the workspace's state folder."""
    space = place.workspace(request)
    slug = request.path_params["slug"]
    return taskfile_read.read(
        space.state, slug, request.path_params["path"], media=picture
    )


async def raw(request: Request) -> Response:
    """An HTML page of the task's folder, under a sandbox of its own."""
    suffix = Path(request.path_params["path"]).suffix.lower()
    body = read(request) if suffix in PAGES else None
    if body is None:
        return PlainTextResponse(NOT_FOUND, status_code=HTTPStatus.NOT_FOUND)
    headers = {"Content-Security-Policy": SANDBOX, "Cache-Control": "no-store"}
    return Response(body, media_type="text/html", headers=headers)


async def media(request: Request) -> Response:
    """A picture of the task's media folder."""
    body = read(request, picture=True) or b""
    name = request.path_params["path"]
    kind = image_type(name, body[:HEAD])
    if kind is None:
        said = (
            "Not found: the board shows only a PNG, JPEG, GIF or WebP picture from a "
            "task's media folder."
        )
        return PlainTextResponse(said, status_code=HTTPStatus.NOT_FOUND)
    return Response(body, media_type=kind, headers=PICTURE)
