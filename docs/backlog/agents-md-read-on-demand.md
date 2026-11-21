---
worth: maybe
where: AGENTS.md
added: 2026-11-20
---
# Lem's own AGENTS.md is read whole by every agent

In Lem's own repository `AGENTS.md` was 18,823 words on 2026-11-20, about 27.4k tokens (characters / 4,
an estimate), and 21,575 words on 2026-11-21 (`wc -w`); Claude Code puts it into the context of every
agent that works here. The token
assessment of 2026-11-19 (a subagent's read of `message.usage` in that day's transcripts) counted
about 2,350 requests that each read it: about 63M tokens of the day's 574.1M (an unmeasured
estimate). Most of the file is the owner's rulings with their dates and words, which an agent needs
only when a change touches one.

The direction: the rules for a change, the layout and the checks stay in `AGENTS.md`; the rulings
move to a file that an agent reads when its change reaches one, as a stage file is read only when
its subcommand runs. The assessment's estimate of the saving: about 50M tokens on such a day.

Open before it is built: how an agent finds the ruling a change reaches without reading them all,
and whether a builder's brief names them. Projects that use Lem do not pay this cost; it is Lem's
own repository only.
