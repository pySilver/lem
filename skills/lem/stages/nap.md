# nap

A nap is an optional part of Lem, and the owner's own nap routine is its model. A fresh agent reads
the recent tasks in the state folder and what Lem made of the owner's corrections, sleeps, dreams,
and writes the dream down, makes one thing from it, and leaves a short waking note. It is Lem's time
off the task: an agent writes a lesson in the moment, without knowing which of them will matter,
and only a look back over the days can hold a lesson against what happened after it ("The
components of agent memory", Anthropic, 2026-11-06, which the owner named as the reason for the
naps on 2026-11-21). The nap is that look in its lightest form: it changes no lesson itself, and a
retro takes from its waking note only what the records bear out (`stages/learn.md`). Lem has not
measured what the naps give. So a nap costs the owner nothing but the agent's minutes: it never
holds a task, a question or him.

A task's session starts a nap by itself, never through a scheduled job and never on a word of the
owner's: when its task ended, before the session closes (`stages/land.md`, step 9), and the
settings' `naps.on` is true.

1. **May one start?**

   ```bash
   lem nap may
   ```

   Its result holds `may` with its `why`, and it writes the nap down as started when it says yes.
   A no is the usual answer: say nothing of it.
2. **Start it** with `start-nap`, with the `time` of that answer and the folder `lem path state`
   prints. Its brief is `prompts/nap.md`, whole and unchanged: it is written to the nap
   the way the owner's routine is written to his, and a line of Lem's added to it turns a dream
   into a report. Nothing waits for the nap but the close of the session, which would end it.
3. **When it ends**, do nothing with it. No page shows it: the retro reads its waking note
   (`stages/learn.md`). Lem does not read a dream, and acts on none.

What is Lem's and not the routine's: the nap's files stay in its own folder under `naps/` in the
state folder, which git never sees; nothing in the repository changes and nothing is committed;
the nap reads only this repository's records, never another repository's and never the session
files of the home directory. `start-nap` gives it no tool that runs a command, and file tools that
reach only the state folder.
