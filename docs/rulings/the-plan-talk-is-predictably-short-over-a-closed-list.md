---
ruled: 2026-11-16
area: The plan, the build and the tests
---

# The plan talk is predictably short, over a closed list

Decisions the owner took on 2026-11-14. Each is reopened only by asking him. A quote is his words.

**The plan talk is predictably short, over a closed list**: he asked "What makes it
predictably short? I don't want them to argue till the end of days. What happens if its a
design issue that causes endless corrections?", and on a Fable second opinion that proposed a
closed list and one repair per position, "Fable idea is good. Actually we should borrow the
idea from revmux which uses the closed list (revmux is weak for plans as I recall)"
(2026-11-16). The form is Fable's proposal, which he approved, with revmux's rule that a
finding which comes back stops the loop: the reviewer's first turn is the whole list; each
question gets one repair; a question that holds a second time is a design choice, asked and
never settled by an edit; a question after the first turn is "raised, not argued", and the
review before the pull request checks it; a scope the plan puts out of the change is no
question. `stages/talk.md` holds the rules, and `project.py`'s `plan.talk` the counts, with
the bound of 4 × questions + 2 turns, which is derived and not measured.
