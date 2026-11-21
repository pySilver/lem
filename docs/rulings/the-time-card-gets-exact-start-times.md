---
ruled: 2026-11-17
area: The board and the pages for him
---

# The time card gets exact start times

Decisions the owner took on 2026-11-14. Each is reopened only by asking him. A quote is his words.

**The time card gets exact start times**: asked in his Inbox on 2026-11-17 whether the board's
time card should get exact start times now, he picked "Build it now: each stage logs its start,
and the card becomes exact". The form is the maintaining session's: one `NAME.start` event for
each stage that logged only its end, with a fixed form that `project.py log` checks (`STARTS`),
and the event that already ended the stage stays its end. `land.py` logs the starts of the
polish pass, the checks and a review that is due; the stage texts give the line for the
interview, the scout (with `scout`, its end, which had no event), the personas' read, an
investigation and each builder's job. `SKILL.md` lists them with their ends.
