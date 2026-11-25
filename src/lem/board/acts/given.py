"""The form of an act, as the board's page posts it (`board/inputs/forms.py`): the question's id
(`key`), the option, the owner's note (`words`), the digest the page showed, the confirm of a
drop or a merge, the commit the merge's step showed (`tip`), a backlog item's path (`item`), the
view under the panel (`in`) and the tab (`tab`).

A form is a few short fields and a note: one over `FORM_BYTES` is no form of the board's.
"""

import msgspec
from starlette.requests import ClientDisconnect, Request

# The largest form an act takes, in bytes: a few short fields and a note of a few paragraphs
# (`serve.FORM_BYTES` on `main` was 4096 with a note of one line; the note box takes 2000
# characters, `board/inputs/forms.TextBox`, each up to 4 bytes).
FORM_BYTES = 12288
# The longest note of an answer, in characters (the note box's own bound).
NOTE_CHARS = 2000
# The fields a form of the board has.
FIELDS = 9


class Given(msgspec.Struct, frozen=True, kw_only=True):
    """The fields of an act's form; a field the form leaves out is empty."""

    key: str = ""
    option: str = ""
    words: str = ""
    digest: str = ""
    confirm: str = ""
    tip: str = ""
    path: str = msgspec.field(default="", name="item")
    under: str = msgspec.field(default="", name="in")
    tab: str = ""

    @property
    def note(self) -> str:
        """The owner's note on one line, at most NOTE_CHARS."""
        return " ".join(self.words.split())[:NOTE_CHARS]


def sized(request: Request) -> bool:
    """Whether the request says its length, and it is a form's."""
    length = request.headers.get("content-length", "")
    return length.isdigit() and int(length) <= FORM_BYTES


async def given(request: Request) -> Given | None:
    """The form of the request, or None when it carries no form of the board's."""
    if not sized(request):
        return None
    try:
        form = await request.form(max_files=0, max_fields=FIELDS * 2)
    except ClientDisconnect:
        return None
    pairs = form.multi_items()
    texts = {name: shown for name, shown in pairs if isinstance(shown, str)}
    return msgspec.convert(texts, Given)
