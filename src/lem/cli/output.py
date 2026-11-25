"""The one place that prints a command's envelope and gives its exit code.

Standard output is one JSON document: exit 0 done, 1 a refusal, 3 a fault. A wrong call is
Click's own, on standard error with exit 2, and prints no envelope.
"""

import sys
from typing import TYPE_CHECKING

import msgspec

from lem.kernel.envelope import Envelope, Failed, Refused

if TYPE_CHECKING:
    from lem.kernel.errors import Refusal

DONE = 0
REFUSED = 1
FAILED = 3


def done(outcome: object) -> int:
    """Print the envelope of a command that succeeded: its own, or one around its outcome."""
    if isinstance(outcome, Envelope):
        printed(outcome)
        return DONE
    if outcome is None:
        printed(Envelope(ok=True))
        return DONE
    encoded = msgspec.json.encode(outcome)
    printed(Envelope(ok=True, outcome=msgspec.Raw(encoded)))
    return DONE


def refused(refusal: Refusal) -> int:
    """Print a refusal with its code, why and fix."""
    said = Refused(code=refusal.code, why=refusal.why, fix=refusal.fix)
    printed(Envelope(ok=False, refusal=said))
    return REFUSED


def failed(line: str, log: str) -> int:
    """Print a fault: one line for the owner, and the log that holds its traceback."""
    printed(Envelope(ok=False, fault=Failed(line=line, log=log)))
    return FAILED


def printed(envelope: Envelope) -> None:
    """Write the envelope as one line of JSON on standard output."""
    text = msgspec.json.encode(envelope).decode()
    sys.stdout.write(f"{text}\n")
    sys.stdout.flush()
