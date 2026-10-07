# 00 — config.md: the one file every skill reads first

Back to [index](index.md). Template: `config.example.md` in the kit repo.
Loader: `skills/job-apply-core/scripts/jak_config.py` (`--check`, `--show`, `--get KEY`).
Missing keys the example gained later? `jak_config.py --sync-keys` adds them without
touching existing values.

Location: `$JAK_CONFIG`, else `~/.config/job-apply-kit/config.md`. One markdown
file, outside the repo, never committed — it holds phone numbers, emails and
ids. Script-read values are bullets written exactly as `- **key:** value`;
lists are comma separated; empty or `<placeholder>` means "not set".

## The config-first rule

Every skill run starts the same way, before any other step:

1. Read `skills/job-apply-core/OPERATIONS.md` (universal rules) — every `SKILL.md` points
   at it in its first lines.
2. Load the config: `python3 skills/job-apply-core/scripts/jak_config.py --check` (fix
   every ERROR) and `--show` (masked values). If a required key is missing,
   stop and ask; do not guess.
3. The skill's own `SKILL.md` lists the exact keys it reads under "Config keys
   read" — those decide behavior, not defaults remembered from earlier sessions.

## What each key means

**Identity.** `name`, `name_file` (underscored, for filenames), `phone`,
`location`, `timezone`, `website`, `github`, `linkedin`, `email_header` (shown
on resumes, cover letters, portals), `email_google` (Google sign-in, Forms,
Gmail drafts — Role A). The two emails may match or differ, never conflate them.

**Sources.** `cv_source` (URLs or local paths, comma separated) is the ONLY
source of candidate facts, plus `projects_source` and `certifications_url` when
set. Skills snapshot what they read to `.cache/profile/<date>/` so a day's runs
share one fact base; when cache and live source disagree, live wins.

**Paths.** `workspace` (default: current directory or `$JAK_WORKSPACE`) holds the
run state: `JDs/` inputs and caches, `output/<company-slug>/` per-job evidence,
`templates/` the picked-as-is PDFs, `SESSIONS.md` the log. `templates_dir`
(default `<workspace>/templates`) is the template library with its `INDEX.md`
(pick best fit, rename-only — see [Templates](07-templates.md)). `cache_dir`
(default `<workspace>/.cache`) holds disposable run state: daily profile
snapshots, seen-post caches, agent scratch files. Safe to delete between runs;
skills rebuild it.

**Google.** `gog_account` selects the identity; `google_backend` is `auto`, `gog`
or `python`. `google_token_dir` (default `~/.config/job-apply-kit/google/`)
stores `google_client_secret.json` (your downloaded OAuth client — password
equivalent), one `google_token_<account>.json` per account, and the pending
OAuth session; dir 700, files 600. `drive_folder_id` is the upload destination
for EVERY generated document (each job's PDF lands here, shared anyone-with-link
at send time); `drive_templates_folder_id` archives template PDFs only.
`sheet_id` (+ `sheet_tab`, default `Sheet1`) is the tracker; paste the link into
`sheet_url` and the id is derived automatically; `sheet_columns` is the saved
header match for an adopted own-sheet (see [Email and tracking](06-email-and-tracking.md)).
Setup: [Google setup](02-google-setup.md), [Cloud Console walkthrough](02-cloud-console.md).

**Browser.** `cdp_port` (default 9222): the debug browser the user runs and the
agent attaches to (see [Browser setup](03-browser-setup.md)).

**Truth gates.** `banned_claims` (never claim), `unproven_claims` (not yet
proven). The agent fills these by asking, one skill group at a time — never by
guessing. Every generated document is checked against them.

**Application defaults.** `default_doc` (`resume` = 1 page, `cv` = 2 pages; a
post asking for a CV overrides per-job). `template_default` (`true` = use the
best template as-is without tailoring).

**Auto-skip.** Filters applied before any work: jobs needing more than
`max_experience_years`, or paying below `min_salary` (`currency`, e.g. BDT) are
skipped. `onsite_locations` lists acceptable onsite cities; `remote_ok` allows
remote posts. `salary_floor_remote` / `salary_floor_onsite` override `min_salary`
per work mode when set.

**Search terms.** `bdjobs_terms` (BDJobs keywords), `linkedin_queries` (one
post-search query per line), `fb_saved_urls`, `discord_channels` (with
`discord_cache_dir`, default `JDs/discord`). See [Job search](04-job-search.md).

**Signature.** `email_signature` (empty = built from Identity).

**Resume preferences.** Free-form prose for the resume skills (bullet variants,
fixed sections, role types, claim framing) — read by the agent, not by scripts.

## What happens per job (Drive + Sheet)

For every processed job, automatically: the PDF uploads to `drive_folder_id`
(anyone-with-link), and the public link lands in the tracker's Resume Drive
column. The row is appended the moment the job passes dedup (`status: Found`,
full post text in Job Description), and the SAME row moves forward after
drafting/staging (`Drafted` → `Staged` → `Applied`) — never a second row.
Full flow: [Email and tracking](06-email-and-tracking.md).

## Stale data: the live source always wins

`config.md` is a cache of the CV, not the truth. Whenever the config is created
or refreshed, the agent re-reads `cv_source` live (full text, contact block to
last line — via the debug browser for Google Docs) and updates the file, showing
a diff of changed keys and asking before overwriting any non-empty value. If the
CV changed since last time, the config changes with it — skills never reuse
yesterday's facts when today's source says otherwise.
