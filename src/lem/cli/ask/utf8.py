"""Half of a UTF-16 pair in text from a spec or an answer."""

import json
import re
from math import isfinite

HALF = re.compile("[\ud800-\udfff]")


def whole(words: str) -> str:
    """Make a half character the UTF-8 replacement character."""
    return HALF.sub("\ufffd", words)


def decode(raw: str) -> object:
    """Read JSON and keep all its strings as UTF-8."""
    return normalized(json.loads(raw))


def normalized(given: object) -> object:
    """Make half characters whole throughout the decoded value."""
    if isinstance(given, str):
        return whole(given)
    if isinstance(given, list):
        return [normalized(part) for part in given]
    if isinstance(given, dict):
        return {whole(key): normalized(part) for key, part in given.items()}
    if isinstance(given, float) and not isfinite(given):
        raise ValueError("numbers in JSON must be finite")
    return given
