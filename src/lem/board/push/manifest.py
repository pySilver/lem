"""The board as an app of a phone's home screen: the web app manifest, which opens the board at
`/` with its own icon (`pages.manifest` on `main`)."""

from typing import TYPE_CHECKING

import msgspec
from starlette.responses import Response

if TYPE_CHECKING:
    from starlette.requests import Request

# The page's dark ground (`board_pages.THEME` on `main`).
DARK = "#1a1813"


class Icon(msgspec.Struct, frozen=True, kw_only=True):
    """An icon of the manifest."""

    src: str
    sizes: str
    kind: str = msgspec.field(default="image/png", name="type")


class Manifest(msgspec.Struct, frozen=True, kw_only=True):
    """The web app manifest: the board added to a home screen opens as an app at `/`."""

    name: str = "Lem"
    short_name: str = "Lem"
    description: str = "The board of Lem's tasks on this machine"
    start_url: str = "/"
    scope: str = "/"
    display: str = "standalone"
    background_color: str = DARK
    theme_color: str = DARK
    icons: tuple[Icon, ...] = (
        Icon(src="/assets/icons/icon-192.png", sizes="192x192"),
        Icon(src="/assets/icons/icon-512.png", sizes="512x512"),
    )


async def manifest(request: Request) -> Response:
    """The manifest of the board as an app."""
    body = msgspec.json.encode(Manifest())
    headers = {"Cache-Control": "no-cache"}
    return Response(body, media_type="application/manifest+json", headers=headers)
