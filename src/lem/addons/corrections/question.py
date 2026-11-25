"""The one question Jev answers of each message the owner types: whether an agent should learn a
lesson from it, as the agent's last message and the owner's reply tell it
(`corrections.QUESTION` on `main`).

Jev is a pre-filter, and a loose one on purpose. With this question at 0.3, on 150 replies their
owner had labeled, it caught 22 of 27 lessons and flagged 67 of the 123 replies that were none
(mybaze's replies, measured 2026-11-23, with the question in Jev's `choice` form; FLAG_AT was
tuned on that same sample on 2026-11-07, so the true rate is lower). Here the question is Jev's
yes-or-no form with the same two texts, the form the `Judge` adapter sends: the rate of this form
is an unmeasured estimate until the sample is read again.
"""

from typing import TYPE_CHECKING

from lem.adapters import judge_jev, judge_jev_ask
from lem.adapters import judge_jev_wire as wire

if TYPE_CHECKING:
    from collections.abc import Mapping

    from lem.ports.judge import NotAsked
    from lem.records.corrections import Correction

FLAG_AT = 0.3
NAME = "lesson"
ASKED = (
    "This is one exchange between a coding agent and the project's owner: the agent's last "
    "message, then the owner's reply. Should an agent remember a lesson from the owner's "
    "reply for later work?"
)
LESSON = (
    "An agent should remember something from this reply. The owner corrects it or disagrees "
    "with its approach or assumption; tells it to take a step it should have taken on its "
    "own, such as cleaning up, getting a second opinion, running work in parallel, "
    "interviewing the owner, or saying what is next; asks for more context or a simpler "
    "explanation because the agent's message was unclear; tells it something it was waiting "
    "on has already happened; or states a lasting preference or rule for how the work should "
    "be done."
)
NO_LESSON = (
    "The reply only moves the work on and teaches nothing for later: it approves or answers "
    "the agent's question as asked, picks one of the options it offered, asks for a retry, or "
    "gives a one-off instruction that is about this moment only."
)


def request_of(model: str, previous: str, owner: str) -> wire.Request:
    """The request of one message: the agent's last message, the owner's reply, the question."""
    state = {"the agent's last message": previous, "the owner's reply": owner}
    asked = wire.question(ASKED, LESSON, NO_LESSON)
    return wire.Request(model=model, state=state, questions={NAME: asked})


def asked(
    jev: judge_jev_ask.Asker, correction: Correction
) -> dict[str, float] | NotAsked:
    """Jev's answer to the message, or why there is none: a request over Jev's limit is never
    sent, and nothing is cut down to fit."""
    request = request_of(jev.model, correction.previous, correction.owner)
    if wire.size_of(request) > wire.LIMIT_BYTES:
        return judge_jev_ask.TOO_LONG
    return jev.sent(request, report_http_status=True)


def asker_of(environ: Mapping[str, str]) -> judge_jev_ask.Asker:
    """Jev with the key, address and model of the environment, as the `Judge` adapter binds."""
    return judge_jev_ask.Asker(
        key=environ.get(judge_jev.KEY) or None,
        url=environ.get("JEV_API_URL", "").strip() or judge_jev.URL,
        model=environ.get("JEV_MODEL", "").strip() or judge_jev.MODEL,
    )
