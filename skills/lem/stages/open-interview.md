# The interview's companion

The standard track with an interview, after step 6 of "Open the task" (`stages/new.md`), and each
other path that comes to an interview (a fix whose investigation calls it `full`, a fast-track
task that takes the standard track). The interview runs in a companion of this session: a fresh
agent that reads the task's files and knows no other task (`prompts/companion.md`), starts the
scout, asks him the questions, has the personas read the criteria and takes his yes, as
`stages/interview.md` says.
This session never runs the interview while he is there.

1. **Copy the talk.** The companion is no fork of this conversation, so the turns that led to the
   ask go to it as a file:

   ```bash
   lem companion talk SLUG --from "THE FIRST WORDS OF HIS TURN WHERE THE TOPIC BEGAN"
   ```

   The turn is the one where he began to speak of this ask, also when the `/lem` line came later;
   type its first words as he typed them, a `/lem` line as it is. Add one `--leave "FIRST WORDS"`
   for each turn of his in between that is another topic: it is left out with your answers to
   it. The command copies the turns word for word from this session's own transcript into
   `talk.md` in the task directory, also those from before a compaction, and refuses with the fix
   when no turn of his starts with those words.
2. **Open it**: `lem companion open SLUG --need interview`. It opens `SLUG · interview` under this
   session, with no focus, and prints `say`: say that line as it is ("the interview of SLUG is
   open in `SLUG · interview` under this session"), and nothing more. When it refuses, its message
   names the fix.
3. **Back to his next message.** Do not wait for the companion and do not watch it: its scout is
   its own builder, and the scout's reply comes to it. When he approves the criteria there, the
   companion tells you `lem: SLUG criteria approved` and closes. At that turn, or at the next one
   when the line was lost, `lem companion due` gives the task under `start`, and its lead starts
   from step 7 of "Open the task" in `stages/new.md` (`stages/start.md`, "The queue").

While he is away no companion opens, and `open` says so. The interview then runs without him in
this session, as step 3 of `stages/away.md` says, with no question to him.
