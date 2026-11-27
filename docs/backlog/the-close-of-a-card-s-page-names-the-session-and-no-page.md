---
worth: no
where: src/lem/app/asking/page_close.py:close
added: 2026-11-27
---
# The close of a card's page names the session and no page

`close` reads the session's overlay tree, and when the tree shows the card's page it runs
`agtermctl session overlay close --target SESSION`, which names the session and no page. The
board server and the session's waiter both close a card's page this way after the board's answer.
When a new question page opens in that session between the read of the tree and the close, the
close shuts the new page in place of the card's. That needs the waiter to return and the
session's agent to ask again within milliseconds of the board's answer; no test measured it.

Decided against: nobody saw it happen, and the close of agterm names no page to aim at.
