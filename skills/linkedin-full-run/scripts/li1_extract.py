#!/usr/bin/env python3
"""li1_extract.py — Phase 1 (REVISED): LinkedIn search sweep.

Runs the fixed dorking query list on the LinkedIn posts search results page,
applies Posts + Sort-by-Latest filters, scroll-collects posts, extracts FULL
post text (expands "see more" in place, no navigation away), writes posts.csv
(post_link | full_text | should_apply | how_to_apply | comment) + run_log.txt.
Idempotent: dedup against seen.json; early-stops a query when its deeper
results look already-swept.

Selectors verified live 2026-09-14: results live under
`[data-testid="lazy-column"] > div[data-display-contents="true"]` (React
re-implementation — no data-urn, no feed-shared-update-v2 classes); post text
in `span[data-testid="expandable-text-box"]`; see-more button text `… more`;
sort flow: click trigger containing "Date posted"/"Sort by" text, then click
`[role="button"]` whose text is exactly `Latest` (URL gains
`sortBy=["date_posted"]`); Posts filter is `[role="radio"]`.

Usage: python3 JDs/linkedin/li1_extract.py [--date D] [--min N] [--queries "a;b"]
"""
import argparse
import json
import os
import time

import li_common as L

# --- extraction (verified live) ---
LIST_SEL = '[data-testid="lazy-column"]'
POST_SEL = f'{LIST_SEL} > div[data-display-contents="true"]'
TEXT_SEL = 'span[data-testid="expandable-text-box"]'

COLLECT_JS = r"""
(function(){
  var posts = [...document.querySelectorAll('POSTSEL')]
    .filter(c => (c.innerText || '').startsWith('Feed post') && (c.innerText || '').length > 200);
  var out = [];
  for (var p of posts) {
    var t = p.querySelector('TEXTSEL');
    var text = t ? t.innerText : (p.innerText || '');
    // permalink: author profile link + name as fallback identity; the search
    // re-impl exposes no data-urn, so we key on author + first 80 chars
    var a = p.querySelector('a[href*="/in/"]');
    var author = a ? a.href.split('?')[0] : '';
    out.push({author: author, text: text.slice(0, 12000),
              key: author + '|' + text.slice(0, 80)});
  }
  return JSON.stringify(out);
})()
""".replace("POSTSEL", POST_SEL).replace("TEXTSEL", TEXT_SEL)

SCROLL_JS = r"""
(function(){
  // The results list sometimes lives in its own scrollable container, so move
  // BOTH the window and any ancestor scroller; a window-only scrollBy stops
  // working once the lazy-column takes over and silently caps the sweep.
  var step = Math.max(1200, Math.round(window.innerHeight * 0.9));
  window.scrollBy(0, step);
  var lc = document.querySelector('[data-testid="lazy-column"]');
  var n = 0, el = lc;
  while (el && el !== document.body) {
    if (el.scrollHeight - el.clientHeight > 200) {
      el.scrollTop += step;
      if (el.scrollTop > 0) n++;
    }
    el = el.parentElement;
  }
  return JSON.stringify({y: Math.round(window.scrollY), scrollers: n,
                         docH: document.body ? document.body.scrollHeight : 0});
})()
"""

EXPAND_JS = r"""
(function(){
  var posts = [...document.querySelectorAll('POSTSEL')];
  var n = 0;
  for (var p of posts) {
    if (p.querySelector('TEXTSEL')) continue;  // already expanded
    var btn = [...p.querySelectorAll('button')].find(b => (b.innerText || '').includes('more'));
    if (btn) { try { btn.click(); n++; } catch (e) {} }
  }
  return String(n);
})()
""".replace("POSTSEL", POST_SEL).replace("TEXTSEL", TEXT_SEL)

def parse_batch(out):
    """cdp.py eval prints a JSON-encoded string; unwrap it robustly."""
    val = parse_json(out)
    return val if isinstance(val, list) else []


def parse_json(out):
    """Unwrap cdp.py's double-encoded output into a Python object."""
    if not out:
        return None
    s = out.strip().splitlines()[-1]
    for _ in range(3):
        try:
            s = json.loads(s)
        except Exception:
            return None
        if not isinstance(s, str):
            return s
    return None


PAGE_STATE_JS = r"""
(function(){
  var lc = document.querySelector('[data-testid="lazy-column"]');
  return JSON.stringify({
    href: location.href,
    sortBy: location.href.indexOf('sortBy') >= 0,
    posts: lc ? lc.children.length : 0
  });
})()
"""


def verify_page(tab, rd):
    """Filters come from the URL only (Posts + Sort by Latest are both encoded
    there), so this just confirms the sorted URL and rendered results.
    No dropdown clicking: the sort control is a set of React <label> rows and
    clicking it is unnecessary and unreliable."""
    state = parse_json(L.cdp_eval(tab, PAGE_STATE_JS)) or {}
    ok = bool(state.get("sortBy")) and int(state.get("posts") or 0) > 0
    L.log(rd, f"  page: sortBy={state.get('sortBy')} posts={state.get('posts')} "
              f"-> {'OK' if ok else 'CHECK'}")
    return ok


def merge(rows, batch, seen_urls, source_query=""):
    """One row per unique post. Identity = author URL + text hash, stored in
    post_link, so two posts by the same author never collapse into one row."""
    by_key = {r["post_link"]: r for r in rows}
    added = 0
    for it in batch:
        text = (it.get("text") or "")
        if not text.strip():
            continue
        ident = L.post_identity(it.get("author", ""), text)
        if ident in by_key:
            continue
        already_seen = (it.get("author") in seen_urls) or (ident in seen_urls)
        verdict = ("skipped-duplicate" if already_seen
                   else "new" if L.looks_like_job(text) else "not-a-job")
        by_key[ident] = {
            "post_link": ident,
            "full_text": text.replace("\r", " "),
            "should_apply": "",
            "how_to_apply": "",
            "comment": "",
            "seen_before": "yes" if already_seen else "no",
            "verdict": verdict,
            "source_query": source_query,
        }
        added += 1
    return list(by_key.values()), added


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None)
    ap.add_argument("--min", type=int, default=L.MIN_ITEMS)
    ap.add_argument("--queries", default=None, help="';'-separated override")
    ap.add_argument("--rounds-per-query", type=int, default=25,
                    help="hard cap on scroll rounds per query")
    ap.add_argument("--idle-rounds", type=int, default=4,
                    help="stop a query after N consecutive scroll rounds that "
                         "yield no new posts (deep-scroll tolerance)")
    ap.add_argument("--scroll-wait", type=float, default=3.0,
                    help="seconds to wait after each scroll step")
    args = ap.parse_args()

    rundir = L.run_dir(args.date)
    posts_csv = os.path.join(rundir, "posts.csv")
    seen_path = os.path.join(L.cache_root(), "seen.json")
    seen = L.load_json(seen_path, [])
    seen_urls = {s.get("post_url") for s in seen if s.get("post_url")}
    queries = (args.queries.split(";") if args.queries else L.SEARCH_QUERIES)

    L.log(rundir, f"li1 REVISED start; {len(queries)} queries; target >= {args.min}")

    tab = None
    try:
        tab = L.cdp_new_tab(L.search_url(queries[0]))
        time.sleep(8)
        href = (L.cdp_eval(tab, "location.href") or "")
        body = L.cdp_eval(tab, "document.body ? document.body.innerText.slice(0,300) : ''")
        if "login" in href.lower() or "authwall" in href.lower() or "Sign in" in body:
            L.log(rundir, "LOGIN WALL — hard stop, tab left open")
            return 2

        rows = L.read_csv(posts_csv, L.ITEMS_CSV_FIELDS)
        total_new = 0
        for qi, q in enumerate(queries, 1):
            L.log(rundir, f"query {qi}/{len(queries)}: {q}")
            L.cdp_eval(tab, f"location.href = {json.dumps(L.sort_latest_url(L.search_url(q)))}")
            time.sleep(8)
            verify_page(tab, rundir)
            q_new, q_eval, idle = 0, 0, 0
            for rnd in range(args.rounds_per_query):
                # expand see-more in place, then collect
                L.cdp_eval(tab, EXPAND_JS)
                time.sleep(1.5)
                out = L.cdp_eval(tab, COLLECT_JS)
                batch = parse_batch(out)
                rows, added = merge(rows, batch, seen_urls, source_query=q)
                q_new += added
                q_eval += len(batch)
                idle = 0 if added else idle + 1
                if idle >= args.idle_rounds:
                    break  # scrolled well past the fresh results
                L.cdp_eval(tab, SCROLL_JS)
                time.sleep(args.scroll_wait)
            total_new += q_new
            L.log(rundir, f"  query done: evaluated {q_eval}, {q_new} new posts "
                          f"({rnd + 1} scroll rounds)")
            L.write_csv(posts_csv, L.ITEMS_CSV_FIELDS, rows)  # checkpoint

        L.write_csv(posts_csv, L.ITEMS_CSV_FIELDS, rows)
        with open(os.path.join(rundir, "posts.md"), "w", encoding="utf-8") as f:
            f.write("| author-link | should_apply | first 120 chars |\n|---|---|---|\n")
            for r in rows:
                f.write(f"| {r['post_link']} | {r['should_apply']} "
                        f"| {r['full_text'][:120].replace('|', '/')} |\n")
        known = {s.get("post_url") for s in seen}
        for r in rows:
            if r["post_link"] not in known:
                seen.append({"post_url": r["post_link"], "verdict": r["verdict"],
                             "author": r["post_link"].split("#post-")[0],
                             "first_seen": L.now_local()[:10], "processed_at": None})
        L.save_json(seen_path, seen)
        L.log(rundir, f"DONE: {len(rows)} total posts ({total_new} new this run) -> posts.csv")
        return 0
    finally:
        if tab:
            L.cdp_close(tab)
            L.log(rundir, f"closed own tab {tab}")


if __name__ == "__main__":
    raise SystemExit(main())
