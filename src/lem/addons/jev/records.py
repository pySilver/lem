"""The spec's questions, the provider's request, and the answers Lem prints."""

from typing import Annotated

import msgspec

from lem.records.base import Frozen

type Probability = Annotated[float, msgspec.Meta(ge=0, le=1)]
type State = str | dict[str, object] | list[object]
type Question = Choice | Noul


class Choice(
    Frozen,
    frozen=True,
    kw_only=True,
    tag="choice",
    tag_field="type",
    forbid_unknown_fields=True,
):
    """A choice between named options."""

    instructions: str
    choices: dict[str, str]


class Noul(
    Frozen,
    frozen=True,
    kw_only=True,
    tag="noul",
    tag_field="type",
    forbid_unknown_fields=True,
):
    """A yes/no question, with optional criteria for both answers."""

    instructions: str
    positive: str | msgspec.UnsetType = msgspec.field(default=msgspec.UNSET, name="yes")
    negative: str | msgspec.UnsetType = msgspec.field(default=msgspec.UNSET, name="no")


class WireSpec(Frozen, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The spec before each question is checked by its name."""

    state: State
    questions: dict[str, msgspec.Raw]
    model: str | None = None


class Spec(Frozen, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The facts and the questions to send to the model."""

    state: State
    questions: dict[str, Question]
    model: str | None = None


class Query(Frozen, frozen=True, kw_only=True):
    """One question in the decisions endpoint's form."""

    type: str
    instructions: str
    criteria: dict[str, str] | None = None


class Request(Frozen, frozen=True, kw_only=True):
    """The JSON body the endpoint reads."""

    model: str
    state: State
    questions: dict[str, Query]
