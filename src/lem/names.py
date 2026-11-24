"""The names of Lem's commands: each name of `lem NAME`, the module of this package it
runs and what it does in one line. The entry (`lem.__main__`) reads this table for
`lem help` and for the name it is given, before any other module of Lem is imported, so
this file imports nothing.
"""

# name -> (the module of this package; what it does, in one line)
COMMANDS = {
    "project": (
        "project",
        (
            "a repository's settings, a task's state and directory, the event log, the "
            "queue, and what waits for the owner"
        ),
    ),
    "land": (
        "land",
        (
            "the landing, one step at a time: checks, review, pull request, the merge "
            "agent's read, the merge and the cleanup"
        ),
    ),
    "criteria": (
        "criteria",
        "a task's acceptance criteria: approve, show, record, and red on the base",
    ),
    "decisions": (
        "decisions",
        "a task's decisions, each taken without the owner, and its breakers",
    ),
    "board": (
        "board",
        "the board of all tasks, or of one task (--task SLUG)",
    ),
    "serve": (
        "serve",
        (
            "the boards of every repository on this machine, and of the machines "
            "joined with --join, over HTTP, for a browser on another device: "
            "--ensure starts it"
        ),
    ),
    "picker": (
        "picker",
        (
            "agterm's picker over the tasks, which goes to the live session of the one "
            "picked, else opens its board (--list prints the rows)"
        ),
    ),
    "session": (
        "session",
        (
            "a task's own session in agterm: open, next, close, wake, wait, list, its "
            "handoff and the copy of the talk; and close-job, "
            "the end of a scheduled night or retro"
        ),
    ),
    "doctor": (
        "doctor",
        "the machine check: the tools Lem needs and recommends",
    ),
    "corrections": (
        "corrections",
        "the queue of the owner's corrections, for a retro",
    ),
    "experts": (
        "experts",
        "the experts' brief of one question, and the record of their answers",
    ),
    "cast": (
        "cast",
        "the persona panel's cast and profile, and a panel's run folder",
    ),
    "issue": (
        "issues",
        (
            "the GitHub tracker: check, read an issue, and a task's start, land, drop "
            "and answer on its issue"
        ),
    ),
    "ask": (
        "ask",
        "the question page: one question to the owner as a page in agterm",
    ),
    "jev": (
        "jev",
        "the Jev model: choice and yes/no questions, answered as JSON",
    ),
}


def module(name: str) -> str | None:
    """The module that the command NAME runs; None for a name of no command."""
    if name in COMMANDS:
        return COMMANDS[name][0]
    return None


def file_name(module: str) -> str:
    """The name of the script MODULE was before it was a module of this package."""
    return module + ".py"
