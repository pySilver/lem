---
decided: 2026-11-21
area: The review, the pull request and the merge
---

# The board's server runs the merge agent's merge, and the agent only writes its review

On 2026-11-16 the owner gave the design to the session that builds Lem: "You are the owner and
long-term maintainer of this codebase, and its design is up to you. Pick recommended action if
you still see it as best oucome." Two reviews of Lem, by Codex and by Fable, had left the points
below open, and that session decided each under his sentence. None of them is his ruling: each
is the session's, and open to him.

The final round of 2026-11-17 took the decisions below, after two real runs of the plugin form in a
scratch repository (R1 to R6) and the final audit of `636b24c` (A1 to A15).

**The board's server runs the merge agent's merge, and the agent only writes its review**
(2026-11-21). The first real task (pySilver/lem-scratch#12) showed it: the merge agent's review
said `Verdict: merge.`, the task's session ran `lem land merge SLUG --by merger`, Claude Code's
auto mode blocked that one Bash call ("1 action blocked by auto mode"), and the pull request
stayed open until the owner opened a second session from his phone, which ran the same command
unblocked. A block that holds in one session and not in the next is no step to rest the flow on.
So the session writes the review down (`lem land merge-review SLUG --file ANSWER`), says one line
and waits, and the server's duty runs `lem land merge SLUG --by merger --via server` in a thread,
as it runs the owner's merge from the board; land.py's rules stay the gate, `merge.start` and
`merged_by` say who merged and who ran the call, and a refusal of that merge, GitHub's or Lem's
own (the base moved, the tip changed), is kept for its tip, so that the server tries the tip once
and wakes the session with `lem: SLUG refused`. The script still takes `--by merger` from an
agent; no text tells one to run it. The same task showed a live session called dead: agterm's
tree gives a task's session as the login shell with the agent inside its `-c` string, and
`agent_runs` read only the first two words, so the board said "No session runs this task" and
the owner opened a second session beside the live one; it now reads the `-c` string as a shell
would.
