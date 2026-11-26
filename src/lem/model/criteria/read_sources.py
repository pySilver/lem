"""The persona name and model family that identify a panel seat."""


def seat(name: str) -> tuple[str, str]:
    """Keep the persona's name and compare the family without case."""
    persona, _, family = name.rpartition(",")
    return persona.strip(), family.strip().casefold()
