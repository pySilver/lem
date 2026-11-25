"""The trusted script hashes in a saved question page."""

from base64 import b64encode
from hashlib import sha256

META = 'meta name="lem-card-scripts" content='


def marker(scripts: tuple[str, ...]) -> str:
    """Keep the trusted hashes inside the page the task cites by digest."""
    sources = " ".join(hashed(script.encode("utf-8")) for script in scripts)
    return f'<{META}"{sources}">'


def hashed(script: bytes) -> str:
    """The browser's CSP hash of the script text."""
    raw = script.decode("utf-8")
    lines = raw.replace("\r\n", "\n").replace("\r", "\n")
    digest = sha256(lines.encode("utf-8")).digest()
    code = b64encode(digest).decode("ascii")
    return f"'sha256-{code}'"
