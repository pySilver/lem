# The shape of decisions.md

The template of `decisions.md`, the file of the decisions that a task took and why. `land.py propose`
writes it into the task's folder from `decisions.jsonl`, beside `built.md`, and commits neither. A
small change gets no such file. Each part below is the text it writes, then one note: where the
content comes from, and what to leave out. `{{...}}` is a value; `[...]` is a part that is written
only when its condition holds. Records named "(new)" do not exist today; `notes.md` says what each
must hold.

One decision is all the lines of `decisions.jsonl` with one `id`, as `lem decisions list` gives it.
The file holds every decision of the task that is not a criterion change (`kind: criterion`, which
`built.md` and the pull request show). A decision that a later one replaced is no item of its own: it
is "the other option" of the one that replaced it, with the words "Lem took this option first".

---

```markdown
[{{ILLUSTRATION LINE}}]

# Decisions: {{TITLE}}
```

Note: as in `built.md`. Leave out: the slug.

```markdown
[> [!CAUTION]
> ... ]
```

Note: the red block of `built.md`, word for word, with the decision's number added to the items that
are decisions. Not written when nothing waits.

```markdown
Pull request [#{{PR}}]({{PR URL}}). {{N}} decisions. {{WHO TOOK HOW MANY, IN ONE SENTENCE}}. The ones that you most likely want to change come first.
```

Note: `landing.json` `pr`; the counts by `by` (new: by `level`). Leave out: the times of the
decisions.

```markdown
| # | The question | What was taken | Who decided |
| --- | --- | --- | --- |
| {{N}} | {{QUESTION}} | {{TAKEN, SHORT}} | {{WHO}}[; **check this one**] |
```

Note: one row for each decision, in the order below. "Who decided" is the plain word of the table
under this block, in bold for "waits for you" and "nobody agreed". Leave out: the reason, which is in
the item.

The order, most likely to be changed first:
1. waits for you: `kind: asked` with no `answered` line (an irreversible step, or a card in the wait);
2. nobody agreed (`level: none`, new; today `by: timeout`);
3. two expert models (`level: experts`, new; today `by: experts`);
4. a for-and-against test (`level: dialectic`, new);
5. the personas (`level: personas`, new; today `by: personas`);
6. the task's agent or Lem alone (`by: lead` or `by: lem`), with "check this one" first among them;
7. your ruling (`level: gate`, new, with the ruling's file);
8. you (`by: owner`, or an `answered` line).
Inside one class: a decision that changed a criterion (a `criterion` line names its `choice`) first,
then the order of `id`.

"Who decided", in plain words, from the record's key:

| Record | Plain words |
| --- | --- |
| `kind: asked`, not answered | waits for you |
| `level: none` (today `by: timeout`) | nobody agreed: the task's agent's pick stands |
| `level: experts` (today `by: experts`) | two expert models, with their names from `seats.experts` |
| `level: dialectic` (new) | a for-and-against test |
| `level: personas`, `by: personas` | the personas, with the count from `said` |
| `level: gate` (new) | your ruling of {{DATE}} in `{{FILE}}` |
| `by: lead` | the task's agent |
| `by: lem` | an agent (Lem, or the agent whose pick Lem took, when `why` names it) |
| `by: owner`, `answered` | you |

```markdown
## {{N}}. {{THE QUESTION, AS A QUESTION}}

[**Waits for you.** {{WHY NO AGENT TAKES IT, ONE SENTENCE}}]
[**Not green. Check this one.** Nobody agreed, so the pick of the task's agent stands.]
[**Check this one.** {{WHY, ONE SENTENCE}}]
```

Note: the question is `what`, rewritten as a question (`what` today is a noun phrase, "the heading
form of a range ..."). The first flag from `irreversible` (its kind in words: "a later no cannot take
back an email" for `person`); the second from `level: none`; the third when one agent alone took a
choice that sets the text of a criterion (`undo` names a criterion or a test's expected text, or a
`criterion` line names the choice) and nobody else read it. Leave out: a flag on any other decision.

```markdown
- **Taken:** {{CHOSE}}
- **The other option(s):** {{EACH OPTION THAT WAS NOT TAKEN}}
- **Who decided:** {{WHO}}[. Your words: "{{HIS WORDS}}"]
- **Why:** {{ONE OR TWO SENTENCES}}
[- **How it went:** {{EACH LEVEL THAT DID NOT SETTLE IT, AND WHAT IT SAID}}]
[- **What followed:** {{ONE SENTENCE}}]
- **To change it:** {{THE WORDS HE SAYS, AND WHAT AN AGENT THEN CHANGES}}
```

Note, line by line:
- Taken: `chose`; for a decision that waits, the line is "The options:" with each `options` item and
  "(recommended)" after `recommended`, and the "Taken" line is left out.
- The other options: `options` minus `chose` (only `kind: asked` has `options` today; a `taken` line
  needs a new key `options`). Each with its effect when the record holds one. Leave out: an option no
  record names; never invent one.
- Who decided: the table above. His words from `owner_words`, `words`, or for `by: owner` the `why`
  (today his words land in `why`).
- Why: `why` of the level that settled it: the ruling's sentence for the gate, the experts' shared
  reason (`experts.fable`, `experts.astra`), the side that held for the dialectic, the personas'
  `said`. For "waits for you", the reason of the recommendation. Leave out: the reasons of the levels
  that did not settle it, which "How it went" holds.
- How it went: the levels below the one that settled it, one item each, with the vote or the result
  (new: plan task 3's log of each level). Left out when the first level settled it.
- What followed: only for a choice whose result the owner cannot see in the diff (a conflict it
  caused, a task it held). From `state.md` and `landing.json` `sync`.
- To change it: `undo`, rewritten as the words he says to Lem and what an agent then changes; "nothing
  to change now" when the result is merged or obsolete; for a ruling, "change the ruling first".
