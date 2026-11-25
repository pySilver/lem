"""The panel of the board's picture of one task, `refund-line-on-receipt`, as today's board draws
it for the owner on this Mac: its header and tabs, its Overview, Criteria and decisions, Checks
and review, and the merge's confirm step."""

import msgspec

from fixtures.board import prose
from fixtures.board.beside import OUTCOME, session
from fixtures.board.moments import BASE, pull
from fixtures.board.receipt import CHART, DECISION_CHART, HOW, REASONS, SLUG, TIP
from fixtures.board.shown import document, gone, since, task
from fixtures.board.waiting import reasons
from lem.board.inputs.forms import ActForm, Field
from lem.board.inputs.parts import Chip, Link, Row
from lem.board.inputs.task.cards import Building, Picture, Review, Shot, Verdict
from lem.board.inputs.task.checks import Checks, Command, Proposal
from lem.board.inputs.task.criteria import Case, Criterion
from lem.board.inputs.task.decisions import Criteria, Decision, Option, Part, Story
from lem.board.inputs.task.head import Fact, HeadActs, KeyLine, Pill, Tab, TaskHead
from lem.board.inputs.task.now import Foot, Now, Phase, Phases, Ring, Stat
from lem.board.inputs.task.overview import Overview
from lem.board.inputs.task.panel import Panel
from lem.board.inputs.task.steps import Confirm, Merge

SESSION = session(SLUG, 479.5)
MEDIA = f"{BASE}/tasks/{SLUG}/media/"
FORGE = f"Open the pull request on the forge: {pull(44)}"
SHORT = TIP[:7]
PULL = Link(href=pull(44), label="acme/shop#44", title=FORGE, out=True)
NOT_GREEN = "\n".join(REASONS)
ROUND_ONE = (
    "round 1, a round with the profiles that fit: must-fix, 1 must-fix, 1 should, 0 nit"
)
ROUND_TWO = (
    "round 2, a round with the profiles that fit: clean, 0 must-fix, 0 should, 1 nit"
)
WHERE = "Merge the pull request on GitHub or on this board."
FIRST = (
    "A refund shows on the receipt as a line of its own, and the total stands under it:"
)
SECOND = "A refund larger than the total shows 0.00 and a credit note for the rest."
IMPORTANT = (
    "It makes the pull request not green, and it went past the personas: the dialectic "
    "took it"
)
HEAD = TaskHead(
    slug=SLUG,
    back=f"{BASE}/",
    pill=Pill(look="you", label="Waits for the merge", since=since(448, "7h 28m")),
    title="Refund line on receipt",
    key_line=KeyLine(link=PULL, word="not green", look="you", icon="code-pull-request"),
    acts=HeadActs(
        merge=Link(
            href=f"{BASE}/tasks/{SLUG}/merge",
            label="Merge #44…",
            icon="code-pull-request",
            press="risk",
            frame=True,
        )
    ),
    ask="Show a refund as a line of its own on the receipt",
    facts=(
        Fact(
            key="type",
            term="Type",
            bold="feat",
            text="standard track",
            title="because the receipt gets a new line",
        ),
        Fact(
            key="careful",
            term="Careful",
            sub="the review calls it, before the proposal",
        ),
        Fact(
            key="waits",
            term="Waits for",
            text=f"Read the merge review; Merge the pull request [#44]({pull(44)})",
            yours=True,
            title=f"Where you answer: {WHERE}",
        ),
        Fact(
            key="branch",
            term="Branch",
            text="feat/refund-line-on-receipt",
            mono=True,
            copy="feat/refund-line-on-receipt",
        ),
        Fact(key="pr", term="Pull request", link=PULL, sub="not green"),
        Fact(
            key="session",
            term="Session",
            text=SLUG,
            mono=True,
            title=f"The agterm session of the task: {SESSION}",
            jump=SESSION,
        ),
        Fact(
            key="time",
            term="In this state",
            when=since(448, "7h 28m"),
            sub="since 08:32 · opened 05:50",
        ),
    ),
    chips=(
        Chip(label="2 criteria", icon="file-lines", title=f"1. {FIRST}\n2. {SECOND}"),
        Chip(
            label="checks green: 2",
            icon="check",
            look="ok",
            title="green  make test  214 passed\ngreen  make lint  All checks passed",
        ),
        Chip(
            label="review 2: clean",
            icon="eye",
            look="ok",
            title=f"{ROUND_ONE}\n{ROUND_TWO}",
        ),
        Chip(
            label="not green", icon="triangle-exclamation", look="you", title=NOT_GREEN
        ),
    ),
)


def tabs(current: str) -> tuple[Tab, ...]:
    """The five tabs, `current` the one shown (none on a step)."""
    named = (
        ("overview", "Overview", None),
        ("criteria", "Criteria and decisions", None),
        ("checks", "Checks and review", None),
        ("timeline", "Timeline", None),
        ("artifacts", "Artifacts", 7),
    )
    return tuple(
        Tab(
            key=key,
            name=name,
            href=task(SLUG, None if key == "overview" else key),
            kbd=str(number),
            current=key == current,
            count=count,
        )
        for number, (key, name, count) in enumerate(named, 1)
    )


OVERVIEW = Overview(
    review=Review(
        calls=True,
        head="The merge review · it calls you",
        why=(
            "Verdict: call. The change does what both criteria say; it is not green for "
            "two choices taken without you, and I would keep both."
        ),
        at=since(440, "7h 20m", "08:40"),
        text=document(f"merge-review-{SLUG}", prose.MERGE_REVIEW, media=MEDIA),
        artifact=Link(
            href=f"{BASE}/tasks/{SLUG}/artifacts/merge-review.md/",
            label="merge-review.md",
            title="Open merge-review.md on Artifacts",
            icon="file-lines",
            frame=True,
        ),
    ),
    building=Building(
        goal="The receipt gets a new line",
        outcome=document(f"outcome-{SLUG}", OUTCOME, media=MEDIA),
        shots=(
            Shot(
                id="shots-receipt",
                caption="Receipt",
                before=Picture(
                    src=f"{MEDIA}receipt-before.png",
                    href=f"{MEDIA}receipt-before.png",
                    alt="Receipt, before",
                ),
                after=Picture(
                    src=f"{MEDIA}receipt-after.png",
                    href=f"{MEDIA}receipt-after.png",
                    alt="Receipt, after",
                ),
            ),
        ),
        important=Link(
            href=task(SLUG, "criteria"),
            label="1 important decision waits for a look",
            title="Open the tab Criteria and decisions · key 2",
            icon="triangle-exclamation",
            frame=True,
        ),
        filed="no backlog item filed · on the task’s branch",
    ),
    verdict=Verdict(
        look="you",
        icon="triangle-exclamation",
        word="not green, for 4 reasons:",
        reasons=reasons("v", None),
    ),
    now=Now(
        look="you",
        icon="code-branch",
        who="You act",
        head="Proposed: it waits for your merge",
        shown=f"pull request [{pull(44)}]({pull(44)})",
        more="not green",
        where=WHERE,
        foot=Foot(
            updated=gone(448, "7h 28m ago"),
            timer=since(448, "7h 28m"),
            note="in this state",
            jump=SESSION,
        ),
    ),
    phases=Phases(
        look="you",
        phases=(
            Phase(name="Criteria", past=True),
            Phase(name="Plan", past=True),
            Phase(name="Build", sub="task 2 of 2", past=True),
            Phase(name="Checks", sub="2 green", past=True),
            Phase(name="Review", sub="clean", past=True),
            Phase(name="Proposed", sub="not green", current=True),
            Phase(name="Landed"),
        ),
        ring=Ring(done=2, current=2, total=2, big="2/2", small="plan tasks"),
        stats=(
            Stat(
                label="Who works on it",
                shown="one agent",
                said=(
                    "one agent plans it, and a fresh builder builds each task of the plan"
                ),
            ),
            Stat(
                label="Last commit",
                shown=SHORT,
                said="docs(plans): the refund line on the receipt",
            ),
            Stat(
                label="Open for",
                shown="10h 10m",
                when=since(610, "10h 10m"),
                said="opened 05:50",
            ),
            Stat(
                label="Checks",
                shown="green",
                said="2 commands in the last run",
                look="ok",
            ),
            Stat(
                label="Review",
                shown="clean",
                said="round 2, a round with the profiles that fit",
                look="ok",
            ),
            Stat(
                label="Decisions",
                shown="2",
                said="2 taken, 1 past the personas",
                look="bad",
            ),
        ),
    ),
)
CRITERIA = Criteria(
    how=document(f"how-{SLUG}", HOW),
    criteria_said=(
        "standard track, because the receipt gets a new line and a rule for a refund "
        "larger than the total."
    ),
    reads=(
        Row(
            id="crit-read",
            look="quiet",
            icon="users",
            head="The personas have not read these criteria yet.",
        ),
        Row(
            id="crit-approved",
            look="quiet",
            icon="user",
            head="Approved without you, as the task ran alone",
            time="06:02",
        ),
    ),
    criteria=(
        Criterion(
            id="criterion-1",
            number=1,
            look="quiet",
            icon="file-lines",
            text=FIRST,
            cases=(
                Case(
                    steps=(
                        "Order 1042 is 100.00 EUR, and a refund of 30.00 EUR comes in.",
                        "The receipt shows `Refund -30.00` under the items.",
                        "The total under it is 70.00.",
                    )
                ),
            ),
            chart=document(f"crit-{SLUG}-1", f"```mermaid\n{CHART}\n```"),
            tests=(("sh tests/refund.sh", "not checked yet"),),
        ),
        Criterion(
            id="criterion-2",
            number=2,
            look="quiet",
            icon="file-lines",
            text=SECOND,
            tests=(("sh tests/refund.sh", "not checked yet"),),
        ),
    ),
    decisions_said="2 taken · 1 important",
    decisions=(
        Decision(
            id=1,
            look="you",
            important=IMPORTANT,
            mark="important",
            what="Where the refund line goes on the receipt",
            chose="B: a line of its own under the items, then the total",
            who="by the dialectic · 06:40",
            story=Story(
                case_was="derived from the code, not run",
                cases=(
                    Case(
                        steps=(
                            "Order 1042 has three items, 100.00 EUR.",
                            "A refund of 30.00 EUR comes in.",
                            "The receipt prints its lines in the order of the choice.",
                            (
                                "A customer reads the last line above the total as the "
                                "price of an item."
                            ),
                        )
                    ),
                ),
                cause=(
                    "The receipt prints every line of an order in one list, and the total "
                    "is the last of them."
                ),
                options=(
                    Option(label="A", leads="in the items, as a negative price"),
                    Option(
                        label="B",
                        leads="a line of its own under the items, then the total",
                        taken=True,
                    ),
                    Option(label="C", leads="in the footer, beside the payment"),
                ),
                who="Taken by the dialectic, because the total stands under what changed it",
            ),
            chart=document(
                f"dec-{SLUG}-1", f"```mermaid\n{DECISION_CHART.strip()}\n```"
            ),
            parts=(
                Part(
                    label="The decision",
                    text="Where the refund line goes on the receipt",
                ),
                Part(label="Important", text=IMPORTANT),
                Part(
                    label="The ladder",
                    lines=(
                        "**The question gate:** no ruling covers it",
                        "**The personas:** two for B, one for C: no clear pick",
                        (
                            "**The dialectic:** B held: the case against it found no reader "
                            "that takes the last line above the total as an item"
                        ),
                    ),
                ),
                Part(
                    label="The personas",
                    text=(
                        "the developer picked B, the support person picked B, the "
                        "accountant leaned to C"
                    ),
                ),
            ),
        ),
        Decision(
            id=2,
            look="done",
            what="How the refund line is colored",
            chose="the theme's green, as a credit",
            who="by the agent · 07:00",
            parts=(
                Part(label="The decision", text="How the refund line is colored"),
                Part(
                    label="Who took it",
                    text=(
                        "Taken by the agent, because a refund is money back to the "
                        "customer, which the shop's receipts show in green"
                    ),
                ),
            ),
        ),
    ),
)


def output(number: int) -> Link:
    """The link to a command's whole output on Artifacts."""
    name = f"gate/{number:02d}.log"
    return Link(
        href=f"{BASE}/tasks/{SLUG}/artifacts/{name}/",
        label="output",
        title=f"Open its output, {name}",
        frame=True,
    )


CHECKS = Checks(
    commands_said="2 commands green",
    commands=(
        Command(
            id="gate-0",
            look="done",
            icon="check",
            word="green",
            command="make test",
            output=output(1),
            last="214 passed",
            tip=SHORT,
            time="08:06",
        ),
        Command(
            id="gate-1",
            look="done",
            icon="check",
            word="green",
            command="make lint",
            output=output(2),
            last="All checks passed",
            tip=SHORT,
            time="08:06",
        ),
    ),
    rounds_said="2 rounds",
    rounds=(
        Row(
            id="review-0",
            look="bad",
            icon="eye",
            head=ROUND_ONE,
            subs=(f"answered: codex, claude · ran correctness · on {SHORT}",),
            time="08:18",
        ),
        Row(
            id="review-1",
            look="done",
            icon="check",
            head=ROUND_TWO,
            subs=(f"answered: codex, claude · ran correctness · on {SHORT}",),
            time="08:30",
        ),
    ),
    proposal=Proposal(
        look="you",
        icon="triangle-exclamation",
        said="Proposed: not green, for 4 reasons",
        reasons=reasons("pr", None),
        time="08:32",
    ),
)
MERGE = Merge(
    confirm=Confirm(
        look="you",
        label="Merge: confirm",
        eyebrow="Merge #44 · confirm",
        form=ActForm(
            action=f"{BASE}/tasks/{SLUG}/merge",
            label="Merge pull request #44",
            icon="code-pull-request",
            press="risk",
            busy="Merging…",
            fields=(Field(name="confirm", shown="yes"), Field(name="tip", shown=TIP)),
        ),
        back=Link(href=task(SLUG), label="Back", frame=True),
        sheet=True,
    ),
    green=False,
    word="Not green",
    sub="The pull request says why, and so do the rows below.",
    reasons=reasons("cf", None),
    facts=(
        Fact(key="pr", term="Pull request", link=PULL),
        Fact(
            key="commit",
            term="Commit",
            text=TIP[:12],
            mono=True,
            sub="docs(plans): the refund line on the receipt",
        ),
        Fact(
            key="branch", term="Branch", text="feat/refund-line-on-receipt", mono=True
        ),
        Fact(key="into", term="Into", text="main", mono=True),
        Fact(
            key="as",
            term="Lands as",
            text="one commit: `feat(receipt): a refund shows as a line of its own`",
        ),
    ),
    note=(
        "A merge cannot be undone from the board. Lem’s merge call reads the base branch "
        "first, and it can take a minute."
    ),
)
OPEN = Panel(slug=SLUG, head=HEAD, tabs=tabs("overview"), overview=OVERVIEW)
CRITERIA_TAB = Panel(
    slug=SLUG, shows="criteria", head=HEAD, tabs=tabs("criteria"), criteria=CRITERIA
)
CHECKS_TAB = Panel(
    slug=SLUG, shows="checks", head=HEAD, tabs=tabs("checks"), checks=CHECKS
)
# A step of an act draws the header with no act of its own.
MERGE_STEP = Panel(
    slug=SLUG,
    shows="merge",
    head=msgspec.structs.replace(HEAD, acts=None),
    tabs=tabs(""),
    merge=MERGE,
)
