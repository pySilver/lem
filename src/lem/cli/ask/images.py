"""An image file embedded in a question page."""

import base64
import mimetypes
from pathlib import Path
from typing import TYPE_CHECKING

from lem.cli.ask.spec import invalid

if TYPE_CHECKING:
    from lem.cli.ask.spec import Spec

# The largest embedded image, the same bound as on main.
IMAGE_BYTES = 8 * 1024 * 1024


def attach(block: Spec, base: Path) -> None:
    """Replace a local image with a data URI or its alternative text."""
    image = block.get("image")
    if not isinstance(image, str) or image.startswith(("http://", "https://", "data:")):
        return
    path = Path(base, Path(image).expanduser())
    embedded = encoded(path)
    block["image"] = embedded or ""
    if embedded is None:
        block.setdefault("alt", f"missing image: {image}")


def encoded(path: Path) -> str | None:
    """The image as a data URI, or None when there is no image file."""
    if not path.is_file():
        return None
    try:
        with path.open("rb") as stream:
            picture = stream.read(IMAGE_BYTES + 1)
    except FileNotFoundError, IsADirectoryError:
        return None
    except OSError as error:
        raise invalid(f"the image {path} could not be read: {error}") from error
    if len(picture) > IMAGE_BYTES:
        raise invalid(f"the image {path} exceeds {IMAGE_BYTES} bytes")
    kind = mimetypes.guess_type(path)[0] or "image/png"
    words = base64.b64encode(picture).decode("ascii")
    return f"data:{kind};base64,{words}"
