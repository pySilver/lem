"""One entry of a task's journal: the union of every kind, told apart by `kind`."""

from lem.records.journal.landing import (
    CarefulMissed,
    CheckEnd,
    CheckWait,
    MergeWait,
    NotGreen,
    ReviewRound,
)
from lem.records.journal.merge import LandAgain, MergeNoted, ReadNoted, RefusalNoted
from lem.records.journal.proposal import ProposalNoted
from lem.records.journal.sessions import (
    SessionClosed,
    SessionOpened,
    SessionStopped,
    SessionWoken,
    SessionWorked,
)
from lem.records.journal.task import (
    CriteriaNoted,
    DecisionNoted,
    OwnerAct,
    SpanMark,
    StateNoted,
    Summary,
)

type Entry = (
    SpanMark
    | StateNoted
    | DecisionNoted
    | OwnerAct
    | CriteriaNoted
    | Summary
    | ReviewRound
    | CarefulMissed
    | ProposalNoted
    | NotGreen
    | CheckWait
    | CheckEnd
    | MergeWait
    | ReadNoted
    | RefusalNoted
    | MergeNoted
    | LandAgain
    | SessionOpened
    | SessionClosed
    | SessionWoken
    | SessionStopped
    | SessionWorked
)
