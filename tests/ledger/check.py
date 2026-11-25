#!/usr/bin/env python3
"""Check that the rebuild accounts for each ledger row and proves its fate."""

import argparse
from collections import defaultdict
import csv
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
TRIALS = HERE.parents[1] / "docs/plans/2026-11-25-lem-built-again/trials"
ROW_COLUMNS = ["id", "kind", "source", "what", "fate", "proof", "note"]
OWNER_COLUMNS = ["id", "step"]
FATE_COLUMNS = ["id", "fate", "proof", "note"]
RESULT_LINE = re.compile(r"(ok|FAIL|SKIP)[ \t]+(\S.*)")
TRIAL_LINE = re.compile(r"- \[x\][ \t]+(\S.*)")


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


def passed_tests(path, proofs):
    if path is None:
        return set()
    passed = set()
    failed_or_skipped = set()
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            match = RESULT_LINE.fullmatch(line.rstrip())
            if not match:
                continue
            status, name = match.groups()
            if status == "ok":
                passed.add(name)
            else:
                failed_or_skipped.add(name)
    # The old unit runner puts a diagnostic after ": " for FAIL and SKIP.
    # Match the full ID first so an ID can itself contain a colon and a space.
    known = proofs | passed
    for name in failed_or_skipped:
        candidate = name
        while candidate not in known and ": " in candidate:
            candidate = candidate.rsplit(": ", 1)[0]
        passed.discard(candidate)
    return passed


def passed_trials(folder):
    passed = set()
    for path in sorted(folder.glob("*.md")):
        for line in path.read_text(encoding="utf-8").splitlines():
            match = TRIAL_LINE.fullmatch(line.strip())
            if match:
                passed.add(match[1])
    return passed


def check(directory, results, trials, step):
    rows = group_by_id(read_tsv(directory / "rows.tsv", ROW_COLUMNS))
    owners = group_by_id(read_tsv(directory / "owners.tsv", OWNER_COLUMNS))
    fates = defaultdict(list)
    for path in sorted((directory / "fates").glob("*.tsv")):
        for fate in read_tsv(path, FATE_COLUMNS):
            fates[fate["id"]].append((path.stem, fate))

    report = {
        "duplicate_rows": [],
        "unknown_owner_rows": [],
        "multiple_owners": [],
        "no_owner": [],
        "no_fate": [],
        "wrong_step": [],
        "multiple_fates": [],
        "invalid_fate": [],
        "no_proof": [],
        "unproved": [],
        "no_note": [],
        "dropped_rulings": [],
    }
    for_owner = []
    all_ids = rows.keys() | owners.keys() | fates.keys()
    selected = sorted(
        identity for identity in all_ids
        if step is None
        or any(owner["step"] == step for owner in owners.get(identity, ()))
        or any(writer == step for writer, _fate in fates.get(identity, ()))
    )
    proofs = {
        fate["proof"].strip()
        for identity in selected
        for _writer, fate in fates.get(identity, ())
        if fate["proof"].strip()
    }
    passed = passed_tests(results, proofs) | passed_trials(trials)

    for identity in selected:
        entries = rows.get(identity, [])
        claims = owners.get(identity, [])
        if len(claims) > 1:
            report["multiple_owners"].append(identity)
        owner = claims[0]["step"] if len(claims) == 1 else ""
        if not entries and claims:
            report["unknown_owner_rows"].append(identity)
        elif len(entries) > 1:
            report["duplicate_rows"].append(identity)
        if entries and not owner:
            report["no_owner"].append(identity)

        valid = []
        for writer, fate in fates.get(identity, ()):
            if entries and writer == owner:
                valid.append(fate)
            elif step is None or step in {writer, owner}:
                report["wrong_step"].append({"id": identity, "step": writer, "owner": owner or None})

        if not entries or (step is not None and owner and step != owner):
            continue
        if not valid:
            report["no_fate"].append(identity)
            continue
        if len(valid) > 1:
            report["multiple_fates"].append(identity)
            continue

        fate = valid[0]
        disposition, proof, note = fate["fate"], fate["proof"].strip(), fate["note"]
        if disposition not in {"kept", "changed", "dropped"}:
            report["invalid_fate"].append(identity)
        if disposition in {"kept", "changed"} and not proof:
            report["no_proof"].append(identity)
        if proof and proof not in passed:
            report["unproved"].append({"id": identity, "proof": proof})
        if disposition in {"changed", "dropped"} and not note.strip():
            report["no_note"].append(identity)
        if disposition == "dropped" and entries[0]["kind"] == "ruling":
            item = {"id": identity, "step": owner, "note": note}
            if note.startswith("for the owner:"):
                for_owner.append(item)
            else:
                report["dropped_rulings"].append(item)

    return {
        "ok": not any(report.values()),
        "step": step,
        "rows_checked": sum(
            step is None or any(owner["step"] == step for owner in owners.get(identity, ()))
            for identity in rows
        ),
        **report,
        "for_owner": for_owner,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--step", help="check one step and its fate file")
    parser.add_argument("--results", type=Path, help="the test entry's results file")
    parser.add_argument("--ledger-dir", type=Path, default=HERE, help="folder with rows, owners and fates")
    parser.add_argument("--trials", type=Path, default=TRIALS, help="folder with trial Markdown files")
    args = parser.parse_args()
    try:
        report = check(args.ledger_dir, args.results, args.trials, args.step)
    except (OSError, ValueError, csv.Error) as error:
        print(json.dumps({"ok": False, "error": str(error)}))
        return 1
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
