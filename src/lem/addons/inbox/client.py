"""Send, withdraw and read through the owner's running Inbox."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

import httpx
import msgspec

from lem.addons.inbox import door, rpc
from lem.addons.inbox.messages import Payload, Read, Sent
from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from pathlib import Path

    from lem.addons.inbox.messages import Door

ACCEPT = "application/json, text/event-stream"


def failed(why: str) -> Refusal:
    """The owner or the next duty can try again later."""
    return Refusal("inbox-call", why, "check the owner's Plannotator Inbox")


def decoded(raw: bytes, *, stream: bool) -> dict[str, object]:
    """Decode a JSON or SSE reply from the local MCP endpoint."""
    body = last_event(raw) if stream else raw
    try:
        found = msgspec.json.decode(body, type=rpc.Reply)
    except msgspec.DecodeError as error:
        raise failed("the owner's Inbox gave no JSON-RPC reply") from error
    if found.error:
        raise failed(found.error.message)
    return receipt(found.answered)


def last_event(raw: bytes) -> bytes:
    """Return the last data frame of a finite SSE reply."""
    events = raw.replace(b"\r\n", b"\n").split(b"\n\n")
    for event in reversed(events):
        lines = event.split(b"\n")
        body = b"\n".join(
            line[5:].lstrip() for line in lines if line.startswith(b"data:")
        )
        if body:
            return body
    return b""


def receipt(tool: rpc.Tool | None) -> dict[str, object]:
    """Keep the service's refusal verbatim for the withdrawal rule."""
    if tool is None:
        raise failed("the owner's Inbox did not return a tool receipt")
    if tool.refused:
        raise failed("\n".join(part.text for part in tool.parts))
    if tool.structured is None:
        raise failed("the owner's Inbox did not return a structured receipt")
    return tool.structured


@dataclass(frozen=True, slots=True, kw_only=True)
class Inbox:
    """A local, already running Inbox and one project's working folder."""

    opened: Door
    cwd: Path
    http: httpx.Client

    def call(
        self, action: str, payload: dict[str, object], session: str | None
    ) -> dict[str, object]:
        """Call one tool without starting or redirecting to another Inbox."""
        if not self.opened.running or not door.local(self.opened.url):
            raise failed("the owner's Inbox is not running at a local address")
        asked = rpc.call(action, payload, str(self.cwd), session)
        address = (self.opened.url or "").rstrip("/")
        url = f"{address}/mcp"
        response = self.request(url, msgspec.json.encode(asked))
        stream = response.headers.get("content-type", "").startswith(
            "text/event-stream"
        )
        return decoded(response.content, stream=stream)

    def request(self, url: str, raw: bytes) -> httpx.Response:
        """Send the request without following a redirect."""
        try:
            return self.http.post(
                url,
                content=raw,
                headers={"Accept": ACCEPT, "Content-Type": "application/json"},
                follow_redirects=False,
            ).raise_for_status()
        except httpx.HTTPError as error:
            raise failed(
                f"the owner's Inbox did not answer: {type(error).__name__}"
            ) from error

    def send(self, payload: Payload, session: str | None) -> Sent:
        """Require a receipt before removing the saved payload."""
        found = self.call("send_message", msgspec.to_builtins(payload), session)
        try:
            sent = msgspec.convert(found, Sent)
        except msgspec.ValidationError as error:
            raise failed("the Inbox did not give a message id") from error
        if not sent.message_id:
            raise failed("the Inbox did not give a message id")
        return sent

    def read(self, message: str) -> Read:
        """Read another session's thread without marking it read."""
        payload: dict[str, object] = {
            "message_id": message,
            "format": "full",
            "project_path": str(self.cwd),
        }
        found = self.call("read_thread", payload, None)
        try:
            return msgspec.convert(found, Read)
        except msgspec.ValidationError as error:
            raise failed("the Inbox did not return the thread") from error
