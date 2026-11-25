"""The before and after pictures of a task (`board_task.pairs_of` and `media_pair` on `main`):
`media/NAME-before.png` beside `media/NAME-after.png`, each that the outcome's text does not
show itself; a view that is new has only its after."""

import re
from urllib.parse import quote

from lem.board.inputs.task.cards import Picture, Shot
from lem.board.views import words

AFTER = "after"
# The files of a task's folder, by their paths in it.
type Files = tuple[str, ...]
PAIR = re.compile(
    r"^media/(?P<name>.+)-(?P<side>before|after)\.(?:png|jpe?g|gif|webp)$",
    re.IGNORECASE,
)


def shots(files: Files, shown: str, media: str) -> tuple[Shot, ...]:
    """Each pair of `files` whose after the text `shown` does not show, by its name, from the
    folder of pictures `media`."""
    found: dict[str, dict[str, str]] = {}
    for path in files:
        named = PAIR.match(path)
        if named:
            sides = found.setdefault(named["name"], {})
            sides[named["side"].lower()] = path
    return tuple(
        shot(name, sides, media)
        for name, sides in sorted(found.items())
        if sides.get(AFTER, shown) not in shown
    )


def shot(name: str, sides: dict[str, str], media: str) -> Shot:
    """One pair: its caption, its before (when there is one) and its after."""
    caption = caption_of(name)
    before = sides.get("before")
    return Shot(
        id=f"shots-{name}",
        caption=caption,
        before=picture(before, caption, "before", media) if before else None,
        after=picture(sides[AFTER], caption, AFTER, media),
    )


def picture(path: str, caption: str, side: str, media: str) -> Picture:
    """A picture, which opens at its full size."""
    parts = path.removeprefix("media/").split("/")
    quoted = (quote(part, safe="") for part in parts)
    src = media + "/".join(quoted)
    return Picture(src=src, href=src, alt=f"{caption}, {side}")


def caption_of(name: str) -> str:
    """`receipt-total` as `Receipt total`."""
    return words.capital(name.replace("-", " ").replace("_", " "))
