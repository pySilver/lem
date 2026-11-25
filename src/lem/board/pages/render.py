"""The board's templates: Jinja2 files of `lem/board/templates`, with every printed text
escaped, and a name a template prints that its input lacks is a failure, never an empty text."""

from typing import TYPE_CHECKING

import jinja2
from starlette.templating import Jinja2Templates

if TYPE_CHECKING:
    import msgspec
    from starlette.requests import Request
    from starlette.responses import Response

TEMPLATES = Jinja2Templates(
    env=jinja2.Environment(
        loader=jinja2.PackageLoader("lem.board", "templates"),
        autoescape=True,
        undefined=jinja2.StrictUndefined,
    )
)


def page(request: Request, name: str, board: msgspec.Struct) -> Response:
    """The page of the template `name`, which prints `board`."""
    return TEMPLATES.TemplateResponse(request, name, {"board": board})
