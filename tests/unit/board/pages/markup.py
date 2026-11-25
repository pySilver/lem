"""Read HTML facts without depending on the template's whitespace or escapes."""

from dataclasses import dataclass, field
from html.parser import HTMLParser

VOID = frozenset(
    [
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    ]
)


@dataclass
class Node:
    tag: str
    attrs: dict[str, str | None] = field(default_factory=dict)
    children: list[Node | str] = field(default_factory=list)

    def has(self, name: str) -> bool:
        return name in (self.attrs.get("class") or "").split()

    def words(self) -> str:
        text = "".join(
            kid.raw() if isinstance(kid, Node) else kid for kid in self.children
        )
        return " ".join(text.split())

    def raw(self) -> str:
        return "".join(
            kid.raw() if isinstance(kid, Node) else kid for kid in self.children
        )

    def all(self, *, id_: str = "", cls: str = "", tag: str = "") -> list[Node]:
        found: list[Node] = []
        for kid in self.children:
            if not isinstance(kid, Node):
                continue
            if (
                (not id_ or kid.attrs.get("id") == id_)
                and (not cls or kid.has(cls))
                and (not tag or kid.tag == tag)
            ):
                found.append(kid)
            found.extend(kid.all(id_=id_, cls=cls, tag=tag))
        return found

    def one(self, *, id_: str = "", cls: str = "", tag: str = "") -> Node:
        found = self.all(id_=id_, cls=cls, tag=tag)
        assert len(found) == 1, (id_, cls, tag, len(found))
        return found[0]


class Parsed(HTMLParser):
    def __init__(self, html: str) -> None:
        super().__init__()
        self.root = Node("#document")
        self.stack = [self.root]
        self.feed(html)
        self.close()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        child = Node(tag, dict(attrs))
        self.stack[-1].children.append(child)
        if tag not in VOID:
            self.stack.append(child)

    def handle_endtag(self, tag: str) -> None:
        for index in reversed(range(1, len(self.stack))):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                break

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.stack[-1].children.append(Node(tag, dict(attrs)))

    def handle_data(self, data: str) -> None:
        self.stack[-1].children.append(data)
