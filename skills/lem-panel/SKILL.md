---
name: lem-panel
description: "Lem's persona panel: the project's personas answer one question or read one text. Lem's stages load it; the owner calls it as `/lem panel`."
disable-model-invocation: true
---

# Persona panel

A hard question never reaches the user cold. Before it does, the people it affects answer it,
each from what they would actually see, and the user gets a card instead of a list of numbers.

## When it runs, and when it does not

- **It runs** on a question whose options each cost something, so that no option is plainly
  right: what shows first, how much a penalty weighs, which default a shopper gets, what a merchant
  sees after a change, and technical forks too, such as how much of a fix to build now, whether to
  measure at full scale first, or how fresh a copy of the data must be. A technical question brings
  the people who run and build the system, never a shopper.
- **It does not run** on a question the code, a test, a probe or an existing ruling can answer.
  Check the project's rulings first (the list `lem project path rulings` prints): a ruled question is quoted,
  never re-asked.
- **It does not decide intent or taste.** "Do we want this at all" and "which looks right" stay
  the user's. The panel can still tell the user what each choice looks like to the people it
  affects.

## The project profile

The project's profile (`.lem/profile.md`, unless the project's settings name another path) says what the project is: the product, who uses
it and where, its scale, the rules every answer works within, the tools and versions it runs,
what a newcomer gets wrong, and the teams to compare with. Every persona reads it before its own file, and so do the practice scout and
the moderator. Without it a persona judges a fifty-million-item catalog as if it held a thousand,
and a shopper persona in a fashion catalog took a drawing for a normal product photo, which the
owner answered with "There is no such thing in FASHION as ILLUSTRATION" (mybaze gate log,
2026-11).

Each project writes its own from `references/profile-template.md`; no other profile
stands in for it. `lem cast` prints its path as `profile`, from the checkout or, like the
cast, from the default branch when the checkout has none or holds only an unchanged older copy. When `profile` is null, the panel still
runs and every card and review says "no project profile"; offer once to draft one from the
project's own documents, for the user to finish and commit.

## The people

The cast is a folder of persona files, one person each, with a `README.md` index: the project's
personas folder (`.lem/personas/`, unless its settings name another path), the project's own
people (in one shop project a shopper, a merchant, an ops admin, the engineer on call and the
CEO).

A panel asks the project's own people and nobody else's. Resolve the cast before every panel
with `lem cast`, which prints the layer, its source, the
index and each persona's path as JSON. Every project that uses Lem has personas, written at its
onboarding. When the command exits 1 the project has none: its setup is not finished. Run no
panel, write no card in a panel's name, and tell the one who asked what the command said, with
the step that writes the personas. Generic people never stand in for a project's own: a panel of
people nobody named answers for nobody.

A worktree branched before the project's
cast landed has none of its own; the script then reads the default branch's cast, from whichever
of the local and remote branch is newer, so the panel keeps the project's people without a rebase,
and `source` names the branch and commit. The same holds for a worktree whose cast is an older copy
it never edited: a persona added on the default branch reaches it without a merge, while a branch
that edits its cast keeps its own.

A persona's file may name the seats it answers on, in a frontmatter that holds this one line,
each seat written as the settings write one (`agent/model:effort`):

```
---
seats: ["claude/opus:high", "codex/gpt-6.2-sol:high"]
---
```

The owner chooses them; nobody writes a seat he did not choose. `lem cast` prints each persona's
`seats` (each with its `name`, the word its answer files carry), its `left_out` and its
`seats_from`, and the panel reads the seats there and nowhere else. A file with no frontmatter,
or none that names seats, answers on the panel's own two seats (`seats_from: default`, named
`opus` and `sol`), as in step 2. The frontmatter is not a part of the person: a persona's agent
reads `person`, the path `lem cast` prints for the file without it. A seat that the settings would
refuse stops `lem cast` with the file and the line to write.

One more cast exists, and it answers no panel: the built-in one in this skill's `cast/` (a person
who uses the product, the engineer who runs it, the engineer who builds the next change on it and
the owner who pays for it). `lem cast init` copies it into the project's personas folder, as files
to rewrite, when the owner asks to set up personas for a project.

A panel brings only the people the question affects, never the whole cast by default. Pick them
before writing the brief: a persona is in when some option changes what that person sees, does or
answers for, and the brief says in one line why each one is there. A question about the storefront order brings the shopper and the merchant; one
about an alert brings the engineer on call; a technical fork brings the engineer who runs the
system and the one who builds the next change on it; the CEO comes in when the options differ in cost to
the company or in how they would be defended to shoppers and merchants. Two is the floor: with one
persona there is no second view to disagree. Add a question-specific persona in the brief when the
question turns on someone the files do not cover, such as a shopper in a market whose language or
currency matters to the answer. Write it as a short paragraph in the same shape as the files: who
they are, what they want, what they notice, what they never see.

## Steps

The panel's files live in one directory, `PANEL_DIR`: the folder
`lem cast run-dir <slug>` makes and prints,
`panels/<YYYY-MM-DD>-<slug>/` in Lem's state folder (`.lem/state/` of the main checkout), which
git never shows. A `codex exec` seat writes its answer there through `-o`. A paired Codex writes
the Sol answers there itself, so its sandbox has to reach the main checkout: one started in another
worktree may not, and then it replies with what stopped it, as the "Sol panel" message asks.

### 1. Evidence first

Write `PANEL_DIR/brief.md` before anyone answers. It holds:

- **The question in user terms.** Not "how many ticks", but "how much broader must a demoted
  shop's page be before it still shows above an approved one".
- **For each option, what a person would actually see.** Real output wherever it can be had: the
  listing a query returns on the test stack under each option, the page a merchant would see, the
  alert the engineer would get. Where no stack can show it, a worked example written as the page:
  shops, products, prices and positions, never scores. In mybaze, a shared test stack is used by
  one session at a time; ask the session holding it over SendMessage before you use it.
- **The personas taking part**, as file paths, each with one line on why the question affects
  them, plus any question-specific persona in full.

Then write `PANEL_DIR/facts.md`, which no persona reads: each fact an option turns on that a source
outside the project can confirm or refute, with where it would be published. Such a fact is a
tool's documented behavior or limit at the version the profile names (a replication slot's
retention, a stream's delivery guarantee, a search engine's partial-update rule), a published
postmortem of the same design, a change after the model's training, or, for a question about what
outside people see, a competitor's or a standard's public page. Write "none" when the question
turns on taste, size, scope, approval or a product fact only the project holds: no search settles
those, and most held questions are of that kind.

The brief is neutral: no recommendation, no option marked as the expected one, no internal names
a persona would not know. Both model families read the same brief, so any lean in it reaches both
and the panel stops measuring anything.

Writing for a persona turns a qualified fact into a plain one, so two kinds of sentence are
checked as they are written. A sentence with "never", "nothing", "always", "the same" or "cannot"
gets its counterexample looked for first. An example table comes from the project's own functions
or its data model: a formula copied into a one-off script once gave a page more distinct sizes
than offers, which one size per offer row rules out.

**The brief is checked before any persona reads it.** Send the paired Codex the "Brief check"
message from `references/messages.md` and wait for its reply: which sentences of `brief.md` are
false against the code, the project's rulings and the corrections already accepted in this run.
Fix the brief for every point that holds. The challenge in step 4 reads the card, not the brief,
so it comes after the answers. In a read of 29 mybaze panels (2026-11-12 and 13), 20 briefs held a
false sentence that the personas read, none of those briefs was checked before they answered, and
11 of the errors reached the owner's page. Without Codex, a fresh Opus subagent checks the brief
with the same message, and the card says so.

A brief fixed after the personas answered means they answer again. When the fix touches a sentence
an answer gives as its reason, run step 2 again on the fixed brief, or the card names the answers
that rest on the false sentence.

### 2. Each persona answers on each of its seats, independently, and the scout searches

After the brief check, start every seat of every persona and the scout at once, then end the turn;
the answers wake you. A persona's agent reads its `person` path as `PERSONA_FILE`. A seat in
`left_out` does not run (its agent, Codex, is not on this machine), and the card says so in the
words below for a panel without Codex. A persona with every seat left out gives no answer, and the
card's persona line names it.

A persona whose `seats_from` is `default` answers twice, on Opus and on Sol:

- **Opus.** One subagent per persona, all in one message so they run in parallel:
  `subagent_type: "general-purpose"`, `model: "opus"`, `run_in_background: true`, with the
  "Opus persona" prompt from `references/messages.md`. Save each reply verbatim to
  `PANEL_DIR/answers/<persona>.opus.md`.
- **Sol.** One mailbox message to the paired Codex (the `mailbox-chat` skill), the "Sol panel"
  message from `references/messages.md`. Codex spawns one `persona` subagent per persona (the
  agent defined in `~/.codex/agents/persona.toml`: `gpt-6.1-sol` at high, read-only), saves each
  reply verbatim to `PANEL_DIR/answers/<persona>.sol.md`, and replies with the paths. Codex caps
  the agents open at once (four including itself on Codex 0.167, so three persona slots), so the
  message asks for batches no larger than its free slots. The
  subagents' replies pass through Codex's own context; in a careful task that is the
  reviewer's, so a panel waits for the next clear boundary when it can, and otherwise the review
  that follows is read knowing Codex saw the answers.

A persona whose file names its seats answers once on each of them, with the "Opus persona" prompt,
and each answer goes to `PANEL_DIR/answers/<persona>.<name>.md`, by the seat's `name`. Each seat
starts the way the harness starts an expert (`ask-experts` in the `lem` skill's harness file), and
never with a model or an effort the seat does not name:

- **A `claude` seat**: a subagent in the same message as the others, `subagent_type:
  "general-purpose"`, `model` the seat's model, `effort` the seat's effort, each only when the seat
  names it, `run_in_background: true`. Save its reply verbatim to the answer file.
- **A `codex` seat**: write the filled prompt to `PANEL_DIR/prompts/<persona>.<name>.md`, then the
  `Bash` tool with `run_in_background`, `-m MODEL` and `-c model_reasoning_effort=EFFORT` only when
  the seat names them, and the checkout as `REPO`:

  ```bash
  codex exec -m MODEL -c model_reasoning_effort=EFFORT -s read-only --skip-git-repo-check --ephemeral -C REPO -o PANEL_DIR/answers/PERSONA.NAME.md - < PANEL_DIR/prompts/PERSONA.NAME.md > PANEL_DIR/prompts/PERSONA.NAME.log 2>&1
  ```

  It needs no paired Codex, so it runs in a lead's ladder too.

- **The practice scout**, only when `facts.md` names at least one fact. One more Opus subagent
  in the same message, `subagent_type: "general-purpose"`, `model: "opus"`,
  `run_in_background: true`, with the "Practice scout" prompt. It checks each named fact on the
  web and writes `PANEL_DIR/practice.md`: each fact confirmed, contradicted or not found, with the
  quoted sentence, its link, date and the version it applies to. It never reports what a team
  "probably" does and never states a belief of its own as a finding: the personas who run and build
  the system already bring what a capable model knows, in two model families. Without a working web
  search, it writes "not searched" and why. It runs on question panels only, not on reads of acceptance criteria or
  reviews.

  A competitor rarely publishes how it builds things, so a search for "what teams like ours do"
  returns little, and what it does return comes from much larger companies whose answer fits their
  size. On a mybaze outbox question (2026-11-13) a review found one competitor engineering blog, its
  newest post from 2021. So the scout checks named facts, not practice in general.

The personas never read `facts.md` or `practice.md`, and the brief never quotes them: a persona
that has read another team's choice can only repeat it, and its vote stops being a second view.
Only the moderator and the challenger read them.

If the paired Codex is unavailable, the default seats run on Opus alone and the card says so on its
persona line: "one model family only; agreement between families unmeasured". It never runs Sol
one-shot instead. The same words go on the card when every answer that came in is from one agent,
`claude` or `codex`: a persona's own seats on one agent, or its `codex` seats left out.

### 3. The moderator writes the card

A fresh Opus subagent, with the "Moderator" prompt from `references/messages.md`, reads the
profile, the brief, every answer, `facts.md` and the scout's `practice.md`, and writes `PANEL_DIR/card.md` in
the format below. It did not take part, so it
has no answer of its own to defend. A recommendation is never "the smaller change" on size alone;
it says what the option costs a user.

### 4. The challenger

Send the card to the paired Codex with the "Challenge" message: Codex, the other model family from
the Opus moderator, argues why the recommendation is wrong. Where it can open web pages, it also
checks that each link in `practice.md` says what the card claims; where it cannot (Codex's sandbox
may have no network), it says so, and the card's "What was checked" line adds "links not checked
again". Hold the exchange under the "Pair
sessions" rules of `~/.agents/AGENTS.md`: each turn brings a refutation, a cite or a changed
position, and a turn that only repeats the one before it ends the exchange. Update the card for
every point you accept; the strongest point that survives is the card's "strongest dissent".
Without Codex, a fresh Opus subagent challenges instead, and the card says so.

### 5. The framing check

Ask Jev whether the card is framed for the user, with the "Framing check" spec from
`references/messages.md` through `lem-jev`, the command Lem's plugin puts on PATH. On "not
framed", send the moderator Jev's verdict and the spec's criteria, once, and check again: the
verdict is one answer for the whole card and names no criterion, so the moderator reads the card
against each. A card that still fails goes to the user with the check's result on it, never
silently.

### 6. Ask the user

Put the card to the user. In agterm: the `lem-ask` skill, the options carrying their "what you
would see" text, the recommendation marked with the reason that names what backs it, and the
checked facts in the page's context with their links; elsewhere as plain text, which also reads on a
phone. A card with "No clear pick" marks no option recommended: the badge appears only when the
card says what backs it. No option is preselected.

The page opens with the panel's answers, above the case: a table with one row per persona (who
they are, why the question affects them, what each model family picked) and one line on where they
agree and where they split. The full card goes below. A card placed as the second block under a
five-step case was not seen: the owner typed "Consult this with personas first" on a page that
held it (mybaze, 2026-11-12).

Record the answer in `PANEL_DIR/answer.md`.

## In the ladder

A lead's level 2 of a decision in doubt (`stages/ladder.md` in the `lem` skill): steps 1 and 2 of
a question, and nothing after them. The brief holds the options and their evidence and no pick
of the lead's. Each persona answers once, so that each is one vote: a persona of the default seats
on Opus, since a lead has no paired Codex, and a persona with its own seats on the first of its
`seats`. No moderator, no card and no
framing check: give the lead each answer's last lines as they are, the option the persona wants
and how sure, and the lead counts them. An answer with no option it wants, or that says the
question does not affect that person, is no vote, and it stops the count: it is never dropped.

## Reading acceptance criteria

The panel's second job is reading a plan's acceptance criteria, where it writes no card. Each
criterion is a short run through a change as one person sees it, and the people it names judge
whether it reads right to them before the user approves it.

1. Write `PANEL_DIR/criteria.md`: each criterion, numbered as in the plan, without its `Test:`
   block, and for each the personas it concerns: the actor it names, plus anyone else an option
   of it changes something for. Two personas per criterion is the floor, as for a question.
2. Run each persona on each of its seats, as in step 2 above, with the "Criteria read"
   prompts from `references/messages.md`, saving the answers as
   `PANEL_DIR/answers/<persona>.criteria.<name>.md` (`.criteria.opus.md` and `.criteria.sol.md`
   on the default seats). Each one answers every
   criterion it concerns: is the outcome
   what they would expect, and is anything confusing, missing or wrong for them?
3. A criterion is **flagged** when any answer says it is unexpected, confusing or wrong. Write
   `PANEL_DIR/criteria-read.md`: the flagged criteria first, each with the answers that flagged
   it, quoted, then one line naming the criteria nobody flagged, then the layer and source the
   cast came from.

The caller puts the flagged criteria in front of the user first, with those answers beside them.
The panel never rewrites a criterion; the user and the agent who drafted it do.

## Reviewing

The panel's third job is reading any artifact as the people it affects: a backlog item, a plan
section, a document, a PR body, the copy a page shows. It asks no question and writes no card; the
review informs whoever acts next, and a decision that follows from it still goes through a card.

1. Write `PANEL_DIR/brief.md`, the only thing a persona reads: the artifact restated in user terms,
   what it changes or leaves broken for a person, and the outcomes on the table, then the personas
   taking part, as paths, each with one line on why the artifact touches them; two is the floor,
   as for a question. The brief stays neutral: no expected verdict and no internal names a persona
   would not know. So an artifact that carries a recommendation, code paths or internal terms (a
   backlog item's `where:` and "Recommendation:", a plan task) is restated, never pasted or cited
   by path. Text a person would meet as written, such as page copy or a notice, is quoted whole.
   When the artifact is internal, the brief says what a person would meet because of it: what they
   would see, when, and how often.
2. Run each persona on each of its seats, as in step 2 of a question, with the "Review"
   prompts from `references/messages.md`, saving `PANEL_DIR/answers/<persona>.<name>.md`.
3. A fresh Opus subagent with the "Review moderator" prompt reads the brief and every answer and
   writes `PANEL_DIR/review.md`:
   - **What it is**, in user terms, one or two sentences.
   - **Each persona**: what they would notice, how much it matters to them (stops them, costs them
     something, annoys them, or goes unnoticed), and the outcome they would want.
   - **Where they agree**, and **where they split**, between personas or between the two answers
     of one persona, which means the panel is unsure there.
   - **What would change the read**: the fact that, if true, would move the verdict most.
   - **The cast**: the layer and source it came from, "one model family only" when every answer
     came from one agent, and "no project profile" when there is none.

The caller reports the review with the artifact it was about, and may offer to fold what the
review changed into it; the panel never edits the artifact itself.

## The card

A card carries, in this order:

1. **The question**, in user terms, one sentence.
2. **Each option as what the people it affects would see**, a short paragraph each, from the
   evidence.
3. **The recommendation**, what it costs a user, and what backs it: how many personas want it in
   each model family. A checked fact never earns the badge by itself: a contradicted fact can rule
   an option out, and a confirmed one only supports a persona's reason. When the personas split
   with no clear side, **No clear pick**, and what each side rests on.
4. **The strongest dissent**: the best case against the recommendation that survived the
   challenge.
5. **Wrong if**: the fact that, if true, would flip the recommendation.
6. **Undo**: whether the choice can be reversed later, and what reversing costs.
7. **What was checked**: each fact the recommendation rests on, marked confirmed or contradicted
   with its link, or not found; then, marked "known, not checked", what the recommendation rests on
   that only the answers assert. Or "no fact needed a search", or "practice not searched" and why.
8. **The personas**, one line: what they said, with any split between personas or between the two
   model families, the layer and source the cast came from, and "no project profile" when there is
   none.

No internal units on the card: no scores, ticks, priors, levels or flags. When a number matters,
say it as a person would meet it ("about one more size on the page").

The user is not in the cast, and still pays for every page. An option that asks for another round
(test again, measure once more) names the miss it aims at and why a change can reach that miss,
and its cost says that the user reads one more page; "it varies from run to run" is not a cause.
When every option ends with nobody worse off than today, there is no question: the card
recommends the option that ships and lists the misses for a later fix. One mybaze question went to
the owner four times in about two hours (2026-11-11); the fourth card recommended a fifth test for
a miss the session itself had called ordinary variation.
