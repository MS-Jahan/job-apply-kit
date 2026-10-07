---
name: job-apply-core
description: Shared core for job-apply-kit. Holds the central rules (OPERATIONS.md), config loader, Google and browser helpers used by every apply skill. Invoke to set up or update the kit config from your CV ("set up my job-apply-kit config"), or to validate it.
---

# job-apply-core

Shared dependency of the job-apply-kit skills. Other skills read this skill's `OPERATIONS.md` for the universal rules and call its scripts through `{{CORE_DIR}}/scripts/`.

## Config setup and update

Config is one markdown file: `$JAK_CONFIG`, else `~/.config/job-apply-kit/config.md`. The template is `config.example.md` in the kit repository.

When the user asks to set up or update the config from their CV:

1. Ask for the CV (URL or file path). Read it fully.
2. Copy `config.example.md` to the config path if no config exists. Fill `name`, `name_file`, contact fields, links and `cv_source` from the CV. Do not invent values; leave unknowns empty and ask.
3. For `banned_claims` and `unproven_claims`: ask the user, one skill group at a time ("Have you really used X?"). Never decide for them.
4. Do not fill Google or sheet ids by hand. Tell the user to run `sheet_init` (it writes them), or ask them for existing ids.
5. When updating from a newer CV: show a diff of changed keys and ask before overwriting any non-empty value.
6. Validate:
   ```bash
   python3 {{CORE_DIR}}/scripts/jak_config.py --check
   python3 {{CORE_DIR}}/scripts/jak_config.py --show
   ```
   Fix every ERROR. Explain every WARN to the user.

Never print the user's phone number or emails back in full unless they ask; `--show` masks them.

## Rules

Every other skill points at `{{CORE_DIR}}/OPERATIONS.md` (universal rules: accounts, never-submit,
naming, truth gates, format, documents, batches, tracking, browser order). Read it before acting on
any job, and follow its anchors when a skill references them.

## Scripts (run with `python3 {{CORE_DIR}}/scripts/<file>`)

| Script | Use |
|---|---|
| `jak_config.py` | `--check`, `--show`, `--get KEY` |
| `jak_google.py` | the one Google interface: `draft` (never sends), `drive-upload`, `drive-mkdir`, `drive-share-anyone`, `sheet-get`, `sheet-append`, `sheet-create`, `backend`, `accounts`. Backend `gog` or `python`, chosen from config |
| `sheet_append.py` | append ONE tracker row (15 columns, RAW writes, header check) |
| `sheet_snapshot.py` | read-only tracker snapshot into `JDs/tracker/` |
| `sheet_init.py` | one-time: create Drive folder, templates subfolder and tracker sheet; writes ids to config |
| `gmail_draft.py` | draft with attachments (wrapper over `jak_google.py draft`) |
| `google_setup.py` | python-backend OAuth: `--account`, `--client-secret`, `--auth-url`, `--auth-code`, `--import-token`, `--check` |
| `browser_setup.py` | detect Chromium browsers (`--list`), generate default-profile debug launchers + desktop shortcuts (`--browser chrome,brave --create`; `--profile`/`--isolated` only for opt-in separate profiles), pre-launch running check + guarded start (`--check-running`, `--launch`) |
| `tool_paths.py` | record tool binary paths to tools.json (`--record`), add user-local bin dirs to the user PATH without admin (`--ensure-path`) |
| `google_api.py` | general Google tool for agents: gmail search/get/labels, calendar, drive, contacts, sheets, docs (no mail send) |
| `cdp.py`, `picker_upload.py` | raw CDP driver and Google Picker upload (last resort browser tools) |

References: `references/tracker-columns.md`, `references/shared-caches.md`,
`references/agent-browser.md`, `references/cdp-tools.md`.
