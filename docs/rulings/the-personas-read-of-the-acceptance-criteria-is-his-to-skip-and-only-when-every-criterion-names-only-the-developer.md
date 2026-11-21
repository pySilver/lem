---
ruled: 2026-11-16
area: The interview, the criteria and the personas
---

# The personas' read of the acceptance criteria is his to skip, and only when every criterion names only the developer

## Changed in part

The title is the rule as it stands. Where the paragraph below says otherwise, the line here holds.

- 2026-11-17, [A complete ticket that someone else wrote needs his yes to its criteria, and no interview](a-complete-ticket-that-someone-else-wrote-needs-his-yes-to-its-criteria-and-no-interview.md): "for a full change from a complete request the read is the only approval and always runs": the read still always runs, and it is the only approval of a complete request he wrote himself; a complete request that someone else wrote needs his yes to the criteria after the read (`stages/plan.md`, step 1)

## As ruled on 2026-11-16, changed in part since

His ruling of 2026-11-16. It is reopened only by asking him. A quote is his words.

**The personas' read of the acceptance criteria is his to skip, and only when every criterion
names only the developer**: he asked whether the read should be optional ("In some cases the owner has all the
knowledge that is needed for task, so personas read would be a pure waste of time and money"),
and answered "I agree" (2026-11-16) to the proposal a Fable second opinion shaped. A criterion that
names a person other than the developer gets the read, and Lem asks nothing. When every
criterion names only the developer, Lem asks one fixed question in the terminal, "The acceptance
criteria name only you. Skip the persona read? (y/n)". Lem never skips the read by its own
judgment: it wrote the criteria, and the author of a wrong reading sees it as clear. On his yes
Lem logs his words and he approves the criteria, and the pull request stays green, because the decision was his. A full
change with an interview only: for a full change from a complete request the read is the only
approval and always runs. The form is
the session's design: his word is the decision `decisions.py log SLUG --by owner --what "the
personas' read of the criteria" --chose "no read: the criteria name only the developer"`, with his
answer in `--why`; `land.py` (`READ_SKIP`) takes a full change with no `criteria.read` only when an
approval of his follows that decision and both come before the first state that names a lead
(`lead: builder` or `lead: session`), which is how the script tells an interview from a
complete request, and its checks then say "the criteria: not read by the personas, on his word (DATE); he
approved them".
