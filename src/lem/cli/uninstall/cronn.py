"""The cronn jobs that run Lem, read from cronn's status (read only), for the owner to delete.

Lem keeps no record of the jobs it added, and the jobs file is the developer's own, with his
comments, so Lem never writes it: it names each job that runs the program `lem` or sends
`/lem night` or `/lem retro` to an agent, and the one step that removes it. cronn reads
`crontab.yml` again every 10 s, and its status names no job, only its command and schedule
(the `cronn` skill, read 2026-11-27).
"""

import re
import shlex
from pathlib import PurePath
from typing import TYPE_CHECKING

import httpx
import msgspec

from lem.cli.doctor import tools
from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from lem.cli.doctor.look import Look
    from lem.cli.uninstall.report import Report

STAGE = re.compile(r"/lem (?:night|retro)\b")
ASSIGNMENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*=.*", re.DOTALL)
# The words before a program that leave it the program: `exec lem`, `env lem`.
PREFIXES = frozenset(("exec", "env", "command"))
OPERATORS = frozenset(";&|()")
# How long cronn's status may take, in seconds. A guess, as the doctor's.
WAIT = 3.0


class Job(msgspec.Struct, frozen=True):
    """One job of cronn's status."""

    command: str
    schedule: str = ""


class Status(msgspec.Struct, frozen=True):
    """cronn's status: its jobs."""

    jobs: tuple[Job, ...] = ()


def runs_lem(command: str) -> bool:
    """Whether the job sends a stage of Lem to an agent, or runs `lem` as the program of one
    of its shell commands."""
    if STAGE.search(command):
        return True
    try:
        words = tuple(shlex.shlex(command, posix=True, punctuation_chars=True))
    except ValueError:
        return False
    return "lem" in programs(words)


def programs(words: tuple[str, ...]) -> Iterator[str]:
    """The program of each shell command of `words`: its first word past the `NAME=value`
    words and an `exec` or an `env`."""
    starts = True
    for word in words:
        if set(word) <= OPERATORS:
            starts = True
        elif starts and not ASSIGNMENT.fullmatch(word) and word not in PREFIXES:
            starts = False
            yield PurePath(word).name


def jobs_file(look: Look) -> Path:
    """cronn's jobs file."""
    return tools.cronn_folder(look) / "crontab.yml"


def lem_jobs(look: Look) -> tuple[Job, ...] | None:
    """The jobs of cronn's status that run Lem; None when cronn is not set up here."""
    port = tools.cronn_port(look)
    if port is None:
        if (tools.cronn_folder(look) / "cronn.env").exists():
            raise Refusal(
                "uninstall-cronn",
                "cronn.env of cronn names no CRONN_PORT",
                "the owner sets up cronn again with the cronn skill",
            )
        return None
    try:
        answer = httpx.get(
            f"http://127.0.0.1:{port}/api/v1/status", trust_env=False, timeout=WAIT
        ).raise_for_status()
    except httpx.HTTPError as error:
        raise Refusal(
            "uninstall-cronn",
            f"cronn's status on port {port} did not answer: {error}",
            "the owner starts cronn (the cronn skill, When something is not running)",
        ) from error
    found = msgspec.json.decode(answer.content, type=Status)
    return tuple(job for job in found.jobs if runs_lem(job.command))


def left(jobs: tuple[Job, ...], path: Path | None, report: Report) -> None:
    """Each job that runs Lem, with the one step that removes it, for the owner."""
    for job in jobs:
        report.owner(
            f"delete the cronn job {job.command!r} ({job.schedule}) from {path}; "
            "cronn reads that file again within 10 s"
        )
