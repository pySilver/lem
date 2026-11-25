"""The requests the `Judge` adapter sends Jev: one finding against the bar, and one finding
against the items of the backlog, as many questions in each request as fit under Jev's limit,
so that every item is asked (`land.jev_spec`, `land.alike_specs` and `land.ask_jev` on
`main`)."""

import time
from dataclasses import dataclass

import httpx
import msgspec

from lem.adapters import judge_jev_wire as wire
from lem.ports.judge import Candidate, Defect, NotAsked, Score

# The seconds one whole request may take, its reply read to its end, before it is "no answer":
# the read only adds a line, and a landing should not wait for it. A guess (2026-11-23), not a
# measurement (`JEV_SECONDS` on `main`).
SECONDS = 20.0
NO_KEY = NotAsked(why="no key")
NO_ANSWER = NotAsked(why="no answer")
TOO_LONG = NotAsked(why="too long")
type Questions = dict[str, wire.Question]


def state_of(defect: Defect) -> dict[str, str]:
    """The finding as the state of a request: its place, title and run, each that it has."""
    told = {"where": defect.where, "title": defect.title, "run": defect.what}
    return {key: text for key, text in told.items() if text}


def item_question(found: Candidate) -> wire.Question:
    """The question whether the finding is the same defect as the item `found`, told by its
    title, place and first line."""
    parts = (
        f"title: {found.title}",
        f"where: {found.where}" if found.where else "",
        f"the first line of its body: {found.first}" if found.first else "",
    )
    told = "; ".join(part for part in parts if part)
    return wire.question(wire.SAME_ASKED.format(told), wire.SAME_ONE, wire.SAME_TWO)


def fits(model: str, state: dict[str, str], questions: Questions) -> bool:
    """Whether a request of these questions is under Jev's limit."""
    request = wire.Request(model=model, state=state, questions=questions)
    return wire.size_of(request) <= wire.LIMIT_BYTES


def split(
    model: str, state: dict[str, str], named: Questions
) -> list[wire.Request] | None:
    """The requests that ask every question, each under Jev's limit, a question in the next
    one where it does not fit; None when the state with one question alone does not fit."""
    groups: list[Questions] = []
    for name, one in named.items():
        if not fits(model, state, {name: one}):
            return None
        if groups and fits(model, state, {**groups[-1], name: one}):
            groups[-1] = {**groups[-1], name: one}
        else:
            groups.append({name: one})
    return [wire.Request(model=model, state=state, questions=group) for group in groups]


def posted(
    client: httpx.Client, url: str, key: str, request: wire.Request, deadline: float
) -> bytes | NotAsked:
    """The reply's body read until `deadline`, or why no reply was read."""
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    body = msgspec.json.encode(request)
    with client.stream("POST", url, content=body, headers=headers) as reply:
        if not reply.is_success:
            return NotAsked(why=f"HTTP {reply.status_code}")
        chunks: list[bytes] = []
        for chunk in reply.iter_bytes():
            if time.monotonic() > deadline:
                return NO_ANSWER
            chunks.append(chunk)
    return b"".join(chunks)


@dataclass(frozen=True, kw_only=True, slots=True)
class Asker:
    """Jev at one address, with one key and one model."""

    key: str | None
    url: str
    model: str
    transport: httpx.BaseTransport | None = None
    timeout: float | None = None

    def sent(
        self, request: wire.Request, *, report_http_status: bool = False
    ) -> dict[str, float] | NotAsked:
        """The scores of one request, or why it got none. The whole request, its reply read
        to its end, is given `timeout` or the landing's `SECONDS`.
        The correction log asks for the HTTP status of a failed reply."""
        if self.key is None:
            return NO_KEY
        timeout = SECONDS if self.timeout is None else self.timeout
        deadline = time.monotonic() + timeout
        try:
            with httpx.Client(transport=self.transport, timeout=timeout) as client:
                body = posted(client, self.url, self.key, request, deadline)
        except httpx.HTTPError:
            return NO_ANSWER
        if isinstance(body, NotAsked):
            return body if report_http_status else NO_ANSWER
        scores = wire.scores_of(body, request)
        return NO_ANSWER if scores is None else scores

    def over(self, defect: Defect, rule: str) -> Score | NotAsked:
        """The finding against the bar's condition `rule`."""
        asked = wire.question(
            wire.OVER_ASKED, wire.OVER_MET.format(rule), wire.OVER_UNMET
        )
        questions = {wire.OVER: asked}
        if not fits(self.model, state_of(defect), questions):
            return TOO_LONG
        said = self.sent(
            wire.Request(model=self.model, state=state_of(defect), questions=questions)
        )
        return said if isinstance(said, NotAsked) else Score(score=said[wire.OVER])

    def same(
        self, defect: Defect, candidates: tuple[Candidate, ...]
    ) -> tuple[Score, ...] | NotAsked:
        """The finding against each item, in as many requests as fit."""
        if self.key is None:
            return NO_KEY
        questions = map(item_question, candidates)
        named = {f"i{place}": one for place, one in enumerate(questions)}
        requests = split(self.model, state_of(defect), named)
        if requests is None:
            return TOO_LONG
        return self.scored(requests, candidates)

    def scored(
        self, requests: list[wire.Request], candidates: tuple[Candidate, ...]
    ) -> tuple[Score, ...] | NotAsked:
        """The score of each item, by its path; the first request with no answer ends it."""
        found: list[Score] = []
        for request in requests:
            said = self.sent(request)
            if isinstance(said, NotAsked):
                return said
            found.extend(
                Score(score=score, path=candidates[int(name[1:])].path)
                for name, score in said.items()
            )
        return tuple(found)
