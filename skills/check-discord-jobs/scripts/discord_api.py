#!/usr/bin/env python3
"""Fetch Discord channel messages via the REST API, run INSIDE the open Discord tab.

Faster and more complete than DOM scraping: no scrolling, embeds and link-only
posts included, and an exact lower bound by date via snowflakes.

Usage:
  python3 discord_api.py <slug> --url https://discord.com/channels/<server>/<channel> [--tab t14]
                         [--last N] [--after-date YYYY-MM-DD] [--limit N] [--out PATH]

The channel id always comes from --url and is matched against the tab URL before
fetching; if the tab drifted to another channel, this run's own tab is navigated
back to the requested channel first.

Run with the Discord tab open in the debug browser. The channel id is read from
the TAB URL (location.pathname) and every returned message id is validated
against it. Auth: Authorization header from ~/.config/job-apply-kit/discord_token
(or $JAK_DISCORD_TOKEN). The HttpOnly Cloudflare cookies are sent automatically
by the same-origin fetch; only the header is needed from us.

Endpoint observed on the live session (see references/discord-api-notes.md):
  GET /api/v9/channels/<channel_id>/messages?limit=<1..100>[&before=<snowflake>][&after=<snowflake>]

Output: <workspace>/<discord_cache_dir>/<today>/raw_<slug>.json — same message
shape as scan_channel.py DOM output ({id, author, time, text, links}), so
downstream dedup/verdict code is unchanged.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                                "job-apply-core", "scripts"))

DISCORD_EPOCH_MS = 1420070400000
API_FETCH = r'''(async (ch, token, qs) => { const r = await fetch('/api/v9/channels/' + ch + '/messages?' + qs, { headers: { Authorization: token } }); const j = await r.json(); const retry = r.headers.get('Retry-After'); return JSON.stringify({ status: r.status, retry: retry ? parseFloat(retry) : null, body: j }); })'''
PAGE_URL = r"(() => location.pathname)()"


def agent_browser() -> str:
    import shutil
    extra = os.pathsep.join([os.path.expanduser("~/.npm-global/bin"), os.path.expanduser("~/.local/bin")])
    path = shutil.which("agent-browser", path=os.environ.get("PATH", "") + os.pathsep + extra)
    if not path:
        raise SystemExit("ERROR: agent-browser not found (npm install -g agent-browser@latest)")
    return path


def ab(args: list[str], timeout: int = 60) -> str:
    import subprocess
    r = subprocess.run([agent_browser()] + args, capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        sys.stderr.write(f"agent-browser {args[0]} failed (rc={r.returncode}): {(r.stderr or r.stdout or '').strip()[:200]}\n")
    return (r.stdout or "").strip()


def load_token() -> str:
    tok = os.environ.get("JAK_DISCORD_TOKEN", "").strip()
    if tok:
        return tok
    p = token_path()
    if p.is_file():
        tok = p.read_text(encoding="utf-8").strip()
        if tok:
            return tok
    return ""


def token_path() -> Path:
    return Path(os.path.expanduser("~/.config/job-apply-kit/discord_token"))


def capture_token(har: str = "") -> str:
    """Get a fresh Authorization token with agent-browser only: record a HAR while the
    Discord tab reloads (the app fires /api/v9 requests with its own token), then read
    the header out of the HAR. The channel tab must already be selected. No MCP, no
    DevTools, no localStorage."""
    har = har or str(Path(os.path.expanduser(
        "~/.config/job-apply-kit/discord_token.har.tmp")))
    Path(har).parent.mkdir(parents=True, exist_ok=True)
    here = current_path()
    ab(["network", "har", "start", har])
    ab(["reload"])
    if here.startswith("/channels/"):
        wait_for_channel(channel_id_from_url("https://x" + here), timeout_s=30)
    time.sleep(4)
    ab(["network", "har", "stop"])
    time.sleep(1)
    try:
        data = json.loads(Path(har).read_text(encoding="utf-8"))
    except Exception as e:
        raise SystemExit(f"ERROR: HAR capture failed ({e}); is the tab on discord.com?")
    token = ""
    for entry in data.get("log", {}).get("entries", []):
        url = (entry.get("request") or {}).get("url", "")
        if "/api/v9/" not in url:
            continue
        for h in (entry.get("request") or {}).get("headers", []):
            if h.get("name", "").lower() == "authorization" and h.get("value"):
                token = h["value"].strip()
                break
        if token:
            break
    Path(har).unlink(missing_ok=True)
    if not token:
        raise SystemExit("ERROR: no Authorization header found in the HAR — is the tab "
                         "logged in to discord.com?")
    p = token_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(token + "\n", encoding="utf-8")
    try:
        p.chmod(0o600)
    except OSError:
        pass
    return token


def eval_js(expr: str, timeout: int = 60) -> str:
    out = ab(["eval", expr], timeout=timeout)
    # agent-browser prints the JSON-encoded result; unwrap once.
    try:
        v = json.loads(out)
        return v if isinstance(v, str) else out
    except Exception:
        return out


def channel_id_from_url(url: str) -> str:
    m = re.search(r"/channels/[^/]+/(\d+)\s*/?\s*$", url or "")
    if not m:
        raise SystemExit(f"ERROR: not a Discord channel URL: {url!r}")
    return m.group(1)


def current_path() -> str:
    return eval_js(PAGE_URL) or ""


def tab_list() -> list[dict]:
    out = ab(["tab", "list", "--json"])
    try:
        data = json.loads(out)
    except Exception:
        return []
    d = data.get("data", data) if isinstance(data, dict) else data
    return d.get("tabs", []) if isinstance(d, dict) else (d if isinstance(d, list) else [])


def find_tab_for_channel(ch: str) -> str:
    """Stable-tab refs (t<N>) die on daemon restarts — match the channel in the URL."""
    for t in tab_list():
        u = t.get("url", "")
        if "/channels/" in u and u.rstrip("/").endswith("/" + ch):
            return t.get("tabId") or ""
    return ""


def wait_for_channel(ch: str, timeout_s: int = 25) -> bool:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        here = current_path()
        if here.startswith("/channels/") and channel_id_from_url("https://x" + here) == ch:
            return True
        time.sleep(1.5)
    return False


def ensure_channel_tab(url: str, tab: str) -> tuple[str, bool, str]:
    """Get a tab on the requested channel. Returns (channel_id, opened_by_us, ref).

    - explicit --tab wins: select it and navigate it if it drifted (operator decision);
    - else reuse an existing tab already showing the channel (rule 3 settle mode);
    - else open a NEW tab (ours — safe to close later).
    Channel id always comes from --url, never from a tab's current state."""
    ch = channel_id_from_url(url)
    opened = False
    ref = tab
    if not ref:
        ref = find_tab_for_channel(ch)
    if ref:
        ab(["tab", ref])
        time.sleep(1)
        if wait_for_channel(ch, timeout_s=6):
            return ch, opened, ref
    if not ref:
        ab(["tab", "new", url])
        opened = True
        time.sleep(3)
    else:
        ab(["open", url])
        time.sleep(2)
    if not wait_for_channel(ch):
        raise SystemExit(f"ERROR: no tab could be placed on channel {ch} (last: {current_path()!r})")
    return ch, opened, ref or find_tab_for_channel(ch)


def api_call(ch: str, token: str, qs: str) -> tuple[int, object, float | None]:
    expr = f"{API_FETCH}('{ch}','{token}','{qs}')"
    out = eval_js(expr, timeout=90)
    try:
        data = json.loads(out)
    except Exception:
        raise SystemExit(f"ERROR: unparseable eval output: {out[:200]}")
    return int(data.get("status", 0)), data.get("body"), data.get("retry")


def to_message(m: dict) -> dict:
    parts = [m.get("content") or ""]
    links: list[str] = re.findall(r"https?://\S+", parts[0])
    for e in m.get("embeds") or []:
        for key in ("title", "description", "url"):
            v = e.get(key)
            if v:
                parts.append(str(v))
        au = (e.get("author") or {}).get("name")
        if au:
            parts.append(str(au))
        for f in e.get("fields") or []:
            if f.get("value"):
                parts.append(str(f["value"]))
        for img in (e.get("image"), e.get("thumbnail")):
            u = (img or {}).get("url")
            if u:
                links.append(u)
    for a in m.get("attachments") or []:
        if a.get("url"):
            links.append(a["url"])
        if a.get("filename"):
            parts.append(str(a["filename"]))
    author = m.get("author") or {}
    return {
        "id": m["id"],
        "author": author.get("global_name") or author.get("username") or "",
        "time": m.get("timestamp") or "",
        "text": "\n".join(p for p in parts if p),
        "links": list(dict.fromkeys(links)),
    }


def fetch_messages(ch: str, token: str, want: int, after_date: str, limit: int) -> list[dict]:
    got: dict[str, dict] = {}
    qs_parts = [f"limit={min(max(limit, 1), 100)}"]
    if after_date:
        ms = int(datetime.datetime.fromisoformat(after_date).replace(
            tzinfo=datetime.timezone.utc).timestamp() * 1000)
        qs_parts.append(f"after={(ms - DISCORD_EPOCH_MS) << 22}")
    before = ""
    recaptured = False
    for _round in range(20):
        qs = "&".join(qs_parts + ([f"before={before}"] if before else []))
        status, body, retry = api_call(ch, token, qs)
        if status == 401 and not recaptured:
            print("  401: token stale, recapturing via agent-browser HAR", flush=True)
            token = capture_token()
            recaptured = True
            continue
        if status == 429:
            wait = min(retry or 2.0, 10.0)
            print(f"  rate limited, sleeping {wait}s", flush=True)
            time.sleep(wait)
            continue
        if status != 200:
            raise SystemExit(f"ERROR: API status {status}: {json.dumps(body)[:300]}")
        msgs = body if isinstance(body, list) else []
        new = 0
        for m in msgs:
            if m["id"] not in got:
                got[m["id"]] = to_message(m)
                new += 1
        print(f"  fetched {len(msgs)} (+{new} new, total {len(got)})", flush=True)
        if len(got) >= want or not msgs:
            break
        before = min(m["id"] for m in msgs)
        time.sleep(0.8)
    return sorted(got.values(), key=lambda m: m.get("time", ""))


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
    ap.add_argument("--url", required=True, help="channel URL https://discord.com/channels/<server>/<channel>")
    ap.add_argument("--tab", default="", help="stable tab ref (t<N>) of the Discord channel tab")
    ap.add_argument("--last", type=int, default=20, help="collect at least N newest messages (default 20)")
    ap.add_argument("--after-date", default="", help="only messages after this YYYY-MM-DD (UTC)")
    ap.add_argument("--limit", type=int, default=50, help="per-request limit, 1..100 (default 50)")
    ap.add_argument("--out", default="", help="override output path")
    ap.add_argument("--capture-token", action="store_true",
                    help="refresh the stored token via agent-browser HAR capture (reload + read "
                         "Authorization from a real /api/v9 request), then continue")
    a = ap.parse_args(argv)

    token = load_token()
    if a.capture_token or not token:
        if not a.capture_token:
            print("  no token stored, capturing via agent-browser HAR", flush=True)
        else:
            print("  capturing fresh token via agent-browser HAR", flush=True)
        token = capture_token()
    ch, opened, ref = ensure_channel_tab(a.url, a.tab)
    print(f"  channel {ch} (tab {ref or 'selected'}, opened_by_us={opened})", flush=True)
    messages = fetch_messages(ch, token, a.last, a.after_date, a.limit)
    path = Path(a.out) if a.out else out_dir() / f"raw_{a.slug}.json"
    path.write_text(json.dumps(messages, indent=1), encoding="utf-8")
    print(f"  saved {len(messages)} messages -> {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
