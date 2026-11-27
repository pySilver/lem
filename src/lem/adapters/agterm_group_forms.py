"""What `agtermctl` prints for the windows of this Mac and for a session attached with its
companions (agterm be92bc63: `window list --json`, the reference's "Windows";
`zmx attach HOST SESSION --companions --json`, `ControlServer+RemoteGroup.swift`).

A group attach that fails for one member keeps the rows it made, and its reply still names them:
`{"ok": false, "error": "kept ... not attached: ...", "result": {"id": ..., "remoteGroup":
{"membershipKnown": ..., "companions": [{"origin": ..., "id": ..., "error": ...}]}}}`.
"""

import msgspec


class Window(msgspec.Struct, frozen=True, kw_only=True):
    """A window of this Mac's agterm, and whether it is open."""

    id: str
    open: bool = True


class Windowed(msgspec.Struct, frozen=True, kw_only=True):
    """The result of `window list --json`."""

    windows: tuple[Window, ...]


class Windows(msgspec.Struct, frozen=True, kw_only=True):
    """`window list --json`'s answer: `{"result": {"windows": [...]}}`."""

    found: Windowed = msgspec.field(name="result")


class Member(msgspec.Struct, frozen=True, kw_only=True):
    """A companion of the group: its id on the far Mac, its row here, or why it has none."""

    origin: str
    id: str | None = None
    error: str | None = None


class Group(msgspec.Struct, frozen=True, kw_only=True):
    """The companions agterm attached, and whether the far Mac said which they are."""

    known: bool = msgspec.field(default=True, name="membershipKnown")
    companions: tuple[Member, ...] = ()


class Attached(msgspec.Struct, frozen=True, kw_only=True):
    """The parent's row here, and its group."""

    id: str | None = None
    group: Group | None = msgspec.field(default=None, name="remoteGroup")


class Reply(msgspec.Struct, frozen=True, kw_only=True):
    """`zmx attach --companions --json`'s answer, done or kept in part."""

    ok: bool = True
    error: str | None = None
    found: Attached | None = msgspec.field(default=None, name="result")
