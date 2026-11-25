"""The afternoon's prose, word for word as today's `tests/board-showcase.py` writes it: the
breakers' documents and the handoff, the merge agent's two reviews, the chart of the refund
line's outcome, and the polish pass's backlog item. An agent writes these files; no record
cites them, and the board reads each as it is (the design's part 3, "Prose and artifacts")."""

GIFT_BREAKER = """# The gift note has no place in the export that keeps criterion 1 and the export's readers

> [!IMPORTANT]
> **The build of {slug} stopped here, and only this task.** No option keeps criterion 1 as you approved it: the gift note "in the last column of its row" takes the place where two readers of the export find the total.
>
> Help with the choice below, `/lem park {slug}`, or `/lem drop {slug}`. `/lem resume {slug}` brings it back after either.

**You asked for the gift note in the CSV export, with every reader of the export working as before. Criterion 1 puts the note in the last column, and the last column is where the accounting import and the packing slip read the total.**

## Today and after

**Today**, as the build left it:

1. Order 1042 has the gift note "for Ania" and a total of 54.90 EUR.
2. The export writes the note into the last column, as criterion 1 says.
3. The accounting import reads "for Ania" as the total of order 1042, and refuses the whole file.

**After**, with the recommendation:

1. Order 1042 has the gift note "for Ania" and a total of 54.90 EUR.
2. The export writes the note into a column of its own, `gift_note`, just before `total`.
3. The accounting import reads 54.90 EUR, and the gift note is in its own cell.

## The case that broke

1. `export/orders_csv.py:41` writes the columns of a row in a fixed order, and `total` is the last.
2. Task 2 of the plan added `gift_note` after it, so that criterion 1 holds: `tests/test_export.py::test_gift_note_last` passes.
3. `accounting/import.py:18` takes `row[-1]` as the total; `make test` fails in `test_import_totals` with `could not convert 'for Ania' to a number`.
4. `warehouse/slip.py:27` prints `row[-1]` as the amount on the packing slip: the slip of order 1042 would say "for Ania" where the amount stands.

```mermaid
flowchart TD
  A["Order 1042: for Ania, 54.90"] --> B{"Where is the note?"}
  B -->|"last, as in criterion 1"| C["Accounting: the total is for Ania"]
  B -->|"A: own column"| D["Every reader finds 54.90"]
  B -->|"B: in the notes"| E["The slip prints it to the packer"]
```

## The root cause

Criterion 1 names a place, "the last column", where it means a column that holds only the gift note. Two readers of the export take the total by its place, and the scout listed neither: they live outside `export/`, and nothing in the export's tests reads them.

The same cause reaches every new column of the export: whatever goes last moves the total. It is a fact only the build could find, not a plan that missed a step.

## The options

| | A: own column | B: notes column |
| --- | --- | --- |
| The row | `gift_note` before `total` | "Leave at door. Gift: for Ania" |
| Criterion 1 | changes: `gift_note`, not last | changes: the notes |
| The readers | as today | the slip prints the note |
| Undo | yes: nothing is sent | yes: nothing is sent |

- **A: a column of its own** leads to one more column before the total: the readers go on as today, and the build goes on with task 3 of 3.
- **B: appended to the notes column** leads to no new column, and the warehouse prints the gift note as a packing instruction on every slip.

## The recommendation

> [!TIP]
> **A: a column of its own, before the total.** It keeps what criterion 1 is for, a cell with only the gift note, and every reader of the export. Only the place the criterion names changes, and that place is yours to change.

What the ladder said:

- The gate: no ruling on the order of the export's columns.
- The personas: both model families picked A.
- The dialectic: A held; the case against it found no reader that takes the gift note by its header.
- The experts: Fable and Astra both picked A.

No option keeps criterion 1 as written, so the build stops here, and the change of the criterion is yours.

## The assumptions

- The accounting import and the packing slip are the only readers of the export: a search for `orders.csv` in the repository found these two.
- Nobody outside the repository reads the file by the place of its columns.
- A gift note holds no line break that the CSV writer leaves unquoted.
- A reader outside the repository that takes the last column would make B the better option.
"""

GIFT_HANDOFF = """# Handoff

- Settled: the export writes the gift note (tasks 1 and 2 of 3, commits on the branch); an empty note is an empty cell (criterion 2).
- Open: the column's place, breaker 1.
- Next: on A, move `gift_note` before `total` in `export/orders_csv.py:41`, change `test_gift_note_last`, then task 3 of 3.
- Tried and failed: the note last, as criterion 1 says (`make test`: `test_import_totals`).
"""

FEE_BREAKER = """# The fee notice goes to 212 merchants, and a mail cannot be called back

> [!IMPORTANT]
> **The build of {slug} stopped here, and only this task.** The next step sends a mail to 212 merchants, which a later "no" cannot undo.
>
> Help with the choice below, `/lem park {slug}`, or `/lem drop {slug}`. `/lem resume {slug}` brings it back after either.

**You asked to tell each merchant about the new card fee. The mail is ready; the date of the fee in it is the one step left to confirm.**

## Today and after

**Today**, as the build left it:

1. 212 merchants are on the list, and the mail says the fee starts on 1 December.
2. `make send-fee-notice` sends it.
3. Each merchant reads a date that nobody confirmed.

**After**, with the recommendation:

1. The date is confirmed, or changed in the mail.
2. `make send-fee-notice` sends it once.
3. Each merchant reads the date that holds.

## The case that broke

1. `billing/fees.py:12` has the fee from 1 December, from the plan.
2. `mail/fee_notice.md` says the same date to every merchant.
3. The send is the next step, and a mail that went out stays out.

```mermaid
flowchart TD
  A["The fee notice, ready for 212 merchants"] --> B{"Is 1 December confirmed?"}
  B -->|"yes"| C["Send it once: every merchant reads the right date"]
  B -->|"not yet"| D["Wait: nothing is sent"]
```

## The root cause

The plan took the date from the ticket, and the ticket took it from a draft of the association's letter.

## The options

| | A: send now | B: wait for the date |
| --- | --- | --- |
| What a person sees | the mail today | the mail after the confirmation |
| Can a later no undo it | no: a mail cannot be called back | yes: nothing is sent |

- **A: send now** leads to 212 mails with a date nobody confirmed.
- **B: wait for the date** leads to a task that waits, with nothing sent.

## The recommendation

> [!TIP]
> **B: wait for the date.** A wrong date in 212 mails costs a second mail and the merchants' trust.

What the ladder said: a step that cannot be undone is never the ladder's to take.

## The assumptions

- The association confirms the date this week.
"""

TYPO_REVIEW = """Verdict: merge. The footer says "Terms and conditions", as the criterion asks, and nothing else changed.

**What was built, and why.** You asked to fix the typo in the footer. One word of the template changed.

**The results.** The checks passed: 212 tests and the lint. One read found no must-fix.

**Decisions taken without you.** None.

**Time.** 18 minutes from the request to the pull request.
"""

MERGE_REVIEW = """Verdict: call. The change does what both criteria say; it is not green for two choices taken without you, and I would keep both.

**What was built, and why.** You asked: "Show a refund as a line of its own on the receipt."

Today:

1. Order 1042 is 100.00 EUR, and a refund of 30.00 EUR comes in.
2. The receipt shows 70.00 EUR, and no line says why.

After:

1. Order 1042 is 100.00 EUR, and a refund of 30.00 EUR comes in.
2. The receipt shows `Refund -30.00` under the items, and `Total 70.00` under it.
3. A refund of 120.00 EUR shows `Total 0.00` and a credit note for 20.00 EUR.

**The results.** `make test` and `make lint` passed. The tests of both criteria pass on the branch and fail on the base. Round 2 of the review left no must-fix.

**Decided without you.**

- Where the line goes, by the dialectic: under the items, before the total. I agree: the receipt prints its total last, so the refund reads as a change of the total and not as an item.
- The criteria were approved at night, while the task ran without you. They say what your words ask, and nothing more.

**The time.** 2 h 42 min, against about 2 h for a change of this size in this repository.

**What I found.** Nothing wrong. One assertion left `tests/test_receipt.py`: it read the total from a fixed row, which the refund line moves, and `test_total_after_refund` now reads the total by its label.
"""

DEMO_CHART = """flowchart TD
  A["A refund of 30 EUR comes in"] --> B{"Is it larger than the total?"}
  B -->|"no"| C["The receipt shows a line: Refund -30.00"]
  B -->|"yes"| D["The receipt shows 0.00 and a credit note"]
  C --> E["The new total stands under it"]"""

FOOTER_ITEM = """---
worth: yes
where: invoice/footer.py:footer
added: {today}
---

# The invoice footer wraps on A5

Seen in the polish pass of the order date: the footer's last line wraps when the invoice prints on A5.
"""
