"""A `lem ask` card of a task's session on the board: its own page, and the owner's answer to
it. Both answer 501 until the step `ask` builds them."""

from lem.board import stub

CARD = "/{host}/{workspace}/tasks/{slug}/cards/{page}"

ROUTES = (
    *stub.routes("ask", "GET", f"{CARD}/{{path:path}}"),
    *stub.routes("ask", "POST", f"{CARD}/answer"),
)
