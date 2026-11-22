---
worth: later
where: tests/lem-land-shop.sh
added: 2026-11-22
---
# Two landing blocks check refusals of a record that a unit case already holds

`tests/unit/test_task_rules.py` calls `read_form`, `talk_start_form` and `talk_form` of `project.py`
and checks each refusal's words, with no `lem project` process. Two landing blocks still check the
same refusals through one real `lem project log` call each:

- `tests/lem-land-local.sh`: `read_with` runs nine refused `criteria.read` records (`bad_by`,
  `bad_one`, `bad_none`, `bad_more`, `bad_quiet`, `bad_families`, `bad_flagged`, `bad_split`,
  `bad_digest`), and `empty_with` three refused records of a read in which nobody answered
  (`empty_family`, `empty_unnamed`, `empty_flagged`).
- `tests/lem-land-shop.sh`: the refused `plan.talk` records `typed`, `missing`, `self_bound`, `lost`,
  `undesigned`, `overrepaired`, `lone` and `quiet_raised`, and the `plan.talk.start` records
  `startless`, `overstarted` and `started`.

`tests/lem-settings.sh` now keeps one refusal through the real command for each record, as `AGENTS.md`
asks ("A journey is run once, not once for each input"). Each landing block could keep one refused
record through `lem project log` (exit 1, nothing appended) and leave the words of the others to the
unit cases. The task `pure-rules-unit-tests` cut only `tests/lem-settings.sh`.
