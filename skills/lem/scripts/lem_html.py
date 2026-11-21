"""HTML for the pages the board server renders, built so that text is escaped unless it says otherwise.

    h("p", {"class": "ask"}, task.ask)      ->  Markup('<p class="ask">...</p>')

`h(tag, attrs, *kids)` is the one way a page of `lem_board_pages` makes an element: every attribute
value and every child that is a plain `str` (or a number) is escaped, and only a `Markup` passes as it
is. `h` returns `Markup`, so elements nest with no second escape, and a task's title, ask, talk or a
backlog item's text can reach the page only as text. A child may be a list, a tuple or a generator,
whose items count one by one; None, False and "" are left out, so a part that has nothing to show is
written `cond and h(...)`. An attribute whose value is None or False is left out, and one whose value
is True is written bare (`hidden`, `open`).

`Markup` is a `str` that says "this is HTML already". The pages make one only from `h`, from `join`,
or from a constant of Lem's own (an SVG file of the plugin): never from what a task, a record or a
request holds. Markdown is not rendered here: the page renders it in the browser with the kit's
reader, from the text an element carries escaped (`text` of a `<template>` or a data attribute).
"""

import html
from collections.abc import Iterable

# The elements that have no end tag.
VOID = frozenset({"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"})


class Markup(str):
    """Text that is HTML already, which `h` and `escape` pass on as they are."""

    __slots__ = ()

    def __html__(self) -> str:
        return self

    def __add__(self, other: object) -> "Markup":
        return Markup(str.__add__(self, escape(other)))

    def __radd__(self, other: object) -> "Markup":
        return Markup(str.__add__(escape(other), self))


def escape(value: object) -> Markup:
    """A value as HTML text: a `Markup` as it is, anything else as its `str` with `&`, `<`, `>`, `"`
    and `'` escaped."""
    if isinstance(value, Markup):
        return value
    return Markup(html.escape(str(value), quote=True))


def flat(kids: Iterable) -> Iterable:
    """The children in their order, with lists, tuples and generators opened, and the empty ones left out."""
    for kid in kids:
        if kid is None or kid is False or kid == "":
            continue
        if isinstance(kid, (list, tuple)) or (hasattr(kid, "__iter__") and hasattr(kid, "__next__")):
            yield from flat(kid)
        else:
            yield kid


def attributes(attrs: dict | None) -> str:
    out = []
    for key, value in (attrs or {}).items():
        if value is None or value is False:
            continue
        if not key or any(c in key for c in ' "\'<>/=\t\n'):
            raise ValueError(f"{key!r} is no attribute name")
        out.append(f" {key}" if value is True else f' {key}="{escape(value)}"')
    return "".join(out)


def h(tag: str, attrs: dict | None = None, *kids: object) -> Markup:
    """One element, its attributes and its children escaped, as `Markup`."""
    if not tag.replace("-", "").isalnum():
        raise ValueError(f"{tag!r} is no element name")
    inner = "".join(escape(kid) for kid in flat(kids))
    if tag in VOID:
        if inner:
            raise ValueError(f"<{tag}> takes no children")
        return Markup(f"<{tag}{attributes(attrs)}>")
    return Markup(f"<{tag}{attributes(attrs)}>{inner}</{tag}>")


def join(parts: Iterable, between: object = "") -> Markup:
    """The parts one after another, each escaped unless it is `Markup`, with `between` between them."""
    sep = escape(between)
    return Markup(sep.join(escape(part) for part in flat(parts)))


def page(head: Iterable, body: Markup, attrs: dict | None = None) -> Markup:
    """A whole document: the doctype, `<html lang="en">` with `attrs`, the head's parts and the body."""
    return Markup("<!doctype html>\n") + h("html", {"lang": "en", **(attrs or {})}, h("head", None, *head), body)
