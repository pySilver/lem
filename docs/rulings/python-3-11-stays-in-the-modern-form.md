---
ruled: 2026-11-20
area: What Lem needs on the machine
---

# Python 3.11 stays, in the modern form.

His rulings of 2026-11-20 and 2026-11-21, while his interview redesigned how a task runs and the
board became a served app; a quote is his words. His answers Q7 to Q11 and notes P1 to P9 are in
`.lem/state/tasks/one-lem-parallel-landings/`, which git ignores. Where a note replaces an earlier
ruling, this is the ruling now.

What agents write, and the Python Lem needs:

**Python 3.11 stays, in the modern form.** Of a floor of 3.9: "Test it but if it will fail hard,
we will use modern version. Its opionated software", and "`from __future__ import annotations`
this considered harmful in python." So no script has that import; `lem_python.py` finds a newer
Python for `bin/lem` and the hooks. Of the finder: "also `uv` can be tried". The form is the
session's: `uv` is asked last, only for a Python it has, and the fix names `uv python install`
beside `brew install python`.
