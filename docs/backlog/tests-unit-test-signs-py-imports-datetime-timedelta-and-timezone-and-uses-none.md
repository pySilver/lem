---
worth: later
where: tests/unit/test_signs.py
added: 2026-11-22
---
# tests/unit/test_signs.py imports datetime, timedelta and timezone, and uses none

The line `from datetime import datetime, timedelta, timezone` is the one line of the file that names any of the three (`grep -c "datetime\|timedelta\|timezone" tests/unit/test_signs.py` gives 1). The file holds the criteria of task dead-tasks-woken-or-shown, so its polish pass could not change it. The fix is to remove the line.

Seen by the builders of task dead-tasks-woken-or-shown (2026-11-22).
