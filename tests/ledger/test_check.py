"""check.py refuses each way a step could close with a row lost, and the ledger follows the design.

Each case builds a small ledger folder of real rows in a temporary folder: two rows of
`land-base`, one of `land-merge` and one ruling, with owners.py's own owners for them.
"""

import csv
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping
    from types import ModuleType

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DESIGN = ROOT / "docs/plans/2026-11-25-lem-built-again.md"
LANDING = ROOT / "docs/plans/2026-11-25-lem-built-again/landing.md"


def script(name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(f"ledger_{name}", HERE / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


check = script("check")
owners_rules = script("owners")


def read(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


def write(path: Path, columns: list[str], rows: Iterable[Mapping[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, columns, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


ROWS = read(HERE / "rows.tsv")
OWNERS = {row["id"]: row["step"] for row in read(HERE / "owners.tsv")}


def first(step: str, kind: str | None = None) -> dict[str, str]:
    return next(
        row for row in ROWS if OWNERS[row["id"]] == step and kind in {None, row["kind"]}
    )


BASE_ONE = first("land-base", "unit")
BASE_TWO = first("land-base", "refusal")
MERGE_ONE = first("land-merge", "path")
RULING = first("guides", "ruling")
PICKED = [BASE_ONE, BASE_TWO, MERGE_ONE, RULING]


class Ledger(unittest.TestCase):
    """A ledger folder of four real rows, a results file and a trials folder."""

    def setUp(self) -> None:
        folder = tempfile.TemporaryDirectory(prefix="lem-ledger-test-")
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        self.trials = self.root / "trials"
        self.trials.mkdir()
        (self.root / "fates").mkdir()
        write(self.root / "rows.tsv", check.ROW_COLUMNS, PICKED)
        write(
            self.root / "owners.tsv",
            check.OWNER_COLUMNS,
            [{"id": row["id"], "step": OWNERS[row["id"]]} for row in PICKED],
        )
        shutil.copy(HERE / "owners-judged.tsv", self.root)
        shutil.copy(HERE / "extra.tsv", self.root)
        self.results = self.root / "results.txt"
        self.results.write_text(
            "collected 4\nok   test-a\nok   test-b\nok   test-c\nSKIP test-skipped: no browser\n",
            encoding="utf-8",
        )
        (self.trials / "skeleton.md").write_text(
            "- [x] S1 the formula installs\n", encoding="utf-8"
        )

    def fates(self, step: str, *rows: tuple[str, str, str, str]) -> None:
        write(
            self.root / "fates" / f"{step}.tsv",
            check.FATE_COLUMNS,
            [dict(zip(check.FATE_COLUMNS, row, strict=True)) for row in rows],
        )

    def all_fated(self) -> None:
        self.fates(
            "land-base",
            (BASE_ONE["id"], "kept", "test-a", ""),
            (BASE_TWO["id"], "changed", "test-b", "the code is new"),
        )
        self.fates("land-merge", (MERGE_ONE["id"], "kept", "S1", ""))
        self.fates("guides", (RULING["id"], "kept", "test-c", ""))

    # The report as check.py prints it in JSON: lists of ids and of small dicts.
    def run_check(
        self, step: str | None = None, *, results: bool = True
    ) -> dict[str, Any]:
        given = check.Results(self.results if results else None)
        return check.check(self.root, given, self.trials, step, commit_read=False)


class TheCheckRefuses(Ledger):
    def test_every_row_fated_and_proved_passes(self) -> None:
        self.all_fated()
        report = self.run_check()
        self.assertTrue(report["ok"], report)
        self.assertEqual(report["rows_checked"], 4)

    def test_no_fates_name_every_row(self) -> None:
        report = self.run_check()
        self.assertFalse(report["ok"])
        self.assertEqual(report["no_fate"], sorted(row["id"] for row in PICKED))

    def test_a_fate_in_a_file_of_a_step_that_does_not_own_the_row(self) -> None:
        self.all_fated()
        self.fates(
            "land-merge",
            (MERGE_ONE["id"], "kept", "S1", ""),
            (BASE_ONE["id"], "dropped", "test-a", "not needed"),
        )
        report = self.run_check()
        self.assertEqual(
            report["wrong_step"],
            [{"id": BASE_ONE["id"], "file": "land-merge.tsv", "owner": "land-base"}],
        )
        self.assertFalse(report["ok"])

    def test_a_row_fated_twice_by_its_owner(self) -> None:
        self.all_fated()
        self.fates(
            "guides",
            (RULING["id"], "kept", "test-c", ""),
            (RULING["id"], "kept", "test-c", ""),
        )
        self.assertEqual(self.run_check()["multiple_fates"], [RULING["id"]])

    def test_a_fate_for_a_row_the_ledger_does_not_hold(self) -> None:
        self.all_fated()
        self.fates(
            "guides",
            (RULING["id"], "kept", "test-c", ""),
            ("unit:made-up", "kept", "test-c", ""),
        )
        report = self.run_check()
        self.assertEqual(
            report["unknown_fate_rows"], [{"id": "unit:made-up", "file": "guides.tsv"}]
        )
        self.assertFalse(report["ok"])

    def test_a_proof_that_was_skipped(self) -> None:
        self.all_fated()
        self.fates("guides", (RULING["id"], "kept", "test-skipped", ""))
        self.assertEqual(
            self.run_check()["unproved"],
            [{"id": RULING["id"], "proof": "test-skipped", "why": "failed or skipped"}],
        )

    def test_a_proof_that_is_not_in_the_results(self) -> None:
        self.all_fated()
        self.fates("guides", (RULING["id"], "kept", "test-gone", ""))
        self.assertEqual(
            self.run_check()["unproved"],
            [{"id": RULING["id"], "proof": "test-gone", "why": "not in the results"}],
        )

    def test_a_proof_with_no_results_given(self) -> None:
        self.all_fated()
        report = self.run_check(results=False)
        self.assertEqual(
            {entry["id"] for entry in report["unproved"]},
            {BASE_ONE["id"], BASE_TWO["id"], RULING["id"]},
        )

    def test_an_empty_results_file(self) -> None:
        self.results.write_text("", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "collected"):
            self.run_check()

    def test_results_that_do_not_add_up(self) -> None:
        self.results.write_text("collected 5\nok   test-a\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "1 result lines for 5 collected"):
            self.run_check()

    def test_a_dropped_row_needs_a_proof_and_a_reason(self) -> None:
        self.all_fated()
        self.fates(
            "land-base",
            (BASE_ONE["id"], "dropped", "", ""),
            (BASE_TWO["id"], "changed", "test-b", "the code is new"),
        )
        report = self.run_check()
        self.assertEqual(report["no_proof"], [BASE_ONE["id"]])
        self.assertEqual(report["no_note"], [BASE_ONE["id"]])

    def test_a_fate_that_is_no_fate(self) -> None:
        self.all_fated()
        self.fates("guides", (RULING["id"], "moved", "test-c", ""))
        self.assertEqual(
            self.run_check()["invalid_fate"], [{"id": RULING["id"], "fate": "moved"}]
        )

    def test_a_dropped_ruling_goes_to_the_owner_only_with_its_note(self) -> None:
        self.all_fated()
        self.fates("guides", (RULING["id"], "dropped", "test-c", "the guide is gone"))
        report = self.run_check()
        self.assertEqual(
            report["ruling_dropped_without_owner_note"],
            [{"id": RULING["id"], "note": "the guide is gone"}],
        )
        self.fates("guides", (RULING["id"], "dropped", "test-c", "for the owner:"))
        self.assertEqual(self.run_check()["no_note"], [RULING["id"]])
        self.fates(
            "guides",
            (RULING["id"], "dropped", "test-c", "for the owner: the guide is gone"),
        )
        report = self.run_check()
        self.assertTrue(report["ok"], report)
        self.assertEqual(
            report["for_owner"],
            [
                {
                    "id": RULING["id"],
                    "note": "for the owner: the guide is gone",
                    "step": "guides",
                }
            ],
        )

    def test_a_trial_check_ticked_in_a_file_of_another_name(self) -> None:
        self.all_fated()
        (self.trials / "skeleton.md").write_text(
            "- [ ] S1 the formula installs\n", encoding="utf-8"
        )
        (self.trials / "ask.md").write_text(
            "- [x] S1 the formula installs\n", encoding="utf-8"
        )
        self.assertEqual(
            self.run_check()["unproved"],
            [
                {
                    "id": MERGE_ONE["id"],
                    "proof": "S1",
                    "why": "not ticked in trials/skeleton.md",
                }
            ],
        )

    def test_an_owner_moved_by_hand(self) -> None:
        self.all_fated()
        write(
            self.root / "owners.tsv",
            check.OWNER_COLUMNS,
            [
                {
                    "id": row["id"],
                    "step": "land-merge" if row is BASE_ONE else OWNERS[row["id"]],
                }
                for row in PICKED
            ],
        )
        self.fates(
            "land-merge",
            (MERGE_ONE["id"], "kept", "S1", ""),
            (BASE_ONE["id"], "kept", "test-a", ""),
        )
        report = self.run_check()
        self.assertEqual(
            report["owners_stale"],
            [{"id": BASE_ONE["id"], "owners_tsv": "land-merge", "rules": "land-base"}],
        )
        self.assertFalse(report["ok"])

    def test_a_fates_file_named_for_no_step(self) -> None:
        self.all_fated()
        self.fates("land_base", (BASE_ONE["id"], "kept", "test-a", ""))
        self.assertEqual(self.run_check()["unknown_fate_files"], ["land_base.tsv"])

    def test_a_step_that_is_not_a_step(self) -> None:
        with self.assertRaisesRegex(ValueError, "land_base is not a step"):
            self.run_check(step="land_base")


class OneStep(Ledger):
    def test_a_builder_with_its_own_fates_and_results_passes_alone(self) -> None:
        self.fates(
            "land-base",
            (BASE_ONE["id"], "kept", "test-a", ""),
            (BASE_TWO["id"], "changed", "test-b", "the code is new"),
        )
        report = self.run_check(step="land-base")
        self.assertTrue(report["ok"], report)
        self.assertEqual(report["rows_checked"], 2)
        self.assertFalse(self.run_check()["ok"])

    def test_a_step_sees_its_row_fated_by_another(self) -> None:
        self.fates(
            "land-base",
            (BASE_ONE["id"], "kept", "test-a", ""),
            (BASE_TWO["id"], "changed", "test-b", "the code is new"),
        )
        self.fates("guides", (BASE_TWO["id"], "dropped", "test-c", "not needed"))
        report = self.run_check(step="land-base")
        self.assertEqual(
            report["wrong_step"],
            [{"id": BASE_TWO["id"], "file": "guides.tsv", "owner": "land-base"}],
        )

    def test_the_command_exits_1_and_names_the_row(self) -> None:
        self.fates(
            "land-base",
            (BASE_ONE["id"], "kept", "test-gone", ""),
            (BASE_TWO["id"], "changed", "test-b", "the code is new"),
        )
        ran = subprocess.run(
            [
                sys.executable,
                "-I",
                "-B",
                str(HERE / "check.py"),
                "--step",
                "land-base",
                "--ledger-dir",
                str(self.root),
                "--results",
                str(self.results),
                "--trials",
                str(self.trials),
                "--no-commit-read",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(ran.returncode, 1, ran.stderr)
        self.assertEqual(
            json.loads(ran.stdout)["unproved"],
            [{"id": BASE_ONE["id"], "proof": "test-gone", "why": "not in the results"}],
        )


def commit_readable() -> bool:
    ran = subprocess.run(
        [
            "git",
            "-C",
            str(HERE),
            "cat-file",
            "-e",
            f"{script('ledger').REV}^{{commit}}",
        ],
        capture_output=True,
        check=False,
    )
    return ran.returncode == 0


@unittest.skipUnless(
    commit_readable(), "the clone does not hold the commit the ledger reads"
)
class TheLedgerIsWhatItsScriptsMake(unittest.TestCase):
    def test_the_rows_and_the_owners_are_the_scripts_output(self) -> None:
        report = check.check(HERE, check.Results(None), HERE / "no-trials", None)
        for name in (
            "rows_missing",
            "rows_unknown",
            "rows_edited",
            "owners_stale",
            "no_owner",
            "multiple_owners",
            "duplicate_rows",
            "owner_unknown_row",
        ):
            self.assertEqual(report[name], [], name)

    def test_a_row_taken_out_of_rows_tsv_is_named(self) -> None:
        with tempfile.TemporaryDirectory(prefix="lem-ledger-test-") as folder:
            root = Path(folder)
            for name in ("owners.tsv", "owners-judged.tsv", "extra.tsv"):
                shutil.copy(HERE / name, root)
            write(
                root / "rows.tsv",
                check.ROW_COLUMNS,
                [row for row in ROWS if row is not RULING],
            )
            report = check.check(root, check.Results(None), root / "trials", None)
        self.assertEqual(report["rows_missing"], [RULING["id"]])
        self.assertEqual(report["owner_unknown_row"], [RULING["id"]])


def table(text: str, heading: str) -> list[list[str]]:
    """The body rows of the first Markdown table after HEADING, as lists of cells."""
    body = text.split(heading, 1)[1]
    rows: list[list[str]] = []
    for line in body.splitlines():
        if line.startswith("| ") and not line.startswith("| ---"):
            rows.append([cell.strip() for cell in line.strip().strip("|").split(" | ")])
        elif rows and not line.startswith("|"):
            break
    return rows[1:]


def path_id(name: str) -> str:
    return "path:" + re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


class TheLedgerFollowsTheDesign(unittest.TestCase):
    def test_one_path_row_for_each_row_of_landing_e_owned_by_its_proof_owner(
        self,
    ) -> None:
        wanted: dict[str, str] = {}
        name = ""
        for cells in table(LANDING.read_text(encoding="utf-8"), "## E. The hard paths"):
            # A row with no name is the row above it on a moved base.
            identity = path_id(cells[0]) if cells[0] else path_id(name) + "-base-moved"
            name = cells[0] or name
            wanted[identity] = cells[-1].strip("`")
        rows = {row["id"] for row in read(HERE / "extra.tsv") if row["kind"] == "path"}
        self.assertEqual(rows, set(wanted))
        self.assertEqual({identity: OWNERS[identity] for identity in rows}, wanted)

    def test_the_seam_rows_are_part_8s_table_word_for_word(self) -> None:
        wanted = {
            cells[0].strip("`"): {
                "what": cells[1],
                "source": cells[2],
                "step": cells[3].strip("`"),
            }
            for cells in table(
                DESIGN.read_text(encoding="utf-8"),
                "**Seams: behavior no other kind shows**",
            )
        }
        rows = {
            row["id"]: {
                "what": row["what"],
                "source": row["source"],
                "step": OWNERS[row["id"]],
            }
            for row in read(HERE / "extra.tsv")
            if row["kind"] == "seam"
        }
        self.assertEqual(rows, wanted)

    def test_every_owner_is_a_step(self) -> None:
        self.assertLessEqual(set(OWNERS.values()), owners_rules.STEPS)


if __name__ == "__main__":
    unittest.main()
