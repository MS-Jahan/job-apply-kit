---
name: bdjobs-full-run
description: Full BDJobs automation pipeline via three scripts (bd1_scrape, bd2_trim_save, bd3_filter_apply). Search sweep to jobs.csv, model pass for should_scrape, detail scrape and Save clicks, model pass for apply decisions, then portal apply or Gmail draft with salary-range logic, Drive and Sheet sync, and a run report. Invoke with /bdjobs-full-run.
user-invocable: true
---

# BDJobs full run (3-script pipeline)

Universal rules: `{{CORE_DIR}}/OPERATIONS.md` (#accounts #truth #documents #tracking #browser).
Config keys read: `bdjobs_terms`, `max_experience_years`, `min_salary`, `onsite_locations`, `remote_ok`,
`salary_floor_remote`, `salary_floor_onsite`, `cv_source`, `sheet_id`, `drive_folder_id`, `cdp_port`, `workspace`.
Scripts: `{{SKILL_DIR}}/scripts/`. State root: `<workspace>/JDs/bdjobs/<run-date>/` (default: today).
Site notes (selectors, login probe, apply-form gotchas, triage): `references/bdjobs-site-notes.md`.

## Hard rules

1. **Debug browser live** on `cdp_port` (`curl -s http://127.0.0.1:<cdp_port>/json/version`). Probe the login with `https://mybdjobs.bdjobs.com/jobseeker-panel/saved-jobs?lang=en` before the Save and apply phases.
2. **Never send Gmail drafts and never submit external portals** (OPERATIONS #accounts). Documented exceptions for THIS skill only, authorized by the user: completing the BDJobs portal apply (the BDJobs "Apply" button and its salary form) and clicking "Apply Anyway" on the salary-warning modal.
3. **One application per unique company + position, ever.** Dedup against the tracker snapshot, `JDs/bdjobs/applied/*.json` and earlier `apply_report.md` files.
4. **Facts from the live sources** (OPERATIONS #sources) and today's `skills_context.md` in the run dir. Keyword gating applies (#truth). Judge deadlines against `TZ=Asia/Dhaka date` (BDJobs shows Dhaka time).
5. **Idempotent and resumable.** Rerun after a crash; the scripts skip finished rows.
6. **Auto-login.** bd2 (Save) and bd3 (apply) detect the login page (`bd_common.login_page_detected`) and log in through `bd_common.ensure_login` (username, Continue, password, Sign in), then return to the intended URL. Credentials live in `<workspace>/JDs/bdjobs/.env` (`BDJOBS_USERNAME=...`, `BDJOBS_PASSWORD=...`); that file is never committed. Missing or empty file = hard stop with a message.
7. **404 retry.** A page saying `Cannot GET ...` is retried twice with a 6-second gap before it counts as failed (apply-online and details fallback).
8. **Details page is ground truth.** If the apply flow ends UNCONFIRMED, open `/h/details/<id>?ln=1`; "Already Applied" or "Undo Application" means the job IS applied (screenshot, decision row, sheet row).

## Auto-skip (model pass 2; helper `bd_common.auto_skip`, limits from config)

Skip a job automatically when any holds:
- required experience is more than `max_experience_years`;
- advertised salary is below `min_salary`;
- on-site and the location text contains none of `onsite_locations` (remote is acceptable anywhere when `remote_ok` is true; an empty list disables this check);
- department mismatch (non-development roles).

Skipped jobs still get a sheet row: status `Skipped`, comment starting with `[Worth Checking]` or `[Worth Overwriting]` plus the reason. After model pass 2 run `python3 {{SKILL_DIR}}/scripts/bd3_filter_apply.py skips`.
Strong fits and user-flagged overrides bypass auto-skip: always select the requested match limit and the advertised salary range when a form offers them.

## Sheet conventions (BDJobs-specific; column contract in `{{CORE_DIR}}/references/tracker-columns.md`)

- Resume Drive (D): always `[bdjobs-profile-CV]` for portal applies. Status information lives only in Job Status (J).
- Salary/Budget (M): the ADVERTISED salary text (`Tk. 40000 - 80000 (Monthly)`), or `Negotiable`. Never our input value: that lives in `apply_decisions.csv` (`salary_input`).
- Contact/Email (L): any contact info in the posting: email, office address (helper `bd_common.extract_contact`).
- Comments (O): meaningless or edge-case entries start with `[Worth Checking]` or `[Worth Overwriting]`, then the note.

## Workflow

### Step 0: bootstrap
- `TZ=Asia/Dhaka date`; login probe.
- `skills_context.md` in the run dir must exist and be fetched today; otherwise build it from `cv_source` (skills list, project catalog, what the candidate does not have).

### Step 1: search sweep
```bash
python3 {{SKILL_DIR}}/scripts/bd1_scrape.py                      # all terms from bdjobs_terms, 6 pages each
python3 {{SKILL_DIR}}/scripts/bd1_scrape.py --terms "Rust,Go" --resume   # chunks (about 4 min per term)
```
Output: `jobs.csv` (all fields quoted) and `scrape_log.txt`. Direct-URL search per term, trusted-click pagination.

### Step 2: model pass 1 (verify and trim)
- Read `scrape_log.txt` and `jobs.csv`; verify page coverage (6 pages, or exhausted, or noted zero results); re-scrape gaps with `--terms <t> --resume`.
- Set `should_scrape` Yes/No per row from title, company and deadline against `skills_context.md` (expired deadline = No; patterns the candidate does not match, such as senior roles beyond the experience cap or unrelated stacks, = No).
- Update the CSV with a small script that keeps all fields quoted.

### Step 3: detail scrape and Save
```bash
python3 {{SKILL_DIR}}/scripts/bd2_trim_save.py                     # should_scrape=Yes rows, clicks Save
python3 {{SKILL_DIR}}/scripts/bd2_trim_save.py --ids 1527109,1522603   # manual override
```
Output: `details.csv` (full JD, buttons, save_action, salary_raw, apply_procedure).

### Step 4: model pass 2 (apply decisions)
Build `apply_decisions.csv` (fields in `bd_common.DECISIONS_CSV_FIELDS`). Per job: `appropriate` Yes/No with a one-line `reason` from the FULL JD against the profile; dedup (rule 3); `method` = `bdjobs` (Apply button present), `email` (email in apply_procedure) or `link`; compute `salary_input`:
```bash
python3 {{SKILL_DIR}}/scripts/bd3_filter_apply.py salary --text "<salary_raw>" [--remote]
```
Range logic: floors come from `salary_floor_remote` / `salary_floor_onsite`; a range whose low bound is above the floor anchors at the low bound; a range crossing the floor uses the midpoint (not below the floor); a range below the floor uses the floor (the Apply Anyway fallback); negotiable or missing uses the floor. Missing floors in the config are a hard error, not a default.

### Step 5: execute
```bash
python3 {{SKILL_DIR}}/scripts/bd3_filter_apply.py apply --dry-run         # preview first
python3 {{SKILL_DIR}}/scripts/bd3_filter_apply.py apply [--limit N]       # portal applies + sheet rows
python3 {{SKILL_DIR}}/scripts/bd3_filter_apply.py email --jid ID --to A --subject S --body-file F --attach PDF
python3 {{SKILL_DIR}}/scripts/bd3_filter_apply.py report
```
- `apply` handles salary fill, submit, Apply Anyway, the confirmation screenshot, the decisions status and the sheet row. UNCONFIRMED becomes `skipped-blocked`: fall back to the email path.
- Email path: the closest-fit template from `templates_dir` as-is (`[template] ` prefix in the sheet, OPERATIONS #documents), humanizer on the body, DRAFT only. For jobs offering both routes, do the portal apply plus a courtesy draft.
- Verify at the applied-jobs panel (ground truth) after the batch.

### Step 6: report
`bd3_filter_apply.py report` writes `apply_report.md`; append manual follow-ups (drafts to send, skipped-blocked jobs). Close tabs this run opened.
