"""The owner's acts from the board (`surfaces.md` B): a new task, a reviewer item's drop, a
merge, a session, an answer and the jump to a session. Each answers 501 until the step
`board-acts` builds it."""

from lem.board import stub

TASK = "/{host}/{workspace}/tasks/{slug}"

ROUTES = stub.routes(
    "board-acts",
    "POST",
    "/{host}/{workspace}/tasks",
    "/{host}/{workspace}/backlog/drop",
    "/{host}/{workspace}/agterm/{session}",
    f"{TASK}/merge",
    f"{TASK}/session",
    f"{TASK}/answer",
)
