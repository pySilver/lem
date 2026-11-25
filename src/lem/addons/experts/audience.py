"""What the expert needs to know about the people affected by its answer."""

import re
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lem.addons.cast.person import Person
    from lem.addons.cast.project import Cast

# The length of the "Who they are" excerpt on main, 2026-11-25.
WHO_WORDS = 60
type Heading = re.Match[str] | None
WHO_HEADING = re.compile(r"^#{2,6}\s+who they are\s*$", re.IGNORECASE | re.MULTILINE)


def who_they_are(text: str, stem: str) -> tuple[str, str]:
    """The first heading and the persona's identity, without quotes or comments."""
    stripped = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    title = re.search(r"^# (.+)$", stripped, re.MULTILINE)
    heading = title[1].strip() if title else stem
    section = WHO_HEADING.search(stripped)
    said = paragraph(stripped, title, section)
    return heading, shortened(said)


def paragraph(text: str, title: Heading, section: Heading) -> str:
    """Use the explicit section, or the first paragraph after the first heading."""
    if section:
        after = text[section.end() :]
        return re.split(r"^#", after, maxsplit=1, flags=re.MULTILINE)[0]
    remaining = text[title.end() :] if title else text
    plain = re.sub(r"^[>#].*$", "", remaining, flags=re.MULTILINE)
    paragraphs = re.split(r"\n\s*\n", plain.strip(), maxsplit=1)
    return paragraphs[0]


def shortened(paragraph: str) -> str:
    """Keep the excerpt short, ending at a sentence when possible."""
    words = " ".join(paragraph.split())
    kept: list[str] = []
    for part in re.split(r"(?<=[.!?])\s+", words):
        more = " ".join((*kept, part))
        if kept and len(more.split()) > WHO_WORDS:
            return " ".join((*kept, "…"))
        kept.append(part)
    return " ".join(kept)


def line(persona: Person) -> str:
    """Name the original file and excerpt the persona's own words."""
    text = Path(persona.person).read_text(encoding="utf-8")
    heading, who = who_they_are(text, persona.stem)
    said = who or "Read the persona file."
    return f"- **{heading}** (`{persona.path}`): {said}"


def describe(found: Cast) -> str:
    """Give the profile and the personas, without their seats."""
    path = found.profile.path if found.profile else ""
    profile = (
        f"Read the project's profile first: `{path}`."
        if path
        else "The project has no profile."
    )
    people = "\n".join(map(line, found.personas))
    return f"""## Who the code is for

{profile}

{people}

Weigh each option by what it does to these people. Answer as an engineer.
"""
