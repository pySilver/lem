"""The `Git` port's first adapter: real `git`, one process for each call (the design's part 4).

The port's four parts are four classes of seven methods or fewer (`git_cli_facts.py`,
`git_cli_acts.py`), joined here as the port joins them; how git runs, a stopped rebase and the
names of files are modules of their own. The step `land-base` built it; it passes the port's
whole contract on real git (`tests/contract/test_git.py`).
"""

from typing import TYPE_CHECKING

from lem.adapters.git_cli_acts import Branches, Rewrite
from lem.adapters.git_cli_facts import History, Places

if TYPE_CHECKING:
    from lem.ports.place import Place


class Facts(History, Places):
    """Every fact."""


class Acts(Rewrite, Branches):
    """Every act."""


class GitCli(Facts, Acts):
    """The whole port."""


def bind(place: Place) -> GitCli:
    """The adapter for `place`: git with the environment the command started with."""
    return GitCli(environ=place.environ)
