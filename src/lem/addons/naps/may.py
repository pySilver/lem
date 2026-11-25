"""`lem nap may`: whether a nap may start now, from the settings and the naps' folder; a yes
writes the nap down as started (`project.cmd_may_nap` on `main`).

The naps are one switch, `naps.on` of the team's file, off by Lem's default; one person's local
file may say no on his machine, since a nap spends his tokens. A nap counts as running until its
folder holds its waking note, and for ASLEEP_MINUTES at most; GAP_HOURS pass between two starts.
"""

import datetime as dt
from typing import TYPE_CHECKING

import msgspec

from lem.addons.naps import folder as naps
from lem.addons.naps.answer import May
from lem.settings import places

if TYPE_CHECKING:
    from pathlib import Path

# A guess, not a measurement: the owner's own nap routine runs three times a day.
GAP_HOURS = 6
# A guess: the owner's own routine leaves a nap "about twenty minutes", and an hour is three
# of those.
ASLEEP_MINUTES = 60

type Switch = tuple[bool, str]


def may_nap(state: Path, switch: Switch, now: dt.datetime) -> May:
    """Whether a nap may start now in the state folder `state`, with the naps' switch and the
    file it comes from; a yes is written down."""
    where = state / naps.NAPS
    found = naps.naps_of(where)
    asleep = naps.asleep_of(where)
    why = running_why(where, asleep, found, now) or off_why(switch)
    said = answer_of(where, found, why)
    return said if why else due(where, said, starts_of(found, asleep), now)


def answer_of(where: Path, found: tuple[naps.Started, ...], why: str | None) -> May:
    """A no, with its reason, the folder and its newest nap."""
    newest = found[-1][1] if found else None
    said = why or ""
    return May(may=False, why=said, folder=str(where), newest=newest)


def running_why(
    where: Path,
    asleep: naps.Asleep | None,
    found: tuple[naps.Started, ...],
    now: dt.datetime,
) -> str | None:
    """Why a nap runs now: its start wrote no waking note and is under ASLEEP_MINUTES old;
    None when none runs."""
    if asleep is None or naps.woke(where, asleep, found):
        return None
    if now - asleep.since >= dt.timedelta(minutes=ASLEEP_MINUTES):
        return None
    since = asleep.since.strftime("%Y-%m-%dT%H:%M:%SZ")
    return (
        f"a nap runs since {since}: it ends when naps/{asleep.time}-... holds "
        f"{naps.WAKING}, or {ASLEEP_MINUTES} minutes after its start"
    )


def off_why(switch: Switch) -> str | None:
    """Why the naps are off, by the file that says so; None when they are on."""
    on, source = switch
    if on:
        return None
    local = places.LOCAL.as_posix()
    if source == local:
        return f"the naps are off on this machine (naps.on = false in {local})"
    team = places.TEAM.as_posix()
    return f"the naps are off (naps.on = false in {team})"


def starts_of(
    found: tuple[naps.Started, ...], asleep: naps.Asleep | None
) -> tuple[dt.datetime, ...]:
    """Every start: each nap's, and the newest start's even when it wrote no folder."""
    starts = tuple(when for when, _ in found)
    return starts if asleep is None else (*starts, asleep.since)


def due(
    where: Path, said: May, starts: tuple[dt.datetime, ...], now: dt.datetime
) -> May:
    """The answer with the naps on: a no while the newest start is under GAP_HOURS old, else
    a yes, written down."""
    last = max(starts, default=None)
    age = None if last is None else now - last
    if age is not None and age < dt.timedelta(hours=GAP_HOURS):
        why = f"{ago(age)}, and {GAP_HOURS} hours pass between two naps"
        return msgspec.structs.replace(said, why=why)
    time = now.strftime(naps.TIME)
    naps.fell_asleep(where, naps.Asleep(since=now, time=time))
    why = "there is no nap yet" if age is None else ago(age)
    return msgspec.structs.replace(said, may=True, why=why, time=time)


def ago(age: dt.timedelta) -> str:
    """`the newest nap started 2.0 hours ago`."""
    hours = age / dt.timedelta(hours=1)
    return f"the newest nap started {hours:.1f} hours ago"
