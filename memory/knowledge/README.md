# Knowledge

What **stays true tomorrow** goes here: how something works, a trap that was costly to find, a
criterion you set. One file per topic, lowercase name with hyphens (`how-lead-time-is-computed.md`,
`traps-in-the-monthly-report.md`).

Each file starts with a short header, so `/recall` finds it without opening it and the monthly quiz
can sample it:

```
---
description: <one line saying what this file resolves>
valid_since: YYYY-MM-DD
last_verified: YYYY-MM-DD
---
```

Two rules that save trouble:

- **Do not copy state.** A count, a version, a "today" expire on their own and are later read as
  current. If the number matters, it goes with its date ("12 as of 7 Oct"). Better still, write how to
  reproduce it, not the value.
- **What happened on a day goes to the log, not here.** If the file starts with "today we did", it is
  in the wrong place.

You can delete this README once there are three real files in the folder.
