# -*- coding: utf-8 -*-
"""Memory health check: what is stale, duplicated or incomplete. It only reads; it never changes a file.

Curated memory degrades quietly. A knowledge file stops being true and nobody re-checks it, the same
topic gets a second file, a decision is recorded without its reason, a log loses the line that makes
it findable. None of that raises an error: /recall and /quiz just get worse, and an empty search reads
as "nothing recorded". This script lists those problems, once a month with /quiz or whenever you
want. Fixing them is a decision: Claude proposes, you approve.

    python tools/memory_check.py
    python tools/memory_check.py --json
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import transcripts  # noqa: E402  (only to locate Claude Code's automatic memory for this folder)

ROOT = Path(__file__).resolve().parent.parent
STALE_DAYS = 90          # knowledge not re-verified for this long is flagged
LAST_KEEP = 5            # /close keeps at most this many sections in LAST.md...
LAST_MAX_AGE_DAYS = 7    # ...and drops the ones older than this
DUP_JACCARD = 0.6        # word overlap between two knowledge files that suggests one topic
STOP = {"the", "and", "for", "how", "what", "why", "when", "with", "from", "into", "this", "that",
        "about", "are", "was", "its", "our", "your", "not", "but", "can", "has", "have", "which"}
RE_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
RE_WORD = re.compile(r"[a-z0-9]+")


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace").lstrip("﻿")


def _header(text: str) -> dict:
    """Fields of the `---` block at the top of a file; {} if there is none."""
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end < 0:
        return {}
    out = {}
    for ln in text[3:end].splitlines():
        if ":" in ln:
            k, v = ln.split(":", 1)
            out[k.strip()] = v.strip().strip("'\"")
    return out


def _missing(value: str) -> bool:
    return not value or value.startswith("<")      # "<one line ...>" is the template placeholder


def _words(text: str, min_len: int) -> set:
    return {w for w in RE_WORD.findall(text.lower()) if len(w) >= min_len and w not in STOP}


def _jaccard(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if a and b else 0.0


def _valid(day: str) -> bool:
    try:
        date.fromisoformat(day)
        return bool(RE_DATE.match(day))
    except ValueError:
        return False


def _age(day: str, today: date) -> int:
    return (today - date.fromisoformat(day)).days


def check(root: Path = ROOT, today: date | None = None) -> dict:
    today = today or date.today()
    mem = root / "memory"
    rel = lambda p: p.relative_to(root).as_posix()  # noqa: E731
    res = {"stale": [], "incomplete": [], "duplicates": [], "decisions_no_reason": [],
           "decisions_no_date": [], "logs_no_description": [], "last_old_sections": 0,
           "auto_memory": {"folder": None, "files": 0, "newest": []}}

    # Knowledge: header complete, verified recently, one file per topic.
    know = []
    for f in sorted((mem / "knowledge").glob("*.md")):
        if f.name.lower() == "readme.md":
            continue
        h = _header(_read(f))
        if _missing(h.get("description", "")):
            res["incomplete"].append({"file": rel(f), "field": "description"})
        lv = h.get("last_verified", "")
        if not _valid(lv):
            res["incomplete"].append({"file": rel(f), "field": "last_verified"})
        elif _age(lv, today) > STALE_DAYS:
            res["stale"].append({"file": rel(f), "last_verified": lv, "days": _age(lv, today)})
        know.append((f, _words(f.stem.replace("-", " "), 3), _words(h.get("description", ""), 4)))
    for i, (fa, na, da) in enumerate(know):
        for fb, nb, db in know[i + 1:]:
            by_name = _jaccard(na, nb) >= DUP_JACCARD and len(na & nb) >= 2
            by_desc = _jaccard(da, db) >= DUP_JACCARD and len(da & db) >= 3
            if by_name or by_desc:
                res["duplicates"].append({"files": [rel(fa), rel(fb)],
                                          "because": "similar names" if by_name else "similar descriptions"})

    # Decisions: every row has a date the quiz can read and a reason.
    dec = mem / "decisions.md"
    if dec.is_file():
        for n, line in enumerate(_read(dec).splitlines(), 1):
            if not line.lstrip().startswith("|"):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            first = cells[0].lower()
            if first in ("date", "example") or set(line.strip()) <= set("|-: "):
                continue
            if not RE_DATE.match(cells[0]):
                res["decisions_no_date"].append({"line": n})
            elif len(cells) < 3 or len(cells[2].strip(" -?.")) < 3:
                res["decisions_no_reason"].append({"line": n, "date": cells[0]})

    # Log: each session file has the description line /recall shows without opening it.
    for f in sorted((mem / "log").glob("20??-??-??-*.md")):
        if _missing(_header(_read(f)).get("description", "")):
            res["logs_no_description"].append(rel(f))

    # LAST.md: /close keeps it short; old sections left behind mean it is not being tidied.
    last = mem / "LAST.md"
    if last.is_file():
        days = [d for d in re.findall(r"^## (\d{4}-\d{2}-\d{2})", _read(last), re.M) if _valid(d)]
        if len(days) > LAST_KEEP:
            res["last_old_sections"] = sum(1 for d in days if _age(d, today) > LAST_MAX_AGE_DAYS)

    # Claude Code's own automatic memory for this folder: written by the system, not curated.
    auto = Path(transcripts.config_dir()) / "projects" / transcripts.slug(str(root)) / "memory"
    if auto.is_dir():
        files = sorted((p for p in auto.glob("*.md") if p.name != "MEMORY.md"),
                       key=lambda p: p.stat().st_mtime, reverse=True)
        res["auto_memory"] = {"folder": str(auto), "files": len(files), "newest": [p.name for p in files[:5]]}
    return res


def report(res: dict, root: Path) -> str:
    out = [f"Memory health check · {root} · {date.today().isoformat()}"]
    issues = 0

    def block(title, rows):
        nonlocal issues
        if rows:
            issues += len(rows)
            out.append(f"\n{title}: {len(rows)}")
            out.extend(f"  {r}" for r in rows)

    block(f"Knowledge not verified in {STALE_DAYS}+ days (re-check it, update last_verified, or drop it)",
          [f"{x['file']}  last verified {x['last_verified']} ({x['days']} days)" for x in res["stale"]])
    block("Knowledge with an incomplete header (/recall and /quiz cannot see it well)",
          [f"{x['file']}  missing {x['field']}" for x in res["incomplete"]])
    block("Possible duplicates (one topic, two files: merge them, check by hand)",
          [f"{' + '.join(x['files'])}  ({x['because']})" for x in res["duplicates"]])
    block("Decisions without a reason (ask for it; without it the decision gets argued again)",
          [f"memory/decisions.md line {x['line']} ({x['date']})" for x in res["decisions_no_reason"]])
    block("Decision rows without a YYYY-MM-DD date (the quiz cannot read them)",
          [f"memory/decisions.md line {x['line']}" for x in res["decisions_no_date"]])
    block("Logs without a description line", res["logs_no_description"])
    if res["last_old_sections"]:
        block("memory/LAST.md sections older than a week, beyond the five /close keeps",
              [f"{res['last_old_sections']} sections: their content is already in the logs"])
    am = res["auto_memory"]
    if am["files"]:
        out.append(f"\nClaude Code's automatic memory for this folder: {am['files']} files "
                   f"(newest: {', '.join(am['newest'])}).")
        out.append("  Written by the system, not curated: move what matters to memory/knowledge/, "
                   "and leave the rest.")
    out.append(f"\n{issues} things to look at." if issues else "\nNothing to fix.")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description="Memory health check (read-only)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    res = check()
    print(json.dumps(res, ensure_ascii=False, indent=1) if a.json else report(res, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
