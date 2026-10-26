# Exo-cortex

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23676244.svg)](https://doi.org/10.5281/zenodo.23676244)

**A folder that turns Claude Code into an external regulator of your thinking, not only a memory.**

Claude Code starts every session remembering nothing. Most fixes for that *store*: they keep what was
said and bring it back. This is a reference implementation of the other idea, the original meaning of
the word *exocortex* (Houston, 1999): a synthetic **regulator** of high-level thought that keeps goals
stable across sessions, under rules you can audit, and that measures what you stop knowing as you
delegate to it.

It is a folder you copy, not software you install. It needs only Claude Code; three small Python
scripts (standard library only) add the measurements.

## What it adds to Claude Code

| Property of a regulator | Where it lives here |
|---|---|
| Declared autonomy: nothing irreversible without you | The autonomy table and rules in [`CLAUDE.md`](CLAUDE.md) |
| Curated memory with explicit write rights | Four territories (who you are · what you know · what happened · what we know), each with who may write it, and a monthly health check (see [How memory is managed](#how-memory-is-managed)) |
| Verification as a first-class function | A five-line contract at the start of every session, checked by `/close` |
| Measuring what the human stops knowing | `/quiz`: ten questions a month about last month's memory, answered without the folder |
| Measuring whether the protocol is followed | `tools/convergence.py`: how many sessions close, how many drag on for days |

The method fits on one page: [`METHOD.md`](METHOD.md).

## Quick start (about 20 minutes)

1. Copy this folder where you want your memory to live (or `git clone` it and delete `.git` if you
   want a private history of your own).
2. Open it in [Claude Code](https://docs.claude.com/en/docs/claude-code/overview) and trust the folder
   when asked.
3. Paste the block in [`SETUP.md`](SETUP.md) as your first message. Claude interviews you and writes
   your `CLAUDE.md`. Do not copy someone else's: this is the part that matters most.
4. Work normally. At the end of each session, type `/close`.

The next time you open Claude Code in the folder, it starts by telling you where you left off.

## Daily use

| When | You type | What happens |
|---|---|---|
| Opening a session | nothing | Claude reads `memory/LAST.md`, says where you left off and proposes the session contract |
| Looking for something already discussed | `/recall <topic>` | Searches all the memory and says where each match came from, and where it looked |
| Closing a session | `/close` | Writes the log, decisions with their reasons, learnings, and where you left off. **The only mandatory step** |
| Once a month | `/quiz` | Ten questions about last month, answered without the folder; the score is recorded, then a memory health check |

## How memory is managed

Memory here is curated, not accumulated: it has a life cycle, and every step has an owner.

| Step | When | Who | How |
|---|---|---|---|
| **Write** | At the end of every session | Claude, through `/close` | The session log, decisions with their reason, learnings into knowledge, and where you left off |
| **Read** | When a session opens, and on demand | Claude | `memory/LAST.md` first; `/recall` searches everything and says where it looked |
| **Verify** | Whenever a knowledge file is used and is still true | Claude, at `/close` | Updates the file's `last_verified` date, so "still true" is a dated claim |
| **Prune** | Once a month, with `/quiz` | Claude proposes, you decide | `tools/memory_check.py` lists what is stale, duplicated or incomplete |

Three rules keep it healthy:

- **One topic, one file.** Knowledge is updated in place, never written twice.
- **No copied state.** A count, a version or a "today" expires on its own and is later read as current:
  it goes with its date, or better, with how to reproduce it.
- **Identity is yours.** `CLAUDE.md` changes only with your approval.

The health check only reads. It flags:

- knowledge not verified in 90 days;
- headers that `/recall` and `/quiz` cannot read;
- two files that look like one topic;
- decisions with no reason, or with a date the quiz cannot parse;
- logs with no description;
- old sections left in `LAST.md`.

None of these raises an error on its own; they just make search and recall quietly worse.

Claude Code also keeps an automatic memory of its own for each folder. The system writes it and nobody
curates it, so treat it as an inbox. The health check shows what is in it, and what matters moves to
`memory/knowledge/`.

## Measuring

```bash
python tools/convergence.py          # sessions in this folder: closed with /close, multi-day, per day
python tools/quiz.py --candidates    # how much memory the next quiz can draw from
python tools/quiz.py --history       # quiz scores, month by month
python tools/memory_check.py         # memory health: stale, duplicated, incomplete (read-only)
```

To have Claude propose closing when a long session has not closed, copy
`.claude/settings.example.json` to `.claude/settings.json` (or merge its `Stop` hook into yours).
The threshold is `EXO_NUDGE_TOKENS` (default 200000 output tokens); the reminder appears at most once
per session. On Windows, if `python` is not on the PATH, write `py` instead.

`tools/transcripts.py` is the only code that reads Claude Code's session files, whose format is not
documented. It keeps counts and dates, never the text of your prompts.

## Layout

```
CLAUDE.md                 who you are, autonomy, session protocol (T1)
METHOD.md · SETUP.md      the method on one page · the setup interview
memory/
  LAST.md                 where you left off, one section per recent session
  log/                    what happened, one file per session (T3)
  decisions.md            what you decided and why (T3)
  knowledge/              what stays true (T2)
  checks/                 monthly quiz results
.claude/skills/           close · recall · quiz
tools/                    transcripts.py · convergence.py · quiz.py · memory_check.py
tests/                    python -m pytest tests
```

## What it does not do

- It does not send, publish or delete anything outside the folder without your confirmation.
- It does not remember on its own. It remembers what you close with `/close`.
- It sends nothing anywhere: no telemetry, no network calls. Your memory stays in the folder.
- It is not anyone else's system. It is the form; what you put in it is yours.

## Status

Reference implementation, version 0.1. It accompanies a dated public definition of the concept
(Sánchez, 2026) and a Perspective article in preparation. Issues and pull requests are welcome, with
no support commitment. The format of Claude Code transcripts may change; if the measures break,
`tools/transcripts.py` is the one file to fix.

## Citing

If you use or discuss this work, please cite the definition and, if relevant, this repository
(see [`CITATION.cff`](CITATION.cff)):

> Sánchez, R. I. (2026). *Exocortex: an operational definition and minimal architecture for a governed
> cognitive regulator*. Zenodo. https://doi.org/10.5281/zenodo.22714567

> Sánchez, R. I. (2026). *Exo-cortex: a reference implementation of a governed cognitive regulator for
> Claude Code*. Zenodo. https://doi.org/10.5281/zenodo.23676244

The second DOI always resolves to the latest version of the software; each release also has its own.

Background: Houston, B. (1999), original definition of the term; see
[Origins of the term "Exocortex"](https://ben3d.ca/blog/origins-of-the-term-exocortex).

## Author and affiliation

Rafael Ignacio Sánchez ([ORCID 0009-0007-8854-2945](https://orcid.org/0009-0007-8854-2945)),
Universidad Argentina de la Empresa (UADE) and Blue Star Group. Built as a personal exploration;
it is not a product of either institution.

## License

Code (`tools/`, `tests/`): [MIT](LICENSE). Text and templates (the `.md` files): [CC BY 4.0](LICENSE-docs.md).
