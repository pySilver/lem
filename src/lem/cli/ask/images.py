"""An image file embedded in a question page."""

import base64
import mimetypes
from typing import TYPE_CHECKING

from lem.cli.ask.spec import invalid

if TYPE_CHECKING:
    from pathlib import Path

# The largest embedded image, the same bound as on main.
IMAGE_BYTES = 8 * 1024 * 1024


def encoded(path: Path) -> str:
    """The image in a data URI, with a bound on what the page reads."""
    try:
        with path.open("rb") as stream:
            picture = stream.read(IMAGE_BYTES + 1)
    except OSError as error:
        raise invalid(f"the image {path} could not be read: {error}") from error
    if len(picture) > IMAGE_BYTES:
        raise invalid(f"the image {path} exceeds {IMAGE_BYTES} bytes")
    kind = mimetypes.guess_type(path)[0] or "image/png"
    words = base64.b64encode(picture).decode("ascii")
    return f"data:{kind};base64,{words}"
