"""Ask the owner's Jev provider, or show the request without sending it."""

from typing import TYPE_CHECKING

import httpx
import msgspec

from lem.adapters.judge_jev import KEY, MODEL, URL
from lem.addons.jev import reply
from lem.kernel.errors import Refusal
from lem.records.base import Frozen

if TYPE_CHECKING:
    from collections.abc import Mapping

    from lem.addons.jev.records import Request

# The default in main's Jev client (2026-11-25).
TIMEOUT_SECONDS = 120.0
# The provider error excerpt on main (2026-11-25).
EXCERPT_CHARS = 400


class Config(Frozen, frozen=True, kw_only=True):
    """The provider's address, model and time limit."""

    url: str
    model: str
    timeout: float


class Check(Frozen, frozen=True, kw_only=True):
    """What the owner can check without making a request."""

    model: str
    questions: tuple[str, ...]
    url: str
    key_from: str | None


def timeout(raw: str) -> float:
    """The time one request may take."""
    try:
        seconds = float(raw)
    except ValueError:
        seconds = 0
    if not 0 < seconds < float("inf"):
        raise Refusal(
            "jev-timeout",
            f"the owner's JEV_TIMEOUT={raw!r} is not a number of seconds above zero",
            "set JEV_TIMEOUT=120 or unset it",
        )
    return seconds


def config(environ: Mapping[str, str]) -> Config:
    """Check the endpoint without reporting any credentials in it."""
    try:
        address = httpx.URL(environ.get("JEV_API_URL", "").strip() or URL)
    except httpx.InvalidURL:
        address = None
    if (
        address is None
        or address.scheme not in {"http", "https"}
        or not address.host
        or address.userinfo
    ):
        raise Refusal(
            "jev-url",
            "the owner's JEV_API_URL is invalid",
            "set JEV_API_URL to the provider's decisions endpoint",
        )
    return Config(
        url=str(address),
        model=environ.get("JEV_MODEL", "").strip() or MODEL,
        timeout=timeout(environ.get("JEV_TIMEOUT", str(TIMEOUT_SECONDS))),
    )


def check(asked: Request, target: Config, environ: Mapping[str, str]) -> Check:
    """Name the input and the credential source without reading the network."""
    return Check(
        model=asked.model,
        questions=tuple(sorted(asked.questions)),
        url=target.url,
        key_from=KEY if environ.get(KEY) else None,
    )


def ask(
    asked: Request,
    target: Config,
    environ: Mapping[str, str],
    transport: httpx.BaseTransport | None = None,
) -> reply.Reply:
    """Send one request with the one credential the owner sets."""
    secret = environ.get(KEY)
    if not secret:
        raise Refusal(
            "jev-key",
            "JEV_API_KEY is the one name Lem reads for the owner's key",
            "set JEV_API_KEY to the key of the Jev provider",
        )
    try:
        with httpx.Client(transport=transport, timeout=target.timeout) as client:
            sent = client.post(
                target.url,
                content=msgspec.json.encode(asked),
                headers={
                    "Authorization": f"Bearer {secret}",
                    "Content-Type": "application/json",
                },
            )
            sent.raise_for_status()
    except httpx.HTTPError as error:
        raise request_error(error, secret) from error
    return reply.read(sent.content, asked)


def request_error(error: httpx.HTTPError, secret: str) -> Refusal:
    """Give the provider's status and a short excerpt without the owner's key."""
    why = f"the owner's Jev request failed: {type(error).__name__}"
    if isinstance(error, httpx.HTTPStatusError):
        status = error.response.status_code
        excerpt = error.response.text.replace(secret, "[redacted]")[:EXCERPT_CHARS]
        why = f"the owner's Jev provider answered HTTP {status}: {excerpt}"
    return Refusal("jev-request", why, "check the provider's status, endpoint and key")
