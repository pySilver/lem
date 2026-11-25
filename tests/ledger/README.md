# The behavior ledger

- `rows.tsv` lists the old Lem behavior and the extra rows. `ledger.py` makes it
  from commit `bf6d2836` and `extra.tsv`.
- `extra.tsv` holds the landing paths and seams from the rebuild design.
- `owners.py` assigns one step to each row in `owners.tsv`. It reads
  `owners-judged.tsv` for the choices that the design leaves open.
- `fates/STEP.tsv` records what one step does with its rows. Use the columns
  `id`, `fate`, `proof` and `note`. Use `kept`, `changed` or `dropped` for
  the fate. Give the exact test or trial check ID as proof for a kept or
  changed row. Give proof for a drop when a test can show it is safe. A
  change or drop needs a reason. Start a dropped ruling's note with
  `for the owner:`.
- `check.py` checks the fates against test results and ticked trial checks.

Run these commands from the repository root. Replace `STEP` with the step ID
and `RESULTS` with the path to the test results file.

1. List your rows.

   ```sh
   awk -F '\t' -v step=STEP '$2 == step {print $1}' tests/ledger/owners.tsv
   ```

2. Check your step.

   ```sh
   python3.14 -I -B tests/ledger/check.py --step STEP --results RESULTS
   ```

3. Add a seam to `extra.tsv` and assign it in `owners.py`. Regenerate both tables.

   ```sh
   python3.14 -I -B tests/ledger/ledger.py && python3.14 -I -B tests/ledger/owners.py
   ```
