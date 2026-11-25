"""What every table of Lem's settings shares: a frozen struct that refuses a key it does not
know, and the forms of its words."""

from typing import Annotated

import msgspec

# A shell command, a sentence or a name: an empty one would run nothing, and pass.
type Words = Annotated[str, msgspec.Meta(pattern=r"\S")]
type Lines = tuple[Words, ...]


class Table(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The base of every table: frozen, keyword fields, an unknown key refused."""
