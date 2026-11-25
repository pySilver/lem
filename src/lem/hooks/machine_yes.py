"""The machine's yes to the correction queue, read from the tables of Lem's home `machine.toml`
as `main`'s `state.machine_table` reads them: a file that holds a table Lem does not know, or a
key `[corrections]` does not take, is refused there, and a refused file is a no."""

# The tables of the machine's file (`state.MACHINE_KEYS` on `main`).
MACHINE_TABLES = frozenset(("load", "serve", "peers", "handoff", "corrections"))


def said_yes(machine: dict[str, object]) -> bool:
    """Whether the machine's tables say yes: every table one Lem knows on this machine, and
    `[corrections]` holds `collect = true` and no other key (`state.machine_table` on `main`
    refuses a file that holds anything else, and a refused file is a no)."""
    if not set(machine) <= MACHINE_TABLES:
        return False
    table = machine.get("corrections")
    if not isinstance(table, dict) or set(table) != {"collect"}:
        return False
    return table["collect"] is True
