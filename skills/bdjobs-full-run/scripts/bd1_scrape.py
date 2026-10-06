#!/usr/bin/env python3
"""bd1: foundational search sweep. All terms x >=6 pages, unfiltered -> jobs.csv + scrape_log.txt.

Usage:
  python3 JDs/bdjobs/bd1_scrape.py [--date YYYY-MM-DD] [--terms "A,B"] [--max-pages 6]
  python3 JDs/bdjobs/bd1_scrape.py --resume            # skip terms already done in log
"""
import argparse
import json
import os
import re
import time

import bd_common as bc

SEARCH_URL = "https://bdjobs.com/h/jobs?txtsearch={term}&lang=en"

SEARCH_FALLBACK_JS = """(() => {
  const inp = document.querySelector('input[placeholder="Search for Jobs..."]') ||
              document.querySelector('form input[type="text"]:not([placeholder="Organization Type"])');
  if (!inp) return 'NO_INPUT';
  const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
  setter.call(inp, '');
  inp.dispatchEvent(new Event('input', { bubbles: true }));
  setter.call(inp, __TERM__);
  inp.dispatchEvent(new Event('input', { bubbles: true }));
  const btn = [...document.querySelectorAll('form button')].find(x => x.type === 'submit');
  if (btn) { btn.click(); return 'TYPED:' + inp.value; }
  inp.focus();
  inp.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', bubbles: true }));
  inp.dispatchEvent(new KeyboardEvent('keyup', { key: 'Enter', code: 'Enter', bubbles: true }));
  return 'TYPED:' + inp.value;
})()"""

SCROLL_JS = """(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const count = () => document.querySelectorAll('app-job-card').length;
  let last = -1, stable = 0;
  for (let i = 0; i < 10 && stable < 3; i++) {
    window.scrollTo(0, document.body.scrollHeight);
    await sleep(1200);
    const c = count();
    if (c === last) stable++; else { stable = 0; last = c; }
  }
  window.scrollTo(0, 0);
  await sleep(400);
  return 'CARDS:' + count();
})()"""

EXTRACT_JS = """(() => {
  const cards = [...document.querySelectorAll('app-job-card')];
  return JSON.stringify(cards.map(c => {
    const a = c.querySelector('a[href*="/h/details/"]');
    const href = a ? a.getAttribute('href') : null;
    const lines = c.innerText.split('\\n').map(s => s.trim()).filter(Boolean);
    return { href: href, lines: lines.slice(0, 8) };
  }));
})()"""

NEXT_JS = """(() => {
  const b = [...document.querySelectorAll('button[aria-label="Next" i]')].find(x => x.offsetParent && !x.disabled);
  if (!b) return 'NO_NEXT';
  const r = b.getBoundingClientRect();
  return JSON.stringify({x: r.x + r.width / 2, y: r.y + r.height / 2});
})()"""

PAGE_READY_JS = """(() => {
  const cards = [...document.querySelectorAll('app-job-card')];
  return JSON.stringify({n: cards.length, first: cards.length ?
    (cards[0].querySelector('a[href*="/h/details/"]') || {}).getAttribute('href') || '' : ''});
})()"""


def parse_card(href, lines):
    jid = ""
    m = re.search(r"/h/details/(\d+)", href or "")
    if m:
        jid = m.group(1)
    lines = list(lines)
    title = lines[0] if lines else ""
    company = lines[1] if len(lines) > 1 else ""
    location = lines[2] if len(lines) > 2 else ""
    experience = ""
    deadline = ""
    for ln in lines:
        dl = re.search(r"(\d{1,2} \w{3} \d{4})", ln)
        if dl and not deadline:
            deadline = dl.group(1)
        if re.search(r"(experience|fresher)", ln, re.I) and not experience:
            experience = ln
    return {"job_id": jid, "title": title, "company": company, "location": location,
            "experience": experience, "deadline": deadline, "href": href or ""}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None)
    ap.add_argument("--terms", default=None, help="comma-separated override")
    ap.add_argument("--max-pages", type=int, default=6)
    ap.add_argument("--resume", action="store_true")
    a = ap.parse_args()

    rd = bc.run_dir(a.date)
    terms = [t.strip() for t in a.terms.split(",")] if a.terms else bc.SEARCH_TERMS
    if not bc.devtools_up():
        raise SystemExit(f"debug browser not reachable on port {bc.cdp.PORT}; start it in debug mode (docs/EXTERNAL_TOOLS.md)")
    logpath = os.path.join(rd, "scrape_log.txt")
    done_terms = set()
    if a.resume and os.path.exists(logpath):
        for ln in open(logpath, encoding="utf-8"):
            m = re.match(r".*TERM DONE: (.+)$", ln)
            if m:
                done_terms.add(m.group(1))
        terms = [t for t in terms if t not in done_terms]
        bc.log(rd, f"resume: {len(done_terms)} terms already done")

    tid = bc.new_tab("https://bdjobs.com/h/jobs")
    bc.log(rd, f"search tab {tid}")
    total_new = 0
    try:
        for term in terms:
            bc.log(rd, f"=== TERM: {term}")
            from urllib.parse import quote
            bc.nav(tid, SEARCH_URL.format(term=quote(term)), wait=9)
            raw = bc.eval_js(tid, EXTRACT_JS)
            try:
                cards = json.loads(raw) if isinstance(raw, str) else raw
            except Exception:
                cards = []
            if not cards:
                typed = bc.eval_js(tid, SEARCH_FALLBACK_JS.replace("__TERM__", json.dumps(term)))
                if "NO_INPUT" in str(typed):
                    bc.log(rd, f"{term}: ERROR no search input")
                    continue
                time.sleep(8)
            for page in range(1, a.max_pages + 1):
                bc.eval_js(tid, SCROLL_JS, await_promise=True)
                raw = bc.eval_js(tid, EXTRACT_JS)
                try:
                    cards = json.loads(raw) if isinstance(raw, str) else raw
                except Exception:
                    cards = []
                rows, seen_ids = [], set()
                for c in cards:
                    r = parse_card(c.get("href"), c.get("lines"))
                    if not r["job_id"] or r["job_id"] in seen_ids:
                        continue
                    seen_ids.add(r["job_id"])
                    r.update({"search_term": term, "page": page,
                              "should_scrape": "", "scrape_status": "pending"})
                    rows.append(r)
                if not rows and page == 1:
                    bc.log(rd, f"{term} p{page}: 0 results")
                    break
                existing_ids = {x["job_id"] for x in bc.read_csv(os.path.join(rd, "jobs.csv"), bc.JOBS_CSV_FIELDS)}
                new = [r for r in rows if r["job_id"] not in existing_ids]
                bc.upsert_csv(os.path.join(rd, "jobs.csv"), bc.JOBS_CSV_FIELDS, rows)
                total_new += len(new)
                bc.log(rd, f"{term} p{page}: {len(rows)} cards ({len(new)} new)")
                if page == a.max_pages:
                    bc.log(rd, f"{term}: page budget {a.max_pages} reached")
                    break
                before = bc.eval_js(tid, PAGE_READY_JS)
                click = bc.trusted_click(tid, NEXT_JS)
                if click != "CLICKED":
                    bc.log(rd, f"{term}: no next-page control (results exhausted)")
                    break
                time.sleep(7)
                after = bc.eval_js(tid, PAGE_READY_JS)
                if before == after:
                    bc.log(rd, f"{term}: page did not advance after next-click; stopping")
                    break
            bc.log(rd, f"TERM DONE: {term}")
    finally:
        bc.close_tab(tid)
        bc.log(rd, f"bd1 complete: {total_new} new rows; tab closed")


if __name__ == "__main__":
    main()
