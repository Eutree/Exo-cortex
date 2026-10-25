# Setup: paste this into Claude Code the first time

Open this folder in Claude Code (terminal: `cd` into it and run `claude`; desktop app: choose it as
the working folder). Copy everything inside the block below and send it as your first message. Claude
interviews you and writes your `CLAUDE.md`. About ten minutes.

```
I am setting up my exocortex in this folder. Interview me and, with my answers, write the CLAUDE.md
file of this folder, replacing the template that is there now.

Ask one or two questions at a time, in plain language, and wait for my answer before going on. If an
answer is enough, do not ask again. Cover these seven blocks:

1. Who I am: name, role, organisation, who I report to, what I am responsible for.
2. What I decide every week: the two or three recurring decisions and the data I rely on.
3. What hurts to lose: what information slips away between one session and the next.
4. How to talk to me: language, tone, length, whether to explain technical terms, one recommendation
   or several options.
5. What you never do without asking: which actions are irreversible or sensitive in my work (sending
   messages, touching a system, sharing data) and need my confirmation. Fill the autonomy table.
6. My tools and places: systems, folders, files or data I use often and where they are, so you know
   where to look before asking me.
7. My vocabulary: three to five terms, acronyms or internal names you must understand without
   explanation.

When the interview is done:
- Write CLAUDE.md in my language and with my words, with the sections: Who I am · How to work with
  me · Autonomy · My tools and places · Vocabulary · Session protocol.
- Copy the "Session protocol" section exactly as it is in the current template: it is the method.
- Keep the "Based on Exo-cortex" line under the title as it is: it says where the method comes from.
- Do not invent anything I did not say. What I do not know yet stays as "to be completed" in one line.
- Show me the whole file before saving it and wait for my approval.
- After saving it, replace the setup section of memory/LAST.md with today's date, "setup done" as the
  state, and "work one real session and close it with /close" as the next step.
```

## After setup

- Work one real session, even a short one. Agree the five-line contract at the start; type `/close`
  at the end.
- The next day, open Claude Code in the folder. It should start by telling you where you left off. If
  it does not, ask it to read `memory/LAST.md` and check that `CLAUDE.md` still has the "Session
  protocol" section.
- After a week, re-read your `CLAUDE.md`. There is probably something you want to correct. Correct it:
  it is yours.
- Optional, once you have Python 3.9+: enable the closing reminder and look at your numbers
  (see "Measuring" in the README).
- After a month: `/quiz`.
