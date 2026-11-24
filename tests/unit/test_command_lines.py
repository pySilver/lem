"""Each command line a text of Lem gives is one the command takes: every `lem NAME ...`,
`lem-ask ...` and `lem-jev ...` in a code span or a code block of the skills
(`skills/**/*.md`), the agents (`agents/*.md`), the guides (`docs/*.md`) and README.md,
read against the shape in tests/unit/commands.json (tests/unit/test_commands.py).

    python3 -B -m unittest discover -s tests/unit

Where a command line is:

- a code span whose text starts with `lem`, `lem-ask` or `lem-jev` and a word after it;
  a span may run over a line break, never over an empty line (`lem land` at the end of
  a line of skills/lem/harness/claude-code/ask-merger.md and `merge-review SLUG
  --no-answer --tip TIP --base BASE` on the next are one call);
- a line of a code block marked `bash`, `sh`, `shell`, `console` or nothing that starts
  so, with the lines after a trailing backslash joined to it
  (`lem corrections record ID --decision lesson --verdict proposed \\`);
- a code span inside any line of any code block, or inside a span of two backticks
  (skills/lem/stages/land.md quotes a brief so). A block marked `text` or anything else
  is a transcript or an output: its lines are not calls (README.md's `lem  docs: "the
  footer says Terms"`, where lem is the one who speaks).

How a line is read:

- A word that has capitals and no small letter, or that stands in angle brackets, is a
  placeholder for one word: `SLUG`, `"WHY"`, `SLUG-2`, `<pageID>`
  (`lem land start SLUG`). In the place of a subcommand it stands for any of them, and
  the line is right when one of them takes the rest (`lem issue STEP SLUG`, `lem NAME
  ARGS...`). A value with small letters is the word itself, and where the slot has
  choices it must be one of them.
- `A|B` as one word is a choice of values, each a choice of its slot or a placeholder
  (`lem land merge SLUG --by owner|merger`).
- Words in `[...]` may be left out: the line is right both with them and without them
  (`lem session close SLUG [--session ID] --why ...`). `(... | ...)` groups
  alternatives, and a lone `|` divides them; both are only marks, and each option
  inside is checked (`lem decisions --repo WORKTREE criterion SLUG (--changed N ... |
  --added N --now TEXT | ...)`).
- `...`, `…` and a placeholder that ends in `...` say that words were left out: the
  count of positional words is not checked where one stands
  (`lem decisions criterion ... --decision ID`). As an option's value it is the value
  (`--why ...`).
- A code span that gives no positional word after its subcommand, or gives only the
  word of a step that has choices, names the command in prose and is not a whole call:
  its names, options and values are checked, and the count is not
  (`lem land merged`, `lem criteria approve`). A code span may also name an option
  without its value (`lem land read --record`). A line of a code block is always a whole
  call.
- From `#` after a space, and from a `<`, `>`, `;` or `&` that is not in quotes, the
  rest is a comment, a redirection or a heredoc, and not read
  (`lem project proposals add --kind retro --file - <<'JSON'`).
- An option is checked at the level it stands: one of `lem project` before the
  subcommand, one of the subcommand after it, as argparse reads them
  (`lem project --repo WORKTREE show`). `--flag=value` is the flag and its value.
  After an option the level does not take, the count is not checked: nobody knows
  whether a value follows it. A required option the line leaves out is not a fault: a
  text gives what it is about.
- `lem-ask` puts `ask` before a first word that is not a subcommand, as its main does
  (`lem-ask /tmp/session-storage.json`).

A line the case cannot read is in ALLOWED with its reason, and a line that is wrong
today is in WRONG with what the command takes instead, each by its exact text: a new
wrong line fails, and so does an entry whose line is gone or now right.
"""

import re
import shlex
import sys
import unittest
from dataclasses import dataclass
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_commands

ROOT = test_commands.ROOT
# The texts that give command lines to agents and people.
TEXTS = ("skills/**/*.md", "agents/*.md", "docs/*.md", "README.md")
# The marks of a code block whose lines are shell lines.
SHELL = ("", "bash", "sh", "shell", "console")
NAMES = ("lem", "lem-ask", "lem-jev")
CALL = re.compile(r"(lem|lem-ask|lem-jev)\s+\S")
FENCE = re.compile(r"^\s*(`{3,}|~{3,})\s*([\w+-]*)")
# A code span, over line breaks but not over an empty line (the paragraph is cut at
# them first).
SPAN = re.compile(r"(?<!`)(`+)(?!`)(.+?)(?<!`)\1(?!`)", re.DOTALL)
PLACEHOLDER = re.compile(r"[^a-z]*[A-Z][^a-z]*|<[^<>\s]+>")
# a placeholder in angle brackets, which is no redirection
ANGLE = re.compile(r"<[^<>\s]+>")
LEFT_OUT = ("...", "…")
CANNOT = "cannot judge: "
# The marks of a synopsis, as the scanner writes them in the place of `[`, `]`, `(`,
# `)` and a lone `|` that stand outside quotes.
OPEN, CLOSE, GROUP, UNGROUP, OR = "\x01", "\x02", "\x03", "\x04", "\x05"
MARKS = {"[": OPEN, "]": CLOSE, "(": GROUP, ")": UNGROUP}

# The lines the case cannot read, each with why.
ALLOWED: dict[str, str] = {}
# The lines that are wrong today, each with what the command takes instead. A defect of
# the text or of the command, listed and left as it is.
WRONG: dict[str, str] = {
    # skills/lem/stages/investigate.md, of the answer to a question: the prose names the
    # call, and the call with no line is refused before its own check runs
    "lem project state SLUG answered": (
        'state takes one LINE or more after the status: lem project state SLUG answered "THE ANSWER"'
    ),
}


@dataclass(frozen=True)
class Line:
    path: str
    number: int
    text: str
    # a code span, which may name a command in prose; a line of a code block is a call
    span: bool


@dataclass(frozen=True)
class Word:
    text: str
    # inside `[...]`: the line is right without it too
    optional: bool


def is_call(text: str) -> bool:
    return CALL.match(text) is not None


def spans(text: str, path: str, first: int) -> list[Line]:
    """The command lines in the code spans of TEXT, which starts at line FIRST, and in
    the spans a span of two backticks quotes."""
    found = []
    for match in SPAN.finditer(text):
        said = " ".join(match.group(2).split())
        number = first + text.count("\n", 0, match.start())
        if is_call(said):
            found.append(Line(path, number, said, span=True))
        elif len(match.group(1)) > 1:
            found += spans(match.group(2), path, number)
    return found


def prose(lines: list[tuple[int, str]], path: str) -> list[Line]:
    """The command lines in the code spans of prose LINES, cut at each empty line."""
    found: list[Line] = []
    block: list[tuple[int, str]] = []
    for number, line in [*lines, (0, "")]:
        if line.strip():
            block.append((number, line))
            continue
        if block:
            found += spans("\n".join(text for _, text in block), path, block[0][0])
        block = []
    return found


def lines_of(text: str, path: str) -> list[Line]:
    """Every command line of the Markdown TEXT, in its order."""
    found: list[Line] = []
    outside: list[tuple[int, str]] = []
    rows = text.split("\n")
    fence: tuple[str, str] | None = None
    index = 0
    while index < len(rows):
        number, row = index + 1, rows[index]
        index += 1
        opened = FENCE.match(row)
        if fence is None and opened:
            fence = (opened.group(1), opened.group(2).lower())
            outside.append((number, ""))
            continue
        if fence is not None and row.strip().startswith(fence[0][0] * len(fence[0])):
            fence = None
            outside.append((number, ""))
            continue
        if fence is None:
            outside.append((number, row))
            continue
        outside.append((number, ""))
        whole = row.strip()
        while whole.endswith("\\") and index < len(rows):
            whole = whole[:-1] + " " + rows[index].strip()
            index += 1
        if fence[1] in SHELL and is_call(whole):
            found.append(Line(path, number, " ".join(whole.split()), span=False))
        else:
            found += spans(row, path, number)
    found += prose(outside, path)
    return sorted(found, key=lambda line: line.number)


def texts() -> list[Path]:
    found: set[Path] = set()
    for pattern in TEXTS:
        found.update(path for path in ROOT.glob(pattern) if path.is_file())
    return sorted(found)


def command_lines() -> list[Line]:
    found: list[Line] = []
    for path in texts():
        found += lines_of(path.read_text(encoding="utf-8"), str(path.relative_to(ROOT)))
    return found


def closing(text: str, index: int) -> int:
    """The index after the quote that closes the one at INDEX of TEXT, or its end when
    none does (shlex then refuses the line)."""
    quote = text[index]
    at = index + 1
    while at < len(text) and text[at] != quote:
        at += 2 if quote == '"' and text[at] == "\\" else 1
    return min(at + 1, len(text))


def ends(text: str, index: int, out: list[str]) -> bool:
    """Whether the line's call ends at INDEX: a comment, a redirection or a heredoc
    starts there, or another command."""
    char = text[index]
    return char in "<>;&" or (char == "#" and (not out or out[-1].isspace()))


def mark(text: str, index: int) -> str:
    """The character at INDEX, or the mark of a synopsis it stands for."""
    char = text[index]
    if char in MARKS:
        return f" {MARKS[char]} "
    if char == "|" and text[index - 1 : index + 2].strip() == "|":
        return f" {OR} "
    return char


def scanned(text: str) -> str:
    """TEXT up to its comment, redirection or heredoc, with the marks of a synopsis
    that stand outside quotes written as words of their own."""
    out: list[str] = []
    index = 0
    while index < len(text):
        angle = ANGLE.match(text, index)
        if text[index] in "'\"":
            end = closing(text, index)
        elif text[index] == "\\" or angle:
            end = angle.end() if angle else index + 2
        elif ends(text, index, out):
            # the number of a stream before its redirection, as in 2>&1
            while text[index] in "<>" and out and out[-1].isdigit():
                out.pop()
            break
        else:
            out.append(mark(text, index))
            index += 1
            continue
        out.append(text[index:end])
        index = end
    return "".join(out)


def words_of(text: str) -> list[Word]:
    """The words of TEXT after its command's name; ValueError when its quotes do not
    close."""
    words: list[Word] = []
    depth: list[str] = []
    for token in shlex.split(scanned(text))[1:]:
        if token in (OPEN, GROUP):
            depth.append(token)
        elif token in (CLOSE, UNGROUP):
            if depth:
                depth.pop()
        elif token != OR:
            words.append(Word(token, optional=OPEN in depth))
    return words


def is_placeholder(text: str) -> bool:
    return PLACEHOLDER.fullmatch(text) is not None


def left_out(text: str) -> bool:
    return text in LEFT_OUT or (is_placeholder(text) and text.endswith(LEFT_OUT))


def is_option(text: str) -> bool:
    return text.startswith("-") and text != "-" and not left_out(text)


def bounds(positionals: list[dict]) -> tuple[int, float]:
    low, high = 0, 0.0
    for item in positionals:
        counted = item["count"]
        if counted.isdigit():
            low, high = low + int(counted), high + int(counted)
        else:
            low += counted in ("1", "+")
            high = float("inf") if counted in ("*", "+", "rest") else high + 1
    return low, high


def unchosen(value: str, choices: list[str] | None, where: str) -> list[str]:
    """The parts of VALUE that are no choice of WHERE."""
    if choices is None or is_placeholder(value) or left_out(value):
        return []
    return [
        f"{where} takes {' or '.join(choices)}, not {part}"
        for part in value.split("|")
        if part not in choices and not is_placeholder(part)
    ]


def option_of(level: dict, flag: str) -> dict | None:
    for name, option in level["options"].items():
        if flag == name or flag in option["aliases"]:
            return option
    return None


def taken(
    level: dict, words: list[Word], at: int, where: str, *, span: bool
) -> tuple[int, list[str], bool]:
    """The option at AT of WORDS: the index after it and its value, what is wrong, and
    whether LEVEL knows the option (when not, nobody knows whether a value follows)."""
    flag, equal, attached = words[at].text.partition("=")
    option = option_of(level, flag)
    if option is None:
        return at + 1, [f"`{where}` takes no option {flag}"], False
    if not option["value"]:
        return at + 1, [f"{flag} of `{where}` takes no value"] if equal else [], True
    if equal:
        return at + 1, unchosen(attached, option.get("choices"), flag), True
    end = at + 1
    many = option.get("count") in ("*", "+")
    while end < len(words) and not is_option(words[end].text):
        end += 1
        if not many:
            break
    if end == at + 1 and option.get("count") not in ("?", "*") and not span:
        return (
            end,
            [f"{flag} of `{where}` takes a value, and the line gives none"],
            True,
        )
    wrong = [
        problem
        for word in words[at + 1 : end]
        for problem in unchosen(word.text, option.get("choices"), flag)
    ]
    return end, wrong, True


def counted(level: dict, given: list[Word], where: str, *, mention: bool) -> list[str]:
    """What is wrong with GIVEN as the positional words of LEVEL."""
    positionals = level["positionals"]
    wrong = []
    for item, word in zip(positionals, given, strict=False):
        if item["count"] != "1":
            break
        wrong += unchosen(word.text, item.get("choices"), f"`{where}` {item['name']}")
    if mention:
        return wrong
    low, high = bounds(positionals)
    if high == float("inf"):
        takes = f"{low} or more"
    else:
        takes = str(low) if low == high else f"{low} to {int(high)}"
    for number in sorted({len(given), sum(not word.optional for word in given)}):
        if not low <= number <= high:
            wrong.append(
                f"the line gives `{where}` {number} positional words, and it takes "
                f"{takes}"
            )
    return wrong


def any_of(level: dict, words: list[Word], where: str, *, span: bool) -> list[str]:
    """What is wrong when the first of WORDS, a placeholder, names a subcommand: nothing
    when one of the subcommands takes the rest."""
    for name, child in level["subcommands"].items():
        if not judge(child, words[1:], f"{where} {name}", span=span):
            return []
    rest = " ".join(word.text for word in words)
    return [f"no subcommand of `{where}` takes `{rest}`"]


def subcommand(
    level: dict, words: list[Word], at: int, where: str, *, span: bool
) -> list[str] | None:
    """What is wrong when the word at AT of WORDS names a subcommand of LEVEL; None when
    it is a positional word of LEVEL itself."""
    text = words[at].text
    if text in level["subcommands"]:
        child = level["subcommands"][text]
        return judge(child, words[at + 1 :], f"{where} {text}", span=span)
    if level["positionals"]:
        return None
    if left_out(text):
        return [f"{CANNOT}`{where}` leaves out its subcommand"]
    if is_placeholder(text):
        return any_of(level, words[at:], where, span=span)
    return [f"`{where}` has no subcommand {text}"]


def judge(level: dict, words: list[Word], where: str, *, span: bool) -> list[str]:
    """What is wrong with WORDS as the words of LEVEL, the shape of the command WHERE."""
    subcommands = level.get("subcommands", {})
    if "default" in level and (not words or words[0].text not in subcommands):
        words = [Word(level["default"], optional=False), *words]
    wrong: list[str] = []
    given: list[Word] = []
    omitted = False
    rest_at = next(
        (n for n, item in enumerate(level["positionals"]) if item["count"] == "rest"),
        None,
    )
    at = 0
    while at < len(words):
        text = words[at].text
        if text == "--" or (rest_at is not None and len(given) >= rest_at):
            given += words[at + (text == "--") :]
            break
        if is_option(text):
            at, said, known = taken(level, words, at, where, span=span)
            wrong += said
            omitted = omitted or not known
            continue
        chosen = (
            subcommand(level, words, at, where, span=span)
            if subcommands and not given
            else None
        )
        if chosen is not None:
            return wrong + chosen
        omitted = omitted or left_out(text)
        given += [] if left_out(text) else [words[at]]
        at += 1
    if subcommands and level.get("subcommand_required") and not given:
        return wrong if span else [*wrong, f"`{where}` needs a subcommand"]
    mention = span and all(
        n < len(level["positionals"]) and "choices" in level["positionals"][n]
        for n in range(len(given))
    )
    return wrong + counted(level, given, where, mention=mention or omitted)


def root(name: str, shapes: dict[str, dict]) -> dict:
    """The shape a line that starts with NAME is read against."""
    if name != "lem":
        return shapes[name]
    links = test_commands.names.ALIASES
    return {
        "options": {"--help": test_commands.HELP},
        "positionals": [],
        "subcommands": {
            key: shape for key, shape in shapes.items() if key not in links
        },
        "subcommand_required": False,
    }


def verdict(line: Line, shapes: dict[str, dict]) -> list[str]:
    """What is wrong with LINE against SHAPES: nothing when the command takes it."""
    name = line.text.split()[0]
    try:
        words = words_of(line.text)
    except ValueError as error:
        return [f"{CANNOT}{error}"]
    return judge(root(name, shapes), words, name, span=line.span)


class Rules(unittest.TestCase):
    """Each rule of the docstring, on a line of a text and on one the command does not
    take."""

    def wrong(self, text: str, *, span: bool = False) -> list[str]:
        shapes = test_commands.written()["commands"]
        return verdict(Line("a text", 1, text, span=span), shapes)

    def test_a_placeholder_is_one_word(self) -> None:
        self.assertEqual(self.wrong("lem land start SLUG"), [])
        self.assertEqual(self.wrong('lem project state SLUG answered "WHY"'), [])
        self.assertIn(
            "the line gives `lem land start` 2 positional words, and it takes 1",
            self.wrong("lem land start SLUG OTHER"),
        )

    def test_a_placeholder_in_a_subcommands_place_is_any_of_them(self) -> None:
        self.assertEqual(self.wrong("lem issue STEP SLUG"), [])
        self.assertEqual(self.wrong("lem NAME ARGS..."), [])
        self.assertEqual(
            self.wrong("lem issue STEP SLUG OTHER"),
            ["no subcommand of `lem issue` takes `STEP SLUG OTHER`"],
        )

    def test_a_value_with_small_letters_is_one_of_its_choices(self) -> None:
        self.assertEqual(self.wrong("lem land merge SLUG --by owner|merger"), [])
        self.assertEqual(self.wrong("lem corrections collect yes"), [])
        self.assertEqual(
            self.wrong("lem land merge SLUG --by owner|someone"),
            ["--by takes owner or merger, not someone"],
        )
        self.assertEqual(
            self.wrong("lem corrections collect maybe"),
            ["`lem corrections collect` answer takes yes or no, not maybe"],
        )

    def test_words_in_brackets_may_be_left_out(self) -> None:
        self.assertEqual(
            self.wrong("lem session close SLUG [--session ID] --why ..."), []
        )
        self.assertEqual(
            self.wrong(
                'lem project state SLUG STATUS "one line" ["a further line" ...]'
            ),
            [],
        )
        self.assertIn(
            "the line gives `lem land start` 2 positional words, and it takes 1",
            self.wrong("lem land start SLUG [OTHER]"),
        )

    def test_a_group_of_alternatives_is_only_marks(self) -> None:
        self.assertEqual(
            self.wrong(
                "lem decisions --repo WORKTREE criterion SLUG (--changed N --was TEXT "
                "--now TEXT | --added N --now TEXT | --removed N --was TEXT) --why TEXT "
                "(--decision ID | --by lead|personas [--said TEXT])"
            ),
            [],
        )
        self.assertEqual(
            self.wrong("lem decisions criterion SLUG (--changed N | --grown N)"),
            ["`lem decisions criterion` takes no option --grown"],
        )

    def test_words_left_out_lift_the_count(self) -> None:
        self.assertEqual(self.wrong("lem decisions criterion ... --decision ID"), [])
        self.assertEqual(self.wrong("lem-ask … --no-wait"), [])
        self.assertEqual(
            self.wrong("lem project ... --words X"),
            ["cannot judge: `lem project` leaves out its subcommand"],
        )

    def test_a_span_with_no_positional_names_the_command_in_prose(self) -> None:
        for text in ("lem land merged", "lem land read --record", "lem criteria red"):
            self.assertEqual(self.wrong(text, span=True), [], text)
        self.assertNotEqual(self.wrong("lem land merged"), [])
        self.assertEqual(
            self.wrong("lem land merge --by nobody", span=True),
            ["--by takes owner or merger, not nobody"],
        )
        self.assertEqual(
            self.wrong("lem project", span=False), ["`lem project` needs a subcommand"]
        )

    def test_a_comment_a_redirection_and_a_heredoc_are_not_read(self) -> None:
        self.assertEqual(
            self.wrong("lem board --task SLUG # the board of one task"), []
        )
        self.assertEqual(
            self.wrong("lem project proposals add --kind retro --file - <<'JSON'"), []
        )
        self.assertEqual(self.wrong("lem project waiting 2>&1"), [])

    def test_an_option_belongs_to_the_level_it_stands_at(self) -> None:
        self.assertEqual(self.wrong("lem project --repo WORKTREE show"), [])
        self.assertEqual(
            self.wrong("lem project show --repo WORKTREE"),
            ["`lem project show` takes no option --repo"],
        )
        self.assertEqual(
            self.wrong("lem land checks SLUG --status=1"),
            ["--status of `lem land checks` takes no value"],
        )
        self.assertEqual(
            self.wrong("lem land merge SLUG --by"),
            ["--by of `lem land merge` takes a value, and the line gives none"],
        )

    def test_a_name_or_a_subcommand_that_is_not_there_is_wrong(self) -> None:
        self.assertEqual(
            self.wrong("lem tickets approve X"), ["`lem` has no subcommand tickets"]
        )
        self.assertEqual(
            self.wrong("lem land go SLUG"), ["`lem land` has no subcommand go"]
        )

    def test_lem_ask_reads_a_first_word_that_names_no_subcommand_as_a_spec(
        self,
    ) -> None:
        self.assertEqual(self.wrong("lem-ask /tmp/session-storage.json"), [])
        self.assertEqual(self.wrong("lem-ask - <<'JSON'"), [])
        self.assertEqual(self.wrong("lem-ask wait PAGEID"), [])
        self.assertEqual(
            self.wrong("lem-ask a.json b.json"),
            ["the line gives `lem-ask ask` 2 positional words, and it takes 0 to 1"],
        )

    def test_quotes_that_do_not_close_cannot_be_judged(self) -> None:
        self.assertEqual(
            self.wrong('lem project state SLUG held "no end'),
            ["cannot judge: No closing quotation"],
        )


class Reading(unittest.TestCase):
    """Where a text gives a command line."""

    def test_a_span_runs_over_a_line_break_and_not_over_an_empty_line(self) -> None:
        text = 'Run `lem project state SLUG\ndropped "WHY"` now.\n\n`lem land` and `x\n\nlem land base SLUG`'
        self.assertEqual(
            [(line.number, line.text) for line in lines_of(text, "t.md")],
            [(1, 'lem project state SLUG dropped "WHY"'), (4, "lem land")],
        )

    def test_a_shell_block_line_is_a_call_and_a_backslash_joins_the_next(self) -> None:
        text = (
            "```bash\nlem corrections record ID --decision lesson \\\n"
            "  --verdict proposed\nlem\n```\n"
        )
        self.assertEqual(
            lines_of(text, "t.md"),
            [
                Line(
                    "t.md",
                    2,
                    "lem corrections record ID --decision lesson --verdict proposed",
                    span=False,
                )
            ],
        )

    def test_a_span_of_two_backticks_quotes_spans(self) -> None:
        text = "Brief: ``Read `a.md` where `lem version` says``."
        self.assertEqual(
            lines_of(text, "t.md"), [Line("t.md", 1, "lem version", span=True)]
        )

    def test_a_text_block_is_a_transcript_whose_spans_alone_are_calls(self) -> None:
        text = "```text\nlem  docs: the footer\nsee `lem land base SLUG`\n```\n"
        self.assertEqual(
            lines_of(text, "t.md"), [Line("t.md", 3, "lem land base SLUG", span=True)]
        )


class TextLines(unittest.TestCase):
    def test_each_command_line_of_the_texts_is_one_the_command_takes(self) -> None:
        shapes = test_commands.written()["commands"]
        seen: set[str] = set()
        wrong, unread, right_now = [], [], []
        for line in command_lines():
            seen.add(line.text)
            if line.text in ALLOWED:
                continue
            said = verdict(line, shapes)
            place = f"{line.path}:{line.number}: {line.text}"
            if line.text in WRONG:
                if not said:
                    right_now.append(place)
            elif any(problem.startswith(CANNOT) for problem in said):
                unread.append(f"{place}\n      {'; '.join(said)}")
            elif said:
                wrong.append(f"{place}\n      {'; '.join(said)}")
        gone = [text for text in [*ALLOWED, *WRONG] if text not in seen]
        found = [
            *(f"the command does not take {item}" for item in wrong),
            *(
                f"the case cannot read {item}; put it in ALLOWED with why"
                for item in unread
            ),
            *(
                f"a line of WRONG is right now, take it out: {item}"
                for item in right_now
            ),
            *(
                f"no text gives this line of ALLOWED or WRONG now: {text}"
                for text in gone
            ),
        ]
        self.assertEqual(found, [], "\n" + "\n".join(found))


if __name__ == "__main__":
    unittest.main()
