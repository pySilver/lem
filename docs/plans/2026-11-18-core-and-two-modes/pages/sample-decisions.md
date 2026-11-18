*Illustration. No run made this file. The task, its records, its names and its numbers are invented, to show every case.*

# Decisions: a CSV export of the orders

> [!CAUTION]
> **Three things wait for you.**
>
> 1. **A step that cannot be reversed.** Lem holds the October file for `accounting@example.com`. An email cannot be taken back. Tell Lem "send it" or "do not send" (decision 1).
> 2. **You did not approve the criteria.** The task ran alone after the interview, so Lem approved them. Read the four criteria in the file of what was built.
> 3. **One decision has no agreement**: the time zone of the dates. Read decision 2.
>
> The pull request is not green because of 2 and 3. Merge it only when you agree with both.

Pull request [#12](https://github.com/example/shop/pull/12). Seven decisions. One waits for you. The ones that you most likely want to change come first.

| # | The question | What was taken | Who decided |
| --- | --- | --- | --- |
| 1 | Send the October file to accounting now? | nothing yet | **waits for you** |
| 2 | Which time zone do the dates use? | the shop's time zone | **nobody agreed**: the task's agent's pick stands |
| 3 | What does a month with no orders give? | the header row only | two expert models |
| 4 | Which form does a date have? | `2026-10-03` | a for-and-against test |
| 5 | Does the file show cancelled orders? | yes, with a status column | the personas, 3 of 3 |
| 6 | Which form does a total have? | `1234.50` | your ruling |
| 7 | Where does the code go? | a new module, `shop/export.py` | the task's agent |

## 1. Send the October file to accounting now?

**Waits for you.** No agent sends it, in either mode: a later "no" cannot take back an email.

- **The options:**
  - send the file now, from the branch;
  - send the file after you merge (recommended);
  - do not send it.
- **Why the recommendation:** after the merge, the file comes from the code on `main`, and not from a branch that can still change.
- **What you do:** tell Lem "send it", "send it after the merge" or "do not send".

## 2. Which time zone do the dates use?

**Not green. Check this one.** Nobody agreed, so the pick of the task's agent stands.

- **Taken:** the shop's time zone, Europe/Warsaw, as the order page shows the dates.
- **The other option:** UTC.
- **Why:** an order at 00:30 on 1 Nov in Warsaw is on 31 Oct in UTC. With UTC, the October file has orders that the order page shows in November. Accounting compares the file with the order page.
- **How it went:**
  - the personas: 2 for UTC, 1 for the shop's time zone;
  - a for-and-against test on UTC: no clear result;
  - two expert models: Fable for UTC, GPT-6 Astra for the shop's time zone.
- **To change it:** say "use UTC in the export". An agent changes the date column and its test.

## 3. What does a month with no orders give?

- **Taken:** the header row only, and the command exits with 0.
- **The other options:**
  - an error message, and the command exits with 1;
  - no output at all.
- **Who decided:** two expert models, Fable and GPT-6 Astra. Both picked this option.
- **Why:** a month with no orders is a correct result, not an error. A run that fails still exits with a number that is not 0, so a script of accounting can tell the two apart.
- **How it went:** the personas split, 2 for the header row and 1 for an error. The for-and-against test gave no clear result.
- **To change it:** say "a month with no orders is an error". An agent changes criterion 4 and its test.

## 4. Which form does a date have in the file?

- **Taken:** `2026-10-03` (ISO 8601).
- **The other option:** the form of the order page, `3 Oct 2026`.
- **Who decided:** a for-and-against test. One agent argued for `2026-10-03`, and one agent argued against it.
- **Why:** Excel reads `2026-10-03` as a date and sorts it correctly. The case against it was that accounting reads `3 Oct 2026` on the order page. That case did not hold: Excel shows a date in its own form in any case.
- **How it went:** the personas split, 2 for `2026-10-03` and 1 for `3 Oct 2026`.
- **To change it:** say "dates as on the order page". An agent changes the date column and its test.

## 5. Does the file show cancelled orders?

- **Taken:** yes. The file shows every order of the month, with a status column.
- **The other option:** show paid orders only.
- **Who decided:** the personas, 3 of 3.
- **Why:** accounting must see a cancelled order next to its refund. A file of paid orders only does not show why the total of the month is lower.
- **To change it:** say "paid orders only". An agent changes criterion 1 and its test.

## 6. Which form does a total have?

- **Taken:** text with two decimal places, as `1234.50`.
- **The other options:**
  - a number in cents, as `123450`;
  - a plain number, as `1234.5`.
- **Who decided:** your ruling of 2026-10-02 in `docs/rulings/money.md`: "Money leaves the system as text with two decimal places, never as a float."
- **Why:** the ruling answers the question, so nobody else was asked.
- **To change it:** change the ruling first. This task follows it.

## 7. Where does the code go?

- **Taken:** a new module, `shop/export.py`.
- **The other option:** a new function in `shop/orders.py`.
- **Who decided:** the task's agent.
- **Why:** `shop/orders.py` holds the code of the order page. The export has its own tests and no code of the page.
- **To change it:** say where. The change moves one module and does not change the behavior.
