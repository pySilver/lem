---
worth: later
where: tests/unit/test_board_model.py:MovedBase
added: 2026-11-22
---
# Two test classes of the board model come after its main guard

In `tests/unit/test_board_model.py` the block `if __name__ == "__main__": unittest.main()` stands
before the classes `MovedBase` and `AfterDropped`. The suite runs the file through
`python3 -B -m unittest discover -s tests/unit`, which imports the whole file and finds all
classes. A run of the file alone, `python3 -B tests/unit/test_board_model.py`, calls
`unittest.main()` before Python reaches those two classes, so their tests do not run and the run
still says `OK`. The guard belongs at the end of the file.

Seen outside the change by the builder of task merge-button-after-failed-merge (2026-11-22); the base commit has it.
