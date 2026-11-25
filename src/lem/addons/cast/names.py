"""The names shared by the panel's seats and the experts."""

import re


def name_of(model: str | None, otherwise: str) -> str:
    """The last word of the model that contains a letter, or the seat's name."""
    if model is None:
        return otherwise
    words = re.findall(r"[a-z0-9]*[a-z][a-z0-9]*", model.lower())
    return words[-1] if words else otherwise
