---
worth: later
where: src/lem/land.py:start_locked
added: 2026-11-23
---
# A new landing of a ready task writes its review over the review files of the landing before

The first landing of the task `seat-defaults-and-fallback` wrote its review as
`reviews/review-1.md` and `reviews/review-1.json` in the task directory at 16:06 on 2026-11-23,
beside the review tool's own `reviews/revmux-01-initial.json` and `.log`. The task came back to
`ready`, and `lem land start` ran again. `start_locked` removes the kept record of a `ready` task
(`landing.json`) and keeps only `pr`, `pushed`, `taken` and a done polish pass, so the record's
`reads` are gone. The next review counts its attempt from those reads, so it is attempt 1 again,
and `prompts/review.md` writes `reviews/review-1.md`, `reviews/review-1.json` and
`reviews/revmux-01-initial.*` over the files of the first landing. The session of the task moved
the first landing's files to `reviews/landing-1/` by hand at 19:30, before the new review wrote
its own. With no such move, the first review's findings and its record are lost, and the merge
agent and the owner can read only the newest landing's review.
