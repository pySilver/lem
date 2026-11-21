---
worth: later
where: skills/lem/scripts/project.py:opening_line_facts
added: 2026-11-21
---
# The first line quotes the ask with its /lem

When `task.md` has no outcome, no criterion and no backlog item stands in, `opening_line_facts`
quotes the first sentence of `ask.txt` as typed. `ask.txt` holds the request with the command that
carried it, so a request typed as `/lem After the gift note: the export keeps the notes in their
order` gives the first line `feat: "/lem After the gift note: ..."`, read in the code by the lead of
`owner-order-open-defects` (2026-11-21). The quote is meant to be his words, and `/lem` is not.
A fix strips a leading `/lem ` from the quote alone; it needs a case in `tests/unit/test_task.py`.
