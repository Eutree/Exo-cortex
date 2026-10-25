# -*- coding: utf-8 -*-
"""Do sessions close, or do they drag on? A view over transcripts.py, plus an optional Stop hook.

Report (default): for the sessions run in this folder, how many ended with the closing routine
(/close), how many spread over more than one day, how many new sessions start per day, and how
many long sessions never closed. These are the numbers that tell you whether the session protocol
in CLAUDE.md is being followed or only written down.

    python tools/convergence.py               # last 30 days and all time, this folder
    python tools/convergence.py --days 7
    python tools/convergence.py --all-projects

Stop hook (opt-in, see .claude/settings.example.json): when a session in this folder has produced
more than EXO_NUDGE_TOKENS output tokens (default 200000) without /close, Claude is asked once to
propose closing. It fires at most once per session and never breaks Claude Code: any error exits 0.
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import transcripts  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(ROOT, ".exo", "nudges.json")
CLOSE = "close"
MIN_HUMAN_CHARS = 200          # below this a session is trivial or aborted, and is not counted


def threshold() -> int:
    try:
        return int(os.environ.get("EXO_NUDGE_TOKENS", "200000"))
    except ValueError:
        return 200000


def sessions(recs):
    out = []
    for r in recs:
        if r["sidechain"] or not r["days"] or r["human_chars"] < MIN_HUMAN_CHARS:
            continue
        out.append({"sid": r["sid"], "d0": r["days"][0], "ndays": len(r["days"]),
                    "out": r["out_tokens"], "closed": transcripts.used(r, CLOSE)})
    return sorted(out, key=lambda s: s["d0"])


def metrics(ses, since=None):
    sub = [s for s in ses if since is None or s["d0"] >= since]
    if not sub:
        return None
    per_day = defaultdict(int)
    for s in sub:
        per_day[s["d0"]] += 1
    big = [s for s in sub if s["out"] >= threshold()]
    n = len(sub)
    return {
        "n": n,
        "closed_pct": 100.0 * sum(s["closed"] for s in sub) / n,
        "multiday_pct": 100.0 * sum(s["ndays"] > 1 for s in sub) / n,
        "longest_days": max(s["ndays"] for s in sub),
        "new_per_day_median": statistics.median(per_day.values()),
        "big": len(big),
        "big_unclosed": sum(not s["closed"] for s in big),
    }


def report(days=30, all_projects=False):
    recs = transcripts.load(None if all_projects else ROOT)
    ses = sessions(recs)
    scope = "all projects" if all_projects else ROOT
    print(f"Sessions with real work in {scope}: {len(ses)} (transcripts read: {len(recs)})")
    if not ses:
        print("Nothing to measure yet. Work a few sessions and close them with /close.")
        return
    since = (date.today() - timedelta(days=days)).isoformat()
    for label, m in ((f"Last {days} days", metrics(ses, since)), ("All time", metrics(ses))):
        if not m:
            print(f"\n{label}: no sessions")
            continue
        print(f"\n{label}: {m['n']} sessions")
        print(f"  closed with /close      {m['closed_pct']:5.1f} %")
        print(f"  spread over >1 day      {m['multiday_pct']:5.1f} %   (longest: {m['longest_days']} days)")
        print(f"  new sessions per day    median {m['new_per_day_median']:.0f}")
        print(f"  >= {threshold() // 1000}k output tokens   {m['big']} sessions, {m['big_unclosed']} never closed")
    print("\nTranscripts older than Claude Code's retention period are gone, so 'all time' is a floor.")


def _load_state():
    try:
        with open(STATE, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def hook_stop() -> int:
    try:
        raw = sys.stdin.buffer.read().decode("utf-8", "replace")
        ev = json.loads(raw) if raw.strip() else {}
        if ev.get("stop_hook_active"):
            return 0
        path, sid = ev.get("transcript_path"), ev.get("session_id") or ""
        if not path or not os.path.isfile(path):
            return 0
        state = _load_state()
        if sid in state:
            return 0
        rec = transcripts.parse(path)
        if rec["sidechain"] or transcripts.used(rec, CLOSE) or rec["out_tokens"] < threshold():
            return 0
        state[sid] = {"ts": datetime.now().isoformat(timespec="minutes"), "out": rec["out_tokens"]}
        os.makedirs(os.path.dirname(STATE), exist_ok=True)
        tmp = STATE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(state, fh, indent=1)
        os.replace(tmp, STATE)
        reason = (
            f"[convergence] This session has produced about {rec['out_tokens'] // 1000}k output tokens "
            f"(threshold {threshold() // 1000}k) without /close. Before continuing, propose closing in five "
            "lines: (1) what was delivered against the session contract; (2) if the exit criterion was not "
            "met, exactly what is missing; (3) the parked items, for the user to decide in one go; "
            "(4) run /close. Do not open new topics. If the user prefers to keep going, keep going and do "
            "not insist: this reminder appears once per session."
        )
        sys.stdout.write(json.dumps({"decision": "block", "reason": reason}))
        return 0
    except Exception:
        return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--all-projects", action="store_true")
    ap.add_argument("--hook-stop", action="store_true", help="Stop hook mode (reads the event on stdin)")
    a = ap.parse_args()
    if a.hook_stop:
        return hook_stop()
    report(a.days, a.all_projects)
    return 0


if __name__ == "__main__":
    sys.exit(main())
