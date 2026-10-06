#!/usr/bin/env python3
"""bd2: detailed trimming + saving. Scrapes should_scrape=Yes rows, clicks Save, -> details.csv.

Usage:
  python3 JDs/bdjobs/bd2_trim_save.py [--date YYYY-MM-DD] [--limit N] [--no-save]
  python3 JDs/bdjobs/bd2_trim_save.py --ids 1527109,1522603   # manual id override
"""
import argparse
import json
import os
import re
import time

import bd_common as bc

DETAIL_JS = r"""(() => {
  const t = document.body.innerText;
  const btns = [...document.querySelectorAll('button,a')].map(b => b.innerText.trim())
    .filter(x => /^(save|saved|unsave|apply|undo)/i.test(x));
  const i0 = t.indexOf('Vacancy:');
  let i1 = t.indexOf('Apply Procedure');
  if (i1 < 0) i1 = t.indexOf('Address:');
  const jd = (i0 >= 0 && i1 > i0) ? t.slice(i0, i1) : t.slice(0, 2600);
  const ap = i1 >= 0 ? t.slice(i1, i1 + 600) : '';
  const dl = (t.match(/Application Deadline\s*:\s*\n*\s*(\d{1,2} \w{3} \d{4})/) || ['', ''])[1];
  const sal = (t.match(/Salary:\s*\n?([^\n]{0,90})/) || ['', ''])[1].trim();
  const h2s = [...document.querySelectorAll('h2')].map(x => x.innerText.trim()).filter(Boolean);
  return JSON.stringify({url: location.href, title: (h2s[1] || h2s[0] || '').slice(0, 120),
    company: (h2s[0] || '').slice(0, 120),
    buttons: [...new Set(btns)].slice(0, 6), deadline: dl, salary_raw: sal,
    jd: jd.slice(0, 8000), apply: ap});
})()"""

STATE_JS = r"""JSON.stringify({url: location.href.slice(0, 95),
  btns: [...document.querySelectorAll('button,a')].map(b => b.innerText.trim())
    .filter(x => /^(save|saved|unsave|apply)/i.test(x)).slice(0, 5)});"""

SAVE_CLICK_JS = """(() => {
  const btn = [...document.querySelectorAll('button, a')].find(b => b.innerText.trim() === 'Save');
  if (!btn) return 'NO_SAVE_BUTTON';
  btn.click();
  return 'CLICKED';
})()"""

PANEL_URL = "https://mybdjobs.bdjobs.com/jobseeker-panel/saved-jobs?lang=en"


def session_live_probe(tid):
    bc.nav(tid, PANEL_URL, wait=8)
    txt = bc.eval_js(tid, "document.body.innerText.slice(0, 400)")
    return "Sign in" not in txt and "signin" not in bc.eval_js(tid, "location.href")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--no-save", action="store_true")
    ap.add_argument("--ids", default=None, help="comma-separated job ids override")
    a = ap.parse_args()

    rd = bc.run_dir(a.date)
    jobs_path = os.path.join(rd, "jobs.csv")
    details_path = os.path.join(rd, "details.csv")
    if not bc.devtools_up():
        raise SystemExit(f"debug browser not reachable on port {bc.cdp.PORT}; start it in debug mode (docs/EXTERNAL_TOOLS.md)")

    if a.ids:
        targets = [{"job_id": i.strip()} for i in a.ids.split(",") if i.strip()]
    else:
        rows = bc.read_csv(jobs_path, bc.JOBS_CSV_FIELDS)
        done = {d["job_id"] for d in bc.read_csv(details_path, bc.DETAILS_CSV_FIELDS)
                if d.get("scrape_status") == "done"}
        targets = [r for r in rows
                   if r.get("should_scrape", "").lower() == "yes" and r["job_id"] not in done]
        if a.limit:
            targets = targets[:a.limit]
    bc.log(rd, f"bd2: {len(targets)} job(s) to detail-scrape"
               + (" (save disabled)" if a.no_save else ""))
    if not targets:
        return

    tid = bc.new_tab("about:blank")
    try:
        for r in targets:
            jid = r["job_id"]
            try:
                bc.nav(tid, f"https://bdjobs.com/h/details/{jid}?ln=1", wait=7)
                if bc.login_page_detected(tid):
                    bc.ensure_login(tid, return_url=f"https://bdjobs.com/h/details/{jid}?ln=1",
                                    log_fn=lambda m: bc.log(rd, f"{jid}: {m}"))
                d = json.loads(bc.eval_js(tid, DETAIL_JS))
                d["job_id"] = jid
                save_action = "disabled" if a.no_save else "none"
                btns = [b for b in d.get("buttons", [])]
                if not a.no_save and any(b == "Save" for b in btns):
                    bc.eval_js(tid, SAVE_CLICK_JS)
                    time.sleep(3)
                    st = json.loads(bc.eval_js(tid, STATE_JS))
                    if "signin" in st.get("url", ""):
                        bc.ensure_login(tid, return_url=f"https://bdjobs.com/h/details/{jid}?ln=1",
                                        log_fn=lambda m: bc.log(rd, f"{jid}: {m}"))
                        bc.eval_js(tid, SAVE_CLICK_JS)
                        time.sleep(3)
                        st = json.loads(bc.eval_js(tid, STATE_JS))
                        if "signin" in st.get("url", ""):
                            save_action = "signin-redirect"
                    if "Save" not in st.get("btns", []) and "signin" not in st.get("url", ""):
                        save_action = "saved"
                    elif save_action == "none":
                        save_action = "uncertain"
                elif not a.no_save:
                    if any("saved" in b.lower() or "unsave" in b.lower() for b in btns):
                        save_action = "already-saved"
                    else:
                        save_action = "no-save-btn"
                m = re.search(r"/h/details/(\d+)", d.get("url", ""))
                row = {"job_id": jid,
                       "title": r.get("title", "") or d.get("title", ""),
                       "company": r.get("company", "") or d.get("company", ""),
                       "location": r.get("location", ""),
                       "deadline": d.get("deadline", "") or r.get("deadline", ""),
                       "url": f"https://bdjobs.com/h/details/{jid}?ln=1",
                       "buttons": json.dumps(btns), "save_action": save_action,
                       "salary_raw": d.get("salary_raw", ""),
                       "jd": d.get("jd", ""), "apply_procedure": d.get("apply", ""),
                       "scrape_status": "done"}
                bc.upsert_csv(details_path, bc.DETAILS_CSV_FIELDS, [row])
                bc.log(rd, f"{jid}: {save_action} | {d.get('title', '')[:50]} | dl={d.get('deadline', '')} | btns={btns}")
            except Exception as e:
                bc.upsert_csv(details_path, bc.DETAILS_CSV_FIELDS,
                              [{"job_id": jid, "scrape_status": f"error: {str(e)[:120]}"}])
                bc.log(rd, f"{jid}: ERROR {str(e)[:150]}")
            time.sleep(1)
    finally:
        bc.close_tab(tid)
        done_n = len([d for d in bc.read_csv(details_path, bc.DETAILS_CSV_FIELDS)
                      if d.get("scrape_status") == "done"])
        bc.log(rd, f"bd2 complete: {done_n} details rows total; tab closed")


if __name__ == "__main__":
    main()
