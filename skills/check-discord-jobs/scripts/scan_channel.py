#!/usr/bin/env python3
"""Scroll a Discord channel tab (already open in the debug browser) via agent-browser and merge the
message extractions into one JSON file.

Usage:
  python3 scan_channel.py <slug> [--stop-date YYYY-MM-DD] [--max-rounds N]

Run it with the channel open and selected (`agent-browser tab list` shows the selection). It extracts
the visible messages, scrolls up, merges by message id, and stops when the oldest message is at or
before --stop-date (default: 7 days ago), when three rounds add nothing, or when there is nothing
left to scroll. Output: <workspace>/<discord_cache_dir>/<today>/raw_<slug>.json
(discord_cache_dir defaults to JDs/discord).
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                                "job-apply-core", "scripts"))

EXTRACT = r"""
(() => JSON.stringify([...document.querySelectorAll('[id^="message-content-"], [data-list-item-id^="chat-messages"]')].map(el => ({
  id: (el.id.match(/message-content-(\d+)/) || [,''])[1] ||
      (el.getAttribute('data-list-item-id') || '').split('-').pop(),
  author: el.querySelector('h3, [class*="header"] [class*="name"]')?.innerText || '',
  time: el.querySelector('time')?.getAttribute('datetime') || '',
  text: el.innerText,
  links: [...el.querySelectorAll('a')].map(a => a.href)
})).filter(m => m.id)))()
"""

SCROLL = """
(() => {
  const scrollers = [...document.querySelectorAll('div[class*="scroller"]')]
    .filter(el => el.scrollHeight > el.clientHeight + 50);
  if (!scrollers.length) return 'none';
  const s = scrollers.sort((a,b) => b.scrollHeight - a.scrollHeight)[0];
  s.scrollTop = Math.max(0, s.scrollTop - s.clientHeight * 1.6);
  return String(s.scrollTop);
})()
"""


def agent_browser() -> str:
    extra = os.pathsep.join([os.path.expanduser("~/.npm-global/bin"), os.path.expanduser("~/.local/bin")])
    path = shutil.which("agent-browser", path=os.environ.get("PATH", "") + os.pathsep + extra)
    if not path:
        raise SystemExit("ERROR: agent-browser not found (npm install -g agent-browser@latest)")
    return path


def ab(args: list[str], timeout: int = 60) -> str:
    r = subprocess.run([agent_browser()] + args, capture_output=True, text=True, timeout=timeout)
    return r.stdout.strip()


def parse_extract(out: str) -> list[dict]:
    """agent-browser prints the JSON string, sometimes double-encoded. Unwrap robustly."""
    for _ in range(2):
        try:
            data = json.loads(out)
        except Exception:
            return []
        if isinstance(data, list):
            return data
        if isinstance(data, str):
            out = data
            continue
        return []
    return []


def extract() -> list[dict]:
    msgs = parse_extract(ab(["eval", EXTRACT]))
    if not msgs:
        ab(["wait", "2000"])
        msgs = parse_extract(ab(["eval", EXTRACT]))
    return msgs


def oldest_date(merged: dict) -> str:
    dates = sorted(m.get("time", "")[:10] for m in merged.values() if m.get("time"))
    return dates[0] if dates else ""


def out_dir() -> Path:
    import jak_config
    cfg = jak_config.load()
    rel = cfg.get("discord_cache_dir") or "JDs/discord"
    d = cfg.path("workspace") / rel / time.strftime("%Y-%m-%d")
    d.mkdir(parents=True, exist_ok=True)
    return d


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("slug")
    ap.add_argument("--stop-date", default=(datetime.date.today() - datetime.timedelta(days=7)).isoformat())
    ap.add_argument("--max-rounds", type=int, default=25)
    a = ap.parse_args(argv)
    merged: dict = {}
    stale = 0
    for i in range(a.max_rounds):
        msgs = extract()
        new = 0
        for m in msgs:
            if m["id"] not in merged:
                merged[m["id"]] = m
                new += 1
        oldest = oldest_date(merged)
        print(f"  round {i + 1}: +{new} total={len(merged)} oldest={oldest}", flush=True)
        if oldest and oldest <= a.stop_date:
            break
        stale = stale + 1 if new == 0 else 0
        if stale >= 3:
            break
        if ab(["eval", SCROLL]) == "none":
            break
        time.sleep(1.8)
    data = sorted(merged.values(), key=lambda m: m.get("time", ""))
    path = out_dir() / f"raw_{a.slug}.json"
    path.write_text(json.dumps(data, indent=1), encoding="utf-8")
    print(f"  saved {len(data)} messages -> {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
