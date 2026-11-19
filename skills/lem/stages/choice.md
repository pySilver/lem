# When a choice waits for the owner

A choice comes here when a lead's ladder (`stages/ladder.md`) went past the personas while he is
there, and for a step that a later "no" cannot reverse in either case. The lead, or the defender
of a plan talk, tells you at once with the line `lem: SLUG choice N waits`, through
`tell-coordinator`: the defender from its companion, and a builder that leads from this session,
where it runs. That line is the wake-up. A line can be lost (a pane that restarted, a brief with
no `coordinator:` line), and the harness file says that the builder's line was not yet seen to
wake an idle Lem, so `lem companion due` at each of your turns (`SKILL.md`) is what finds a
choice that waits: it reads `lem decisions pending`. At the same turns, run `lem land merged SLUG` for each `open` task with a
pull request, as `SKILL.md` says under Status: a merge he made on the forge frees the queue and
brings a pull request it made conflicting onto the new base (`stages/land.md`, step 9). A task
that was dropped or landed while a choice waited is under `ended`, and its choices need no answer.

**Open its companion**, and show no card in your own session:

```bash
lem companion open SLUG --need choice --choice N
```

It opens `SLUG · choice N` under this session, with no focus, and prints `say`: say that line as
it is, and go back to his next message. Two choices are two companions, also of two tasks. The
companion shows the card of step 1 at once, answers what he asks about it there ("what do the
experts say?") from the choice's record, and writes his answer as step 2 says; then it tells you
`lem: SLUG choice N answered` and closes. While he is away `open` refuses: his "away" took every
choice that is no irreversible step, and an irreversible one opens at `/lem im-back`.

1. **The card**, which the companion shows through `ask-owner` in its own session.
   Above the card, the run: the choice's `case` in its numbered steps, whether it was
   reproduced or derived (`case_was`), and its `cause` line. On the card's top what each level of
   the ladder answered (`said`), and the experts' answers when the record holds them (`advice`),
   with the experts named in a few words from the settings' `seats.experts`; then what the choice
   is, the options, and the ladder's pick (`recommended`) with its reason. The choice waits for his
   answer with no time limit, and the rest of the task goes on; say so, and that his "away", typed
   in any repository on this machine, takes the ladder's pick and the pull request is then not
   green for it. Say too how it opens again
   when he closes the card with no answer: its row in the board's "Waits for you", or `/lem` in
   Lem's session, by the name the sidebar shows; such a close takes nothing, and the choice still
   waits. The levels ran before the card, so none runs again here, unless he asks for all
   opinions: the levels that did not run then run as `stages/ladder.md` says under "All
   opinions", and their answers come onto his card. A choice with `irreversible`
   set waits also while he is away: say which of the four kinds it is, and that only that part of
   the plan waits for his word.
2. **Write his answer**: `lem decisions answer SLUG N --chose OPTION --words TEXT`. `--chose` is
   the option his answer takes, word for word as the choice has it; the script refuses any
   other text. `--words` is his answer as he gave it, when it is not that text, and `--why`
   his reason, when he gave one, in his words. Never put the recommendation's reason there:
   the record keeps that one beside it. When he decided something that none of the options
   says, settle the choice with it: `lem decisions answer SLUG N --instead TEXT`, with `--words`
   and `--why` as above. Never log it as a new decision: the choice would wait for ever, and an
   irreversible one would hold the pull request. A choice carries no criterion: a criterion his
   answer changes is the lead's to record with `lem decisions criterion ... --choice N`, and the checks
   refuses the plan until it does. When you cannot tell what he decided, ask him again. When
   `lem: SLUG choice N answered` reaches you, a defender's companion gets the answer from you as
   one message; a builder that leads finds it at its next `lem decisions wait`; and a lead that
   stopped `held` for it starts again when `lem companion due` gives the task under `start`.
3. **An answer after the choice was taken** (his "away" took it, or the task ran without him)
   is written down the same way, and the script says it is late: what was taken stands. When
   the answer differs from it, it is his correction: tell the lead while the task builds, and
   after that it is a new ask. The pull request names it either way.
4. **When he leaves or comes back** (`/lem im-away`, `/lem im-back`), here or in another
   repository on this machine, where only the end of the watch of his mark tells you:
   `stages/away.md`.
