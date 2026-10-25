---
name: close
description: Session closing routine. Checks the session contract, shows the parked items once for a decision in bulk, writes the day's log, moves decisions (with their reason) to memory/decisions.md and learnings to memory/knowledge/, and updates memory/LAST.md so the next session starts where this one ends. Use when the user says "close", "let's wrap up", "save where we are", types /close, or when the exit criterion of the session contract is met.
---

# /close: closing routine

Five minutes. The point is not to document: it is that **the next session starts where this one ends**.
Everything you write must be useful to someone who was not here.

## Steps

**0. Real date.** Get today's date from the system (`date` in bash, `Get-Date` in PowerShell), not from
memory. Format `YYYY-MM-DD`.

**1. Contract.** Re-read the contract agreed at opening (deliverable · exit criterion · out of scope ·
assumptions · instruments). Say in one line whether it was met and, if not, what is missing. If there
was no contract, say that too: it is information for next time.

**2. Parked.** List everything noted as parked during the session. Ask the user to decide on each:
**pending** (goes to the log as pending), **drop**, or **knowledge** (if it was really a learning).
Do not propose anything new here. If nothing was parked, say so.

**3. Log.** Write `memory/log/YYYY-MM-DD-<topic>.md` following `memory/log/_TEMPLATE.md`. Topic in
lowercase with hyphens. The `description` line says what was done and what is left: it is what
`/recall` shows without opening the file. If a log for today with the same topic exists, add a
"Continued" section instead of a second file.

**4. Decisions.** For each decision the user took, append a row to `memory/decisions.md`:
date | decision | **reason**. If there is no reason, ask for it before writing: a decision without its
reason gets argued again. If there were no decisions, do not invent one.

**5. Learnings.** For each thing that turned out to work differently from what we believed and will
stay true, create or update `memory/knowledge/<topic>.md` with the header described in that folder's
README. If a file on the topic exists, update it and its `last_verified` date; do not create a parallel
one. Do not copy state that expires (counts, versions, "today"): if a number matters, it goes with its
date, or better, with how to reproduce it. If a knowledge file was used during the session and turned
out to be still true, update its `last_verified` date too: that is how memory gets verified, not only
written.

**6. LAST.md.** `memory/LAST.md` holds one section per recent session, newest first:

```
## YYYY-MM-DD · <topic>
**State.** What is done and verified. If something is done but not verified, say so.
**Next.** One concrete action, the first thing someone picking this up would do. If it depends on
another person, name them and what is expected of them.
**Context.** The minimum to resume without reading the log: paths, names, a trap if there was one.
```

Replace the section with today's date and the same topic if it exists; otherwise add yours on top.
Keep the other sections: another session may have written them. Drop sections older than seven days
once there are more than five; their content is already in the logs.

**7. What still has to leave.** If the session produced something that must reach someone (a message,
a file, a notice) and it has not gone out, say so explicitly in the summary and in LAST.md. A finished
deliverable that was not sent is the same as one not done.

**8. Git (if this folder is a repository).** Show `git status --short`. If what changed is only this
session's memory, propose a commit `close: YYYY-MM-DD <topic>` and make it when the user agrees. Leave
out and name any change that is not from this session.

**9. Summary.** At most five lines: contract met or not · what was written · decisions recorded ·
what still has to leave · next step.

## What this routine does not do

- It does not send, publish or touch anything outside this folder.
- It does not summarise the session from memory: it re-reads what happened before writing. An
  invented close is worse than none, because the next session believes it.
- It does not skip step 2 when nothing was parked: saying so is also information.
- It does not edit CLAUDE.md. If something there should change, it proposes the change and waits.

---

Part of [Exo-cortex](https://github.com/Eutree/Exo-cortex) (Sánchez, 2026, https://doi.org/10.5281/zenodo.22714567) · CC BY 4.0
