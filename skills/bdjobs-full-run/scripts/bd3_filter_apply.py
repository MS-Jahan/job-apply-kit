#!/usr/bin/env python3
"""bd3: final filtering + concluding steps. Consumes apply_decisions.csv.

Settings (salary floors, location whitelist, caps) come from the user config; see SKILL.md.

Subcommands:
  salary --text "BDT 40,000 - 70,000" [--remote]        compute salary input value
  apply  [--date D] [--limit N] [--dry-run]             portal apply flow per decisions row
  email  --jid ID --to A --subject S --body-file F [--attach PDF]
  sheet  --json '<row>'                                 append tracker sheet row
  report [--date D]                                     write apply_report.md summary
"""
import argparse
import importlib.util
import json
import os
import sys
import time

import bd_common as bc

HERE = bc.HERE
sys.path.insert(0, HERE)

import gmail_draft  # noqa: E402  (core: draft helper, never sends)


FILL_T = r"""(() => {
  const inps = [...document.querySelectorAll('input')].filter(i => i.placeholder === 'e.g. 50000');
  const inp = inps.find(i => i.offsetParent || i.getClientRects().length) || inps[inps.length - 1];
  if (!inp) return 'NO_INPUT';
  inp.focus();
  const set = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
  set.call(inp, '');
  inp.dispatchEvent(new Event('input', {bubbles: true}));
  set.call(inp, SALARY_PLACEHOLDER);
  inp.dispatchEvent(new Event('input', {bubbles: true}));
  inp.dispatchEvent(new Event('change', {bubbles: true}));
  inp.blur();
  return 'FILLED:' + inp.value;
})()"""

SUBMIT = r"""(() => {
  const b = [...document.querySelectorAll('button[type=submit]')].find(x => !x.disabled && (x.offsetParent || x.getClientRects().length));
  if (!b) return 'NO_ENABLED_SUBMIT';
  b.focus();
  b.click();
  return 'CLICKED';
})()"""

ANYWAY = r"""(() => {
  const b = [...document.querySelectorAll('button')].find(x => x.innerText.trim() === 'Apply Anyway' && x.offsetParent);
  if (!b) return 'NO_ANYWAY';
  b.click();
  return 'CLICKED';
})()"""

STATE = r"""JSON.stringify({url:location.href.slice(0,95),modal:(()=>{const m=[...document.querySelectorAll('div')].find(d=>d.offsetParent&&/expected salary is higher/i.test(d.textContent)&&d.textContent.length<400);return m?'SALARY_MODAL':'NONE';})(),submitted:/Application Submitted/i.test(document.body.innerText),btns:[...document.querySelectorAll('button')].map(b=>b.innerText.trim()).filter(t=>t&&t.length<28).slice(0,12)});"""


def cdp_eval(tid, js):
    return bc.eval_js(tid, js).strip('"')


def parse_out(s):
    if not s:
        return None
    if isinstance(s, dict):
        return s
    try:
        v = json.loads(s.replace('\\"', '"'))
    except Exception:
        return None
    return v if isinstance(v, dict) else None


def decisions_path(rd):
    return os.path.join(rd, "apply_decisions.csv")


def update_decision(rd, job_id, **kv):
    import csv as _csv
    path = decisions_path(rd)
    rows = bc.read_csv(path, bc.DECISIONS_CSV_FIELDS)
    for r in rows:
        if r["job_id"] == job_id:
            r.update(kv)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = _csv.DictWriter(f, fieldnames=bc.DECISIONS_CSV_FIELDS, quoting=_csv.QUOTE_ALL)
        w.writeheader()
        w.writerows(rows)


def sheet_row_for(r, note, status="Applied", drive_link="[bdjobs-profile-CV]"):
    status_map = {"applied": "Applied", "drafted": "Drafted", "staged": "Staged", "skipped": "Skipped"}
    status = status_map.get(status.lower(), status)
    tag = ""
    if note.startswith("["):
        tag, _, note = note.partition("] ")
        tag = tag + "] "
    return {"date": bc.now_dhaka().split()[0].replace("-", "/"), "company": r.get("company", ""),
            "position": r.get("position", ""), "drive_link": drive_link,
            "job_nature": "Remote" if str(r.get("remote", "")).lower() in ("1", "true", "yes") else "On-site",
            "job_type": "Full Time", "location": r.get("location", ""),
            "job_link": f"https://bdjobs.com/h/details/{r['job_id']}?ln=1",
            "status": status, "how_applied": r.get("method", ""),
            "contact": r.get("contact", "") or bc.extract_contact(r.get("apply_procedure", "")),
            "salary": bc.salary_display(r.get("salary_raw", ""), r.get("jd", "")),
            "deadline": r.get("deadline", ""),
            "job_desc": r.get("jd", "")[:4000], "comments": tag + note}


def load_decisions_enriched(rd):
    rows = bc.read_csv(decisions_path(rd), bc.DECISIONS_CSV_FIELDS)
    det = {d["job_id"]: d for d in bc.read_csv(os.path.join(rd, "details.csv"), bc.DETAILS_CSV_FIELDS)}
    for r in rows:
        d = det.get(r["job_id"], {})
        r.setdefault("jd", "")
        r.update({"jd": r.get("jd") or d.get("jd", ""),
                  "salary_raw": r.get("salary_raw") or d.get("salary_raw", ""),
                  "apply_procedure": d.get("apply_procedure", ""),
                  "contact": bc.extract_contact(d.get("apply_procedure", ""))})
    return rows


def cmd_salary(a):
    val, why = bc.compute_salary(a.text, a.remote)
    print(f"{val}\t{why}")


def details_already_applied(tid, jid, log_fn=None):
    """Ground-truth fallback: job details page shows 'Already Applied' / 'Undo Application'."""
    url = f"https://bdjobs.com/h/details/{jid}?ln=1"
    bc.nav(tid, url, wait=8)
    time.sleep(2)
    if bc.login_page_detected(tid):
        bc.ensure_login(tid, return_url=url, log_fn=log_fn)
        time.sleep(2)
        # 404 retry rule
        for attempt in (1, 2):
            body = str(cdp_eval(tid, "document.body?document.body.innerText.slice(0,300):''") or "")
            if "Cannot GET" not in body:
                break
            time.sleep(6)
            bc.nav(tid, url, wait=8)
            time.sleep(2)
    body = str(cdp_eval(tid, "document.body?document.body.innerText.slice(0,2500):''") or "")
    return "Already Applied" in body or "Undo Application" in body


def cmd_apply(a):
    rd = bc.run_dir(a.date)
    if not bc.devtools_up():
        raise SystemExit(f"debug browser not reachable on port {bc.cdp.PORT}; start it in debug mode (docs/EXTERNAL_TOOLS.md)")
    rows = load_decisions_enriched(rd)
    todo = [r for r in rows
            if r.get("appropriate", "").lower() == "yes"
            and r.get("status", "pending") in ("", "pending")
            and "bdjobs" in r.get("method", "").lower()]
    if a.limit:
        todo = todo[:a.limit]
    bc.log(rd, f"bd3 apply: {len(todo)} job(s)")
    if not todo:
        return
    tid = bc.new_tab("about:blank")
    try:
        for r in todo:
            jid = r["job_id"]
            sal = r.get("salary_input") or str(bc.settings()["floors"]["onsite"] or "")
            try:
                if a.dry_run:
                    print(f"{jid}: DRY salary={sal} {r.get('company')} {r.get('position')}")
                    continue
                bc.nav(tid, f"https://bdjobs.com/h/apply-online/{jid}", wait=8)
                time.sleep(2)
                # 404 retry rule (2026-09-14): "Cannot GET" => retry twice, 6s gap
                for attempt in (1, 2):
                    body = str(cdp_eval(tid, "document.body?document.body.innerText.slice(0,300):''") or "")
                    if "Cannot GET" not in body:
                        break
                    bc.log(rd, f"{jid}: apply-online 404 (attempt {attempt}/2), retry in 6s")
                    time.sleep(6)
                    bc.nav(tid, f"https://bdjobs.com/h/apply-online/{jid}", wait=8)
                    time.sleep(2)
                if bc.login_page_detected(tid):
                    bc.ensure_login(tid, return_url=f"https://bdjobs.com/h/apply-online/{jid}",
                                    log_fn=lambda m: bc.log(rd, f"{jid}: {m}"))
                    time.sleep(2)
                st = parse_out(cdp_eval(tid, STATE)) or {}
                if "Undo Application" in st.get("btns", []) or st.get("submitted"):
                    bc.log(rd, f"{jid}: ALREADY-APPLIED")
                    update_decision(rd, jid, status="applied", notes="already applied")
                    try:
                        bc.sheet_append(sheet_row_for(
                            r, f"bdjobs id {jid}; already applied, salary {sal}"))
                    except Exception as se:
                        bc.log(rd, f"{jid}: SHEET-SYNC-FAILED {str(se)[:150]}")
                    continue
                fill = cdp_eval(tid, FILL_T.replace("SALARY_PLACEHOLDER", json.dumps(sal)))
                time.sleep(2)
                sub = cdp_eval(tid, SUBMIT)
                time.sleep(5)
                st = parse_out(cdp_eval(tid, STATE)) or {}
                if st.get("modal") == "SALARY_MODAL":
                    cdp_eval(tid, ANYWAY)
                    time.sleep(5)
                    st = parse_out(cdp_eval(tid, STATE)) or {}
                if st.get("submitted") or "Undo Application" in st.get("btns", []):
                    shot_p = os.path.join(bc.REPO, "output", "bdjobs-applied", jid, "confirmation.png")
                    bc.shot(tid, shot_p)
                    bc.log(rd, f"{jid}: APPLIED fill={fill} submit={sub} salary={sal}")
                    update_decision(rd, jid, status="applied",
                                    notes=f"submitted via apply-online, salary {sal}; shot {shot_p}")
                    try:
                        bc.sheet_append(sheet_row_for(
                            r, f"bdjobs id {jid}; applied via bd3, salary {sal}"))
                    except Exception as se:
                        bc.log(rd, f"{jid}: SHEET-SYNC-FAILED {str(se)[:150]}")
                else:
                    if details_already_applied(tid, jid,
                                               log_fn=lambda m: bc.log(rd, f"{jid}: {m}")):
                        shot_p = os.path.join(bc.REPO, "output", "bdjobs-applied", jid, "confirmation.png")
                        bc.shot(tid, shot_p)
                        bc.log(rd, f"{jid}: APPLIED (details-page fallback) salary={sal}")
                        update_decision(rd, jid, status="applied",
                                        notes=f"details page shows Already Applied, salary {sal}; shot {shot_p}")
                        try:
                            bc.sheet_append(sheet_row_for(
                                r, f"bdjobs id {jid}; applied (details-page fallback), salary {sal}"))
                        except Exception as se:
                            bc.log(rd, f"{jid}: SHEET-SYNC-FAILED {str(se)[:150]}")
                        continue
                    blocked = "form-reset-or-unconfirmed"
                    bc.log(rd, f"{jid}: UNCONFIRMED fill={fill} submit={sub} state={json.dumps(st)[:200]}")
                    update_decision(rd, jid, status=f"skipped-blocked",
                                    notes=f"{blocked}; state {json.dumps(st)[:150]}")
            except Exception as e:
                bc.log(rd, f"{jid}: ERROR {str(e)[:180]}")
                update_decision(rd, jid, status=f"error", notes=str(e)[:150])
            time.sleep(2)
    finally:
        bc.close_tab(tid)


def cmd_email(a):
    body = open(a.body_file, encoding="utf-8").read()
    args = ["--to", a.to, "--subject", a.subject, "--body", body]
    if a.attach:
        args += ["--attach", a.attach]
    if gmail_draft.main(args) != 0:
        raise SystemExit("draft creation failed")
    if a.jid:
        rd = bc.run_dir(a.date)
        if os.path.exists(decisions_path(rd)):
            update_decision(rd, a.jid, status="drafted", notes=f"gmail draft created; user must send")


def cmd_sheet(a):
    bc.sheet_append(a.json)


def cmd_skips(a):
    rd = bc.run_dir(a.date)
    rows = load_decisions_enriched(rd)
    n = 0
    for r in rows:
        if r.get("appropriate", "").lower() != "no":
            continue
        if str(r.get("status", "")).startswith("skipped-synced"):
            continue
        reason = r.get("reason", "") or r.get("notes", "")
        note = f"[Worth Checking] auto-skipped: {reason}" if "override" in reason.lower() \
            else f"auto-skipped: {reason}"
        bc.sheet_append(sheet_row_for(r, note, status="Skipped"))
        update_decision(rd, r["job_id"], status="skipped-synced")
        n += 1
    print(f"synced {n} skipped row(s) to sheet")


def cmd_report(a):
    rd = bc.run_dir(a.date)
    rows = bc.read_csv(decisions_path(rd), bc.DECISIONS_CSV_FIELDS)
    det = bc.read_csv(os.path.join(rd, "details.csv"), bc.DETAILS_CSV_FIELDS)
    out = [f"# BDJobs Run Report — {bc.now_dhaka()}", "",
           f"- jobs.csv rows: {len(bc.read_csv(os.path.join(rd, 'jobs.csv'), bc.JOBS_CSV_FIELDS))}",
           f"- details.csv rows: {len(det)} (saved: "
           f"{len([d for d in det if d.get('save_action') == 'saved'])}, "
           f"already-saved: {len([d for d in det if d.get('save_action') == 'already-saved'])})", "",
           "| job | company | position | salary | method | status | notes |", "|---|---|---|---|---|---|---|"]
    for r in rows:
        out.append(f"| {r['job_id']} | {r.get('company','')} | {r.get('position','')} | "
                   f"{r.get('salary_input','')} | {r.get('method','')} | {r.get('status','')} | "
                   f"{r.get('notes','')} |")
    path = os.path.join(rd, "apply_report.md")
    open(path, "w", encoding="utf-8").write("\n".join(out) + "\n")
    print("wrote", path)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("salary")
    s.add_argument("--text", required=True)
    s.add_argument("--remote", action="store_true")

    s = sub.add_parser("apply")
    s.add_argument("--date", default=None)
    s.add_argument("--limit", type=int, default=0)
    s.add_argument("--dry-run", action="store_true")

    s = sub.add_parser("email")
    s.add_argument("--jid", default="")
    s.add_argument("--date", default=None)
    s.add_argument("--to", required=True)
    s.add_argument("--subject", required=True)
    s.add_argument("--body-file", required=True)
    s.add_argument("--attach", default="")

    s = sub.add_parser("sheet")
    s.add_argument("--json", required=True)

    s = sub.add_parser("skips")
    s.add_argument("--date", default=None)

    s = sub.add_parser("report")
    s.add_argument("--date", default=None)

    a = ap.parse_args()
    {"salary": cmd_salary, "apply": cmd_apply, "email": cmd_email,
     "sheet": cmd_sheet, "skips": cmd_skips, "report": cmd_report}[a.cmd](a)


if __name__ == "__main__":
    main()
