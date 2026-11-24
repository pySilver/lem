---
worth: yes
where: src/lem/peers.py:Peers.table
added: 2026-11-24
---
# A join of a peer, with one bad line in the peers table, drops the good neighbors

`Peers.table` gives `{}` when `machine_table("peers")` raises a `StateError`, and `join` then writes
`{**table, name: port}`. With `beta = 4537` beside `broken = "bad"` in `[peers]` of `machine.toml`,
a join of gamma leaves the table as `{'gamma': 4537}`: beta is gone, with no word. The join should
refuse a table it cannot read, with the line that is wrong and the fix, and the read and the write
of one change should be under `state.machine_lock` together.

Seen by the outside read of 2026-11-24 (`docs/plans/2026-11-24-lem-as-an-app/astra-read.md`), which
ran the settings writer on a scratch file with a stand-in for the network reply.
