"""Each pull request a line names, as a markdown link (`board_model.pull_refs` and
`pull_links_md` on `main`): `OWNER/REPO#N` on the forge's host, a bare `#N` on the task's own
repository, and an address as it is, since the reader makes it a link itself. Code, a link and a
fenced block keep their text."""

import re

PULL_REF = re.compile(
    r"(?P<url>https?://[^\s<>()\"'`]+?/pull/\d+)(?![\w/])"
    r"|(?<![\w./-])(?P<repo>[A-Za-z0-9][\w.-]*/[\w.-]+)#(?P<n2>\d+)\b"
    r"|(?<![\w&#/])#(?P<n3>\d+)\b"
)
# The parts of a markdown text a link is never put into.
KEEP = re.compile(
    r"```[\s\S]*?(?:```|\Z)|~~~[\s\S]*?(?:~~~|\Z)|`[^`\n]*`"
    r"|!?\[[^\]\n]*\]\([^)\n]*\)|<[^>\n]*>"
)
GITHUB = "https://github.com"
SCHEME = len("https://")


def forge_of(url: str | None) -> str | None:
    """`https://github.com/OWNER/REPO` of a pull request's address, or None."""
    if url is None or "/pull/" not in url:
        return None
    return url[: url.index("/pull/")]


def linked(text: str, forge: str | None) -> str:
    """`text` with each pull request it names as a markdown link, outside its code, its
    links and its fenced blocks."""
    out, start = [], 0
    for kept in KEEP.finditer(text):
        before = text[start : kept.start()]
        out += [refs(before, forge), kept[0]]
        start = kept.end()
    out.append(refs(text[start:], forge))
    return "".join(out)


def refs(text: str, forge: str | None) -> str:
    """A part of no code with each pull request it names as a link."""
    return PULL_REF.sub(lambda found: link_of(found, forge), text)


def link_of(found: re.Match[str], forge: str | None) -> str:
    """The link of one pull request; an address, or a bare number with no forge, as it is."""
    named = found[0]
    if found["url"]:
        return named
    if found["repo"]:
        host = forge[: forge.index("/", SCHEME)] if forge else GITHUB
        number, repo = found["n2"], found["repo"]
        return f"[{named}]({host}/{repo}/pull/{number})"
    if forge is None:
        return named
    number = found["n3"]
    return f"[{named}]({forge}/pull/{number})"
