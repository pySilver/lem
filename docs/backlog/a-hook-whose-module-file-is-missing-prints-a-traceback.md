---
worth: yes
where: src/lem/python.py:run
added: 2026-11-24
---
# A hook whose module file is missing prints a traceback

`hooks/hooks.json` starts each hook as `python3 src/lem/python.py NAME`, and `run()` opens
`src/lem/NAME.py` with no check. Run at c674b18d with `python.py` alone in a copy of the folder:
`echo '{}' | python3 -B src/lem/python.py corrections hook` printed a `FileNotFoundError` traceback
and exited 1; with `corrections.py` there and `state.py` gone, an `ImportError` traceback from its
import at the top. The module's own text says that a hook that fails must not fail the session and
that with no Python it prints nothing, and `bin/lem` says in one line that the folder is not whole
(967aa1d3). The hook should end as it does with no Python: nothing printed, exit 0.

Seen in the review of the package move, 2026-11-24; the base before the move had it too.
