# The behavior ledger

- `rows.tsv` lists the old Lem behavior and the extra rows. `ledger.py` makes it
  from commit `bf6d2836` and `extra.tsv`.
- `extra.tsv` holds the landing paths (`landing.md` E) and the seams (part 8).
- `owners.py` gives one step to each row in `owners.tsv`. It reads
  `owners-judged.tsv` for the rows that the design leaves open (a row with no
  `from`). Then it applies each `moves/STEP.tsv`.
- `moves/STEP.tsv` gives a row that the rules give to the step `STEP` to the step
  that builds it, in the columns `id`, `to` and `why`. The receiving step proves
  the row, or gives it on in its own moves file. `owners.py` writes each move
  into `owners-judged.tsv`, with the giving step in `from`.
- `fates/STEP.tsv` records what one step does with its rows, in the columns
  `id`, `fate` (`kept`, `changed` or `dropped`), `proof` and `note`. Every fate names its proof: the exact test name of a result line,
  or a trial check such as `S1`, ticked in its own trial file. A changed or
  dropped row gives the reason in `note`. A dropped ruling's note starts with
  `for the owner:`.
- `check.py` checks the fates against a results file and the trial files. A
  results file holds the `collected N`, `ok`, `FAIL` and `SKIP` lines of whole
  runs. It also compares `rows.tsv` and `owners.tsv` with what the scripts make.
- `test_check.py` tests `check.py` and holds the ledger to the design.

Run these commands from the repository root. `STEP` is your step ID, and
`RESULTS` is your results file.

1. List your rows.

   ```sh
   awk -F '\t' -v step=STEP '$2 == step {print $1}' tests/ledger/owners.tsv
   ```

2. Check your step.

   ```sh
   python3.14 -I -B tests/ledger/check.py --step STEP --results RESULTS
   ```

3. Give a row that another step builds to that step (`TO`, with the reason
   `WHY`). Then make `owners.tsv` again, and check your step.

   ```sh
   test -f tests/ledger/moves/STEP.tsv || printf 'id\tto\twhy\n' > tests/ledger/moves/STEP.tsv
   printf '%s\t%s\t%s\n' 'ROW' 'TO' 'WHY' >> tests/ledger/moves/STEP.tsv
   python3.14 -I -B tests/ledger/owners.py
   ```

4. Add a seam to `extra.tsv` and give it an owner in `owners.py`. Then make
   both tables again.

   ```sh
   python3.14 -I -B tests/ledger/ledger.py && python3.14 -I -B tests/ledger/owners.py
   ```
