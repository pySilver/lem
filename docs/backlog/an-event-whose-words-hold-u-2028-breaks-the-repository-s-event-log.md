---
worth: later
where: skills/lem/scripts/project.py:events_named
added: 2026-11-20
---
# An event whose words hold U+2028 breaks the repository's event log

On the base code in a throwaway repository, `lem project owner away --words "away<U+2028>now"` and then `lem project waiting` exits 1 with `.lem/state/events.jsonl:1 does not read as JSON (Unterminated string ...)`: append_event writes with ensure_ascii=False and events_named splits each line with str.splitlines(), which breaks at U+2028, U+2029 and U+0085.

Seen outside the change by review round 1 of task away-for-the-whole-machine (2026-11-20); the base commit has it.
