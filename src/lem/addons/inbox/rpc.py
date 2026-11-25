"""The local Inbox's MCP tool calls over HTTP, as its CLI sends them."""

import msgspec

from lem.records.base import Frozen


class Arguments(Frozen, frozen=True, kw_only=True):
    """One call to the local MCP server, with the same session and folder as the CLI."""

    name: str
    arguments: dict[str, object]
    meta: dict[str, object] = msgspec.field(name="_meta")


class Call(Frozen, frozen=True, kw_only=True, omit_defaults=False):
    """The JSON-RPC request accepted by the running Inbox."""

    arguments: Arguments = msgspec.field(name="params")
    jsonrpc: str = "2.0"
    id: int = 1
    method: str = "tools/call"


class Words(Frozen, frozen=True, kw_only=True):
    """A text part of the tool response."""

    text: str = ""


class Tool(Frozen, frozen=True, kw_only=True):
    """The receipt or the Inbox's refusal."""

    structured: dict[str, object] | None = msgspec.field(
        default=None, name="structuredContent"
    )
    refused: bool = msgspec.field(default=False, name="isError")
    parts: tuple[Words, ...] = msgspec.field(default=(), name="content")


class Failed(Frozen, frozen=True, kw_only=True):
    """A JSON-RPC error from the Inbox."""

    message: str


class Reply(Frozen, frozen=True, kw_only=True):
    """One JSON-RPC response, with its tool receipt or its fault."""

    id: int | None = None
    answered: Tool | None = msgspec.field(default=None, name="result")
    error: Failed | None = None


def call(
    action: str,
    payload: dict[str, object],
    project: str,
    session: str | None,
) -> Call:
    """Name the task's Claude Code session only on a session's send."""
    meta: dict[str, object] = {"ai.plannotator/working-folder": project}
    if session:
        payload = {
            **payload,
            "agent_host": "claude-code",
            "agent_session": session,
            "agent_name": "Claude Code",
        }
    elif action == "read_thread":
        meta["ai.plannotator/inbox-peek"] = True
    return Call(arguments=Arguments(name=action, arguments=payload, meta=meta))
