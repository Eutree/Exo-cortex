# -*- coding: utf-8 -*-
"""Tests over synthetic transcripts and a synthetic memory folder. Run: python -m pytest tests"""
import io
import json
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import convergence  # noqa: E402
import memory_check  # noqa: E402
import quiz  # noqa: E402
import transcripts  # noqa: E402


def _line(**kw):
    return json.dumps(kw) + "\n"


def _session(path, sid, cwd, days, closed=False, out_tokens=100, repeat_lines=3):
    lines = []
    for d in days:
        ts = f"{d}T10:00:00Z"
        lines.append(_line(sessionId=sid, cwd=cwd, timestamp=ts,
                           message={"role": "user", "content": "x" * 300}))
        # one assistant reply split over several lines that repeat id and usage
        for _ in range(repeat_lines):
            lines.append(_line(sessionId=sid, cwd=cwd, timestamp=ts,
                               message={"role": "assistant", "id": f"msg-{sid}-{d}",
                                        "usage": {"output_tokens": out_tokens},
                                        "content": [{"type": "text", "text": "ok"}]}))
    if closed:
        lines.append(_line(sessionId=sid, cwd=cwd, timestamp=f"{days[-1]}T11:00:00Z",
                           message={"role": "user", "content": "<command-name>/close</command-name>"}))
    lines.append('{"torn": ')  # torn last line must be tolerated
    path.write_text("".join(lines), encoding="utf-8")


def test_tokens_counted_once_per_message(tmp_path):
    f = tmp_path / "a.jsonl"
    _session(f, "s1", "/w", ["2026-10-01"], out_tokens=500, repeat_lines=4)
    rec = transcripts.parse(str(f))
    assert rec["out_tokens"] == 500
    assert rec["days"] == ["2026-10-01"]
    assert rec["human_chars"] == 300


def test_close_detected_typed_and_invoked(tmp_path):
    f = tmp_path / "a.jsonl"
    _session(f, "s1", "/w", ["2026-10-01"], closed=True)
    assert transcripts.used(transcripts.parse(str(f)), "close")
    rec = {"skills": {"myplugin:close": 1}, "commands": {}}
    assert transcripts.used(rec, "close")
    assert not transcripts.used({"skills": {}, "commands": {"closet": 1}}, "close")


def test_load_filters_by_project(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    root = tmp_path / "work"
    inside = tmp_path / "projects" / transcripts.slug(str(root / "sub"))
    sibling = tmp_path / "projects" / transcripts.slug(str(tmp_path / "workshop"))
    other = tmp_path / "projects" / "unrelated"
    for d in (inside, sibling, other):
        d.mkdir(parents=True)
    _session(inside / "in.jsonl", "in", str(root / "sub"), ["2026-10-01"])
    _session(sibling / "sib.jsonl", "sib", str(tmp_path / "workshop"), ["2026-10-01"])
    _session(other / "x.jsonl", "x", str(root), ["2026-10-01"])   # outside the slug: not read
    assert {r["sid"] for r in transcripts.load(str(root))} == {"in"}
    assert {r["sid"] for r in transcripts.load(None)} == {"in", "sib", "x"}


def test_convergence_metrics(tmp_path):
    recs = []
    for i, (days, closed) in enumerate([(["2026-10-01"], True), (["2026-10-01", "2026-10-03"], False)]):
        f = tmp_path / f"{i}.jsonl"
        _session(f, f"s{i}", "/w", days, closed=closed)
        recs.append(transcripts.parse(str(f)))
    m = convergence.metrics(convergence.sessions(recs))
    assert m["n"] == 2
    assert m["closed_pct"] == 50.0
    assert m["multiday_pct"] == 50.0
    assert m["longest_days"] == 2


def test_hook_fires_once_and_never_on_closed(tmp_path, monkeypatch):
    monkeypatch.setattr(convergence, "STATE", str(tmp_path / ".exo" / "nudges.json"))
    monkeypatch.setenv("EXO_NUDGE_TOKENS", "1000")
    big = tmp_path / "big.jsonl"
    _session(big, "big", "/w", ["2026-10-01"], out_tokens=5000)

    def run(path, sid):
        monkeypatch.setattr(sys, "stdin", io.TextIOWrapper(io.BytesIO(
            json.dumps({"transcript_path": str(path), "session_id": sid}).encode())))
        out = io.StringIO()
        monkeypatch.setattr(sys, "stdout", out)
        assert convergence.hook_stop() == 0
        return out.getvalue()

    first = run(big, "big")
    assert json.loads(first)["decision"] == "block"
    assert run(big, "big") == ""
    closed = tmp_path / "closed.jsonl"
    _session(closed, "closed", "/w", ["2026-10-01"], out_tokens=5000, closed=True)
    assert run(closed, "closed") == ""


def test_hook_survives_garbage(monkeypatch):
    monkeypatch.setattr(sys, "stdin", io.TextIOWrapper(io.BytesIO(b"not json")))
    assert convergence.hook_stop() == 0


def _memory(tmp_path, monkeypatch, day):
    mem = tmp_path / "memory"
    for sub in ("log", "knowledge", "checks"):
        (mem / sub).mkdir(parents=True)
    monkeypatch.setattr(quiz, "LOG", mem / "log")
    monkeypatch.setattr(quiz, "KNOWLEDGE", mem / "knowledge")
    monkeypatch.setattr(quiz, "DECISIONS", mem / "decisions.md")
    monkeypatch.setattr(quiz, "CHECKS", mem / "checks")
    monkeypatch.setattr(quiz, "HISTORY", mem / "checks" / "_history.json")
    rows = "\n".join(f"| {day} | Decision number {i} | Because of reason {i} |" for i in range(8))
    (mem / "decisions.md").write_text("| Date | Decision | Reason |\n|---|---|---|\n"
                                      "| example | ignored | ignored |\n" + rows + "\n", encoding="utf-8")
    (mem / "log" / f"{day}-topic.md").write_text(
        "# Log\n\n## Learnings\n- The monthly report double counts returns when the store closes early.\n"
        "  It is fixed by filtering on the closing date.\n\n## Pending\n- nothing\n", encoding="utf-8")
    (mem / "knowledge" / "lead-time.md").write_text(
        f"---\ndescription: How lead time is computed for imports\nlast_verified: {day}\n---\n", encoding="utf-8")


def test_quiz_select_is_reproducible_and_reads_all_sources(tmp_path, monkeypatch):
    day = (date.today() - timedelta(days=5)).isoformat()
    _memory(tmp_path, monkeypatch, day)
    since, until = (date.today() - timedelta(days=30)).isoformat(), date.today().isoformat()
    a, pool = quiz.select("2026-10", since, until)
    b, _ = quiz.select("2026-10", since, until)
    assert [x["id"] for x in a] == [x["id"] for x in b]
    assert pool == {"decision": 8, "learning": 1, "knowledge": 1}
    assert len(a) == 10
    learning = next(x for x in a if x["kind"] == "learning")
    assert "filtering on the closing date" in learning["text"]


def test_quiz_record_brings_back_misses(tmp_path, monkeypatch):
    day = (date.today() - timedelta(days=5)).isoformat()
    _memory(tmp_path, monkeypatch, day)
    since, until = (date.today() - timedelta(days=30)).isoformat(), date.today().isoformat()
    items, _ = quiz.select("2026-09", since, until)
    for k, i in enumerate(items):
        i.update(question="q", answer="a", correct="a" if k else "b")
    out = quiz.record({"month": "2026-09", "items": items})
    assert out.is_file() and "9/10" in out.read_text(encoding="utf-8")
    nxt, _ = quiz.select("2026-10", since, until)
    assert any(x.get("repeat") and x["id"] == items[0]["id"] for x in nxt)


def test_memory_check_finds_each_problem(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "cfg"))
    root = tmp_path / "proj"
    mem = root / "memory"
    (mem / "knowledge").mkdir(parents=True)
    (mem / "log").mkdir()
    w = lambda p, t: p.write_text(t, encoding="utf-8")  # noqa: E731
    w(mem / "knowledge" / "lead-time.md",
      "---\ndescription: How lead time is computed for imports\nlast_verified: 2026-05-01\n---\n")
    w(mem / "knowledge" / "lead-time-imports.md",
      "---\ndescription: Lead time of imports, step by step\nlast_verified: 2026-10-20\n---\n")
    w(mem / "knowledge" / "no-header.md", "# Just a title\n")
    w(mem / "knowledge" / "bad-date.md", "---\ndescription: Something useful\nlast_verified: 2026-13-45\n---\n")
    w(mem / "knowledge" / "README.md", "not a memory")
    w(mem / "decisions.md", "# Decisions\n\n| Date | Decision | Reason |\n|---|---|---|\n"
      "| example | x | y |\n| 2026-10-01 | Use X | |\n| 2026-10-02 | Use Y | Because Z is slow |\n"
      "| 1 Oct | Use W | Because |\n")
    w(mem / "log" / "2026-10-01-a.md", "---\ndescription: <one line: what was done>\n---\n")
    w(mem / "log" / "2026-10-02-b.md", "---\ndescription: Did the thing; the report is pending\n---\n")
    secs = "".join(f"## 2026-10-{d:02d} · t{d}\n**State.** x\n\n" for d in (24, 23, 22, 21, 20, 10, 5))
    w(mem / "LAST.md", "# Where we left off\n\n" + secs)
    auto = tmp_path / "cfg" / "projects" / transcripts.slug(str(root)) / "memory"
    auto.mkdir(parents=True)
    w(auto / "MEMORY.md", "index")
    w(auto / "user_role.md", "x")

    r = memory_check.check(root, date(2026, 10, 25))
    assert [x["file"] for x in r["stale"]] == ["memory/knowledge/lead-time.md"]
    assert {(x["file"], x["field"]) for x in r["incomplete"]} == {
        ("memory/knowledge/no-header.md", "description"), ("memory/knowledge/no-header.md", "last_verified"),
        ("memory/knowledge/bad-date.md", "last_verified")}
    assert [x["files"] for x in r["duplicates"]] == [["memory/knowledge/lead-time-imports.md",
                                                      "memory/knowledge/lead-time.md"]]
    assert [x["line"] for x in r["decisions_no_reason"]] == [6]
    assert [x["line"] for x in r["decisions_no_date"]] == [8]
    assert r["logs_no_description"] == ["memory/log/2026-10-01-a.md"]
    assert r["last_old_sections"] == 2
    assert r["auto_memory"]["files"] == 1 and r["auto_memory"]["newest"] == ["user_role.md"]
    assert "things to look at" in memory_check.report(r, root)


def test_memory_check_clean_and_empty_folders(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "cfg"))
    r = memory_check.check(tmp_path / "nothing-here", date(2026, 10, 25))
    assert memory_check.report(r, tmp_path).endswith("Nothing to fix.")
    shipped = memory_check.check(memory_check.ROOT, date(2026, 10, 25))
    assert not any(shipped[k] for k in ("stale", "incomplete", "duplicates", "decisions_no_reason",
                                         "decisions_no_date", "logs_no_description", "last_old_sections"))
