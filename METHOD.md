# The method on one page

## The idea in one sentence

Claude Code starts every session remembering nothing. This folder is **the memory you lend it**: it
reads it when a session opens, uses it while working and writes it when the session closes. You bring
the two things it does not have: the framing of the problem and the verification of what comes out.

## Storing is not regulating

Most memory tools for AI assistants **store**: they keep what was said and bring it back. Some also
**act** on your behalf and rewrite their own memory. This folder tries to **regulate**: to keep your
goals stable across sessions and to tell you when your own knowledge is slipping into the tool. The
difference is not in the software. It is in five properties, each of which this folder turns into a
habit or a file you can inspect:

1. **Declared autonomy.** Every kind of task has a level, and nothing irreversible happens without you.
   The autonomy table in `CLAUDE.md`.
2. **Curated memory with explicit write rights.** Four territories, each answering one question, each
   with someone who is allowed to write it. The table below.
3. **Verification as a first-class function.** Every session opens with a contract that has an exit
   criterion, and closes by checking it. Every answer carries where it came from.
4. **Measuring what the human stops knowing.** A monthly quiz you answer without the folder
   (`/quiz`), and the closing rate of your sessions (`tools/convergence.py`).
5. **The pair as the unit.** Neither you nor the model is the system; the system is the two of you
   working with this folder. That is why the measures look at both sides.

## Four territories

| Territory | Question | Where | Who writes |
|---|---|---|---|
| **T1** | Who are you | `CLAUDE.md` | Only you; Claude proposes |
| **T2** | What do you know | `memory/knowledge/` | Claude at closing; you prune |
| **T3** | What happened | `memory/log/`, `memory/LAST.md`, `memory/decisions.md` | Claude at closing |
| **T4** | What do we know | this folder as a shared git repository | Everyone, through commits |

Knowledge is what **stays true** tomorrow. The log is what **happened** one day. A decision is both:
it happened one day and rules afterwards, so it carries its reason. Mixing them is the most common
mistake.

## Three steps of a session

**Open.** Claude reads `LAST.md` and says in three lines where you left off. You agree in five lines
on what will come out of the session: deliverable · exit criterion · out of scope · assumptions ·
instruments. It looks like bureaucracy; it is the opposite: five lines at the start save the session
that wanders off.

**Work.** What comes up on the side is not discussed then: it is noted as *parked* and looked at when
closing. When you decide something, it is named as a decision. When something turns out to work
differently from what you believed, it is named as a learning.

**Close.** `/close`. Claude writes the log, moves decisions to the table with their reason, moves
learnings to knowledge, updates `LAST.md` and shows you the parked items to decide on all at once.
Five minutes.

## Why closing is the one thing that is not negotiable

Because it is the only step that turns a session into memory. Without it Claude worked well and the
next morning nothing is left. With it, the next session starts where the last one ended, and after
three weeks you have something no assistant gives you out of the box: a system that knows how you
think, and a measure of how much of that thinking is still yours.

If after three weeks the folder looks like the first day, the folder did not fail: the habit asked
for more than you wanted to put in, and that is also information.

---

This method is described in Sánchez, R. I. (2026), *Exocortex: an operational definition and minimal
architecture for a governed cognitive regulator*, Zenodo, https://doi.org/10.5281/zenodo.22714567.
Text under CC BY 4.0: if you share or adapt it, credit the source.
