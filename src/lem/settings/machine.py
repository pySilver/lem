"""This machine's file, `machine.toml` of Lem's home folder: what is true for the whole
machine, which no other file overrides (docs/settings.md).

The load average under which the checks of a landing start is the owner's 40 for every new
user (2026-11-22), and 0 takes the gate away. A task's session compacts past 600,000 tokens (the
owner, 2026-11-21); 0 leaves it to Claude Code, which refuses a window under 100,000
(`research-compaction.md`, read 2026-11-21). The board's ports are a pick of the proof of
concept, not a measurement. The correction queue is off unless the machine says yes.
"""

from typing import Annotated

import msgspec

from lem.settings.table import Table

LOAD_START = 40.0
PORT = 4536
DOOR_PORT = 4537
HANDOFF_TOKENS = 600_000
HANDOFF_FLOOR = 100_000
HIGHEST_PORT = 65535

type Port = Annotated[int, msgspec.Meta(ge=1, le=HIGHEST_PORT)]
# A machine's name on the tailnet: one DNS label, in lower case.
type Host = Annotated[
    str, msgspec.Meta(pattern="^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")
]


class Load(Table, frozen=True, kw_only=True):
    """`[load]`: the load average under which the checks of a landing start; 0, no gate."""

    start: Annotated[
        float,
        msgspec.Meta(
            ge=0,
            description="load.start: a load average above 0, or 0 for no gate "
            "(lem settings set load.start N --machine)",
        ),
    ] = LOAD_START


class Serve(Table, frozen=True, kw_only=True):
    """`[serve]`: the board server's port, and the door for the owner's phone."""

    port: Annotated[
        Port, msgspec.Meta(description="serve.port: a port from 1 to 65535")
    ] = PORT
    tailscale: Annotated[
        bool, msgspec.Meta(description="serve.tailscale: true or false")
    ] = False
    tailscale_port: Annotated[
        Port, msgspec.Meta(description="serve.tailscale_port: a port from 1 to 65535")
    ] = DOOR_PORT


class Handoff(Table, frozen=True, kw_only=True):
    """`[handoff]`: the tokens past which a task's session compacts; 0, Claude Code's own."""

    tokens: Annotated[
        int,
        msgspec.Meta(
            ge=0,
            description="handoff.tokens: 0, or a whole number of 100000 or more "
            "(lem settings set handoff.tokens N --machine)",
        ),
    ] = HANDOFF_TOKENS


class Corrections(Table, frozen=True, kw_only=True):
    """`[corrections]`: whether the correction queue collects the owner's corrections."""

    collect: Annotated[
        bool,
        msgspec.Meta(
            description="corrections.collect: true or false "
            "(lem settings set corrections.collect yes --machine)"
        ),
    ] = False


class Machine(Table, frozen=True, kw_only=True):
    """`machine.toml` whole."""

    load: Load = Load()
    serve: Serve = Serve()
    peers: Annotated[
        dict[Host, Port],
        msgspec.Meta(
            description="peers.HOST: a machine's name on the tailnet, and its door's port"
        ),
    ] = msgspec.field(default_factory=dict)
    handoff: Handoff = Handoff()
    corrections: Corrections = Corrections()
