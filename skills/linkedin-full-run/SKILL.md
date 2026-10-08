---
name: linkedin-full-run
description: Full LinkedIn pipeline via three scripts (li1_extract, li2_details, li3_apply). Sweeps LinkedIn post-search results (Posts filter, Latest sort set in the URL), captures full post text, lets the agent review the CSV, enriches approved rows, then stages each approved job: tracker check first, Gmail draft (never sent), or form or link filled and staged with the resume uploaded (never submitted). Invoke with /linkedin-full-run.
user-invocable: true
---

# LinkedIn full run (search-sweep pipeline)

Universal rules: `{{CORE_DIR}}/OPERATIONS.md` (#accounts #truth #documents #tracking #browser).
Config keys read: `linkedin_queries`, `max_experience_years`, `min_salary`, `currency`, `onsite_locations`,
`timezone`, `templates_dir`, `name`, `name_file`, `email_signature`, `sheet_id`, `drive_folder_id`, `cdp_port`, `workspace`.
Scripts: `{{SKILL_DIR}}/scripts/`. State root: `<workspace>/JDs/linkedin/<run-date>/`.

The source is LinkedIn **post search results**, not saved posts (`check-linkedin-saved` owns saved posts; the two skills share
`JDs/linkedin-saved/applied_cache.json`, see `{{CORE_DIR}}/references/shared-caches.md`). Queries come from `linkedin_queries`;
`linkedin-job-search` documents how to write them.

**Query format.** `linkedin_queries` is agent-mediated: the agent reads it from config.md, applies the separator convention
(**comma is the default separator** — one query per line with trailing commas, or all comma-separated on one line), asks the
user when a comma inside a query makes the separator ambiguous, and hands the resolved list to the sweep as
`--queries "a;b"`. The script does not parse the config itself: a script-side parser cannot tell a separator comma from a
comma inside a query, and LinkedIn silently returns zero results for a wrongly merged or over-long keywords string (a
~700-character multi-query string once swept 0 posts), so a wrong guess would fail invisibly.

## Role split

- **Scripts** do the mechanical work: sweep, capture text, parse fields, open pages, upload the PDF, write the sheet row, keep caches.
- **The agent** does the judgement: deciding `should_apply`, identifying the employer, writing the email subject and body, driving forms.
- **Scripts never search for company identity.** If a post does not name the employer, the agent finds it while reviewing and writes it into `agent_review.csv`.

## Hard rules

1. **Never submit, never send.** Forms are filled and left at the final Submit button; Gmail drafts are created and never sent; multi-page forms may click Next but the last page is left untouched.
2. **Tracker check before drafting or filling anything.** For every row call `li_common.is_applied_live(company, position)` (live sheet + local history), and again with `url=<resolved destination>` once a short link is resolved. A hit means `already-applied`: no draft, no form, no upload. The URL check matters because a repost often hides the employer ("Unnamed (post)"), so company + position alone can miss a duplicate that is already staged from another source.
3. **Tabs:** only close tabs this run opened. Staged application tabs stay open for the user. Login wall = hard stop, tab left open, recorded.
4. **Facts only from the live sources** (OPERATIONS #sources). Keyword gating applies (#truth). Templates come from `templates_dir`, used as-is (`[template] ` prefix in the sheet column); humanizer on every written text before it is saved.
5. **Email bodies are written by the agent**, humanized, saved as `<run-dir>/bodies/<company-slug>.txt` (optional `bodies/<slug>.subject` when the post dictates the subject). A row without a body file is marked `skipped-blocked` instead of drafting something generic. `--generic-body` allows a neutral body that makes no skill claims.
6. **Short links are recorded as-is.** `lnkd.in/...` stays verbatim in the CSV. During staging the script opens the link, reads the destination LinkedIn prints on its outbound-link interstitial (`li_common.resolve_short_link`), navigates on and records it. It never guesses the employer from a URL.
7. **Account:** every form or portal is handled as the Google role in OPERATIONS #accounts; check the banner before filling and after every reload.
8. **Sheet:** one row per processed job, full JD text in column I, extra notes only in column O, `[template] <link>` in the Resume Drive column (OPERATIONS #tracking).
9. **Auto-skip** (limits from config): experience above `max_experience_years`, advertised salary below `min_salary`, on-site outside `onsite_locations` (remote always OK), department mismatch. Skipped rows still get a sheet row with `[Worth Checking]` and the reason.

## Workflow

### Step 1: sweep (`li1_extract.py`)
```bash
python3 {{SKILL_DIR}}/scripts/li1_extract.py --date D --queries "a;b" [--rounds-per-query N]
```
`--queries` is required: prepare it first by reading `linkedin_queries` from config.md and splitting on the separator
(see Query format above), then pass the queries `;`-joined.
- The **Posts** filter and **Sort by Latest** are set in the URL (`&origin=FACETED_SEARCH&sortBy=%5B%22date_posted%22%5D`). Clicking the dropdown is unreliable, so every query navigates to the sorted URL and the run log must show `sort-by-latest: OK`.
- Expands every "see more" in place, then collects the full post text. A query stops early when the feed turns stale: N
  consecutive rounds with no fresh content (new posts, or a round that is mostly new — LinkedIn pads a spent query with
  suggested job-flavored posts, which would otherwise scroll past the real results indefinitely), N rounds with the page
  physically unable to scroll further, or the `--rounds-per-query` cap. Per-round counts land in `run_log.txt`.
- Verified selectors: posts live under `[data-testid="lazy-column"] > div[data-display-contents="true"]`, text in `span[data-testid="expandable-text-box"]`. Class names are hashed and unstable; there is no `data-urn` and no shadow DOM. There is no per-post permalink, so `post_link` is a stable identity (author URL + text hash), not a URL to open.
- Output: `posts.csv` (`post_link, full_text, should_apply, how_to_apply, comment, seen_before, verdict, source_query`), `posts.md`, `run_log.txt`; dedup verdicts go to `JDs/linkedin-saved/seen.json` (this skill's own file).

### Step 2: agent review (agent edits the CSV)
- Read `posts.csv` full text against the live profile facts.
- Author `<run-dir>/agent_review.csv`: `post_key, should_apply, company, position, how_to_apply, comment`. Resolve the employer yourself when the post omits it.
- Apply it: `python3 {{SKILL_DIR}}/scripts/apply_review.py --date <D>`
- Reject: individual open-to-work posts, agency or recruiter ads, project showcases, auto-generated hiring cards with no apply route, expired deadlines, stack mismatches. Mark reposts as duplicates of the kept row.

### Step 3: enrich (`li2_details.py`)
```bash
python3 {{SKILL_DIR}}/scripts/li2_details.py --date D --fresh
```
Parses approved rows from the captured text into `details.csv`. Links are kept as captured; no external resolution.

### Step 4: decide (`li3_apply.py prepare`)
```bash
python3 {{SKILL_DIR}}/scripts/li3_apply.py prepare --date D
```
Builds `apply_decisions.csv`, runs the auto-skip rules and the tracker plus history check, and marks `already-applied`, `skipped` or `pending`. Rows stay `pending` until the agent sets `appropriate=Yes`.

### Step 5: stage (`li3_apply.py apply`)
```bash
python3 {{SKILL_DIR}}/scripts/li3_apply.py dry-run --date D      # report only, no side effects
python3 {{SKILL_DIR}}/scripts/li3_apply.py apply   --date D [--limit N] [--generic-body]
python3 {{SKILL_DIR}}/scripts/li3_apply.py report  --date D
```
1. **Tracker check first** (`is_applied_live`); blocked rows stop here.
2. **Gmail draft** when the post gives an email: the template resume chosen from `templates_dir/INDEX.md` by keyword match, subject `Application for <position> - <name>` (or the per-slug override), the agent-written body, **draft only**. The draft id goes into the decision notes and sheet column O.
3. **Form or link staging** when the route is a form or link: open it, fill it, upload the resume, then **stop at Submit** (Easy Apply stops at Review). Screenshot to `output/linkedin-staged/<company-slug>/staged.png` and leave the tab open. A screenshot under about 20 KB means the page did not load: treat it as a failure.
4. **Drive, sheet and cache** for every row: the renamed template PDF is uploaded to the configured Drive folder, the sheet row is appended through the core guarded helper, `applied_cache.json` is updated.

Browser: `agent-browser` first, then the chrome-devtools MCP, then `{{CORE_DIR}}/scripts/cdp.py` (OPERATIONS #browser). Either way:
- Open the form in a NEW page; confirm the account banner (click "Switch account" and pick the Google role if needed; re-check after every reload). Google Forms account switch URL: `https://accounts.google.com/AccountChooser?continue=<form-url>&service=wise`, then click the entry for the account.
- Google Forms questions are `div[role=listitem]` blocks. Scope every fill to the block whose heading contains the question text and prefer the SMALLEST matching block (options are also `listitem`s, and clicking a checkbox twice turns it back off). Set text inputs through the native value setter plus `input`/`change` events, or Google ignores them.
- **Resume upload (the step that fails first).** "Add file" opens the Google Picker in a cross-origin iframe, not a native chooser, so `Page.fileChooserOpened` never fires. Use `{{CORE_DIR}}/scripts/picker_upload.py <tab-needle> <abs-file>` (pierced DOM, set in one connection). Verify: the file name appears in the form text and no `[role=progressbar]` remains.
- Fill every field, then **stop at the final Submit button**. Screenshot as evidence. Never click Submit.

### Step 5b: second hop after staging a short link
The `lnkd.in` URL lands on a LinkedIn safety page. After staging, open the revealed destination on the same tab, re-screenshot, and append both URLs to sheet column O.

### Step 6: report
`apply_report.md` lists per row: company, position, method, draft id, staged tab and screenshot, sheet result and the applied-history verdict, plus manual follow-ups (drafts to send, tabs awaiting Submit).

## Environment notes

- Some Chromium versions ignore `/json/new?url=` and land on `about:blank`; `li_common.cdp_new_tab` navigates explicitly and verifies before returning.
- `lnkd.in` links first show a LinkedIn "external link" interstitial; that is expected, not an error.

## Maintenance
Sheet rows added outside this skill: reconcile `applied_cache.json` on the next run.
