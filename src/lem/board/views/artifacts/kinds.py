"""How a file of a task is shown, by the kind its extension names, and the icon and the word of
each kind (`artifacts.KINDS`, `board_task.KIND_ICON` and `KIND_WORD` on `main`)."""

from types import MappingProxyType
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lem.board.inputs.task.artifacts import Kind

TEXT: Kind = "text"
BINARY: Kind = "binary"
IMAGE: Kind = "image"
MARKDOWN: Kind = "markdown"
LOG: Kind = "log"
HTML: Kind = "html"
KINDS: MappingProxyType[str, Kind] = MappingProxyType(
    {
        ".md": MARKDOWN,
        ".markdown": MARKDOWN,
        ".txt": TEXT,
        ".py": TEXT,
        ".js": TEXT,
        ".css": TEXT,
        ".toml": TEXT,
        ".yaml": TEXT,
        ".yml": TEXT,
        ".sh": TEXT,
        ".diff": TEXT,
        ".patch": TEXT,
        ".csv": TEXT,
        ".svg": TEXT,
        ".json": "json",
        ".jsonl": "jsonl",
        ".log": LOG,
        ".out": LOG,
        ".err": LOG,
        ".html": HTML,
        ".htm": HTML,
        ".png": IMAGE,
        ".jpg": IMAGE,
        ".jpeg": IMAGE,
        ".gif": IMAGE,
        ".webp": IMAGE,
        ".ico": BINARY,
        ".pdf": BINARY,
        ".zip": BINARY,
        ".gz": BINARY,
        ".tar": BINARY,
        ".sqlite": BINARY,
        ".db": BINARY,
    }
)
ICONS: MappingProxyType[Kind, str] = MappingProxyType(
    {
        MARKDOWN: "file-lines",
        TEXT: "file",
        "json": "brackets-curly",
        "jsonl": "list",
        LOG: "terminal",
        HTML: "globe",
        BINARY: "file-zipper",
        IMAGE: "image",
    }
)
WORDS: MappingProxyType[Kind, str] = MappingProxyType(
    {
        MARKDOWN: "markdown",
        TEXT: "text",
        "json": "JSON",
        "jsonl": "JSON lines",
        LOG: "log",
        HTML: "page",
        BINARY: "binary",
        IMAGE: "picture",
    }
)


def kind_of(path: str) -> Kind:
    """The kind of the file at `path`, by its extension; one the table does not know is a
    text (`main` read its first bytes for a NUL, which a view does not)."""
    name = path.rpartition("/")[2]
    dot = name.rfind(".")
    suffix = name[dot:].lower() if dot > 0 else ""
    return KINDS.get(suffix, TEXT)
