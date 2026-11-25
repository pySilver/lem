#!/usr/bin/env python3
"""Check that the rebuild accounts for each ledger row and proves its fate.

The rule is the design's (part 8, the `close` row of part 9, builder-rules.md item 4): every
row has one owner, as owners.py gives it; the owner, and only the owner, gives the row one fate
in `fates/STEP.tsv`; every fate names its proof, a test or a trial check, and that proof passed;
a changed or dropped row says why; a dropped ruling goes on the owner's list.
"""

import argparse
from collections import defaultdict
import csv
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import tarfile
from tempfile import TemporaryDirectory

HERE = Path(__file__).resolve().parent
TRIALS = HERE.parents[1] / "docs/plans/2026-11-25-lem-built-again/trials"
ROW_COLUMNS = ["id", "kind", "source", "what", "fate", "proof", "note"]
OWNER_COLUMNS = ["id", "step"]
FATE_COLUMNS = ["id", "fate", "proof", "note"]
FATES = ("kept", "changed", "dropped")
FOR_OWNER = "for the owner:"
# The lines of the test entry (main's tests/unit/conftest.py and tests/checks.sh): a
# `collected N` for each suite, then `ok   NAME`, `FAIL NAME: why` or `SKIP NAME: why`.
COLLECTED_LINE = re.compile(r"collected[ \t]+(\d+)")
RESULT_LINE = re.compile(r"(ok|FAIL|SKIP)[ \t]+(\S.*)")
# A trial check is proved only by its tick in the file part 9 names for it.
TRIAL_CHECK = re.compile(r"([SAPR])[1-9]\d*")
TRIAL_FILES = {"S": "skeleton.md", "A": "ask.md", "P": "pack.md", "R": "real.md"}
TRIAL_TICK = re.compile(r"- \[[xX]\][ \t]+([A-Z][1-9]\d*)\b.*")


def script(name):
    """A sibling script of this folder as a module: the rules are owners.py's and ledger.py's."""
    spec = importlib.util.spec_from_file_location(f"ledger_{name}", HERE / f"{name}.py")
    if spec is None or spec.loader is None:
        raise OSError(f"{HERE / name}.py cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_tsv(path, columns):
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t", strict=True)
        if reader.fieldnames != columns:
            raise ValueError(f"{path}: use the header {' '.join(columns)}")
        for row in reader:
            if None in row or None in row.values() or not row["id"].strip():
                raise ValueError(f"{path}:{reader.line_num}: fix the TSV row")
            yield row


def group_by_id(table):
    groups = defaultdict(list)
    for row in table:
        groups[row["id"]].append(row)
    return groups


class Results:
    """The result lines of one or more whole runs; a run that does not add up is refused."""

    def __init__(self, path):
        self.path = path
        self.passed = set()
        self.bad = set()
        if path is None:
            return
        collected = 0
        lines = 0
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.rstrip()
            if count := COLLECTED_LINE.fullmatch(line):
                collected += int(count[1])
            elif result := RESULT_LINE.fullmatch(line):
                lines += 1
                (self.passed if result[1] == "ok" else self.bad).add(result[2])
        if not collected:
            raise ValueError(
                f"{path} has no `collected N` line: give the results of a run of the test entry"
            )
        if lines != collected:
            raise ValueError(
                f"{path} has {lines} result lines for {collected} collected cases: give the "
                "results of a whole run"
            )

    def why_not(self, proof):
        """None when the test PROOF passed, else why not."""
        if self.path is None:
            return "no results were given (--results)"
        # A FAIL or SKIP line carries its reason after ": ".
        if any(name == proof or name.startswith(proof + ": ") for name in self.bad):
            return "failed or skipped"
        if proof not in self.passed:
            return "not in the results"
        return None


def trial_ticks(folder):
    ticks = {}
    for letter, name in sorted(TRIAL_FILES.items()):
        path = folder / name
        lines = path.read_text(encoding="utf-8").splitlines() if path.is_file() else []
        ticks[letter] = {
            tick[1] for line in lines if (tick := TRIAL_TICK.fullmatch(line.strip()))
        }
    return ticks


def why_unproved(proof, results, ticks):
    check = TRIAL_CHECK.fullmatch(proof)
    if check is None:
        return results.why_not(proof)
    if proof in ticks[check[1]]:
        return None
    return f"not ticked in trials/{TRIAL_FILES[check[1]]}"


def commit_rows(directory):
    """The rows ledger.py makes now from its commit and DIRECTORY's extra.tsv."""
    ledger = script("ledger")
    with TemporaryDirectory(prefix="lem-ledger-check-") as folder:
        made = ledger.collect_commit(ledger.REV, Path(folder), False)
    ledger.add_extra(made, directory / "extra.tsv")
    return {row.id: (row.kind, row.source, row.what) for row in made.rows.values()}


def ledger_drift(directory, rows):
    """The rows of rows.tsv that ledger.py would not write as they are."""
    made = commit_rows(directory)
    kept = {identity: (entries[0]["kind"], entries[0]["source"], entries[0]["what"])
            for identity, entries in rows.items()}
    return {
        "rows_missing": sorted(made.keys() - kept.keys()),
        "rows_unknown": sorted(kept.keys() - made.keys()),
        "rows_edited": sorted(
            identity for identity in made.keys() & kept.keys() if made[identity] != kept[identity]
        ),
    }


def owner_drift(directory, owners):
    """The rows whose owner in owners.tsv is not the one owners.py's rules give."""
    rules = script("owners")
    rows, _ = rules.index(directory / "rows.tsv", rules.LEDGER_HEADER)
    judged, _ = rules.index(directory / "owners-judged.tsv", rules.JUDGED_HEADER)
    ruled, _ = rules.assign(rows, judged)
    given = {identity: claims[0]["step"] for identity, claims in owners.items() if len(claims) == 1}
    return rules.STEPS, [
        {"id": identity, "owners_tsv": given.get(identity), "rules": ruled.get(identity)}
        for identity in sorted(ruled.keys() | given.keys())
        if given.get(identity) != ruled.get(identity)
    ]


def fate_report(identity, kind, fate, results, ticks):
    """The lists one fate fails, and its entry on the owner's list."""
    failed = defaultdict(list)
    disposition = fate["fate"].strip()
    proof = fate["proof"].strip()
    note = fate["note"].strip()
    if disposition not in FATES:
        failed["invalid_fate"].append({"id": identity, "fate": disposition})
    if not proof:
        failed["no_proof"].append(identity)
    elif why := why_unproved(proof, results, ticks):
        failed["unproved"].append({"id": identity, "proof": proof, "why": why})
    if disposition in {"changed", "dropped"} and not note.removeprefix(FOR_OWNER).strip():
        failed["no_note"].append(identity)
    if disposition == "dropped" and kind == "ruling":
        if note.startswith(FOR_OWNER):
            return failed, {"id": identity, "note": note}
        failed["ruling_dropped_without_owner_note"].append({"id": identity, "note": note})
    return failed, None


LISTS = (
    "rows_missing", "rows_unknown", "rows_edited", "owners_stale", "duplicate_rows",
    "owner_unknown_row", "no_owner", "multiple_owners", "unknown_fate_files",
    "unknown_fate_rows", "wrong_step", "no_fate", "multiple_fates", "invalid_fate",
    "no_proof", "unproved", "no_note", "ruling_dropped_without_owner_note",
)


def written_fates(directory, steps, report):
    """Each fate of fates/, by row, with the step whose file wrote it."""
    fates = defaultdict(list)
    for path in sorted((directory / "fates").glob("*.tsv")):
        if path.stem not in steps:
            report["unknown_fate_files"].append(path.name)
            continue
        for fate in read_tsv(path, FATE_COLUMNS):
            fates[fate["id"]].append((path.stem, fate))
    return fates


def misplaced(fates, rows, owner, step, report):
    """A fate of a row that is not in the ledger, or that a step wrote for another's row."""
    for identity, written in sorted(fates.items()):
        for writer, _fate in written:
            if step is not None and step not in {writer, owner.get(identity)}:
                continue
            if identity not in rows:
                report["unknown_fate_rows"].append({"id": identity, "file": f"{writer}.tsv"})
            elif writer != owner.get(identity):
                report["wrong_step"].append(
                    {"id": identity, "file": f"{writer}.tsv", "owner": owner.get(identity)}
                )


def row_fates(selected, rows, owners, fates, proofs, report):
    """Each selected row's one fate by its owner, checked; the dropped rulings he reads."""
    results, ticks = proofs
    for_owner = []
    for identity in selected:
        claims = owners.get(identity, [])
        if len(claims) != 1:
            report["multiple_owners" if claims else "no_owner"].append(identity)
            continue
        step = claims[0]["step"]
        own = [fate for writer, fate in fates.get(identity, ()) if writer == step]
        if len(own) != 1:
            report["multiple_fates" if own else "no_fate"].append(identity)
            continue
        failed, listed = fate_report(identity, rows[identity][0]["kind"], own[0], results, ticks)
        for name, entries in failed.items():
            report[name].extend(entries)
        if listed:
            for_owner.append({**listed, "step": step})
    return for_owner


def check(directory, results, trials, step, *, commit_read=True):
    rows = group_by_id(read_tsv(directory / "rows.tsv", ROW_COLUMNS))
    owners = group_by_id(read_tsv(directory / "owners.tsv", OWNER_COLUMNS))
    steps, stale = owner_drift(directory, owners)
    if step is not None and step not in steps:
        raise ValueError(f"{step} is not a step of part 9: give --step one of {' '.join(sorted(steps))}")
    owner = {identity: claims[0]["step"] for identity, claims in owners.items() if len(claims) == 1}

    report = defaultdict(list)
    if commit_read:
        report.update(ledger_drift(directory, rows))
    report["owners_stale"] = [
        entry for entry in stale if step is None or step in {entry["owners_tsv"], entry["rules"]}
    ]
    report["duplicate_rows"] = sorted(identity for identity, entries in rows.items() if len(entries) > 1)
    report["owner_unknown_row"] = sorted(owners.keys() - rows.keys())
    fates = written_fates(directory, steps, report)
    misplaced(fates, rows, owner, step, report)
    selected = sorted(
        identity for identity in rows
        if step is None or owner.get(identity) == step
        or any(claim["step"] == step for claim in owners.get(identity, ()))
    )
    for_owner = row_fates(selected, rows, owners, fates, (results, trial_ticks(trials)), report)

    lists = {name: report.get(name, []) for name in LISTS}
    return {
        "ok": not any(lists.values()),
        "step": step,
        "rows_checked": len(selected),
        "results": None if results.path is None else str(results.path),
        "commit_read": commit_read,
        **lists,
        "for_owner": for_owner,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--step", help="check only the rows this step owns, and the fates it wrote")
    parser.add_argument("--results", type=Path, help="the result lines of the test entry's run")
    parser.add_argument("--ledger-dir", type=Path, default=HERE,
                        help="the folder of rows.tsv, owners.tsv, owners-judged.tsv, extra.tsv and fates/")
    parser.add_argument("--trials", type=Path, default=TRIALS, help="the folder of the trial files")
    parser.add_argument("--no-commit-read", action="store_true",
                        help="do not compare rows.tsv with ledger.py's rows (for a test's own ledger folder)")
    args = parser.parse_args()
    try:
        report = check(args.ledger_dir, Results(args.results), args.trials, args.step,
                       commit_read=not args.no_commit_read)
    except (OSError, ValueError, SyntaxError, csv.Error, subprocess.CalledProcessError,
            tarfile.TarError) as error:
        print(json.dumps({"ok": False, "error": str(error)}))
        return 1
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
