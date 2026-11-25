"""Half of a UTF-16 pair in text from a spec or an answer."""

import json
import re

HALF = re.compile("[\ud800-\udfff]")


def whole(words: str) -> str:
    """Make a half character the UTF-8 replacement character."""
    return HALF.sub("\ufffd", words)


def decode(raw: str) -> object:
    """Read JSON and keep all its strings as UTF-8."""
    given = json.loads(raw)
    encoded = json.dumps(given, ensure_ascii=False, allow_nan=False)
    return json.loads(whole(encoded))
