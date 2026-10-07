# OPERATIONS: universal rules for job-apply-kit

This is the single place for rules that apply to every skill. Skills keep only their own steps and
point here with `OPERATIONS.md#<anchor>`. Values in `<angle brackets>` or `config key` come from the
user's `config.md` (see `jak_config.py --show`). Never write personal facts into this file or into skills.

<a id="precedence"></a>
## 1. Precedence

1. A newer rule in this file beats an older one. The changelog (section 14) records every conflict that was decided.
2. A skill may be stricter than this file, never looser.
3. User instructions in the current conversation beat both, except the never-submit and truth rules (sections 4 and 6), which a user can relax only explicitly and for one task.

<a id="setup"></a>
## 2. Setup

- Config is one markdown file: `$JAK_CONFIG` or `~/.config/job-apply-kit/config.md`. Load keys through `{{CORE_DIR}}/scripts/jak_config.py` (`--check`, `--show`, `--get KEY`). If a required key is missing, stop and ask; do not guess.
- Run `doctor.sh` when something external fails (tools, Google backend, debug browser). Tool details live in `docs/EXTERNAL_TOOLS.md`.
- Runtime data lives in the workspace (`workspace` key): `JDs/` inputs, caches and run state; `output/<company-slug>/` per-job files and evidence; `templates/` the user's templates; `SESSIONS.md` the session log; `.cache/` live-source snapshots.

<a id="sources"></a>
## 3. Sources of candidate facts

- The only source of facts about the candidate is `cv_source` (URLs or local files), plus `projects_source` if set. At the start of every session that touches candidate content (tailoring, cover letters, critiques, applications) read all of them.
- If a source is unreachable, stop and tell the user. Do not fall back to memory, old resumes or old outputs.
- Snapshot what you read to `.cache/profile/<date>/` so sub-agents share one fact base for that day.
- Local libraries (`resumes/`, `resume_builder` experience files and bundles, old `output/` folders) are caches. If they disagree with the live source, the live source wins.
- Education, dates, grades, titles and certification lists are always read from the source, never hard-coded in rules, skills or templates' prose rules.

<a id="accounts"></a>
## 4. Accounts, never-submit, drafts

- Two roles. Role A, `email_google`: Google sign-in, Google Forms, Gmail drafts, Drive and Sheets owner. Role B, `email_header`: shown on resume headers, cover letters, company portals and direct web forms. They may be the same address.
- **Never submit.** Every external application (Google Forms, company portals, Easy Apply flows) is filled and staged at the final Submit/Apply button. The user clicks it. Multi-page forms may use Next; the last page is left untouched. Save a screenshot as evidence to `output/<company-slug>/`. A tiny screenshot (under about 20 KB) means the page did not load: treat it as a failure.
- **Never send.** Email applications are Gmail drafts only. No script in this kit can send mail; do not look for another way.
- Documented exceptions are stated inside the one skill that has them (for example a portal's own "apply" button that the user explicitly authorized for that skill). Anywhere else, the rule above holds.
- Google Forms: the browser session must be signed in as Role A. If the form banner shows another account, use "Switch account" and pick Role A before filling; uploads record the logged-in identity. A page reload can silently switch the account back, so re-check the banner after every reload and refill if the form was staged under the wrong account.
- Login wall = hard stop: leave the tab open, record it, move on.
- Tabs: only close tabs this run opened. Staged application tabs stay open for the user.

<a id="naming"></a>
## 5. Naming

- File name: `<name_file>_<CV|RESUME>_<Company>.pdf`, each word capitalized, short company name or standard abbreviation.
- Email subject: `Application for <Position> - <name>` (ASCII hyphen).
- If the job post dictates a file-name format or an exact subject line, use that exactly.

<a id="truth"></a>
## 6. Truth gates

- **No fabrication.** No invented employers, titles, projects, metrics or claims. If a skill or claim is not in the sources, it does not go in a document.
- **Skill-keyword gating.** A job-post keyword enters a CV or resume only if it appears in the sources. Otherwise mention willingness to learn it in the email or cover letter, never in the CV or resume.
- **Banned and unproven claims.** Never list anything in `banned_claims`. Do not claim anything in `unproven_claims`; express willingness in the cover letter instead. Both lists belong to the user and are only changed by the user.
- **Verb discipline.** Full-ownership verbs (built, designed, engineered, developed) only for work stated as independent. Hedged verbs (contributed to, supported, assisted, extended) for joint work, shared or pre-existing codebases, or work the source frames as extending someone else's platform.
- **Provenance framing.** Employer platforms are "maintained or extended", not "built". Personal projects with no stated production users are not described as deployed at scale. Metrics are used exactly as the source states them.
- **Published work.** Never present unpublished work as published or internal tools as peer-reviewed or widely adopted.
- **Certifications.** Include a link to the full list (`certifications_url`, else taken from the source) in the section header and after the last item. One certification, honor or competition per line, not pipe-separated, while the page budget allows.
- **Priority order.** Accuracy > Relevance > Impact > ATS fit > Brevity. Never trade truth for impression.

<a id="format"></a>
## 7. Format

- Pure black text (#000000). No grey text in body or titles.
- Compile LaTeX with `tectonic -X compile`; `pdflatex` is the fallback. Margins `0.38in` sides, `0.28in` top and bottom.
- Page budget: resume = exactly 1 page, CV = exactly 2 pages, cover letter = 1 page. Verify with `pdfinfo <file>.pdf | grep Pages` after every edit.
- Resume is the default document. Use a CV only when the post asks for a CV or a multi-page profile.
- Density: agents under-fill. Add everything true and relevant (all relevant skills, projects, metric bullets). Put the post's required skills and projects first and bold them; put less relevant items later. If over budget, drop one or two irrelevant items; never thin relevant content or truncate bullets globally. A resume should end near the bottom of page 1 (within about 70 pt); a CV's page 2 should be nearly full.
- Zero em-dashes in every document and email. Date-range en-dashes (`Jan 2026 -- Present`) are fine. Subject lines use a plain hyphen.
- LaTeX: `$\sim$` for "approximately", never a raw `~`; `$\beta$` for Greek letters; use `mhchem` only if chemistry is present. No internal folder or repo names in text; describe the method or tool. No lines-of-code or test counts.
- Co-authors: bold the candidate's name; truncate author lists with "et al." above four authors.
- `resume.cls`/`cv.cls` documents (resume-kit) run `char_count.py` on bullets to confirm 1L/2L/3L limits; article-class templates are checked by compile and page count instead. Do not mix the two systems in one document.

<a id="documents"></a>
## 8. Documents, emails, forms

**Template default.** Unless the user explicitly asks for a customized document, do not create one. Pick the best-fitting template from `templates_dir` using its `INDEX.md` (match the post's keywords to each category), and attach it as-is. Rename-only: `cp` the template PDF to the per-company name from section 5; no edits, no recompile; check `pdfinfo` after copying. If no template fits well or `templates_dir` is empty, offer `/create-template`.

**Customization exception.** Create a customized document only if (1) the user asks, or (2) the post needs a combined skill set no single template covers. Then: read the post fully, read the sources, use the resume skills (`make-resume`, `make-cl`, `edit-resume`, `critique`), run the **humanizer** on all prose before compiling, and verify the page budget.

**Email applications.**
- An email body is mandatory for every email application.
- Run the humanizer on it before saving.
- State exactly which documents are attached (resume, CV and/or cover letter, exactly what the post requested).
- Create a Gmail draft (Role A account) with the documents attached. Never send.
- If the careers page or a job-board listing cannot be found, still draft the email to the contact in the post (or the company's HR address) and stage it for the user.

**Cover letters.** If the post gives cover-letter instructions, make small edits to a copy of the matching `CL_*` template; never change the template's structure. Run the humanizer on any edited letter before compiling. No salary discussion.

**Google Forms.** Open the form in a new tab, confirm the account banner (section 4), fill every required field, upload the document, stop at Submit. Dropdowns are ARIA listboxes: click the listbox, take a fresh snapshot, click the option. File upload opens the Google Picker in a cross-origin iframe; use `{{CORE_DIR}}/scripts/picker_upload.py`.

**Humanizer.** The `humanizer` skill runs on email bodies, cover letters, and CV/resume prose, before the PDF is compiled or the draft saved.

<a id="batch"></a>
## 9. Batches, sub-agents, search

- **Intake.** Job-post image batches go to `JDs/pasted-batch-<date>/` as `img_NN.png` in order, with a `STATUS.md` recording done, not-done and needs-search verdicts.
- **Tracker snapshot.** Before a batch, run `sheet_snapshot.py` (it writes `JDs/tracker/sheet_snapshot_<date>.md`), and snapshot the sources (section 3).
- **One sub-agent per job**, with a self-contained prompt (post facts, image path, apply method, page budget, deadline). At most 5 run at once. If a sub-agent has no browser tools, it reports back and the orchestrator stages the form.
- **Dedup.** Before processing any post, check the tracker snapshot and local caches for the same company and position (posts are often reposted, and a repost may hide the employer: also compare the apply link). One application per unique job.
- **Search only when needed.** If a post clearly shows the company, the requirements and a contact or apply link, do not search. Otherwise: SearXNG MCP first, then read pages with `agent-browser`; the chrome-devtools MCP only if agent-browser cannot drive the page. Never write curl/grep scrapers against search-engine result pages. On a 429, retry once after a pause, then switch to browser reading.

<a id="tracking"></a>
## 10. Tracking (Drive and Sheet)

- Every processed job, including skipped, drafted and staged ones, gets one tracker row. Update the sheet after every application.
- Upload documents with `python3 {{CORE_DIR}}/scripts/jak_google.py drive-upload <file> --name <name>` (goes to `drive_folder_id` and is shared as anyone-can-view; refused outside that folder).
- Append rows only with `python3 {{CORE_DIR}}/scripts/sheet_append.py append '<json-row>'`. Never hand-roll an append: a miscounted field list shifts every column. The 15 columns A..O are in `references/tracker-columns.md`.
- Column I holds the full job description text, never a summary. Column O holds extra info only (message or draft ids, staged-form notes, file references), never job text.
- Resume Drive column (D): when a template was used, the entry starts with `[template] ` followed by the link. If CV, resume and cover letter are all provided, put all links in that same cell, comma-separated. Template documents need no manual CV review; only the email or filled form does.
- Never overwrite statuses the user set by hand (for example "sent" or "skipped").
- The Drive `templates` subfolder (`drive_templates_folder_id`) archives template PDFs; it is not used by the apply flow.
- `sheet_init.py` creates the folder, subfolder and sheet for a new user and writes the ids to config.

<a id="browser"></a>
## 11. Browser tooling

- Order: **`agent-browser`** (default) → **chrome-devtools MCP** (fallback) → raw CDP scripts (`cdp.py`, last resort).
- All three attach to the debug browser the user already runs (same profile, logins, extensions). The kit never launches, restarts or kills that browser. Port: `cdp_port`.
- Debug-browser setup is agent-driven: `browser_setup.py --list` detects installed Chromium browsers (Chrome, Edge, Brave, Chromium — Firefox excluded) and suggests one; after the user picks (several allowed), `--browser <names> --create` writes per-browser launchers (`browser-debug-<name>.bat`/`.sh`) plus desktop shortcuts. The user clicks a shortcut and leaves the browser running.
- Use the MCP only when agent-browser keeps failing to attach, the daemon cannot be recovered, it cannot drive the page, or the step needs an MCP-only capability (console or network inspection, performance trace, Lighthouse, uid-targeted element work).
- Chain related commands in one shell call, and wrap each in `timeout`:
  ```bash
  export PATH="$HOME/.npm-global/bin:$PATH"
  agent-browser connect <cdp_port> && agent-browser tab list   # only about:blank = re-connect
  agent-browser tab new && timeout 60 agent-browser open <url> && timeout 30 agent-browser snapshot -c
  ```
- Open pages in new tabs, never reuse the user's tabs, close only tabs you opened.
- A fallback never changes the hard rules: never submit, never close a tab you did not open, never kill the user's browser.
- Details: `references/agent-browser.md` and `references/cdp-tools.md`.

<a id="skills"></a>
## 12. Skill index

| Skill | Purpose |
|---|---|
| `job-apply-core` | this file, config setup, shared scripts |
| `humanizer` | strip AI-isms from prose |
| `create-template` | generate the user's own CV, resume and cover-letter templates |
| `make-resume`, `make-cl`, `critique`, `edit-resume` | tailored documents for a specific post (deep-tailoring flow) |
| `setup-extract`, `setup-build-kb` | build the optional knowledge base for the deep-tailoring flow |
| `bdjobs-full-run` | BDJobs scripted pipeline: search, save, decide, apply or draft |
| `li-full-run` | LinkedIn post-search pipeline: sweep, review, enrich, stage |
| `linkedin-job-search` | save matching LinkedIn posts (save-only) |
| `check-li-saved`, `check-fb-saved`, `check-ph-discord`, `check-image-batch` | scan a source and process new jobs end to end |

<a id="logging"></a>
## 13. Session log

Record each job session in `SESSIONS.md` (local, never shared): date, source, what was drafted or staged, ids, what the user must do next. Do not keep session logs in this file or in skills.

<a id="changelog"></a>
## 14. Changelog (conflicts decided)

| Topic | Old conflict | Decision |
|---|---|---|
| Tracker columns | 14, 15 or 8 columns in different docs | 15 columns A..O, `references/tracker-columns.md` |
| Resume or CV when unsure | one doc said CV, others resume | resume (1 page); CV only when asked |
| Resume pages | 2 in one config, 1 in rules | 1 |
| Subject separator | en-dash vs em-dash ban | plain hyphen |
| Gmail drafts | three helpers, "cannot attach" | `jak_google.py draft --attach` (gog or python backend) |
| Compiler | pdflatex vs tectonic | tectonic default, pdflatex fallback |
| Sheet writes | formula-looking text corrupted cells | RAW writes only |
| Public sharing | any file | only inside the configured Drive folder |
