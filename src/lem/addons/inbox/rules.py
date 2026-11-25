"""What to send, keep, forget, retry or withdraw on one look."""

from lem.addons.inbox.records import Act, Actions, Entry, Look, Wait

KEPT = frozenset((Act.keep, Act.retry))


def decide(look: Look, saved: tuple[Entry, ...]) -> Actions:
    """Keep a held answer intact and never send a new wait when the owner is back."""
    if not look.known:
        return Actions()
    current = {wait.key: wait for wait in look.waits}
    edits = tuple((entry, action(look, entry, current)) for entry in saved)
    waiting = kept_keys(edits)
    return Actions(
        forget=tuple(entry for entry, act in edits if act == Act.forget),
        withdraw=tuple(entry for entry, act in edits if act == Act.withdraw),
        retry=tuple(entry for entry, act in edits if act == Act.retry),
        send=tuple(wait for wait in look.waits if wait.key not in waiting)
        if can_send(look)
        else (),
    )


def kept_keys(edits: tuple[tuple[Entry, Act], ...]) -> frozenset[str]:
    """These waits already have a message or a retry."""
    kept = (entry.wait for entry, act in edits if act in KEPT)
    return frozenset(wait.key for wait in kept)


def can_send(look: Look) -> bool:
    """The owner is away and can reach the Inbox from the phone."""
    return look.away and look.door.running and bool(look.door.tailnet_url)


def action(look: Look, entry: Entry, current: dict[str, Wait]) -> Act:
    """What one old entry needs, including replacement after a change of session."""
    key = entry.wait.key
    if key in look.held:
        return Act.keep
    wait = current.get(key)
    if entry.sent is None:
        return pending(look, entry, wait)
    if same(look, entry.wait, wait):
        return Act.keep
    if not entry.wait.session:
        return Act.forget
    return Act.withdraw if look.door.running else Act.keep


def same(look: Look, saved: Wait, wait: Wait | None) -> bool:
    """Keep a wait that matches or cannot be replaced because the door is closed."""
    if saved == wait:
        return True
    return not can_send(look) and session_change(look, saved, wait)


def pending(look: Look, entry: Entry, wait: Wait | None) -> Act:
    """A lost reply is retried with its original payload and key."""
    if not look.away or entry.wait != wait or entry.payload is None:
        return Act.forget
    return Act.retry if can_send(look) else Act.keep


def session_change(look: Look, saved: Wait, current: Wait | None) -> bool:
    """A change only of session cannot replace a question with the door closed."""
    if current is None:
        return saved.key in look.behind
    return (saved.asks, saved.tip, saved.since, saved.review_digest) == (
        current.asks,
        current.tip,
        current.since,
        current.review_digest,
    )
