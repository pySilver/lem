"""What `agtermctl` prints for a session of another Mac: the list of `zmx tree HOST --json` and the
restore mode of `restore mode --json` (agterm be92bc63, `RemoteTree.swift` and
`ControlServer+RestoreMode.swift`; the owner's `restore mode --json` on 2026-11-27 printed
`{"result":{"restore":{"active":"rerun",...}},"ok":true}`). Keys Lem does not read are read past.
A list with no `sessions` is no list: agterm always writes the key.
"""

import msgspec


class Listed(msgspec.Struct, frozen=True, kw_only=True):
    """A session the far Mac offers: its id there."""

    id: str


class Remote(msgspec.Struct, frozen=True, kw_only=True):
    """The far Mac's sessions whose every pane has a live daemon."""

    sessions: tuple[Listed, ...]


class Found(msgspec.Struct, frozen=True, kw_only=True):
    """The result of `zmx tree HOST --json`."""

    remote: Remote


class Listing(msgspec.Struct, frozen=True, kw_only=True):
    """`zmx tree HOST --json`'s answer: `{"result": {"remote": {"sessions": [...]}}}`."""

    found: Found = msgspec.field(name="result")


class Restore(msgspec.Struct, frozen=True, kw_only=True):
    """The restore mode this launch of agterm runs: `none`, `rerun` or `live`."""

    active: str | None = None


class Restored(msgspec.Struct, frozen=True, kw_only=True):
    """The result of `restore mode --json`."""

    restore: Restore


class Moded(msgspec.Struct, frozen=True, kw_only=True):
    """`restore mode --json`'s answer: `{"result": {"restore": {"active": ...}}}`."""

    found: Restored = msgspec.field(name="result")
