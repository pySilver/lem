---
worth: later
where: skills/lem/scripts/project.py:outcome_of
added: 2026-11-22
---
# The outcome quote drops the first line of a bold paragraph

`outcome_of` skips every line under `## Outcome` that opens with `**`, so that a label such as
`**Today:**` is no sentence to quote. A paragraph that opens with a bold sentence and wraps loses
its first line that way, and the quote starts on its second line, mid-sentence. Run on the code:
`outcome_of("## Outcome\n\n**The reviewer reads everything and writes one file.** A\nreal talk in a
throwaway repository shows that, with three receipts.\n")` returns `'real talk in a throwaway
repository shows that, with three receipts'`. The first `say` of the task
`plan-reviewer-read-only` quoted "real talk in a throwaway repository does not show that, ..." in
the same way (2026-11-21T23:25Z). A fix tells a bold label of a few words from a bold opening
sentence, takes the `**` marks out of the quote, and needs a case beside `test_the_words_it_quotes`
in `tests/unit/test_task.py`.
