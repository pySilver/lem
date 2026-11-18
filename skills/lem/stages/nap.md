# nap

A nap is an optional part of Lem, and the owner's own nap routine is its model. A fresh agent reads
the recent tasks in the state folder, sleeps, dreams, and writes the dream down, makes one thing
from it, and leaves a short waking note. It is there for the pleasure of reading it, and for what
a retro may find in a waking note (`stages/learn.md`); nobody has shown that it helps. So it costs
the owner nothing but the agent's minutes: it never holds a task, a question or him.

Lem starts a nap by itself, never through a scheduled job and never on a word of the owner's: at
the moment "The queue" of `stages/start.md` names at its end, when a task ended or nothing is left
for Lem but the owner's word, and the settings' `naps.on` is true.

1. **May one start?**

   ```bash
   lem project may-nap
   ```

   It answers in JSON, `may` with its `why`, and writes the nap down as started when it says yes.
   It also removes the naps older than `naps.keep_days`. A no is the usual answer: say nothing of
   it.
2. **Start it** with `start-nap`, with the `time` of that answer and the folder `lem project
   state-dir` prints. Its brief is `prompts/nap.md`, whole and unchanged: it is written to the nap
   the way the owner's routine is written to his, and a line of Lem's added to it turns a dream
   into a report. Then go on at once with what you were doing; nothing waits for the nap.
3. **When it ends**, do nothing with it. No page shows it: the retro reads its waking note
   (`stages/learn.md`). Lem does not read a dream, and acts on none.

What is Lem's and not the routine's: the nap's files stay in its own folder under `naps/` in the
state folder, which git never sees; nothing in the repository changes and nothing is committed;
the nap reads only this repository's records, never another repository's and never the session
files of the home directory. `start-nap` gives it no tool that runs a command, and file tools that
reach only the state folder.
