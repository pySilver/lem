"""One board server's fresh Tailscale facts, shared across peer reads."""

import asyncio
from dataclasses import dataclass, field
from time import monotonic

from lem.addons.peers import local, tailnet
from lem.addons.peers.look import LIST_FRESH


@dataclass(slots=True)
class Address:
    """Resolve peer addresses from one successful status per freshness interval."""

    space: tailnet.Status | None = None
    until: float = 0
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def __call__(self, host: str, port: int) -> str:
        """Read the tailnet off the request loop and leave failures due for retry."""
        async with self.lock:
            space = self.space
            stale = space is None or monotonic() >= self.until
            if stale:
                space = await asyncio.to_thread(local.status)
            base = tailnet.address(space.suffix, host, port)
            if stale:
                self.space = space
                self.until = monotonic() + LIST_FRESH
            tailnet.member(host, space)
            return base
