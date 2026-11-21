---
worth: later
where: skills/lem/scripts/project.py:events_named
added: 2026-11-20
---
# An event whose words hold U+2028 breaks the repository's event log

append_event writes with ensure_ascii=False and events_named splits each line with str.splitlines(), which breaks at U+2028, U+2029 and U+0085. At 65df09a in a throwaway repository, `lem project log demo gate.end "say=a<U+2028>b" result=passed` writes one line, and `events_named(root, "gate.end")` then raises `.lem/state/events.jsonl:1 does not read as JSON (Unterminated string ...)` (2026-11-21). A reader that asks for another event is not hit, since events_named skips a line that does not name the event.

The case of 2026-11-20 was `lem project owner away --words "away<U+2028>now"`, then `lem project waiting`, which exited 1 with the same error. The owner's status is in the machine's mark now, `owner.jsonl`, whose reader splits at "\n" alone; the repository's event log keeps the defect.

Seen outside the change by review round 1 of task away-for-the-whole-machine (2026-11-20); the base commit has it.
