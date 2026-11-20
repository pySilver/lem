---
worth: later
where: skills/lem/assets/board.html:waitsOf
added: 2026-11-20
---
# The tab "Waits for you" hides a held task's step while one of its choices waits

A task held with "the reviewer's pane waits for the owner's trust of the folder" and with choice 1 open in decisions.jsonl shows only the row "Answer choice 1". The held row needs !t.asks.length, so the step has no row until the owner answers the choice.

Seen outside the change by review round 1 of task waiting-counts-a-choice-once (2026-11-20); the base commit has it.
