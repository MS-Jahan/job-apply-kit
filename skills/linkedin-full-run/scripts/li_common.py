#!/usr/bin/env python3
"""Shared helpers for the LinkedIn search-sweep pipeline."""
import csv
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from urllib.parse import quote

HERE = os.path.dirname(os.path.abspath(__file__))
CORE_SCRIPTS = os.path.join(os.path.dirname(os.path.dirname(HERE)), "job-apply-core", "scripts")
for _p in (HERE, CORE_SCRIPTS):
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    import cdp  # noqa: E402  (core skill: raw CDP driver)
    import jak_config  # noqa: E402
except ImportError as _e:  # pragma: no cover
    raise SystemExit(f"ERROR: job-apply-core is required next to this skill ({_e}). Run install.sh.")

CDP_PY = os.path.join(CORE_SCRIPTS, "cdp.py")
DEFAULT_QUERIES = [
    '"Software Engineer" AND (hiring OR vacancy)',
    '"Software Developer" AND (hiring OR vacancy)',
    '(Fullstack OR Backend OR Frontend) AND developer AND (hiring OR vacancy)',
]
_SETTINGS = None


def settings():
    """Personal tuning comes from the user's config, never from this file."""
    global _SETTINGS
    if _SETTINGS is None:
        try:
            cfg = jak_config.load()
        except jak_config.ConfigError as e:
            raise SystemExit(f"ERROR: {e}")
        _SETTINGS = {
            "cfg": cfg,
            "workspace": str(cfg.path("workspace")),
            "queries": cfg.lines("linkedin_queries") or DEFAULT_QUERIES,
            "ok_locations": tuple(x.lower() for x in cfg.list("onsite_locations")),
            "max_exp": cfg.int("max_experience_years") or 5,
            "min_salary": cfg.int("min_salary") or 15000,
            "currency": cfg.get("currency") or "",
            "timezone": cfg.get("timezone") or "",
        }
    return _SETTINGS


def __getattr__(name):  # lazy attributes for the scripts: L.REPO, L.SEARCH_QUERIES, ...
    if name == "REPO":
        return settings()["workspace"]
    if name == "SEARCH_QUERIES":
        return settings()["queries"]
    if name == "ACCEPTED_LOCATIONS":
        return settings()["ok_locations"]
    raise AttributeError(name)


# sortBy is set in the URL: the UI dropdown click is unreliable on this
# React re-implementation, and this param is what the manual Latest click
# produces (verified 2026-09-14).
SORT_LATEST = '&origin=FACETED_SEARCH&sortBy=%5B%22date_posted%22%5D'
SEARCH_URL = "https://www.linkedin.com/search/results/content/?keywords={kw}" + SORT_LATEST
MIN_ITEMS = 50

POSTS_CSV_FIELDS = ["post_link", "full_text", "should_apply", "how_to_apply",
                    "comment", "seen_before", "verdict", "source_query"]
# Compatibility alias for callers that used the first implementation.
ITEMS_CSV_FIELDS = POSTS_CSV_FIELDS
DETAILS_CSV_FIELDS = ["post_link", "company", "position", "deadline", "location",
                      "remote", "experience", "apply_method", "contact", "apply_link",
                      "salary_raw", "skills", "cover_letter_required", "jd_text",
                      "scrape_status", "notes"]
DECISIONS_CSV_FIELDS = ["post_link", "company", "position", "deadline", "remote",
                        "appropriate", "reason", "method", "template_used", "status", "notes"]

JOB_HINTS = re.compile(r"(hiring|vacanc|position|job|role|apply|deadline|recruit|opening|we are looking|join our team|candidate)", re.I)
NOT_JOB_HINTS = re.compile(r"(celebrat|congratul|poll|newsletter|course|birthday|anniversar)", re.I)
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
URL_RE = re.compile(r"https?://[^\s)]+", re.I)


def run_dir(date=None):
    path = os.path.join(settings()["workspace"], "JDs", "linkedin", date or datetime.now().strftime("%Y-%m-%d"))
    os.makedirs(path, exist_ok=True)
    return path


def cache_root():
    path = os.path.join(settings()["workspace"], "JDs", "linkedin-saved")
    os.makedirs(path, exist_ok=True)
    return path


def now_local():
    """Current time in the user's configured timezone (else the system one)."""
    env = dict(os.environ)
    tz = settings()["timezone"]
    if tz:
        env["TZ"] = tz
    result = subprocess.run(["date", "+%Y-%m-%d %H:%M %a"], capture_output=True, text=True, env=env)
    return result.stdout.strip()


def log(rundir, message):
    line = f"[{datetime.now().strftime('%H:%M:%S')}] {message}"
    print(line, flush=True)
    with open(os.path.join(rundir, "run_log.txt"), "a", encoding="utf-8") as stream:
        stream.write(line + "\n")


def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as stream:
        return json.load(stream)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as stream:
        json.dump(data, stream, indent=2, ensure_ascii=False)


def applied_cache_path():
    return os.path.join(cache_root(), "applied_cache.json")


def live_sheet_rows(range_=None):
    """Read the live tracker. Returns [(company, position, status, link)] or [] on failure."""
    try:
        import jak_google
        cfg = settings()["cfg"]
        tab = cfg.get("sheet_tab") or "Sheet1"
        values = jak_google.sheet_get(cfg.require("sheet_id"), range_ or f"{tab}!A2:P")
    except Exception:
        return []
    rows = []
    for r in values:
        if len(r) < 3:
            continue
        rows.append((r[1], r[2], r[9] if len(r) > 9 else "sent",
                     r[7] if len(r) > 7 else ""))
    return rows


TRACKING_PARAMS = ("utm_", "trk", "trackingid", "refid", "src", "fbclid", "gclid")


def canonical_url(url):
    """Normalize a job URL so the same posting compares equal.

    Host case, scheme, trailing slash, fragment and tracking params are dropped;
    meaningful params (e.g. ?job=<id>) are kept and sorted.
    """
    if not url:
        return ""
    url = url.strip()
    m = re.match(r"^[a-zA-Z][\w+.-]*://([^/?#]+)([^?#]*)(?:\?([^#]*))?", url)
    if not m:
        return ""
    host = m.group(1).lower()
    if host.startswith("www."):
        host = host[4:]
    path = (m.group(2) or "/").rstrip("/") or ""
    keep = []
    for pair in (m.group(3) or "").split("&"):
        if not pair or "=" not in pair:
            continue
        k, v = pair.split("=", 1)
        if k.lower().startswith(TRACKING_PARAMS):
            continue
        keep.append((k.lower(), v.rstrip("/")))
    keep.sort()
    query = "&".join(f"{k}={v}" for k, v in keep)
    return f"{host}{path}" + (f"?{query}" if query else "")


SHORT_LINK_HOSTS = ("lnkd.in", "bit.ly", "tinyurl.com", "t.co", "shorturl.at")


def is_short_link(url):
    return any(h in (url or "").lower() for h in SHORT_LINK_HOSTS)


INTERSTITIAL_JS = (
    "(function(){var t=document.body?document.body.innerText:'';"
    "var m=t.match(/https?:\\/\\/[^\\s\"'<>]+/g)||[];"
    "return JSON.stringify(m.filter(function(u){return u.indexOf('linkedin.com')<0"
    "&&u.indexOf('licdn.com')<0;}).slice(0,3));})()"
)


def resolve_short_link(tab):
    """Read the destination from LinkedIn's outbound-link interstitial.

    LinkedIn wraps outbound links in a safety page that prints the real target
    URL as text. Returns '' when the tab is not on that page.
    """
    out = cdp_eval(tab, INTERSTITIAL_JS)
    try:
        urls = json.loads(out) if isinstance(out, str) else out
    except Exception:
        urls = None
    if isinstance(urls, str):
        try:
            urls = json.loads(urls)
        except Exception:
            urls = None
    if not urls:
        return ""
    return urls[0].rstrip(".,)\"'")


def is_applied_live(company, position, applied=None, snapshot_paths=None, url=""):
    """Sheet-first application check. Must be called before any draft or form fill.

    Matches on company+position AND independently on the application URL, so a
    repost that hides the employer ("Unnamed (post)") is still caught."""
    hit, why = is_applied(company, position, applied=applied, snapshot_paths=snapshot_paths)
    if hit:
        return hit, why
    rows = live_sheet_rows()
    if not rows:
        return False, "live sheet unreachable (local history checked only)"
    company_key, position_key = normalize_key(company), normalize_key(position)
    want_url = canonical_url(url)
    for row_company, row_position, row_status, row_link in rows:
        if APPLIED_STATUS_RE.search(row_status or ""):
            if want_url and canonical_url(row_link) and canonical_url(row_link) == want_url:
                return True, (f"live sheet URL match: {row_link} "
                              f"[{row_company} / {row_position} {row_status}]")
            rc, rp = normalize_key(row_company), normalize_key(row_position)
            if not company_key or not rc or (rc not in company_key and company_key not in rc):
                continue
            if position_key and rp and position_key not in rp and rp not in position_key:
                continue
            return True, f"live sheet row: {row_company} / {row_position} [{row_status}]"
    return False, ""


def normalize_key(value):
    return re.sub(r"[^a-z0-9]+", "", (value or "").lower())


def application_key(company, position):
    return normalize_key(company) + "+" + normalize_key(position)


APPLIED_STATUS_RE = re.compile(
    r"(sent|applied|interview|submitted|draft|staged|cancelled|rejected|no response)", re.I)


def _history_rows(path):
    """Yield (company, position, status) triples from a tracker artifact."""
    name = os.path.basename(path)
    if name.endswith(".json"):
        try:
            data = load_json(path, [])
        except Exception:
            return
        if not isinstance(data, list) or not data:
            return
        header = [str(h).strip().lower() for h in data[0]]
        def idx(*names):
            for n in names:
                if n in header:
                    return header.index(n)
            return None
        ci, pi, si = idx("company"), idx("position"), idx("job status")
        if ci is None or pi is None:
            return
        for row in data[1:]:
            if not isinstance(row, list) or len(row) <= max(ci, pi):
                continue
            yield (str(row[ci]), str(row[pi]), str(row[si]) if si is not None and len(row) > si else "sent")
        return
    with open(path, encoding="utf-8", errors="ignore") as stream:
        for line in stream:
            cells = []
            if line.lstrip().startswith("|"):
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
            elif not name.startswith("agent_review"):
                try:
                    cells = [c.strip().strip('"') for c in next(csv.reader([line]))]
                except Exception:
                    cells = []
            if len(cells) >= 4 and cells[0].lower() not in ("row", "date", "post_link", "post_key"):
                yield (cells[1], cells[2], " ".join(cells[3:7]))


def is_applied(company, position, applied=None, snapshot_paths=None):
    """Check application history per row (company AND position in the SAME row)."""
    company_key = normalize_key(company)
    position_key = normalize_key(position)
    if not company_key:
        return False, ""

    applied = applied if applied is not None else load_json(applied_cache_path(), {})
    for existing in applied:
        if "+" not in existing:
            continue
        ec, ep = existing.split("+", 1)
        if normalize_key(ec) == company_key and (not position_key or normalize_key(ep) == position_key):
            return True, f"applied_cache match ({existing})"

    for path in snapshot_paths or []:
        if not os.path.exists(path):
            continue
        for row_company, row_position, row_status in _history_rows(path):
            rc, rp = normalize_key(row_company), normalize_key(row_position)
            if not rc or rc not in company_key and company_key not in rc:
                continue
            if position_key and rp and position_key not in rp and rp not in position_key:
                continue
            if APPLIED_STATUS_RE.search(row_status or ""):
                return True, f"history row match in {os.path.basename(path)}: {row_company} / {row_position}"
    return False, ""


def application_history_paths(exclude_dir=None):
    """Prior-application artifacts only. Never the current run's own files."""
    paths = []
    exclude_dir = os.path.abspath(exclude_dir) if exclude_dir else None
    ws = settings()["workspace"]
    tracker = os.path.join(ws, "JDs", "tracker")
    names = os.listdir(tracker) if os.path.isdir(tracker) else []
    paths.extend(os.path.join(tracker, n) for n in names if n.startswith("sheet_snapshot_") and n.endswith(".md"))
    paths.extend(os.path.join(tracker, n) for n in names if n.startswith("sheet_raw_") and n.endswith(".json"))
    for root, _, files in os.walk(os.path.join(ws, "JDs")):
        if exclude_dir and os.path.abspath(root).startswith(exclude_dir):
            continue
        for name in files:
            if name in ("STATUS.md", "apply_report.md", "apply_decisions.csv"):
                paths.append(os.path.join(root, name))
    return [p for p in paths if not (exclude_dir and os.path.abspath(p).startswith(exclude_dir))]


def read_csv(path, fields=None):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if fields:
        for row in rows:
            for field in fields:
                row.setdefault(field, "")
    return rows


def write_csv(path, fields, rows):
    with open(path, "w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, quoting=csv.QUOTE_ALL, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def search_url(query):
    return SEARCH_URL.format(kw=quote(query))


def sort_latest_url(url):
    """Force Sort-by-Latest onto any LinkedIn content-search URL."""
    if "sortBy" in url:
        return url
    sep = "&" if "?" in url else "?"
    return url + sep + SORT_LATEST.lstrip("&")


def looks_like_job(text):
    return bool(text and JOB_HINTS.search(text) and not (NOT_JOB_HINTS.search(text) and not re.search(r"(hiring|vacanc|apply|position)", text, re.I)))


def post_identity(author, text):
    """Return a stable identity when LinkedIn omits post permalinks from cards.

    LinkedIn's current search DOM exposes an author URL but no post URN. The
    hash prevents two posts by the same author from collapsing. `post_link` is
    therefore an identity URL, not claimed to be a navigable permalink.
    """
    author = (author or "").split("?")[0].rstrip("/")
    digest = hashlib.sha256((author + "\n" + (text or "")[:500]).encode("utf-8")).hexdigest()[:20]
    return f"{author}#post-{digest}" if author else f"linkedin-post://{digest}"


def extract_email(text):
    return (EMAIL_RE.search(text or "") or [""])[0]


def extract_links(text):
    return [u.rstrip(".,;]}") for u in URL_RE.findall(text or "")]


def auto_skip(details):
    """Return (skip?, reason). Limits come from config (Auto-skip section)."""
    st = settings()
    experience = details.get("experience", "")
    match = re.search(r"(\d+)\s*\+?\s*(?:years?|yrs?)", experience, re.I)
    if match and int(match.group(1)) > st["max_exp"]:
        return True, f"experience > {st['max_exp']} years ({experience})"
    salary = details.get("salary_raw", "").replace(",", "")
    values = [int(n) for n in re.findall(r"\d{4,6}", salary) if 3000 <= int(n) <= 900000]
    if values and min(values) < st["min_salary"]:
        return True, f"advertised salary below {st['min_salary']} {st['currency']} ({details.get('salary_raw')})".replace("  ", " ")
    if details.get("remote") != "yes" and st["ok_locations"]:
        location = details.get("location", "").lower()
        if location and not any(name in location for name in st["ok_locations"]):
            return True, f"on-site location not acceptable ({details.get('location')})"
    return False, ""


def cdp_new_tab(url, wait=8, tries=2):
    """Open a new tab and make sure the URL actually loaded.

    Chrome 151 ignores the `/json/new?url=` parameter and lands on about:blank,
    so we navigate explicitly and verify the committed URL before returning.
    """
    last = ""
    for _ in range(tries):
        result = subprocess.run(["python3", CDP_PY, "newtab", url],
                                capture_output=True, text=True, timeout=30)
        lines = result.stdout.strip().splitlines()
        tab_id = lines[-1].strip() if lines else ""
        if not tab_id or " " in tab_id:
            raise RuntimeError("newtab failed: " + result.stdout + result.stderr)
        subprocess.run(["python3", CDP_PY, "nav", tab_id, url,
                        "--wait", str(wait)], capture_output=True, text=True, timeout=120)
        last = tab_id
        href = cdp_href(tab_id)
        if href and not href.startswith("about:"):
            return tab_id
        time.sleep(3)
    raise RuntimeError(f"tab {last} stayed on about:blank for {url}")


def cdp_href(tab_id):
    try:
        return (cdp_eval(tab_id, "location.href") or "").strip().strip('"')
    except Exception:
        return ""


def cdp_eval(tab_id, js, await_promise=False):
    command = ["python3", CDP_PY, "eval", tab_id]
    if await_promise:
        command.append("--await")
    command.append(js)
    result = subprocess.run(command, capture_output=True, text=True, timeout=90)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result.stdout


def cdp_close(tab_id):
    subprocess.run(["python3", CDP_PY, "close", tab_id], capture_output=True, text=True, timeout=30)
