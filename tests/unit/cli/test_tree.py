"""The command tree of `lem`: its help, its two tables, each leaf's words against its `Call`,
the stubs' refusal, the exit codes of the envelope, `lem version`, and the tree as `tree.json`
holds it."""

import importlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import click
import msgspec
import pytest

from lem.cli import lazy, nouns
from lem.cli.group import LazyGroup
from unit.cli import shapes

ROOT = Path(__file__).resolve().parents[3]
DESIGN = ROOT / "docs" / "plans" / "2026-11-25-lem-built-again.md"
STEP_ROW = re.compile(r"^\| \d+ \| `([a-z-]+)` \|", re.MULTILINE)
NOT_BUILT = re.compile(r"the step `([a-z-]+)` builds it")
# What no leaf may load when it is imported: the board's, the add-ons' and the settings'
# libraries, and the commands of another noun.
HEAVY = ("starlette", "uvicorn", "jinja2", "httpx", "tomlkit", "psutil", "pywebpush")

type Leaf = tuple[tuple[str, ...], str]


def leaves() -> list[Leaf]:
    """Each leaf of the two tables: its words after `lem`, and its module's path."""
    found: list[Leaf] = []
    for noun, path in nouns.NOUNS:
        command = importlib.import_module(path).COMMAND
        if isinstance(command, LazyGroup):
            found += [((noun, verb), leaf) for verb, leaf in command.table]
        else:
            found.append(((noun,), path))
    return found


LEAVES = leaves()
IDS = [" ".join(words) for words, _ in LEAVES]


def steps() -> set[str]:
    """The step ids of the design's table "All steps, in order"."""
    return set(STEP_ROW.findall(DESIGN.read_text(encoding="utf-8")))


def called(capsys: pytest.CaptureFixture[str], *argv: str) -> tuple[int, str, str]:
    """`lem ARGV` in this process: its exit code, its stdout and its stderr."""
    code = lazy.main(list(argv))
    out, err = capsys.readouterr()
    return code, out, err


def sample(param: click.Parameter) -> str:
    """A word PARAM takes."""
    if isinstance(param.type, click.Choice):
        return str(param.type.choices[0])
    if isinstance(param.type, click.types.IntParamType):
        return "1"
    if isinstance(param.type, click.types.FloatParamType):
        return "1.5"
    return "x"


def minimal(command: click.Command) -> list[str]:
    """The fewest words COMMAND takes: one for each argument and option it requires."""
    words: list[str] = []
    for param in command.params:
        if not param.required:
            continue
        if isinstance(param, click.Option):
            words.append(shapes.long_flag(param))
        words.append(sample(param))
    return words


def no_value_default(param: click.Parameter) -> object:
    """What a `Call` field's default is when PARAM has none of its own."""
    if isinstance(param, click.Option) and param.is_bool_flag:
        return False
    if param.multiple or param.nargs == -1:
        return ()
    return None


def test_lem_alone_lem_help_and_its_help_option_list_every_noun(
    capsys: pytest.CaptureFixture[str],
) -> None:
    said = {
        argv: called(capsys, *argv) for argv in ((), ("help",), ("--help",), ("-h",))
    }
    texts = {(code, out, err) for code, out, err in said.values()}
    assert len(texts) == 1
    code, out, err = texts.pop()
    assert (code, err) == (0, "")
    assert out.startswith("Usage: lem [OPTIONS] COMMAND [ARGS]...")
    listed = re.findall(r"^  ([a-z-]+)  ", out, re.MULTILINE)
    assert listed == [*(noun for noun, _ in nouns.NOUNS), "help", "version"]


@pytest.mark.parametrize("noun", [noun for noun, _ in nouns.NOUNS])
def test_lem_help_noun_is_the_nouns_own_help(
    capsys: pytest.CaptureFixture[str], noun: str
) -> None:
    helped = called(capsys, "help", noun)
    own = called(capsys, noun, "--help")
    assert helped == own
    code, out, err = own
    assert (code, err) == (0, "")
    assert out.startswith(f"Usage: lem {noun} ")


def test_lem_help_of_no_noun_is_a_wrong_call(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, out, err = called(capsys, "help", "tickets")
    assert (code, out) == (2, "")
    assert "`lem` has no command tickets: `lem help` lists them" in err


@pytest.mark.parametrize(("words", "path"), LEAVES, ids=IDS)
def test_each_leaf_takes_the_words_of_its_call(
    words: tuple[str, ...], path: str
) -> None:
    module = importlib.import_module(path)
    command = module.COMMAND
    assert isinstance(command, click.Command)
    assert not isinstance(command, click.Group)
    assert command.name == words[-1]
    fields = {field.encode_name: field for field in msgspec.structs.fields(module.Call)}
    params = {param.name: param for param in command.params}
    assert sorted(params) == sorted(fields)
    for name, param in params.items():
        field = fields[name]
        if param.required:
            assert field.required, f"{name} is required by the command and not by Call"
            continue
        assert not field.required, f"{name} is required by Call and not by the command"
        default = param.default
        if default is click.core.UNSET:
            default = no_value_default(param)
        assert field.default == default, name


@pytest.mark.parametrize(("words", "path"), LEAVES, ids=IDS)
def test_each_stub_refuses_not_built_and_names_a_step_of_the_plan(
    capsys: pytest.CaptureFixture[str], words: tuple[str, ...], path: str
) -> None:
    argv = [*words, *minimal(importlib.import_module(path).COMMAND)]
    code, out, err = called(capsys, *argv)
    assert (code, err) == (1, "")
    envelope = json.loads(out)
    assert envelope["ok"] is False
    refusal = envelope["refusal"]
    assert refusal["code"] == "not-built"
    assert f"`lem {' '.join(words)}`" in refusal["why"]
    named = NOT_BUILT.search(refusal["fix"])
    assert named is not None
    assert named.group(1) in steps()


@pytest.mark.parametrize(
    "argv",
    [
        ("land", "start"),
        ("land", "start", "x", "--no-such-option"),
        ("land", "go", "x"),
        ("tickets",),
        ("land", "merge", "x", "--by", "nobody"),
        ("owner", "watch", "--every", "often"),
        ("land",),
    ],
    ids=" ".join,
)
def test_a_wrong_call_is_clicks_own_with_exit_2_and_no_envelope(
    capsys: pytest.CaptureFixture[str], argv: tuple[str, ...]
) -> None:
    code, out, err = called(capsys, *argv)
    assert (code, out) == (2, "")
    assert err.startswith("Usage: lem")


def test_a_fault_exits_3_with_one_line_and_its_traceback_in_lem_log(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    from lem.cli.land import start

    def broken(call: start.Call) -> None:
        raise RuntimeError("the record\nis torn")

    monkeypatch.setattr(start, "run", broken)
    code, out, err = called(capsys, "land", "start", "x")
    assert (code, err) == (3, "")
    assert out.count("\n") == 1
    fault = json.loads(out)
    assert fault["ok"] is False
    log = Path(fault["fault"]["log"])
    assert fault["fault"]["line"] == "Lem failed: RuntimeError: the record is torn"
    assert log == Path(os.environ["XDG_CONFIG_HOME"]) / "lem" / "lem.log"
    logged = log.read_text(encoding="utf-8")
    assert "a fault of Lem" in logged
    assert "Traceback" in logged
    assert "RuntimeError: the record" in logged


def test_a_fault_whose_log_cannot_be_written_goes_to_stderr_and_says_why(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from lem.cli.land import start

    def broken(call: start.Call) -> None:
        raise RuntimeError("the record is torn")

    blocked = tmp_path / "a-file"
    blocked.write_text("")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(blocked))
    monkeypatch.setattr(start, "run", broken)
    code, out, err = called(capsys, "land", "start", "x")
    assert code == 3
    log = json.loads(out)["fault"]["log"]
    assert log.startswith(
        f"standard error: {blocked}/lem/lem.log could not be written ("
    )
    assert "Traceback" in err
    assert "RuntimeError: the record is torn" in err


def test_an_outcome_is_printed_in_the_envelope_with_exit_0(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    from lem.cli.land import next as due

    class Due(msgspec.Struct):
        step: str

    monkeypatch.setattr(due, "run", lambda call: Due(step=f"base of {call.slug}"))
    code, out, err = called(capsys, "land", "next", "x")
    assert (code, err) == (0, "")
    assert json.loads(out) == {"ok": True, "result": {"step": "base of x"}}
    monkeypatch.setattr(due, "run", lambda call: None)
    assert called(capsys, "land", "next", "x") == (0, '{"ok":true}\n', "")


def test_lem_version_prints_root_version_and_commit_as_json(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, out, err = called(capsys, "version")
    assert (code, err) == (0, "")
    said = json.loads(out)
    assert list(said) == ["root", "version", "commit"]
    assert said["root"] == str(ROOT)
    manifest = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())
    assert said["version"] == manifest["version"]
    assert isinstance(said["commit"], str)
    assert said["commit"]


@pytest.mark.parametrize(
    ("argv", "command"),
    [
        (("ask", "spec.json"), "ask ask"),
        (("ask", "-", "--no-wait"), "ask ask"),
        (("ask", "--follow", "spec.json"), "ask ask"),
        (("ask",), "ask ask"),
        (("ask", "wait", "PAGE"), "ask wait"),
        (("jev", "spec.json"), "jev check"),
        (("jev", "check", "spec.json"), "jev check"),
    ],
    ids=lambda value: " ".join(value) if isinstance(value, tuple) else value,
)
def test_the_default_verb_takes_a_first_word_that_names_no_verb(
    capsys: pytest.CaptureFixture[str], argv: tuple[str, ...], command: str
) -> None:
    code, out, _ = called(capsys, *argv)
    assert code == 1
    assert f"`lem {command}`" in json.loads(out)["refusal"]["why"]


def test_a_help_option_after_a_noun_with_a_default_verb_is_the_nouns_help(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, out, _ = called(capsys, "ask", "--help")
    assert code == 0
    assert out.startswith("Usage: lem ask [OPTIONS] COMMAND [ARGS]...")


def test_the_tree_is_the_one_tree_json_holds() -> None:
    built, written = shapes.tree(), shapes.written()
    assert built == written, (
        f"the tree is not the one {shapes.FILE} holds: after a meant change, run "
        f"{shapes.WRITE}"
    )


def test_a_call_loads_its_own_leaf_and_no_other_noun_and_nothing_heavy() -> None:
    probe = (
        "import sys; from lem.cli import lazy; lazy.main(['land', 'start', 'x']); "
        "print(' '.join(sorted(sys.modules)))"
    )
    ran = subprocess.run(
        [sys.executable, "-I", "-B", "-c", probe],
        capture_output=True,
        text=True,
        check=True,
    )
    loaded = ran.stdout.splitlines()[-1].split()
    cli = sorted(name for name in loaded if name.startswith("lem.cli."))
    others = [
        name
        for name in cli
        if name.count(".") >= 2 and name.split(".")[2] in dict(nouns.NOUNS)
    ]
    assert others == ["lem.cli.land", "lem.cli.land.start", "lem.cli.land.verbs"]
    assert [name for name in loaded if name.split(".")[0] in HEAVY] == []
    # help, version and the fault's log load only when a call needs them
    for name in ("lem.cli.usage", "lem.cli.version", "lem.cli.faults", "traceback"):
        assert name not in loaded, name


def test_the_command_lem_runs_the_tree_from_its_entry() -> None:
    command = ROOT / ".venv" / "bin" / "lem"
    assert command.is_file(), f"{command} is not there: run `uv sync` in the checkout"
    stub = subprocess.run(
        [command, "land", "start", "x"], capture_output=True, text=True, check=False
    )
    assert stub.returncode == 1
    assert json.loads(stub.stdout)["refusal"]["code"] == "not-built"
    version = subprocess.run(
        [command, "version"], capture_output=True, text=True, check=False
    )
    assert version.returncode == 0
    assert json.loads(version.stdout)["root"] == str(ROOT)
