---
name: recall
description: Search all the memory in this folder (memory/knowledge/, memory/decisions.md, memory/log/, memory/LAST.md, CLAUDE.md) for keywords and return which files mention the topic, with the line that describes each file and where the match is. Use when the user asks "what do we know about X", "is there anything recorded on", "when did we decide", "remember the thing about", types /recall, and always before asserting that something is not recorded. Plain text search, no external tools.
---

# /recall: search the memory

Before saying "there is nothing on X", this must have been run. And the answer says **where it looked**,
so an empty result reads as "not here", never as "does not exist".

## Steps

**1. Terms.** Take two to four nouns or names from the request. Add obvious variants (singular and
plural, with and without accents, an acronym and its expansion if CLAUDE.md gives it). Drop empty
words ("thing", "topic", "that").

**2. Scope.** Always these places, in this order of weight:
1. `memory/knowledge/`: what stays true.
2. `memory/decisions.md`: what was decided and why.
3. `memory/log/` and `memory/LAST.md`: what happened.
4. `CLAUDE.md`: identity and rules.

If the user's CLAUDE.md declares other memory places ("My tools and places"), add them and say so.

**3. Search.** One case-insensitive search per term over those places (`grep -ril` in bash,
`Select-String -List` in PowerShell). Count how many distinct terms appear in each file: that is the
order. A file with three terms goes before a file with one term twenty times.

**4. Trail.** For each file found, up to ten, show:
- the path,
- its `description:` line if it has one (otherwise its first heading),
- one or two lines where a term appears, with line numbers.

Do not summarise or interpret yet: the user chooses what to open. When they ask, open the file in full
and only then answer the underlying question, citing the file.

**5. If nothing.** Say it with the scope: "I searched *terms* in knowledge, decisions, log and
CLAUDE.md: nothing". Suggest one thing only: an alternative term, or that it may live somewhere not
declared.

## What this routine does not do

- It does not invent: if no file says it, it is not asserted.
- It does not replace reading the file: the trail is for choosing what to read.
- It does not search outside the folder unless CLAUDE.md declares another place.

---

Part of [Exo-cortex](https://github.com/Eutree/Exo-cortex) (Sánchez, 2026, https://doi.org/10.5281/zenodo.22714567) · CC BY 4.0
