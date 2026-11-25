"""The words a task's first line quotes: the first sentence of a criterion, an outcome, a
backlog item's title or the owner's ask, as the middle of a line (`first_sentence`,
`in_his_words` and `criterion_of` on `main`)."""

import re
from itertools import takewhile

# A few words: a bold run of no more opens a paragraph as its label, and a paragraph or a
# sentence of no more is no outcome.
FEW_WORDS = 3
SENTENCE = re.compile(r"(.+?[.!?])(?=\s|$)")
# A code span, kept as it is, or a bold run, whose text is kept without its `**`: the `**` a
# code span names (`src/**/*.py`, `**kwargs`) never opens or closes a run.
BOLD_RUN = re.compile(r"(`[^`]*`)|\*\*(?=\S)((?:`[^`]*`|[^`])+?)(?<=\S)\*\*")
FIRST = re.compile(r"(?m)^1\.[ \t]+(.+)$")
# What ends a criterion's sentence: its case, a test line, or a chart.
CASE = re.compile(r"\s*(\d+\.|[-*+]|```)")
HEADING = re.compile(r"# (.+)")


def first_sentence(text: str) -> str:
    """The first sentence of `text` on one line, without its closing period or colon; the
    whole text when it has no sentence's end."""
    flat = " ".join(text.split())
    found = SENTENCE.match(flat)
    said = (found[1] if found else flat).strip()
    if said.endswith((".", ":")):
        return said[:-1].rstrip()
    return said


def in_his_words(text: str) -> str:
    """A sentence as the middle of a line: its first word lower-cased when it is an ordinary
    word with a capital ("The footer says" reads "the footer says"), never a name such as
    README or I."""
    word = text.split(" ", 1)[0]
    rest = word[1:]
    ordinary = rest.isalpha() and rest.islower()
    if ordinary and word[:1].isupper():
        return text[:1].lower() + text[1:]
    return text


def goes_on(row: str) -> bool:
    """Whether a row under a criterion's first line goes on with its sentence: indented, and
    no case, test line or chart."""
    if not row.strip() or CASE.match(row):
        return False
    return row.startswith((" ", "\t"))


def criterion_of(text: str) -> str | None:
    """The sentence of the first criterion of a `criteria.md`, or None."""
    found = FIRST.search(text)
    if found is None:
        return None
    rest = text[found.end() :].splitlines()[1:]
    said = " ".join((found[1], *takewhile(goes_on, rest)))
    return first_sentence(said) or None


def quoted(paragraph: tuple[str, ...]) -> str | None:
    """The first sentence of a paragraph without the marks of its bold runs, or None for a
    paragraph of a few words."""
    joined = " ".join(paragraph)
    said = BOLD_RUN.sub(unbolded, joined)
    return first_sentence(said) if len(said.split()) > FEW_WORDS else None


def unbolded(run: re.Match[str]) -> str:
    """A code span as it is, or a bold run's text without its marks."""
    return run[1] or run[2]


def title_of(text: str) -> str | None:
    """The first sentence of a backlog item's title, its first `# ` heading, or None."""
    matches = map(HEADING.match, text.splitlines())
    found = next(filter(None, matches), None)
    return first_sentence(found[1].strip()) if found else None
