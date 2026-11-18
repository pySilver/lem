*Illustration. No run made this file. The task, its records, its names and its numbers are invented, to show every case.*

# What was built: a CSV export of the orders

> [!CAUTION]
> **Three things wait for you.**
>
> 1. **A step that cannot be reversed.** Lem holds the October file for `accounting@example.com`. An email cannot be taken back. Tell Lem "send it" or "do not send".
> 2. **You did not approve the criteria.** The task ran alone after the interview, so Lem approved them. Read the four criteria below.
> 3. **One decision has no agreement**: the time zone of the dates. Read decision 2 in the decisions file.
>
> The pull request is not green because of 2 and 3. Merge it only when you agree with both.

Pull request [#12](https://github.com/example/shop/pull/12), branch `feat/csv-export-of-the-orders`. The task ran alone from the end of the interview.

## What you asked

> add a CSV export of the orders, so that accounting gets a file each month. send them the October file when it works

In the interview you also said:

- "one month at a time is enough"
- "accounting opens it in Excel"

## What was built

A new command writes the orders of one month as CSV:

```bash
python3 -m shop.export orders --month 2026-10 > orders-2026-10.csv
```

The code is a new module, `shop/export.py`, with its tests in `tests/test_export.py`. Nothing else changed.

The criteria that the change holds. Lem approved them, not you. Each one has a test that fails on `main` and passes on the branch.

1. The command writes a header row and then one row for each order of the month.
2. The columns are: order number, date, status, customer, total, currency.
3. A total is text with two decimal places, as `1234.50`, never `1234.5`.
4. A month with no orders gives the header row only, and the command exits with 0.

## Why we want it

Accounting gets the orders of each month as one file that Excel opens. Nobody copies rows from the order page by hand.

## What did not get built

- No schedule. The command does not run each month by itself. You run it, or a later task adds a job.
- No export of customers or of products.
- The October file is not sent. It waits for you (item 1 at the top).
- An agent saw a defect outside this change and filed it: `docs/backlog/order-page-shows-totals-as-floats.md`. The order page shows `1234.5`.

## How to see it work

In the task's worktree:

```bash
python3 -m shop.export orders --month 2026-10 | head -3
```

It prints the header row and the first two orders of October 2026.
