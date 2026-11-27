"""The machine's list of workspaces, from each command that makes a task wait for this machine's
board server: the open of a task and of its session, the pull request, and the merge agent's
read. The server's duties (its look at GitHub, the merge, the wakes, the queue and the guard) run
only for a workspace on the list (`board/workspaces.py`), and a task whose workspace the list
lacks waits with nothing to tell the owner so.

The command puts its main checkout there once its own work is done, so that its refusal (a state
folder of Lem 0.3, a wrong slug), which it raises, writes nothing into Lem's home folder; a
checkout on the list already is no change, and a list that cannot be written is a refusal.
"""

import os

from lem.board import workspaces
from lem.cli import place
from lem.kernel import folders


def listed[Made](made: Made) -> Made:
    """`made`, the command's outcome, once the workspace of the command's folder is on the
    machine's list."""
    workspaces.noted(folders.home_for_writing(os.environ), place.folder())
    return made
