"""A check that judged another tree or had red commands gives the owner its exact repair."""

from lem.model.landing import checks_ended
from unit.landing.worlds import OTHER, TIP


def test_a_tracked_edit_names_the_changes_and_how_to_put_them_back() -> None:
    refused = checks_ended.tree_moved("fix-login", "/work/fix-login", " M login.py")
    assert (refused.code, refused.why, refused.fix) == (
        "tracked-change",
        (
            "a command of the checks changed what git tracks, so its result is about another "
            "tree:\n M login.py"
        ),
        (
            "put the files back (`git -C /work/fix-login checkout -- FILE`) and make the command "
            "change no tracked file, then run `lem land checks fix-login` again"
        ),
    )


def test_a_commit_names_both_heads_and_the_command_to_restore_the_start() -> None:
    refused = checks_ended.committed("fix-login", "/work/fix-login", TIP, OTHER)
    assert (refused.code, refused.why, refused.fix) == (
        "tracked-change",
        (
            "a command of the checks made a commit on the branch (111111111..999999999), "
            "so its result is about another tree"
        ),
        (
            f"make the command commit nothing, put the branch back with `git -C /work/fix-login "
            f"reset --hard {TIP}`, then run `lem land checks fix-login` again"
        ),
    )


def test_red_checks_name_each_failed_command_in_run_order() -> None:
    refused = checks_ended.red(("npm test", "make check"))
    assert (refused.code, refused.why, refused.fix) == (
        "red",
        "the checks are red on 2 command(s): npm test; make check",
        (
            "a builder reads the output files and repairs the change; the checks are never "
            "edited to pass"
        ),
    )
