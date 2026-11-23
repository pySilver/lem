---
worth: later
where: skills/lem/scripts/lem_state.py:write_machine
added: 2026-11-23
---
# A write of machine.toml drops the comments the owner typed in it

`~/.config/lem/machine.toml` holds the owner's own line `# the Mac in the office: keep the gate low` above `[load]` with `start = 30`. He runs `lem project load --start 12`. `write_machine("load", {"start": 12})` writes the file whole from its tables: the file then holds Lem's header comment, `[load]`, Lem's comment `` # `lem project load --start N` writes it `` and `start = 12`, and his comment is gone with no message. Every writer of the file takes this path: `lem project load`, `lem project handoff`, `lem serve --port` and `--tailscale`, `lem serve --join` and `--leave`, and `lem corrections collect`.

The settings files that `lem project set` writes keep every other line and comment (`lem_state.write_edits`, criterion 6 of seat-defaults-and-fallback); `machine.toml` does not. The task seat-defaults-and-fallback first moved `write_machine` onto that line edit (its decision 6), and the owner's decision 41 took the seats out of `machine.toml` and kept `write_machine` as main has it, so the loss stays.

Seen by the polish pass of seat-defaults-and-fallback (2026-11-23), from the scout's report of that task; the base commit `b49029ac` has it.
