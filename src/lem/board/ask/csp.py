"""The scripts a question page can run on the board's origin."""

import re

from lem.app.asking.scripts import META

HASHES = re.compile(rb"'sha256-[A-Za-z0-9+/]{43}='(?: 'sha256-[A-Za-z0-9+/]{43}=')*")


def policy(body: bytes) -> str:
    """Only the trusted scripts in the verified page may run."""
    prefix = f'<{META}"'.encode("ascii")
    _, _, marked = body.partition(prefix)
    listed, _, _ = marked.partition(b'"')
    sources = listed.decode("ascii") if HASHES.fullmatch(listed) else "'none'"
    return (
        f"script-src {sources}; connect-src 'self'; form-action 'none'; base-uri 'none'; "
        "object-src 'none'; frame-src 'none'; frame-ancestors 'self'"
    )
