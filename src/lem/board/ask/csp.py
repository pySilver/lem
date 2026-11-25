"""The scripts a question page can run on the board's origin."""

from base64 import b64encode
from hashlib import sha256

from lem.kernel import paths


def policy() -> str:
    """Only the installed runtime and chart library may run as scripts."""
    root = paths.root() / "skills"
    script = root / "lem-ask" / "runtime" / "ask.js"
    charts = root / "lem" / "assets" / "vendor" / "pele.js"
    trusted = (script, charts)
    sources = " ".join(hashed(path.read_bytes()) for path in trusted)
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
