<!-- lem: old form -->
# `im-away`, `im-back`

Read when the owner says that he is away or back again, and when the watch of his mark ends, and
at no other time. His status changes nothing in a build, which asks him nothing either way: "I'd
rather review the PR and request a fix then find a work blocked on some question that automated
anwers could answer right" (2026-11-20). It changes nothing in a landing or a merge either. It
matters for a shape that waits for him: an interview, and criteria that wait for his yes. He says
whether he is there, and Lem assumes nothing: "Owner either tells dnd or not, no assumptions"
(2026-11-18). His status is the machine's: his word in any session of any repository on this
machine holds in every one, and a repository has no status of its own.
`/lem im-away` and `/lem im-back` are his words, and so is a plain sentence that plainly says the
same ("I'm away", "I'm back", "I'm here again").
When his words are not that plain ("I have to go, carry on"), ask once in the terminal: "Mark you
away until you say /lem im-back? (y/n)".
His words go into the record as he typed them; no script can tell who typed, so write them only
for words he typed in this session. A text for him says "without you", never "alone".

## His word

`lem project owner away --words "HIS WORDS"`, or `lem project owner back --words "HIS WORDS"`. It
writes the machine's mark: from away on, every task that did not end, in every repository on this
machine, runs without him, and so does each task opened while he is away; from back on, every task
that ran without him comes back to him, except a night's, which runs without him until it ends.
Say in one line what it means: the interviews and the criteria go on without him, a breaker waits
for him, the merge agent merges what it may as always. What still waits for him while he is away
also reaches his inbox, where he can answer it (`inbox-reply`), and a question there stays open
after his back. At back, one line for each task the
command's `tasks` names: whether its criteria were approved without him, and `/lem status SLUG` for
the rest. Nothing is undone: a wish of his that differs from what was decided is a correction, for
the lead while the task builds and a new ask after that.

Each task's session in the shape acts on the mark through its watch. In this session, when it is
one, take "When the watch ends" at once.

## The watch

A task's session in the shape keeps one watch of his mark in the background while it waits for
him, never two: read `owner` of `lem project waiting`, and `run-in-background` with `lem project
owner watch --seen N`, N being its `seen`, the number of records in the mark. It looks at the mark
once every 5 seconds (a guess, not a measurement) and ends with exit 0 and his status (`away`,
`since`, `words`, `seen`) as soon as the mark holds another number of records than N. Its end wakes
you: take "When the watch ends", then start it again with the `seen` it gave. A watch that ends
with exit 1 was stopped, or the mark has a line that does not read (its message names the file
and the line): start no other until that reason is gone. No other session keeps one, and a task
of the night acts on none: it runs without him until it ends.

## When the watch ends

- **Away**: the shape goes on without him, with no question to him, except a task held with `the
  order waits for the owner`.
  - *An order of his that names no task you can tell*: the task held with `the order waits for the
    owner` waits for him, and nothing of it starts; his back asks its one question
    (`prompts/session.md`, "What comes next").
  - *An interview*: the steps of `stages/interview.md` go on with your guess for each question
    left, each logged, `lem decisions log SLUG --by lem --what "THE QUESTION" --chose "YOUR GUESS"
    --why WHY`. The personas' read runs, since nobody can skip it now. Each criterion it flagged is
    settled as below, and then `lem criteria approve SLUG --file FILE --alone`, and the end of its
    step 7. The read's answers go into the pull request.
  - *Criteria that wait for his yes*: settle each flagged criterion as below, then `lem criteria
    approve SLUG --file FILE --alone` with the criteria as the ladder left them, and the start of
    the build (`stages/start.md`). A task held with `the criteria wait for the owner: a small change
    that someone else asked for` is on the fast track: FILE is its `criteria.md`, and the start
    starts its one builder. A task held with `the criteria wait for the owner: the small
    change is a full change` has had no interview yet: it takes the interview without him, from its
    first question.
  - *His No to the criteria on record* (on the board, or typed before he left): `--alone` refuses
    the text he said No to. Make the change from his note first, with no page while he is away: as
    `stages/interview.md`, step 6 says, or on the fast track as "The fast track" of
    `stages/new.md`, step 1 says. Then approve the changed text with `--alone`.
  - A request read while he is away asks nothing: where a stage would ask him, take the safer read
    (the standard track, and careful in doubt) and log it.
- **Back**: go on with him from where the files stand. What was taken without him stands.

**A flagged criterion without him** (one a persona called unexpected, confusing or wrong, or one
on which the two families split) is a decision in doubt whose personas answered and split. It
goes on from the dialectic of `stages/ladder.md`, level 3, and to the experts, level 4, when the
dialectic finds a break. Write the criterion into FILE as the level that settled it picked, and
log it with that level: `lem decisions log SLUG --what "criterion N" --option "AS YOU WROTE IT"
--option "AS THE PERSONA EXPECTED IT" --chose OPTION --by dialectic|experts --level
"personas=WHAT THEY SAID" --why WHY`. When no level settles it, it stays as you wrote it, with
`--by lead --unsettled`. Nothing waits for him: the pull request is not green in any case, since
he did not approve the criteria.
