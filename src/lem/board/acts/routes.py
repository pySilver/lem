"""The owner's acts from the board (`surfaces.md` B): a new task, a reviewer item's drop, the jump
to a session, and on a task the approval of its merge, a session, and an answer.

The new task's form posts to `/start`, as the board's page has it (`board/inputs`), and to
`/tasks`, as the design names it. The park and the yes to the criteria are answers of
`.../answer` (option `park`, and `yes` to the criteria's question), not addresses of their own.
"""

from starlette.routing import Route

from lem.board.acts import answer, backlog, jump, merge, session, start

WORKSPACE = "/{host}/{workspace}"
TASK = f"{WORKSPACE}/tasks/{{slug}}"
POST = ("POST",)

ROUTES = (
    Route(f"{WORKSPACE}/start", start.endpoint, methods=POST),
    Route(f"{WORKSPACE}/tasks", start.endpoint, methods=POST),
    Route(f"{WORKSPACE}/backlog/drop", backlog.endpoint, methods=POST),
    Route(f"{WORKSPACE}/agterm/{{session}}", jump.endpoint, methods=POST),
    Route(f"{TASK}/merge", merge.endpoint, methods=POST),
    Route(f"{TASK}/session", session.endpoint, methods=POST),
    Route(f"{TASK}/answer", answer.endpoint, methods=POST),
)
