"""`POST /HOST/WORKSPACE/tasks/SLUG/merge`: the owner's approval of the merge, from its confirm
step only, with the commit that step showed (`serve.act_merge` on `main`; `surfaces.md` B;
amendment A4 of the build's roadmap).

The step's button says Approve: his approval of the tip he read, which the landing merges at
once when it may, and which stands through a moved base and a conflict as the landing keeps it
(`merging.py`). A form with no confirm, or another commit than the one proposed now, merges
nothing; a press while his approval stands starts nothing, and says so; a press while the
merge runs gets that merge's note.
"""

import threading
from typing import TYPE_CHECKING

from starlette.concurrency import run_in_threadpool

from lem.board.acts import acting, approval, back, merging, noting
from lem.board.acts.asked import Asked
from lem.board.acts.notes import NOTES

if TYPE_CHECKING:
    from starlette.requests import Request
    from starlette.responses import Response

    from lem.board.acts.notes import Merging, Note

ACT = approval.ACT


def started(asked: Asked, key: Merging, note: Note) -> str:
    """Start the merge of his approval in a thread of its own, unless one runs, and give the
    token of its note."""
    token, new = NOTES.started(key, note)
    if new:
        entry = noting.act_of(ACT, asked.asker, asked.now, option=asked.given.tip)
        noting.noted(asked.state, asked.slug, entry)
        thread = threading.Thread(
            target=merging.merged, args=(asked, token, key), daemon=True
        )
        thread.start()
    return token


def approved(asked: Asked) -> str:
    """The token of the note of his approval; its merge runs in a thread of its own."""
    key: Merging = (str(asked.checkout), asked.slug)
    running = NOTES.running(key)
    if running is not None:
        return running
    note = approval.note_of(asked)
    if note.state != "running":
        return NOTES.put(note)
    return started(asked, key, note)


async def endpoint(request: Request) -> Response:
    """Take his approval, then the task's page with the note of the merge."""
    asked = await acting.asked_of(request)
    if not isinstance(asked, Asked):
        return asked
    token = await run_in_threadpool(approved, asked)
    return back.to_token(request, asked.slug, token, asked.given)
