#!/usr/bin/env python3
"""Phase 3: prepare decisions, dry-run, and LIVE staging (never submits).

Subcommands:
  prepare  -> build apply_decisions.csv with the applied-history guard
  dry-run  -> report only; zero external side effects
  apply    -> LIVE: Gmail DRAFT (never sent), Drive upload, Sheet row,
              form/link opened and STAGED at Submit (never clicked)

Usage:
  python3 li3_apply.py prepare|dry-run|apply [--date D] [--limit N] [--generic-body]

--generic-body lets a row without bodies/<slug>.txt use a neutral body with no skill claims.
Without it such rows are marked skipped-blocked: an email body must be written and humanized.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time

import li_common as L

import jak_google  # noqa: E402  (core: Google interface, never sends)
import sheet_append  # noqa: E402
import template_index  # noqa: E402



def prepare(args):
    rd = L.run_dir(args.date)
    details = L.read_csv(os.path.join(rd, "details.csv"), L.DETAILS_CSV_FIELDS)
    out = os.path.join(rd, "apply_decisions.csv")
    history = L.application_history_paths(exclude_dir=rd)
    decisions = []
    for d in details:
        applied, why = L.is_applied_live(d.get("company"), d.get("position"), snapshot_paths=history)
        skip, skip_reason = L.auto_skip(d)
        decisions.append({
            "post_link": d.get("post_link", ""), "company": d.get("company", ""),
            "position": d.get("position", ""), "deadline": d.get("deadline", ""),
            "remote": d.get("remote", ""),
            "appropriate": "No" if (applied or skip) else "Pending",
            "reason": why or skip_reason or "Requires explicit LLM Yes against live profile facts",
            "method": d.get("apply_method", ""), "template_used": "RESUME_FULLSTACK.pdf",
            "status": "already-applied" if applied else ("skipped" if skip else "pending"),
            "notes": "prepare performed no external action"})
    L.write_csv(out, L.DECISIONS_CSV_FIELDS, decisions)
    L.log(rd, f"prepared {len(decisions)} decisions; applied-history guard checked")
    return 0


def dry_run(args):
    rd = L.run_dir(args.date)
    decisions = L.read_csv(os.path.join(rd, "apply_decisions.csv"), L.DECISIONS_CSV_FIELDS)
    lines = [f"# LinkedIn dry-run report — {L.now_local()}", "",
             "No Gmail, Drive, Sheet, browser-form, or submission side effects were performed.", "",
             "| company | position | decision | method | action |", "|---|---|---|---|---|"]
    for d in decisions:
        if d.get("status") == "already-applied":
            action = "BLOCKED: already applied"
        elif d.get("appropriate") != "Yes":
            action = "NO ACTION: not approved"
        else:
            action = "WOULD STAGE ONLY"
        lines.append(f"| {d.get('company','')} | {d.get('position','')} | {d.get('appropriate','')} "
                     f"| {d.get('method','')} | {action} |")
    with open(os.path.join(rd, "apply_report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(os.path.join(rd, "apply_report.md"))
    return 0


def _email_body(rd, row, d, contact, allow_generic=False):
    """Per-application email body.

    An agent-written, humanized body in <run-dir>/bodies/<slug>.txt is required (OPERATIONS #documents).
    The generic fallback (only with --generic-body) states NO skills or experience, because a hard-coded
    claim would break the truth gates for every role it was not written for.
    """
    slug = L.normalize_key(row.get("company", ""))[:40] or "unknown"
    path = os.path.join(rd, "bodies", f"{slug}.txt")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            text = fh.read().strip()
        if text:
            return text
    if not allow_generic:
        return ""
    company = row.get("company", "")
    position = row.get("position", "")
    sig = L.settings()["cfg"].signature()
    return (f"Dear Hiring Team,\n\nI am applying for the {position} role at {company}. "
            f"My resume is attached in PDF format.\n\nThank you for your time.\n\n"
            f"Best regards,\n{sig}")


def _email_subject(rd, row, position):
    """Subject line, with an optional per-run override.

    Some posts dictate the subject format themselves (DeepMind AI asks for
    YrsOf-Exp-UniversityName), so bodies/<slug>.subject wins when it exists.
    """
    slug = L.normalize_key(row.get("company", ""))[:40] or "unknown"
    path = os.path.join(rd, "bodies", f"{slug}.subject")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            text = fh.read().strip()
        if text:
            return text
    return f"Application for {position} - {L.settings()['cfg'].require('name')}"


def _draft(to, subject, body, attach, rd):
    try:
        r = jak_google.draft(to, subject, body, [attach] if attach and os.path.exists(attach) else [])
    except Exception as e:  # noqa: BLE001
        L.log(rd, f"  draft FAILED: {e}")
        return ""
    return f"DRAFT_CREATED id={r['draft_id']}"


def _drive_upload(pdf, name, rd):
    if not os.path.exists(pdf):
        L.log(rd, f"  drive skipped: missing {pdf}")
        return ""
    try:
        return jak_google.drive_upload(pdf, name)["link"]
    except Exception as e:  # noqa: BLE001
        L.log(rd, f"  drive FAILED: {e}")
        return ""


def _sheet_row(row, rd):
    try:
        out = "APPENDED " + sheet_append.append(row).get("range", "")
    except Exception as e:  # noqa: BLE001
        out = f"FAILED {e}"
    L.log(rd, f"  sheet: {out}")
    return out


def _stage_link(url, slug, rd):
    """Open the application link AS CAPTURED and stage it. Never clicks Submit.

    Short links (lnkd.in) are opened verbatim, but the destination LinkedIn
    prints on its outbound-link interstitial is read back so the job can be
    checked against application history by URL. Verifies the page really
    loaded (not about:blank) and screenshots it.

    Returns (status, screenshot_path, destination_url, tab_id).
    """
    stage_dir = os.path.join(L.REPO, "output", "linkedin-staged")
    os.makedirs(os.path.join(stage_dir, slug), exist_ok=True)
    shot = os.path.join(stage_dir, slug, "staged.png")
    tab = None
    try:
        tab = L.cdp_new_tab(url)
        time.sleep(5)
        href = L.cdp_href(tab)
        if not href or href.startswith("about:"):
            L.log(rd, f"  stage FAILED: tab landed on {href or 'unknown'} for {url}")
            return "stage-failed", "", "", tab
        dest = L.resolve_short_link(tab) if L.is_short_link(url) else ""
        if dest:
            L.log(rd, f"  resolved -> {dest}")
            subprocess.run(["python3", L.CDP_PY, "nav", tab, dest],
                           capture_output=True, text=True, timeout=120)
            time.sleep(6)
            href = L.cdp_href(tab) or dest
        subprocess.run(["python3", L.CDP_PY, "shot", tab, shot],
                       capture_output=True, text=True, timeout=90)
        size = os.path.getsize(shot) if os.path.exists(shot) else 0
        if size < 20000:
            L.log(rd, f"  stage SUSPECT: screenshot only {size} bytes ({href})")
        L.log(rd, f"  staged {href} (shot {size}B)")
        return f"staged-open at {href} (no submit clicked)", shot, dest, tab
    except Exception as e:
        L.log(rd, f"  stage FAILED {url}: {e}")
        return "stage-failed", "", "", tab


def apply_live(args):
    rd = L.run_dir(args.date)
    dec_path = os.path.join(rd, "apply_decisions.csv")
    decisions = L.read_csv(dec_path, L.DECISIONS_CSV_FIELDS)
    details = {d["post_link"]: d for d in L.read_csv(
        os.path.join(rd, "details.csv"), L.DETAILS_CSV_FIELDS)}
    applied = L.load_json(L.applied_cache_path(), {})
    history = L.application_history_paths(exclude_dir=rd)

    todo = [r for r in decisions if r.get("appropriate") == "Yes"
            and r.get("status") == "pending"]
    if args.limit:
        todo = todo[:args.limit]
    L.log(rd, f"li3 apply LIVE start; {len(todo)} approved pending rows")

    for r in todo:
        d = details.get(r["post_link"], {})
        company = r.get("company") or d.get("company") or "Unknown"
        position = r.get("position") or d.get("position") or "Unknown"
        slug = L.normalize_key(company)[:40] or "unknown"

        # Re-check application history immediately before any action.
        already, why = L.is_applied_live(company, position, applied=applied, snapshot_paths=history)
        if already:
            r["status"] = "already-applied"
            r["notes"] = f"blocked pre-action: {why}"
            L.log(rd, f"BLOCKED already-applied: {company} / {position}")
            L.write_csv(dec_path, L.DECISIONS_CSV_FIELDS, decisions)
            continue

        cfg = L.settings()["cfg"]
        jd_text = " ".join(str(v) for v in d.values()) + " " + position + " " + company
        chosen = template_index.resolve(jd_text, "resume", cfg.path("templates_dir"))
        if not chosen:
            r["status"] = "skipped-blocked"
            r["notes"] = "no usable template in templates_dir (add INDEX.md or run /create-template)"
            L.log(rd, f"BLOCKED no template: {company} / {position}")
            L.write_csv(dec_path, L.DECISIONS_CSV_FIELDS, decisions)
            continue
        template_pdf = chosen["file"]
        r["template_used"] = os.path.basename(template_pdf)
        cv_name = f"{cfg.require('name_file')}_RESUME_{slug}.pdf"
        pdf_path = os.path.join(rd, cv_name)
        if not os.path.exists(pdf_path):
            import shutil
            shutil.copyfile(template_pdf, pdf_path)
        drive_link = _drive_upload(pdf_path, cv_name, rd)

        method = r.get("method") or d.get("apply_method") or ""
        contact = d.get("contact") or ""
        link = d.get("apply_link") or ""

        if contact:
            subject = _email_subject(rd, r, position)
            body = _email_body(rd, r, d, contact, getattr(args, "generic_body", False))
            if not body:
                r["status"] = "skipped-blocked"
                r["notes"] = "no email body: write and humanize <run-dir>/bodies/<slug>.txt (or pass --generic-body)"
                L.log(rd, f"BLOCKED no body: {company} / {position}")
                L.write_csv(dec_path, L.DECISIONS_CSV_FIELDS, decisions)
                continue
            result = _draft(contact, subject, body, pdf_path, rd)
            if result:
                draft_id = result.split("id=")[-1].split()[0]
                r["status"] = "drafted"
                r["notes"] = f"gmail draft {draft_id} (NOT sent); to {contact}"
            else:
                r["status"] = "skipped-blocked"
                r["notes"] = "draft creation failed"
        elif link:
            status, shot, dest, tab = _stage_link(link, slug, rd)
            # The employer may be hidden in the post ("Unnamed (post)"), so
            # re-check history against the resolved destination URL too.
            if dest:
                already, why = L.is_applied_live(company, position, applied=applied,
                                                snapshot_paths=history, url=dest)
                if already:
                    subprocess.run(["python3", L.CDP_PY,
                                    "close", tab], capture_output=True, text=True, timeout=60)
                    r["status"] = "already-applied"
                    r["notes"] = f"blocked post-resolve: {why}; {dest}"
                    L.log(rd, f"BLOCKED already-applied (URL): {company} / {position} -> {dest}")
                    L.write_csv(dec_path, L.DECISIONS_CSV_FIELDS, decisions)
                    continue
            r["status"] = "staged" if status.startswith("staged") else "skipped-blocked"
            r["notes"] = f"{status}; {link}" + (f"; dest {dest}" if dest else "") \
                         + (f"; shot {shot}" if shot else "")
        else:
            r["status"] = "skipped-blocked"
            r["notes"] = "no email and no apply link captured"

        drive_cell = f"[template] {drive_link}" if drive_link else "[template] not uploaded"
        _sheet_row({
            "date": L.now_local()[:10], "company": company, "position": position,
            "drive_link": drive_cell,
            "job_nature": d.get("location", "") or ("Remote" if d.get("remote") == "yes" else ""),
            "job_type": "Full-time", "location": d.get("location", ""),
            "job_link": r.get("post_link", ""),
            "job_desc": (d.get("jd_text") or "")[:45000],
            "status": {"drafted": "Drafted", "staged": "Staged",
                       "skipped-blocked": "Skipped", "already-applied": "Skipped"}.get(r["status"], "Staged"),
            "how_applied": "Gmail draft" if r["status"] == "drafted" else "Form/link staged",
            "contact": contact or link, "salary": d.get("salary_raw", "") or "Negotiable",
            "deadline": d.get("deadline", ""),
            "comments": f"LinkedIn post: {r.get('post_link','')}; {r['notes']}",
        }, rd)

        key = L.application_key(company, position)
        applied.setdefault(key, {"sheet_row": 0, "date": L.now_local()[:10], "how": r["notes"]})
        L.save_json(L.applied_cache_path(), applied)
        L.write_csv(dec_path, L.DECISIONS_CSV_FIELDS, decisions)

    L.log(rd, "li3 apply LIVE done (nothing submitted)")
    return 0


def write_report(args):
    rd = L.run_dir(args.date)
    decisions = L.read_csv(os.path.join(rd, "apply_decisions.csv"), L.DECISIONS_CSV_FIELDS)
    lines = [f"# LinkedIn run report — {L.now_local()}", "",
             "Nothing was submitted and no email was sent.", "",
             "| company | position | method | status | notes |", "|---|---|---|---|---|"]
    drafts, staged = [], []
    for r in decisions:
        lines.append(f"| {r.get('company','')} | {r.get('position','')} | {r.get('method','')} "
                     f"| {r.get('status','')} | {r.get('notes','')[:100]} |")
        if r.get("status") == "drafted":
            drafts.append(f"- {r.get('company')} / {r.get('position')}: {r.get('notes')}")
        if r.get("status") == "staged":
            staged.append(f"- {r.get('company')} / {r.get('position')}: {r.get('notes')}")
    lines += ["", "## Gmail drafts to review and send (never auto-sent)"] + (drafts or ["- none"]) + \
             ["", "## Staged tabs awaiting your Submit click"] + (staged or ["- none"]) + \
             ["", "## Blocked", "- already-applied rows were skipped before any action (see status column)."]
    out = os.path.join(rd, "apply_report.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    L.log(rd, f"report written: {out}")
    return 0


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("prepare", "dry-run", "apply", "report"):
        p = sub.add_parser(name)
        p.add_argument("--date", default=None)
        p.add_argument("--limit", type=int, default=0)
        p.add_argument("--generic-body", action="store_true", help="allow a neutral email body when bodies/<slug>.txt is missing")
    args = ap.parse_args()
    if args.cmd == "prepare":
        return prepare(args)
    if args.cmd == "dry-run":
        return dry_run(args)
    if args.cmd == "report":
        return write_report(args)
    return apply_live(args)


if __name__ == "__main__":
    raise SystemExit(main())
