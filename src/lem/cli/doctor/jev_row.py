"""The row of the key of the Jev model, which the correction queue needs where the machine
turns it on: JEV_API_KEY, the one name Lem reads for it. The key is never printed.
"""

from typing import TYPE_CHECKING

from lem.cli.doctor.checkouts import main_checkout
from lem.cli.doctor.machine_rows import machine_file
from lem.cli.doctor.row import OPTIONAL, REQUIRED, Row
from lem.hooks.corrections import machine_says_yes
from lem.settings import places

if TYPE_CHECKING:
    from lem.cli.doctor.look import Look

JEV_USED_FOR = (
    "the Jev decision model, which the correction queue, a card's framing check and the "
    "landing's read of each finding called under the bar ask"
)
JEV_MISSING = "JEV_API_KEY is not set, and it is the one name Lem reads for the key"
# Where the key and the address of the Jev model come from.
JEV_WHERE = (
    "JEV_API_KEY in the environment the agent starts with, the key of the Jev model's "
    "provider; the provider is OpenRouter unless JEV_API_URL names another (then JEV_MODEL "
    "names its model)"
)


def collects(look: Look) -> bool:
    """Whether the correction queue is on here, by the hook's own reading: `machine.toml`
    says yes, and the repository of the call uses Lem. Another file that does not read
    changes nothing of it, as it changes nothing for the hook."""
    if not machine_says_yes(look.environ):
        return False
    checkout = main_checkout(look.folder)
    return checkout is not None and (checkout / places.TEAM).is_file()


def jev_row(look: Look) -> Row:
    """The key of the Jev model: JEV_API_KEY, the one name Lem reads for it. Required where
    the correction queue is on: without it the hook writes a failure for each message to a
    file nobody reads, and the queue stays empty. The key is never printed."""
    given = bool(look.environ.get("JEV_API_KEY"))
    url = look.environ.get("JEV_API_URL", "").strip() or "OpenRouter"
    detail = f"JEV_API_KEY, to {url}" if given else JEV_MISSING
    if collects(look):
        return Row(
            name="Jev key",
            need=REQUIRED,
            found=given,
            detail=f"{detail}; the correction queue is on here (collect = true under "
            f"[corrections] in {machine_file(look)})",
            used_for=JEV_USED_FOR,
            without_it=(
                "the correction hook writes each message of the owner to the queue's log as "
                "a failure, the queue stays empty, and the retro reads nothing. Put "
                f"{JEV_WHERE}, or turn the queue off for every repository on this machine "
                "with `lem settings set corrections.collect no --machine`"
            ),
        )
    return Row(
        name="Jev key",
        need=OPTIONAL,
        found=given,
        detail=detail,
        used_for=JEV_USED_FOR,
        without_it=(
            "a card's framing check gets no answer, a pull request says \"Jev: not asked (no "
            'key)" on the line of each finding called under the bar, and the correction '
            f"queue, which is off here, would stay empty if it were on; put {JEV_WHERE}"
        ),
    )
