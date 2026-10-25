# -*- coding: utf-8 -*-
"""Read Claude Code session transcripts into one small record per session.

This module is the ONLY place that knows the transcript format. The format is not documented by
Anthropic; what is used here was observed on Claude Code 2.x (2026):

- transcripts live in  <claude config dir>/projects/<project slug>/<session id>.jsonl
  (the config dir is $CLAUDE_CONFIG_DIR if set, else ~/.claude);
- one line = one JSON object with `timestamp` (ISO 8601), `cwd`, `sessionId`, `isSidechain`,
  and `message` = {role, content, usage, id};
- `content` is a string or a list of blocks (`text`, `tool_use`, `tool_result`);
- an assistant reply can span several lines that repeat the same `message.id` and `usage`,
  so tokens are counted once per `message.id`, never once per line.

If the format changes, fix it here; every measure in tools/ is a view over `load()`.
Nothing here stores prompt text: a record keeps counts, dates and names of skills.
"""
from __future__ import annotations

import glob
import json
import os
import re
from datetime import datetime

RE_CMD = re.compile(r"\s*<command-name>\s*/?([^<]+?)\s*</command-name>")
# Prompts longer than this are context injected by the harness, not typed by a person.
PROMPT_MAX_CHARS = 3000


def config_dir() -> str:
    return os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(os.path.expanduser("~"), ".claude")


def _text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(b.get("text") or "" for b in content
                       if isinstance(b, dict) and b.get("type") == "text")
    return ""


def parse(path: str) -> dict:
    """One transcript -> one record. Tolerates a torn last line."""
    rec = {"path": path, "sid": None, "cwd": None, "sidechain": False, "days": set(),
           "human_chars": 0, "skills": {}, "commands": {}, "first_ts": None, "last_ts": None}
    out_by_msg = {}
    first_user_seen = False
    try:
        fh = open(path, encoding="utf-8", errors="replace")
    except OSError:
        rec["days"] = []
        rec["out_tokens"] = 0
        return rec
    with fh:
        for line in fh:
            try:
                o = json.loads(line)
            except ValueError:
                continue
            if not isinstance(o, dict):
                continue
            rec["sid"] = rec["sid"] or o.get("sessionId")
            rec["cwd"] = rec["cwd"] or o.get("cwd")
            msg = o.get("message") or {}
            role = msg.get("role") or o.get("type")
            if role == "user" and not first_user_seen:
                first_user_seen = True
                rec["sidechain"] = bool(o.get("isSidechain"))
            ts = o.get("timestamp")
            if ts:
                try:
                    dt = datetime.fromisoformat(ts.replace("Z", "+00:00")).replace(tzinfo=None)
                except ValueError:
                    dt = None
                if dt:
                    rec["days"].add(dt.date().isoformat())
                    iso = dt.isoformat()
                    rec["first_ts"] = min(rec["first_ts"] or iso, iso)
                    rec["last_ts"] = max(rec["last_ts"] or iso, iso)
            content = msg.get("content")
            if role == "user":
                if isinstance(content, str) and content.lstrip().startswith("<command-name>"):
                    m = RE_CMD.match(content)
                    if m:
                        name = m.group(1).strip().lower()
                        rec["commands"][name] = rec["commands"].get(name, 0) + 1
                else:
                    t = _text(content).strip()
                    if t and not t.startswith("<") and len(t) <= PROMPT_MAX_CHARS:
                        rec["human_chars"] += len(t)
            usage = msg.get("usage")
            if role == "assistant" and isinstance(usage, dict):
                key = msg.get("id") or f"line{len(out_by_msg)}"
                out_by_msg[key] = max(out_by_msg.get(key, 0), usage.get("output_tokens") or 0)
            if isinstance(content, list):
                for b in content:
                    if isinstance(b, dict) and b.get("type") == "tool_use" and b.get("name") == "Skill":
                        sk = str((b.get("input") or {}).get("skill", "?")).lower()
                        rec["skills"][sk] = rec["skills"].get(sk, 0) + 1
    rec["days"] = sorted(rec["days"])
    rec["out_tokens"] = sum(out_by_msg.values())
    return rec


def _norm_path(p: str | None) -> str:
    return (p or "").replace("\\", "/").rstrip("/").lower()


def slug(path: str) -> str:
    """Folder name Claude Code uses for a project: every non-alphanumeric character becomes '-'."""
    return re.sub(r"[^A-Za-z0-9]", "-", os.path.abspath(path))


def load(project_root: str | None = None) -> list[dict]:
    """Every transcript under the config dir; with project_root, only sessions run inside it.

    With project_root, only folders whose name starts with the project's slug are read (that covers
    subfolders too); the cwd recorded in each transcript is then checked, so a sibling folder whose
    name merely shares the prefix is not counted."""
    pattern = (slug(project_root) + "*") if project_root else "*"
    files = glob.glob(os.path.join(config_dir(), "projects", pattern, "*.jsonl"))
    recs = [parse(f) for f in files]
    if project_root:
        root = _norm_path(os.path.abspath(project_root))
        recs = [r for r in recs if _norm_path(r["cwd"]) == root
                or _norm_path(r["cwd"]).startswith(root + "/")]
    return recs


def used(rec: dict, name: str) -> bool:
    """True if the session ran skill `name`, typed or invoked by the model (plugin prefixes ignored)."""
    names = {k.split(":")[-1] for k in list(rec["skills"]) + list(rec["commands"])}
    return name.lower() in names
