# When a choice waits for the owner

Every decision that is the owner's comes here, at plan time and in the build: a lead that meets
one, in its plan or in a task of it, has the personas read it and asks it with `lem decisions
ask` when they leave it unclear, and the task goes on without it (`stages/plan.md`, step 5, and
`stages/build.md`, "A choice in the build"). The defender of a plan talk asks the choices the
talk left open the same way. Either lead tells you at once with the
line `lem: SLUG choice N waits`, through `tell-coordinator`: the defender from its companion,
and a builder that leads from this session, where it runs. That line is the wake-up, and the
wait counts from the ask. A line can be lost (a pane that restarted, a brief with no
`coordinator:` line), and the harness file says that the builder's line was not yet seen to
wake an idle Lem, so also run `lem decisions pending` at each of your
turns: its `waiting` list is what needs his answer. At the same turns, run `lem land merged SLUG`
for each `open` task with a pull request, as `SKILL.md` says under Status: a merge he made on
the forge frees the queue and brings a pull request it made conflicting onto the new base
(`stages/land.md`, step 9). A task that was dropped or landed while a choice waited is under `ended`, and
its choices need no answer.

1. **Ask him at once**, through `ask-owner`.
   Above the card, the run: the choice's `case` in its numbered steps, whether it was
   reproduced or derived (`case_was`), and its `cause` line. On the card's top the two experts'
   answers (`advice`: each one's pick, or that none fits, with its reasons) beside the personas'
   (`said`), then what the choice is, the options, the recommended one with its reason, and the
   time the wait ends, in his clock (`deadline` is in UTC). The lead ran the persona panel
   (`lem-panel`) before the ask, so it is not run again here. After that time the lead takes the option both experts
   picked (`experts_pick`), or the recommended one when they split, and the pull request is not
   green for it either way: say which of the two it will be. A choice with `irreversible` set has
   no such time: say which of the four kinds it is, that the experts' answers are advice only,
   and that only that part of the plan waits for his word.
   The lead gives each choice to the experts (the `lem-ask-expert` skill) right after its ask, and
   their answers take some seconds to minutes. When `advice` is not complete yet, say on the card
   that the experts were asked; the lead sends `lem: SLUG choice N advised` when both answers
   are in, and then you tell him both in one short message. When the task's
   directory has no `experts/choice-N.brief.md`, nobody gave the choice to them: run the
   `lem-ask-expert` skill yourself, at once.
2. **Write his answer**: `lem decisions answer SLUG N --chose OPTION --words TEXT`. `--chose` is
   the option his answer takes, word for word as the choice has it; the script refuses any
   other text. `--words` is his answer as he gave it, when it is not that text, and `--why`
   his reason, when he gave one, in his words. Never put the recommendation's reason there:
   the record keeps that one beside it. When he decided something that none of the options
   says, settle the choice with it: `lem decisions answer SLUG N --instead TEXT`, with `--words`
   and `--why` as above. Never log it as a new decision: the choice would wait for ever, and an
   irreversible one would hold the pull request. A choice carries no criterion: a criterion his
   answer changes is the lead's to record with `lem decisions criterion ... --choice N`, and the checks
   refuses the plan until it does. When you cannot tell what he decided, ask him again. A lead in a
   session gets the answer as one message too; a builder that leads finds it at its next
   `lem decisions wait`.
3. **An answer after the wait** is written down the same way, and the script says it is late,
   also when nobody wrote the timeout yet: it writes the timeout then, and what the timeout
   takes stands. When the answer differs from what was taken, it is his correction: tell the
   lead while the task builds, and after that it is a new ask. The pull request names it either
   way. An answer after the experts settled the choice is late in the same way.
4. **When he is away**, the choice does not wait its time for him: once both experts picked the
   same option, `lem decisions settle SLUG N --away` takes it at once, and the pull request is not
   green for it. He is away on two facts only, as the harness file's `ask-owner` says: his own
   words in this session that he is away or leaves, or a question of this turn that went to his
   away channel. His silence is no such fact. The script refuses when the experts split, when
   one has not answered, after the wait ended (the timeout takes it then) and always for an
   irreversible step; a choice it refuses waits its time. A defender whose companion is open
   gets one message with the option taken; a builder that leads finds it at its next
   `lem decisions wait`. Tell him at
   his return what was taken for him and the experts' reasons.
