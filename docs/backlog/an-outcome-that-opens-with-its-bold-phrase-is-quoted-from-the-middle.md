---
worth: later
where: skills/lem/scripts/project.py:outcome_of
added: 2026-11-22
---
# An outcome that opens with its bold phrase is quoted from the middle

`outcome_of` skips a line under `## Outcome` that starts with `**`, to skip a label such as
`**Today:**`. `prompts/writing.md` asks the outcome to open with its point in bold, so the first
line of the paragraph is skipped and the quote starts on its second line. With the outcome
"**The board lists an interview only while a question of his is open**, and the task's card says"
on one line and "who acts in the other moments. See it on the board." on the next,
`project.outcome_of` returns `'who acts in the other moments'` (run at `823c147`). The task
`interview-end-tells-board` got a first line of the same kind: `fix: "list the task as his.** A row
says ..."`. A fix tells a label of a few words that ends in `:**` from a sentence that opens in
bold; its case goes beside the others of `outcome_of` in `tests/unit/test_task.py`.
