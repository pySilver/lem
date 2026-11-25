# Claude Code: the correction hook

A part of `../claude-code.md`, read when the correction queue is offered, turned on or reported.

## The correction hook

For a machine whose owner keeps a correction queue (`stages/learn.md`). The switch is the
machine's: `collect` under `[corrections]` in `~/.config/lem/machine.toml`, which `lem settings set
corrections.collect yes --machine` or `lem settings set corrections.collect no --machine` writes. It
holds in every repository on the machine that uses Lem, and no file of a repository can hold it:
`lem settings show` refuses the table in `.lem/settings.toml` and in `.lem/settings.local.toml`, and
names `machine.toml` as its place. The no is the line `collect = false` there, and a machine with no
such line is a no too: the hook exits at once, and sends nothing. `lem settings show` gives the
answer as `corrections.collect`, with `from`, the file or "Lem's default".

The hook comes with the plugin, in its `hooks/hooks.json`, and nobody registers anything. It
starts on each message in every repository where the plugin is on, as `lem-hook corrections`
through the plugin's `hooks/run`.

A settings file may name the hook too (`~/.claude/settings.json`, or a checkout's
`.claude/settings.local.json`). Beside the plugin it
starts a second copy for each message; the first copy claims the message, so it is still judged
once, and the machine check's `correction hook` row names each such file with the entry to delete
from it by hand. Say that in one line, and do not edit the file: it is the owner's.

- It runs on the Python of Lem's own app, with the standard library alone, and starts no `git`:
  it finds the main checkout from the files git keeps. It writes the message into a file of its
  own in `.lem/state/corrections-waiting/`, readable by the owner alone, and starts `lem
  corrections worker` on it, the `lem` beside its own Python, detached. The worker asks the model
  over its own client. It needs `JEV_API_KEY`, the one name it reads for the key, in the
  environment Claude Code starts with, `JEV_API_URL` there for a provider other than OpenRouter,
  and `JEV_MODEL` for another model.
- It prints nothing and does not wait for the model. Its one wait, for its input, ends after two
  seconds, a bound chosen by guess on 2026-11-15. The `timeout` of 10 seconds in `hooks/hooks.json`
  is the value its source ran with in one repository since 2026-11-07; it is not a measurement.
- What fails goes to `corrections.log` in Lem's state folder (`.lem/state/`), and
  `lem corrections list` counts it.
- The yes is a line of a file in the owner's home, which no branch and no review carries. A hook
  that sends the owner's messages to an outside service is his to turn on: the command runs only
  on his answer, in his words. With a `machine.toml` that does not read, the hook sends nothing and
  prints nothing, and `lem settings show` refuses with the file's name.
