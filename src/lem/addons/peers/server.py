"""The small part of a peer's server facts read on join."""

from lem.records.base import Frozen


class Install(Frozen, frozen=True, kw_only=True):
    """The peer's Lem install."""

    version: str


class Server(Frozen, frozen=True, kw_only=True):
    """The peer's name and version, in the board's server response."""

    host: str
    install: Install
