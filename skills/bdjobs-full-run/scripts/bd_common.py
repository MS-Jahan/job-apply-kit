#!/usr/bin/env python3
"""Shared helpers for the bd1/bd2/bd3 core scripts (CDP, CSV, logging, salary ranges)."""
import csv
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime

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
DEFAULT_TERMS = ["Software Engineer", "Software Developer", "Backend", "Frontend", "Full stack"]
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
            "terms": cfg.list("bdjobs_terms") or DEFAULT_TERMS,
            "floors": {"remote": cfg.int("salary_floor_remote"), "onsite": cfg.int("salary_floor_onsite")},
            "ok_locations": tuple(x.lower() for x in cfg.list("onsite_locations")),
            "max_exp": cfg.int("max_experience_years") or 5,
            "min_salary": cfg.int("min_salary") or 15000,
            "remote_ok": cfg.bool("remote_ok"),
            "currency": cfg.get("currency") or "BDT",
        }
    return _SETTINGS


def __getattr__(name):  # lazy attributes for the scripts: bc.REPO, bc.SEARCH_TERMS, ...
    if name == "REPO":
        return settings()["workspace"]
    if name == "SEARCH_TERMS":
        return settings()["terms"]
    if name == "SALARY_FLOORS":
        return settings()["floors"]
    if name == "OK_LOCATIONS":
        return settings()["ok_locations"]
    if name == "DEV":
        return f"http://127.0.0.1:{cdp.PORT}"
    if name == "CREDS_FILE":
        return os.path.join(settings()["workspace"], "JDs", "bdjobs", ".env")
    raise AttributeError(name)


JOBS_CSV_FIELDS = ["job_id", "title", "company", "location", "experience",
                   "deadline", "search_term", "page", "should_scrape", "scrape_status"]
DETAILS_CSV_FIELDS = ["job_id", "title", "company", "location", "deadline", "url",
                      "buttons", "save_action", "salary_raw", "jd", "apply_procedure",
                      "scrape_status"]
DECISIONS_CSV_FIELDS = ["job_id", "company", "position", "location", "deadline", "remote",
                        "appropriate", "reason", "salary_input", "salary_raw", "method",
                        "status", "notes"]


def run_dir(date=None):
    d = date or datetime.now().strftime("%Y-%m-%d")
    p = os.path.join(settings()["workspace"], "JDs", "bdjobs", d)
    os.makedirs(p, exist_ok=True)
    return p


def now_dhaka():
    out = subprocess.run(["bash", "-c", "TZ=Asia/Dhaka date '+%Y-%m-%d %H:%M %a'"],
                         capture_output=True, text=True)
    return out.stdout.strip()


def log(run_dir_, msg):
    line = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(os.path.join(run_dir_, "scrape_log.txt"), "a", encoding="utf-8") as f:
        f.write(line + "\n")


def devtools_up():
    try:
        subprocess.run(["curl", "-s", "--max-time", "3", f"http://127.0.0.1:{cdp.PORT}/json/version"],
                       capture_output=True, timeout=6, check=True)
        return True
    except Exception:
        return False


def tab_id(needle):
    return cdp.find(needle)


def new_tab(url):
    req = subprocess.run(["python3", CDP_PY, "newtab", url],
                         capture_output=True, text=True, timeout=30)
    tid = req.stdout.strip().splitlines()[-1].strip()
    if not tid or " " in tid:
        raise RuntimeError("newtab failed: " + req.stdout + req.stderr)
    return tid


def close_tab(tid):
    subprocess.run(["python3", CDP_PY, "close", tid],
                   capture_output=True, text=True, timeout=30)


def nav(tid, url, wait=7):
    subprocess.run(["python3", CDP_PY, "nav", tid, url,
                    "--wait", str(wait)], capture_output=True, text=True, timeout=90)


def eval_js(tid, js, await_promise=False, tries=2):
    last = None
    for _ in range(tries):
        r = subprocess.run(["python3", CDP_PY, "eval", tid]
                           + (["--await"] if await_promise else []) + [js],
                           capture_output=True, text=True, timeout=90)
        if r.returncode == 0:
            out = r.stdout.strip()
            if out.startswith('"'):
                try:
                    return json.loads(out)
                except Exception:
                    return out
            return out
        last = r.stderr
        time.sleep(2)
    raise RuntimeError((last or "eval failed")[-300:])


def shot(tid, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    subprocess.run(["python3", CDP_PY, "shot", tid, path],
                   capture_output=True, text=True, timeout=60)


def trusted_click(tid, locator_js):
    pos_raw = eval_js(tid, locator_js)
    pos = json.loads(str(pos_raw).strip('"')) if "{" in str(pos_raw) else None
    if not pos:
        return "NO_TARGET"
    import websocket
    ws = websocket.create_connection(f"ws://127.0.0.1:{cdp.PORT}/devtools/page/{tid}",
                                     timeout=30, suppress_origin=True)
    mid = 0

    def cmd(method, **params):
        nonlocal mid
        mid += 1
        ws.send(json.dumps({"id": mid, "method": method, "params": params}))
        deadline = time.time() + 15
        while time.time() < deadline:
            msg = json.loads(ws.recv())
            if msg.get("id") == mid:
                return msg.get("result", {})

    cmd("Input.dispatchMouseEvent", type="mouseMoved", x=pos["x"], y=pos["y"])
    cmd("Input.dispatchMouseEvent", type="mousePressed", x=pos["x"], y=pos["y"],
        button="left", clickCount=1)
    cmd("Input.dispatchMouseEvent", type="mouseReleased", x=pos["x"], y=pos["y"],
        button="left", clickCount=1)
    ws.close()
    return "CLICKED"


def read_csv(path, fields):
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def upsert_csv(path, fields, rows, key="job_id"):
    existing = {r[key]: i for i, r in enumerate(rows) if r.get(key)}
    merged = read_csv(path, fields)
    for r in rows:
        k = r.get(key)
        if k and k in {m[key] for m in merged}:
            for i, m in enumerate(merged):
                if m[key] == k:
                    merged[i].update({f: r[f] for f in fields if f in r})
        else:
            merged.append({f: r.get(f, "") for f in fields})
    tmp = path + ".tmp"
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, quoting=csv.QUOTE_ALL)
        w.writeheader()
        w.writerows(merged)
    os.replace(tmp, path)


NUM = r"(\d[\d,]*\s*[kK]?)"

def _to_int(s):
    s = s.strip().replace(",", "").lower()
    if s.endswith("k"):
        return int(float(s[:-1]) * 1000)
    return int(float(s))


def parse_salary_range(text):
    if not text:
        return None
    t = text.replace("\n", " ")
    m = re.search(NUM + r"\s*(?:-|–|—|to)\s*" + NUM, t)
    if m:
        try:
            lo, hi = _to_int(m.group(1)), _to_int(m.group(2))
            if 1000 <= lo <= hi <= 10_000_000:
                return lo, hi
        except Exception:
            pass
    m = re.search(r"(?:BDT|Tk\.?|Salary)\s*:?\s*" + NUM, t, re.I)
    if m:
        try:
            v = _to_int(m.group(1))
            if 1000 <= v <= 10_000_000:
                return v, v
        except Exception:
            pass
    return None


def compute_salary(salary_raw, remote, floors=None):
    floors = floors or settings()["floors"]
    floor = floors["remote"] if remote else floors["onsite"]
    if floor is None:
        raise SystemExit("ERROR: set salary_floor_remote and salary_floor_onsite in your config (Auto-skip section)")
    rng = parse_salary_range(salary_raw)
    if rng:
        lo, hi = rng
        if lo >= floor:
            return lo, f"range {lo}-{hi}: anchored at low bound"
        if hi >= floor:
            mid = (lo + hi) // 2
            val = max(floor, mid)
            return val, f"range {lo}-{hi} crosses floor: used {val}"
        return floor, f"range {lo}-{hi} below floor: kept floor (Apply Anyway fallback)"
    return floor, "no range detected: floor"


def salary_display(salary_raw, jd_text=""):
    raw = (salary_raw or "").strip()
    if raw:
        return raw
    m = re.search(r"Salary:\s*\n?([^\n]{1,60})", jd_text or "")
    return m.group(1).strip() if m else "Negotiable"


def extract_contact(apply_text=""):
    src = apply_text or ""
    m = re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", src)
    if m:
        return m.group(0)
    m = re.search(r"Address:\s*\n+([^\n]+(?:\n[^\n]+){0,2})", src)
    if m:
        return " ".join(m.group(1).split())[:120]
    return ""




def login_page_detected(tid):
    out = eval_js(tid, """(() => JSON.stringify({
      loginUrl: /signin|login/i.test(location.href),
      pw: !!document.querySelector('input[type=password]'),
      user: !![...document.querySelectorAll('input')].find(i => (i.placeholder || '').toLowerCase().includes('username'))
    }))()""")
    try:
        st = json.loads(str(out))
        if isinstance(st, str):
            st = json.loads(st)
        return bool(st.get("loginUrl") or st.get("pw") or st.get("user"))
    except Exception:
        return False


def load_bdjobs_creds():
    CREDS_FILE = __getattr__("CREDS_FILE")
    if not os.path.exists(CREDS_FILE):
        raise RuntimeError(
            f"BDJobs credentials missing: create {CREDS_FILE} with lines "
            "BDJOBS_USERNAME=... and BDJOBS_PASSWORD=...")
    creds = {}
    for line in open(CREDS_FILE, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        creds[k.strip()] = v.strip().strip('"').strip("'")
    user, pwd = creds.get("BDJOBS_USERNAME", ""), creds.get("BDJOBS_PASSWORD", "")
    if not user or not pwd:
        raise RuntimeError(
            f"BDJobs credentials incomplete in {CREDS_FILE} — set BDJOBS_USERNAME and BDJOBS_PASSWORD")
    return user, pwd


LOGIN_STEP1 = """(() => {
  const inp = [...document.querySelectorAll('input')].find(i =>
    (i.placeholder || '').toLowerCase().includes('username'));
  if (!inp) return 'NO_USER_INPUT';
  const set = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
  set.call(inp, '');
  inp.dispatchEvent(new Event('input', {bubbles: true}));
  set.call(inp, __USER__);
  inp.dispatchEvent(new Event('input', {bubbles: true}));
  const btn = [...document.querySelectorAll('button')].find(b => b.offsetParent &&
    /^continue$/i.test(b.innerText.trim()));
  if (!btn) return 'NO_CONTINUE';
  btn.click();
  return 'USER_SUBMITTED';
})()"""

LOGIN_STEP2 = """(() => {
  const pw = document.querySelector('input[type=password]');
  if (!pw) return 'NO_PASSWORD_YET';
  const set = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
  set.call(pw, '');
  pw.dispatchEvent(new Event('input', {bubbles: true}));
  set.call(pw, __PASS__);
  pw.dispatchEvent(new Event('input', {bubbles: true}));
  const btn = [...document.querySelectorAll('button')].find(b => b.offsetParent &&
    /^sign in$/i.test(b.innerText.trim()));
  if (!btn) return 'NO_SIGNIN_BTN';
  btn.click();
  return 'SUBMITTED';
})()"""


def ensure_login(tid, return_url=None, wait=8, log_fn=None):
    """Detect a BDJobs login page on tab and auto-login. Returns 'ok', 'logged-in', or raises."""
    if not login_page_detected(tid):
        return "ok"
    if log_fn:
        log_fn("login page detected - auto-logging in")
    user, pwd = load_bdjobs_creds()
    r1 = eval_js(tid, LOGIN_STEP1.replace("__USER__", json.dumps(user)))
    if "NO_" in str(r1):
        raise RuntimeError(f"login step1 failed: {r1}")
    for _ in range(10):
        time.sleep(2)
        r2 = eval_js(tid, LOGIN_STEP2.replace("__PASS__", json.dumps(pwd)))
        if "NO_PASSWORD_YET" not in str(r2):
            break
    if "NO_" in str(r2):
        raise RuntimeError(f"login step2 failed: {r2}")
    time.sleep(wait)
    out = eval_js(tid, "JSON.stringify({url: location.href, name: document.body.innerText.slice(0, 80)})")
    if "signin" in str(out).lower() and "sign out" not in str(out).lower():
        raise RuntimeError(f"login did not complete: {str(out)[:120]}")
    if log_fn:
        log_fn("login OK")
    if return_url:
        nav(tid, return_url, wait=wait)
    return "logged-in"


def auto_skip(exp_years=None, salary_low=None, location="", remote=False):
    """Return a skip reason or None. Limits come from config (Auto-skip section)."""
    st = settings()
    loc = (location or "").lower()
    if exp_years is not None and exp_years > st["max_exp"]:
        return f"skip: requires {exp_years}y experience (>{st['max_exp']}y cap)"
    if salary_low is not None and salary_low < st["min_salary"]:
        return f"skip: advertised salary {salary_low} below {st['min_salary']} floor"
    if remote and st["remote_ok"]:
        return None
    if st["ok_locations"] and not any(k in loc for k in st["ok_locations"]):
        return f"skip: on-site location '{location}' not in {', '.join(st['ok_locations'])}"
    return None


def sheet_append(row):
    """Append ONE tracker row (dict or JSON string) through the core guarded helper."""
    import sheet_append as sa
    if isinstance(row, str):
        row = json.loads(row)
    return sa.append(row)
