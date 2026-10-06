#!/usr/bin/env python3
"""Phase 2: enrich LLM-approved LinkedIn posts from captured full text."""
import argparse
import os
import re

import li_common as L

POSITION_PATTERNS = [
    r"(?:position|role|designation)\s*[:\-]\s*([^\n]{3,90})",
    r"(?:we(?:'|’)?re|we are|now)\s+hiring\s*(?:for|a|an)?\s*[:\-]?\s*([^\n]{3,90})",
    r"hiring\s*(?:for|a|an)?\s*[:\-]?\s*([^\n]{3,90})",
    r"looking for\s*(?:a|an)?\s*([^\n]{3,90})",
    r"(?:urgent\s+)?(?:hiring|vacancy)\s*[:\-]\s*([^\n]{3,90})",
    r"is\s+(?:looking for|hiring)\s*(?:a|an)?\s*([^\n]{3,90})",
    r"join\s+our\s+team\s+as\s+(?:a|an)?\s*([^\n]{3,90})",
]
COMPANY_PATTERNS = [
    r"(?:company|organization|organisation)\s*[:\-]\s*([^\n]{2,60})",
    r"join\s+([A-Z][\w&.,' -]{2,50}?)(?:'s|\s+team|\s+is|\s+and|\.|,)",
    r"\bat\s+([A-Z][\w&.,' -]{2,50}?)(?:\s+is|\s+are|\s+looking|\s+and|,|\.|\n|$)",
    r"([A-Z][\w&.,' -]{2,50}?)\s+(?:is|are)\s+(?:hiring|looking for|seeking|recruiting)",
    r"([A-Z][\w&.,' -]{2,50}?(?:Ltd|Limited|Inc|LLC|Solutions|Technologies|Technology|Systems|Software|Group|Consulting|Lab|Labs|Company))\b",
    r"@\s*([A-Z][\w&.' -]{2,40})",
]
NOISE = r"(?:are you|if you|we are|we're|apply|send|visit|please|interested|requirements?|responsibilit|about the (?:role|company))"


def _clean(value):
    value = re.sub(r"[*_#`>]", "", value or "")
    value = re.sub(r"[\U0001F300-\U0001FAFF\u2600-\u27BF]", "", value)
    value = value.strip(" \t-–—:|,.")
    value = re.sub(r"\s+", " ", value)
    return value


def _trim(value, limit=80):
    value = _clean(value)
    cut = re.split(r"\s+(?:are you|if you|who is|who can|we are|we're|and\s+you|join us)\b", value, flags=re.I)[0]
    cut = re.split(r"[.!?]\s", cut)[0]
    return _clean(cut)[:limit]


def parse_text(text, post_link=""):
    flat = " ".join((text or "").split())
    first_lines = "\n".join((text or "").splitlines()[:6])

    def pick(patterns, source, limit=80):
        for pattern in patterns:
            m = re.search(pattern, source, re.I | re.M)
            if m:
                cand = _trim(m.group(1), limit)
                if cand and len(cand) >= 3 and not re.match(r"^" + NOISE, cand, re.I):
                    return cand
        return ""

    position = pick(POSITION_PATTERNS, first_lines) or pick(POSITION_PATTERNS, flat, 70)
    company = pick(COMPANY_PATTERNS, first_lines, 50) or pick(COMPANY_PATTERNS, flat, 50)

    def first(pattern, default="", limit=60):
        m = re.search(pattern, flat, re.I)
        return _clean(m.group(1))[:limit] if m else default

    emails = L.extract_email(flat)
    links = L.extract_links(flat)
    location = first(r"(?:location|workplace|work location|office)\s*[:\-]\s*([^|\n]{3,60})")
    deadline = first(r"(?:application\s+)?deadline\s*[:\-]\s*([^|\n]{3,35})", limit=35)
    salary = first(r"((?:BDT|Tk\.?|Taka)\s*[\d,]+(?:\s*[Kk])?\s*(?:[-–]|to)\s*(?:BDT|Tk\.?|Taka)?\s*[\d,]+(?:\s*[Kk])?(?:\s*/\s*month)?|(?:BDT|Tk\.?|Taka)\s*[\d,]+(?:\s*[Kk])?(?:\s*/\s*month)?|negotiable)")
    exp = first(r"(?:experience(?:\s+required)?|exp)\s*[:\-]\s*([^|\n]{1,35})", limit=35)
    remote = "yes" if re.search(r"\bremote\b|work from home", flat, re.I) else "no"
    form_link = next((u for u in links if "forms.gle" in u or "docs.google.com/forms" in u), "")
    method = ("form" if form_link else "email" if emails else
              "easy-apply" if "easy apply" in flat.lower() else "link" if links else "unknown")
    return {"post_link": post_link, "company": company or "Unknown company",
            "position": position or "Unknown position", "deadline": deadline,
            "location": location, "remote": remote, "experience": exp,
            "apply_method": method, "contact": emails,
            "apply_link": form_link or (links[0] if links else ""),
            "salary_raw": salary, "skills": "",
            "cover_letter_required": "yes" if re.search(r"cover letter", flat, re.I) else "no",
            "jd_text": text or "", "scrape_status": "parsed",
            "notes": "captured from posts.csv"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--fresh", action="store_true", help="rebuild details.csv")
    args = ap.parse_args()
    rd = L.run_dir(args.date)
    posts = L.read_csv(os.path.join(rd, "posts.csv"), L.POSTS_CSV_FIELDS)
    out = os.path.join(rd, "details.csv")
    details = [] if args.fresh else L.read_csv(out, L.DETAILS_CSV_FIELDS)
    done = {r.get("post_link") for r in details}
    todo = [r for r in posts
            if r.get("should_apply", "").strip().lower() in ("yes", "y", "apply")
            and r.get("post_link") not in done]
    if args.limit:
        todo = todo[:args.limit]
    for row in todo:
        details.append(parse_text(row.get("full_text", ""), row.get("post_link", "")))
        L.write_csv(out, L.DETAILS_CSV_FIELDS, details)
    L.log(rd, f"li2 parsed {len(todo)} approved posts; {len(details)} total details")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
