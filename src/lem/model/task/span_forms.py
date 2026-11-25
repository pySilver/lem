"""The form of each span's start and end: the one field it takes, and the values that field may
have (`STARTS` on `main`). A start that takes nothing refuses a field, and an end takes only the
field that tells its span from another of the same name."""

from types import MappingProxyType
from typing import Literal, get_args

import msgspec

from lem.kernel.errors import Refusal
from lem.records.base import Frozen
from lem.records.work import SpanName

type Edge = Literal["start", "end"]
type Field = Literal["of", "job", "by"]

FIELDS: tuple[Field, ...] = get_args(Field.__value__)
JOB: Field = "job"
# A builder's jobs beside a task of the plan (the span `task`) and the fast track's one
# builder (the span `small`).
BUILDER_JOBS = (
    "the repair of a conflict with the base",
    "the repair of a failed check",
    "the fix of a review's findings",
    "the removal of the task's item",
)
JOBS = ", ".join(BUILDER_JOBS)
LEADS = ("builder", "session")
NOTHING = "takes nothing"
ONLY = "and nothing else"


class Given(Frozen, frozen=True, kw_only=True):
    """The words of one mark: the span's name, its edge, and its fields."""

    name: str
    edge: Edge
    of: str | None = None
    job: str | None = None
    by: str | None = None


class Form(Frozen, frozen=True, kw_only=True):
    """A span's form: its name, the field its start takes and the values it may have (none
    named: any words), the field its end takes, and the words that say so."""

    name: SpanName
    start: Field | None = None
    allowed: tuple[str, ...] = ()
    end: Field | None = None
    says: str


FORMS: MappingProxyType[str, Form] = MappingProxyType(
    {
        form.name: form
        for form in (
            Form(
                name="lead",
                start="by",
                allowed=LEADS,
                says=f"the span lead takes --by builder|session, {ONLY}: a lead that "
                "plans or builds, or the plan talk's pair",
            ),
            Form(
                name="small",
                says=f"the span small, the fast track's builder, {NOTHING}",
            ),
            Form(
                name="task",
                start="of",
                end="of",
                says=f"the span task, a task of the plan, takes --of N/M, {ONLY}",
            ),
            Form(
                name="builder",
                start=JOB,
                allowed=BUILDER_JOBS,
                end=JOB,
                says=f"the span builder takes --job JOB, {ONLY}: one of {JOBS}; the fast "
                "track's builder is the span small, a task of the plan the span task, and "
                "the polish pass is lem land's",
            ),
            Form(name="interview", says=f"the span interview {NOTHING}"),
            Form(name="scout", says=f"the span scout {NOTHING}"),
            Form(
                name="investigation",
                start=JOB,
                allowed=("fix", "question"),
                says=f"the span investigation takes --job fix|question, {ONLY}",
            ),
            Form(
                name="plan-talk",
                start="by",
                says=f"the span plan-talk takes --by AGENT, the reviewer, {ONLY}",
            ),
        )
    }
)
NAMES = ", ".join(FORMS)
# The landing's own spans, which `lem land` marks.
LANDING = frozenset(("polish", "checks", "review"))


def form_of(name: str) -> Form:
    """The form of the span `name`; refused for the landing's spans and for a name that is
    no span."""
    form = FORMS.get(name)
    if form is not None:
        return form
    if name in LANDING:
        raise Refusal(
            "span-landing",
            f"the span {name} is the landing's: lem land marks its start and its end itself",
            "mark nothing: lem land next names the landing's step",
        )
    raise Refusal(
        "span-name", f"{name!r} is no span of a task's work", f"name one of {NAMES}"
    )


def given_fields(given: Given) -> dict[Field, str]:
    """The fields a mark gives, by name."""
    words = msgspec.structs.asdict(given)
    return {key: words[key] for key in FIELDS if words[key] is not None}


def refused(says: str, given: Given, detail: str | None = None) -> Refusal:
    """The refusal of a mark that is not in its form, with what it gave."""
    keys = [f"--{key}" for key in given_fields(given)]
    if detail is None:
        listed = ", ".join(keys) or "no field"
        detail = f"this one has {listed}"
    return Refusal(
        "span-form",
        f"{says}; {detail}",
        f"mark it again in its form: lem task span SLUG {given.name} {given.edge} --help",
    )


def says_of(form: Form, *, at_end: bool) -> str:
    """The words of a span's form at its start, or at its end."""
    if not at_end:
        return form.says
    takes = "nothing" if form.end is None else f"--{form.end}"
    return f"the end of the span {form.name} takes {takes}"


def check(form: Form, given: Given, *, at_end: bool) -> None:
    """Refuse a mark whose fields are not those of its form, or whose field has a value the
    form does not take: blank words, or words that are not among the values it names."""
    wanted = form.end if at_end else form.start
    named = given_fields(given)
    if set(named) != {wanted} - {None}:
        raise refused(says_of(form, at_end=at_end), given)
    if wanted is None:
        return
    word = named[wanted]
    allowed = form.allowed or (word,)
    if not word.strip() or word not in allowed:
        detail = f"--{wanted} is {word!r}"
        raise refused(says_of(form, at_end=at_end), given, detail)
