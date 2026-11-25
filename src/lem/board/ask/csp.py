"""The scripts a question page can run on the board's origin."""

import re
from base64 import b64encode
from hashlib import sha256

META = 'meta name="lem-card-scripts" content='
HASHES = re.compile(rb"'sha256-[A-Za-z0-9+/]{43}='(?: 'sha256-[A-Za-z0-9+/]{43}=')*")


def marker(scripts: tuple[str, ...]) -> str:
    """Keep the trusted hashes inside the page the task cites by digest."""
    sources = " ".join(hashed(script.encode("utf-8")) for script in scripts)
    return f'<{META}"{sources}">'


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


def hashed(script: bytes) -> str:
    """The browser's CSP hash of the script text."""
    raw = script.decode("utf-8")
    lines = raw.replace("\r\n", "\n").replace("\r", "\n")
    digest = sha256(lines.encode("utf-8")).digest()
    code = b64encode(digest).decode("ascii")
    return f"'sha256-{code}'"
