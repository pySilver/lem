"""Each expert gets one brief and one verbatim answer, without launching an agent."""

import os
from pathlib import Path

import pytest

from fakes.command import lem
from fakes.repo import RealRepo, run_git, write
from lem.addons.experts import ask, audience, record, seats
from lem.addons.experts.records import Asked, Brief
from lem.kernel.errors import Refusal

SELLER = ".lem/personas/seller.md"
PROFILE = ".lem/profile.md"
PERSON = b"# The seller\n\n## Who they are\n\nSells gifts.\n\n## What they want\n\nFast shipping.\n"
EXPLICIT = ("claude/fable:high", "codex/gpt-6.2-astra:high")


def test_brief_and_shared_pick(tmp_path: Path) -> None:
    repo = RealRepo.init(tmp_path / "repo", {SELLER: PERSON, PROFILE: b"# Store\n"})
    saved = ask.ask(
        repo.checkout,
        Asked(
            question="Which store?",
            context="One export needs it.",
            options=("Redis", "Postgres"),
            files=(SELLER,),
            seats=EXPLICIT,
        ),
    )
    path = Path(saved.brief)
    text = path.read_text()
    assert text.index("## Who the code is for") < text.index("## Your answer")
    for phrase in (
        "Which store?",
        "One export needs it.",
        "1. Redis",
        "2. Postgres",
        str(repo.checkout / SELLER),
        str(repo.checkout / PROFILE),
        "Sells gifts.",
        "Weigh each option",
        "Read only. Change no file",
    ):
        assert phrase in text
    assert "Fast shipping." not in text
    assert not any(seat in text for seat in EXPLICIT)
    assert path.parent.parent.name == "experts"
    assert (
        run_git(repo.checkout, "status", "--porcelain", "--untracked-files=all") == ""
    )
    assert saved.ask == ("fable", "astra")
    first = Path(saved.answers["fable"])
    for bad in ("answer: Redis\nwhy: Existing", "pick: Memcached\nwhy: Existing"):
        first.write_text(bad)
        with pytest.raises(Refusal):
            record.record(repo.checkout, saved.folder, "fable")
    with pytest.raises(Refusal, match="no seat"):
        record.record(repo.checkout, saved.folder, "opus")
    exact = "pick: Redis\nwhy: Existing.\n"
    first.write_text(exact)
    half = record.record(repo.checkout, saved.folder, "fable")
    assert half.agree is None and half.waiting == ("astra",)
    with pytest.raises(Refusal, match="already"):
        record.record(repo.checkout, saved.folder, "fable")
    Path(saved.answers["astra"]).write_text(exact)
    whole = record.record(repo.checkout, saved.folder, "astra")
    assert not whole.waiting and whole.agree == "Redis"
    assert first.read_text() == exact


def test_open_question_persists_words_and_never_picks(tmp_path: Path) -> None:
    repo = RealRepo.init(tmp_path / "repo", {SELLER: PERSON})
    saved = ask.ask(repo.checkout, Asked(question="What works?", seats=EXPLICIT))
    text = Path(saved.brief).read_text()
    audience_end = text.index("## Your answer")
    audience_words = text[text.index("## Who the code is for") : audience_end]
    assert "The project has no profile" in audience_words
    assert "Sells gifts." in audience_words
    assert "Answer as an engineer." in audience_words
    first = Path(saved.answers["fable"])
    first.write_text("pick: Redis\nwhy: Example")
    with pytest.raises(Refusal, match="brief"):
        record.record(repo.checkout, saved.folder, "fable")
    exact = "answer: Use Redis\n with expiry.\nwhy: Existing."
    first.write_text(exact)
    recorded = record.record(repo.checkout, saved.folder, "fable")
    assert recorded.answers["fable"].answer == "Use Redis with expiry."
    assert recorded.agree is None
    assert first.read_text() == exact
    second = ask.ask(repo.checkout, Asked(question="What works?", seats=EXPLICIT))
    assert second.folder != saved.folder and Path(saved.brief).is_file()


def test_seat_names_and_unavailable_codex(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = RealRepo.init(tmp_path / "repo", {SELLER: PERSON})
    monkeypatch.setattr("lem.settings.experts.answers", lambda agent, environ: False)
    single = ask.ask(repo.checkout, Asked(question="Which path?"))
    assert single.ask == ("fable",)
    assert "The owner asks one expert this question." in Path(single.brief).read_text()
    assert tuple(
        seat.name for seat in seats.chosen(repo.checkout, ("claude", "codex:high"))
    ) == (
        "fable",
        "astra",
    )
    for invalid in (
        ("claude-opus",),
        ("gemini/pro:high",),
        ("claude/opus:high", "claude/opus:low"),
    ):
        with pytest.raises(Refusal):
            seats.chosen(repo.checkout, invalid)
    monkeypatch.setattr("lem.settings.experts.answers", lambda agent, environ: True)
    write(
        repo.checkout,
        {
            ".lem/settings.toml": b'[seats]\nexperts = ["claude/opus:high", "codex/gpt-6.1-sol:xhigh"]\n'
        },
    )
    assert tuple(seat.name for seat in seats.chosen(repo.checkout, ())) == (
        "opus",
        "sol",
    )
    write(
        repo.checkout,
        {".lem/settings.local.toml": b'[seats]\nexperts = ["claude/sonnet:high"]\n'},
    )
    assert tuple(seat.name for seat in seats.chosen(repo.checkout, ())) == ("sonnet",)


def test_refusals_before_an_expert_folder_exists(tmp_path: Path) -> None:
    repo = RealRepo.init(tmp_path / "repo", {".lem/personas/README.md": b"Index\n"})
    for invalid in (
        Asked(question=""),
        Asked(question="Choice?", options=("One",)),
        Asked(question="Choice?", options=("One", "One")),
        Asked(question="Read?", files=("absent",)),
    ):
        with pytest.raises(Refusal):
            ask.ask(repo.checkout, invalid)
    with pytest.raises(Refusal, match="no personas"):
        ask.ask(repo.checkout, Asked(question="What works?"))
    assert not (repo.checkout / ".lem/state/experts").exists()
    with pytest.raises(Refusal, match="invalid or absent"):
        record.record(repo.checkout, "../outside", "fable")


def test_persona_excerpt_uses_identity_first_and_ends_at_a_sentence() -> None:
    long = " ".join(("Word",) * audience.WHO_WORDS) + "."
    text = f"# Seller\n\n## Who they are\n\n{long} Another sentence.\n\n## What next\nUnrelated."
    assert audience.who_they_are(text, "seller") == ("Seller", long + " …")
    assert audience.who_they_are(
        "# Seller\n<!-- secret -->\n> A quote\n\nSells gifts.\n\nSomething else.",
        "seller",
    ) == ("Seller", "Sells gifts.")


def test_cli_envelope_and_no_bytecode(tmp_path: Path) -> None:
    repo = RealRepo.init(tmp_path / "repo", {SELLER: PERSON})
    ran = lem(
        "--repo",
        str(repo.checkout),
        "experts",
        "brief",
        "--question",
        "What works?",
        "--seat",
        "claude",
    )
    assert ran.code == 0, ran.stdout
    outcome = ran.result()
    assert isinstance(outcome, dict)
    assert outcome["experts"][0]["model"] is None
    assert outcome["experts"][0]["effort"] is None
    answer = Path(outcome["answers"]["fable"])
    answer.write_text("answer: A note.\nwhy: It fits.")
    received = lem(
        "--repo",
        str(repo.checkout),
        "experts",
        "record",
        "--folder",
        outcome["folder"],
        "--expert",
        "fable",
    )
    assert received.code == 0, received.stdout
    assert received.envelope()["ok"] is True
    assert not tuple(Path(ask.__file__).parent.glob("__pycache__"))
    assert str(repo.checkout) not in os.environ["HOME"]


@pytest.mark.parametrize(
    "bad", ("codex/sol:high/extra", "codex/sol/tool:high", "claude/opus:HIGH")
)
def test_invalid_explicit_expert_seat_is_refused_before_publication(
    tmp_path: Path, bad: str
) -> None:
    repo = RealRepo.init(tmp_path / "repo", {SELLER: PERSON})
    with pytest.raises(Refusal, match="--seat"):
        ask.ask(repo.checkout, Asked(question="Which path?", seats=(bad,)))
    assert not (repo.checkout / ".lem/state/experts").exists()


def test_expert_brief_passes_the_same_strict_input_to_the_addon(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import msgspec

    from lem.cli.experts import brief

    called = Asked(question="Which path?", seats=EXPLICIT)

    def capture(folder: Path, given: Asked) -> Brief:
        assert folder == tmp_path
        assert given is called
        raise Refusal("captured", "captured the input", "no fix")

    monkeypatch.setattr(brief, "folder", lambda: tmp_path)
    monkeypatch.setattr(brief.ask, "ask", capture)
    with pytest.raises(Refusal, match="captured"):
        brief.run(called)
    with pytest.raises(msgspec.ValidationError, match="unknown field"):
        msgspec.convert({"question": "Which path?", "extra": True}, Asked)
