---
name: quiz
description: Monthly memory quiz. Ten yes/no or multiple-choice questions, sampled at random by tools/quiz.py from last month's decisions, learnings and knowledge, that the user answers without looking at the folder; grades them, records the result in memory/checks/ and says what to re-read. Use when the user types /quiz, says "monthly quiz", "test my memory", or when LAST.md or a reminder says the month's quiz is due.
---

# /quiz: what lives in you and what only lives here

The quiz measures the human side of the system: whether what was decided last month is still in the
person or only in the folder. A miss is not a failure; it is a pending decision: re-read it, or
delegate it knowingly.

## Steps

**1. Draw.** Run `python tools/quiz.py --select` and read the JSON. Do not choose items yourself: the
draw is mechanical on purpose, so it does not lean towards what you remember from this session. If the
pool has fewer than five items, say so and stop: there is not enough memory yet for a quiz to mean
anything.

**2. Write the questions.** For each item write one question that can be answered from memory:
- yes/no or multiple choice with three or four options;
- about the **substance** (what was decided, why, what turned out to be true), never about wording,
  dates or file names;
- distractors must be plausible: options that were considered and rejected, or a common belief the
  item corrected. Include two "familiarity traps": options that sound right because they use the
  item's words but say the opposite.
Do not show the source or the item text.

**3. Ask.** Present the questions one or two at a time, with the user's question tool if available
(AskUserQuestion), and wait. Remind the user once, at the start, not to open the folder.

**4. Grade and record.** Write a JSON file in the scratch area with
`{"month", "date", "items": [{id, kind, date, text, source, repeat?, question, answer, correct}],
"reading"}` where `reading` is two or three lines: which kind of item was missed and what that
suggests. Then run `python tools/quiz.py --record <file>`.

**5. Close.** Show the score, the previous month's score if there is one, and the list of files to
re-read. Missed items come back next month automatically.

## What this routine does not do

- It does not let the user look up answers during the quiz, and it does not reveal them before the
  end.
- It does not soften the score. The number is only useful if it is honest.
