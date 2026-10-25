# -*- coding: utf-8 -*-
"""Monthly memory quiz: does what was decided still live in you, or only in the folder?

Once a month you answer ten yes/no or multiple-choice questions, WITHOUT looking at the folder,
about items sampled at random from the last month of your memory. This script does the mechanical
half: it selects the items (seed = month, so the draw is reproducible and does not lean towards
whatever Claude remembers from the current session) and records the result. The /quiz skill writes
the questions and the distractors and grades the answers.

Sources (window: 30 days ending 2 days before today, because what is fresh measures nothing):
  decision     memory/decisions.md, one table row = date | decision | reason
  learning     memory/log/YYYY-MM-DD-*.md, bullets under "## Learnings"
  knowledge    memory/knowledge/*.md whose `last_verified` falls in the window (its description)

Missed items from the previous month come back first (up to 3).

    python tools/quiz.py --candidates
    python tools/quiz.py --select                # JSON with the items to ask
    python tools/quiz.py --record result.json    # written by /quiz
    python tools/quiz.py --history
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MEM = ROOT / "memory"
LOG = MEM / "log"
KNOWLEDGE = MEM / "knowledge"
DECISIONS = MEM / "decisions.md"
CHECKS = MEM / "checks"
HISTORY = CHECKS / "_history.json"

N = 10
QUOTAS = {"decision": 5, "learning": 4, "knowledge": 1}
REPEAT = 3
EXCLUDE_DAYS = 2
WINDOW_DAYS = 30
MAX_TEXT = 700

RE_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
RE_VERIFIED = re.compile(r"^last_verified:\s*(\d{4}-\d{2}-\d{2})", re.M)
RE_DESC = re.compile(r"^description:\s*(.+)$", re.M)


def _item(kind, day, text, source):
    text = re.sub(r"\s+", " ", text).strip()[:MAX_TEXT]
    iid = hashlib.sha1(f"{kind}|{day}|{text[:80]}".encode("utf-8")).hexdigest()[:8]
    return {"id": iid, "kind": kind, "date": day, "text": text, "source": source}


def _decisions(since, until):
    out = []
    if not DECISIONS.is_file():
        return out
    for line in DECISIONS.read_text(encoding="utf-8", errors="replace").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 3 and RE_DATE.match(cells[0]) and since <= cells[0] <= until:
            out.append(_item("decision", cells[0], f"DECISION: {cells[1]} | REASON: {cells[2]}",
                             "memory/decisions.md"))
    return out


def _section(text, title):
    lines, inside = [], False
    for ln in text.splitlines():
        if ln.startswith("## "):
            inside = ln[3:].strip().lower().startswith(title.lower())
            continue
        if inside:
            lines.append(ln)
    return lines


def _bullets(lines):
    out, cur = [], None
    for ln in lines:
        if ln.startswith("- "):
            if cur:
                out.append(cur)
            cur = ln[2:]
        elif cur is not None and ln.startswith(" ") and ln.strip():
            cur += " " + ln.strip().lstrip("- ")
        elif cur is not None and ln.strip():
            out.append(cur)
            cur = None
    if cur:
        out.append(cur)
    return out


def _learnings(since, until):
    out = []
    for f in sorted(LOG.glob("20??-??-??-*.md")):
        day = f.name[:10]
        if not since <= day <= until:
            continue
        text = f.read_text(encoding="utf-8", errors="replace")
        for b in _bullets(_section(text, "Learnings")):
            if len(b) >= 40:
                out.append(_item("learning", day, b, f"memory/log/{f.name}"))
    return out


def _knowledge(since, until):
    out = []
    for f in sorted(KNOWLEDGE.glob("*.md")):
        if f.name.lower() == "readme.md":
            continue
        text = f.read_text(encoding="utf-8", errors="replace")
        m, d = RE_VERIFIED.search(text), RE_DESC.search(text)
        if m and d and since <= m.group(1) <= until:
            out.append(_item("knowledge", m.group(1), d.group(1).strip().strip("'\""),
                             f"memory/knowledge/{f.name}"))
    return out


def candidates(since, until):
    return _decisions(since, until) + _learnings(since, until) + _knowledge(since, until)


def _history():
    try:
        return json.loads(HISTORY.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _previous_month(month):
    y, m = map(int, month.split("-"))
    return f"{y - 1}-12" if m == 1 else f"{y}-{m - 1:02d}"


def select(month, since, until, n=N):
    rng = random.Random(f"quiz-{month}")
    cands = candidates(since, until)
    repeats = [dict(x, repeat=True) for x in _history().get(_previous_month(month), {}).get("missed", [])][:REPEAT]
    used = {x["id"] for x in repeats}
    chosen = list(repeats)
    for kind, k in QUOTAS.items():
        pool = [c for c in cands if c["kind"] == kind and c["id"] not in used]
        k = max(0, k - sum(1 for r in repeats if r["kind"] == kind))
        for c in rng.sample(pool, min(k, len(pool))):
            chosen.append(c)
            used.add(c["id"])
    rest = [c for c in cands if c["id"] not in used]
    rng.shuffle(rest)
    while len(chosen) < n and rest:
        chosen.append(rest.pop())
    rng.shuffle(chosen)
    return chosen[:n], {k: sum(1 for c in cands if c["kind"] == k) for k in QUOTAS}


def render(res):
    items = res["items"]
    right = [i for i in items if i["answer"] == i["correct"]]
    wrong = [i for i in items if i["answer"] != i["correct"]]
    prev = _history().get(_previous_month(res["month"]))
    trend = f" · previous month {prev['right']}/{prev['n']}" if prev else ""
    rows = [f"| {k} | {i['kind']}{' (repeat)' if i.get('repeat') else ''} | {i['question']} | {i['answer']} "
            f"| {i['correct']} | {'yes' if i in right else 'NO'} | `{i['source']}` |"
            for k, i in enumerate(items, 1)]
    reread = sorted({i["source"] for i in wrong})
    nl = "\n"
    return f"""---
description: Memory quiz {res['month']}, {len(right)}/{len(items)} right; what to re-read is at the end
---

# Memory quiz {res['month']}

**Result: {len(right)}/{len(items)}**{trend} · answered on {res.get('date', date.today().isoformat())} without looking at the folder.
Window: {res.get('since', '?')} to {res.get('until', '?')} · random draw with seed `quiz-{res['month']}`.

| # | Kind | Question | Your answer | Correct | Right | Source |
|---|---|---|---|---|---|---|
{nl.join(rows)}

## What to re-read

{nl.join(f'- `{s}`' for s in reread) or 'Nothing: all right.'}

## Reading

{res.get('reading', '_(none)_')}
""", right, wrong


def record(res):
    md, right, wrong = render(res)
    CHECKS.mkdir(parents=True, exist_ok=True)
    out = CHECKS / f"{res['month']}-quiz.md"
    out.write_text(md, encoding="utf-8")
    hist = _history()
    hist[res["month"]] = {"date": res.get("date", date.today().isoformat()), "n": len(res["items"]),
                          "right": len(right),
                          "missed": [{k: i[k] for k in ("id", "kind", "date", "text", "source")} for i in wrong]}
    HISTORY.write_text(json.dumps(hist, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Monthly memory quiz: mechanical selection and record")
    ap.add_argument("--month", help="YYYY-MM (default: this month)")
    ap.add_argument("--days", type=int, default=WINDOW_DAYS)
    ap.add_argument("--candidates", action="store_true")
    ap.add_argument("--select", action="store_true")
    ap.add_argument("--record", metavar="JSON")
    ap.add_argument("--history", action="store_true")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    today = date.today()
    month = a.month or today.strftime("%Y-%m")
    until = (today - timedelta(days=EXCLUDE_DAYS)).isoformat()
    since = (date.fromisoformat(until) - timedelta(days=a.days)).isoformat()
    if a.history:
        for m, h in sorted(_history().items()):
            print(f"{m}: {h['right']}/{h['n']} ({h['date']}) · missed {len(h['missed'])}")
    elif a.candidates:
        c = candidates(since, until)
        print(f"window {since} to {until}: {len(c)} candidates")
        for k, q in QUOTAS.items():
            print(f"  {k:<10} {sum(1 for x in c if x['kind'] == k):>3}  (quota {q})")
    elif a.select:
        items, pool = select(month, since, until)
        print(json.dumps({"month": month, "since": since, "until": until, "pool": pool, "items": items},
                         ensure_ascii=False, indent=1))
    elif a.record:
        res = json.loads(Path(a.record).read_text(encoding="utf-8"))
        res.setdefault("month", month)
        res.setdefault("since", since)
        res.setdefault("until", until)
        print(f"recorded: {record(res)}")
    else:
        ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
