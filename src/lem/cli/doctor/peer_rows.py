"""The rows of the machines joined to this board (`lem serve join`), one for each: whether this
Mac's agterm can show a task's session of that machine.

ssh from this Mac reaches the machine and finds there an `agtermctl` new enough to list its
sessions (`agtermctl zmx tree HOST --json`, run here), and its board says that its agterm runs
Live sessions (`peer_look.py`). HOST is the machine's name on the tailnet, as `lem serve join`
keeps it; another name is a `Host` alias of `~/.ssh/config`. Optional: the board relays the
machine's pages without it.
"""

from typing import TYPE_CHECKING

from lem.adapters.agterm_ctl import TOOL
from lem.adapters.agterm_remote_forms import Listing
from lem.adapters.agterm_reply import checked
from lem.addons.peers import agterm_said, refused_steps
from lem.cli.doctor.look import RUN_WAIT
from lem.cli.doctor.machine_rows import settled
from lem.cli.doctor.row import OPTIONAL, Row
from lem.kernel.errors import Refusal
from lem.ports.faults import Unanswered

if TYPE_CHECKING:
    from lem.cli.doctor.look import Look

USED_FOR = (
    "the board's Open the session on a task of a joined machine: this Mac's agterm "
    "attaches the session of that machine over ssh"
)


def peer_rows(look: Look) -> tuple[Row, ...]:
    """One row for each machine joined; none when no machine is joined."""
    peers = settled(look).settings.peers.items()
    rows = (peer_row(look, name, port) for name, port in peers)
    return tuple(rows)


def far_refusal(look: Look, name: str) -> Refusal | None:
    """Why this Mac's agterm cannot list the machine's sessions over ssh, or None."""
    if look.which(TOOL) is None:
        return Refusal(
            "agtermctl",
            "this Mac has no agtermctl on its PATH",
            "on this Mac, the owner installs agterm's command line tool, from agterm's "
            "Help menu or its Homebrew cask",
        )
    ran = look.ran((TOOL, "zmx", "tree", name, "--json"))
    if ran is None:
        return agterm_said.no_ssh(name, f"no answer in {RUN_WAIT} s")
    try:
        checked(ran, Listing, "zmx tree")
    except Unanswered as failure:
        return refused_steps.of_list(name, name, failure)
    return None


def live_refusal(look: Look, name: str, port: int) -> Refusal | None:
    """Why the machine's agterm does not run Live sessions, or None."""
    live, why = look.peer_live(name, port)
    if live is None:
        return Refusal(
            "peer-board",
            f"the board of {name} did not say whether its agterm runs Live sessions: {why}",
            f"the owner checks that the board of {name} answers, with lem serve peers, "
            "and runs this Lem release",
        )
    return None if live else agterm_said.not_live(name)


def peer_row(look: Look, name: str, port: int) -> Row:
    """The row of one joined machine."""
    refused = far_refusal(look, name) or live_refusal(look, name, port)
    if refused is not None:
        return Row(
            name=f"joined machine {name}",
            need=OPTIONAL,
            found=False,
            detail=refused.why,
            used_for=USED_FOR,
            without_it=refused.fix,
        )
    return Row(
        name=f"joined machine {name}",
        need=OPTIONAL,
        found=True,
        detail=(
            f"ssh {name} reaches it and agtermctl there lists its sessions; its agterm "
            "runs Live sessions"
        ),
        used_for=USED_FOR,
        without_it=None,
    )
