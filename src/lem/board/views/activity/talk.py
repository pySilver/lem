"""A plan talk's record in words: its questions and turns, how its questions ended, its repairs
(`board_model.talk_counts` on `main`)."""

from typing import TYPE_CHECKING

from lem.board.inputs.names import plural

if TYPE_CHECKING:
    from lem.records.work import Talk


def counts(talk: Talk) -> str:
    """`3 questions in 7 turns · 2 settled, 1 open · 1 repaired: 1 at the cause`."""
    questions = plural(talk.questions, "question")
    turns = plural(talk.turns, "turn")
    parts = [
        f"{questions} in {turns}",
        f"{talk.settled} settled, {talk.open} open{design(talk.design)}",
        repaired(talk),
    ]
    if talk.shared:
        decision = "decision" if talk.shared == 1 else "decisions"
        parts.append(f"{talk.shared} {decision} two questions named")
    if talk.unargued:
        parts.append(f"{talk.unargued} raised, not argued")
    return " · ".join(parts)


def design(count: int) -> str:
    """`, 2 of them design choices`, or nothing."""
    if not count:
        return ""
    choice = "a design choice" if count == 1 else "design choices"
    return f", {count} of them {choice}"


def repaired(talk: Talk) -> str:
    """`2 repaired: 1 at the cause, 1 a layer over a cited decision`."""
    where = []
    if talk.root:
        where.append(f"{talk.root} at the cause")
    if talk.layer:
        layer = "a layer" if talk.layer == 1 else "layers"
        where.append(f"{talk.layer} {layer} over a cited decision")
    said = f"{talk.repaired} repaired"
    if not where:
        return said
    named = ", ".join(where)
    return f"{said}: {named}"
