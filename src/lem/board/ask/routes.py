"""A question card's page, headers, and answer on the task's board."""

from starlette.routing import Route

from lem.board.ask import page, post

CARD = "/{host}/{workspace}/tasks/{slug}/cards/{page}"

ROUTES = (
    Route(f"{CARD}/", page.endpoint, methods=("GET",), name="ask-card"),
    Route(CARD, page.endpoint, methods=("GET",), name="ask-card-no-slash"),
    Route(f"{CARD}/answer", post.endpoint, methods=("POST",), name="ask-answer"),
)
