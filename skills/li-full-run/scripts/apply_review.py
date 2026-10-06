#!/usr/bin/env python3
"""apply_review.py — apply the AI agent's review decisions into a run.

This is the "AI agent edits the CSV" phase of the LinkedIn sweep: the agent
reads posts.csv full text against the live profile sources, authors
`agent_review.csv` (post_key, company, position, should_apply, how_to_apply,
comment), and this script writes those decisions into posts.csv and builds
details.csv for the approved rows.

Usage: python3 JDs/linkedin/apply_review.py --date 2026-09-14
"""
import argparse
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import li_common as L
import li2_details as D


def loose(value):
    return L.normalize_key((value or "").replace("\u2019", "'").replace("\u2018", "'"))


def post_token(key):
    """Identity part of a post key: the per-post hash at the end of the key.

    normalize_key() strips punctuation, so '#post-' and '://' are already gone
    from the normalized string. Match on the trailing "post<hex>" token instead,
    and only fall back to the whole key when there is none.

    Without this, every post by one author shares the same prefix and the loose
    fallback collapses a whole author's posts onto one review row (2026-10-05 run
    approved eight unrelated posts as the same Mid-Level Software Engineer).
    """
    k = loose(key)
    idx = k.rfind("post")
    tail = k[idx + 4:]
    if idx >= 0 and len(tail) >= 16 and all(c in "0123456789abcdef" for c in tail):
        return tail
    return k


def load_review(path):
    with open(path, encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def match_for(key, exact, loose_map):
    """Match one post identity to a review row: exact key, then loose post token."""
    if key in exact:
        return exact[key]
    token = post_token(key)
    if not token:
        return None
    row = loose_map.get(token)
    if row:
        return row
    # Only fall back to prefix matching on the post token, never on the author.
    for candidate, row in loose_map.items():
        if candidate and (candidate.startswith(token[:32]) or token.startswith(candidate[:32])):
            return row
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None)
    args = ap.parse_args()
    rd = L.run_dir(args.date)

    review = load_review(os.path.join(rd, "agent_review.csv"))
    posts = L.read_csv(os.path.join(rd, "posts.csv"), L.POSTS_CSV_FIELDS)
    exact = {r["post_key"]: r for r in review if r.get("post_key")}
    loose_map = {}
    for k, v in exact.items():
        token = post_token(k)
        if token and token not in loose_map:
            loose_map[token] = v

    changed = 0
    # agent_review.csv is the sole source of truth for the decision, so clear the
    # previous pass's values first. Without this a stale "Yes" from an earlier run
    # (or from a loose match) survives a corrected review and still reaches
    # details.csv.
    for p in posts:
        p["should_apply"] = ""
        p["how_to_apply"] = ""
        p["comment"] = ""
    for p in posts:
        match = match_for(p["post_link"], exact, loose_map)
        if match:
            p["should_apply"] = match.get("should_apply", "No")
            p["how_to_apply"] = match.get("how_to_apply", "")
            p["comment"] = match.get("comment", "")
            changed += 1
        elif not p["should_apply"]:
            # Unreviewed rows are never approved implicitly.
            if not p["comment"]:
                p["comment"] = "AI review: no decision entry for this post."
    L.write_csv(os.path.join(rd, "posts.csv"), L.POSTS_CSV_FIELDS, posts)

    # details.csv: structured fields parsed from the captured text, with the
    # agent-reviewed company/position/comment overlaid (regex names are the
    # weakest part of the parse, the review is authoritative).
    rows = []
    for p in posts:
        if p["should_apply"].strip().lower() not in ("yes", "y", "apply"):
            continue
        match = match_for(p["post_link"], exact, loose_map)
        if not match:
            continue
        text = p["full_text"]
        detail = D.parse_text(text, p["post_link"])
        detail["company"] = match.get("company") or detail["company"]
        detail["position"] = match.get("position") or detail["position"]
        detail["notes"] = match.get("comment", "")
        how = (match.get("how_to_apply") or "").strip()
        if "@" in how:
            detail["apply_method"] = "email"
            detail["contact"] = how
            detail["apply_link"] = ""
        elif how:
            detail["apply_method"] = "link"
            detail["apply_link"] = how
        else:
            detail["apply_method"] = "unknown"
        # preserve any manually set method (e.g. form) from the post text
        if detail["apply_method"] == "unknown" and L.extract_email(text):
            detail["apply_method"] = "email"
            detail["contact"] = L.extract_email(text)
        rows.append(detail)

    L.write_csv(os.path.join(rd, "details.csv"), L.DETAILS_CSV_FIELDS, rows)
    approved = sum(1 for p in posts if p["should_apply"].strip().lower() in ("yes", "y", "apply"))
    print(f"APPLIED_REVIEW changed={changed} approved={approved} details={len(rows)}")


if __name__ == "__main__":
    raise SystemExit(main())
