# Processing a NEW job end to end (shared by the scan skills)

Used by `check-li-saved`, `check-fb-saved`, `check-ph-discord` and `check-image-batch`. The scan skill finds
and filters items; this is what happens to each NEW job. Universal rules apply throughout:
`OPERATIONS.md` (#accounts #truth #documents #tracking #browser).

## 0. Cache and dedup (before anything is opened)

Each scan skill keeps `JDs/<source>/seen_*.json` (per item) and `JDs/<source>/applied_cache.json`
(`{ "company+position": { sheet_row, date, how } }`). Shapes are in `shared-caches.md`.
- If a cache file is missing, rebuild it from the latest `JDs/tracker/sheet_snapshot_<date>.md` plus every
  `STATUS.md` under `JDs/` (run `sheet_snapshot.py` first).
- Cross-check every candidate against: the local caches, the tracker snapshot, and `JDs/pasted-batch-*/STATUS.md`.
  One application per unique company + position, ever. Already applied: do not open it, do not apply.
- Write every verdict (`new`, `applied`, `drafted`, `skipped-duplicate`, `expired`, `not-a-job`) back to the
  skill's `seen_*.json` BEFORE doing any work on the item.

## 1. Order of work

Email-only posts first (fastest), then direct application links, then forms (Google Forms, Easy Apply),
then login-walled items (record and stop; leave the tab open).

## 2. Per job

1. **Parse the facts:** company, position, deadline, required skills, apply method (`email`, `link`, `form`,
   `easy-apply`), contact email, whether a cover letter is required and in what form (PDF attachment or body text).
   An expired deadline: record `expired`, skip.
2. **Choose the document type:** resume (1 page) by default; CV (2 pages) only if the post says CV or asks for a
   multi-page profile (OPERATIONS #format).
3. **Template (default, as-is):** `python3 {{CORE_DIR}}/scripts/template_index.py match "<post text>" [--kind cv|resume|cover_letter]`
   returns the best-fitting template from the user's `templates_dir/INDEX.md`. Copy the PDF under the per-company
   name (OPERATIONS #naming); no edits, no recompile; check `pdfinfo <file> | grep Pages`. Customize only under the
   exception in OPERATIONS #documents (then read the post and the live sources first, use the resume skills, run the
   humanizer before compiling). If no template exists, offer `/create-template`.
4. **Upload:** `python3 {{CORE_DIR}}/scripts/jak_google.py drive-upload <pdf> --name <name>.pdf` (configured Drive
   folder, shared anyone-can-view). Keep the returned link.
5. **Stage, according to the apply method:**
   - **Email:** write the email body (mandatory), run the humanizer on it, state exactly which documents are
     attached, then `python3 {{CORE_DIR}}/scripts/gmail_draft.py --to <contact> --subject <subject> --body-file <file> --attach <pdf> [--attach <cover letter pdf>]`.
     Subject per OPERATIONS #naming unless the post dictates one. Draft only.
   - **Link or portal:** open it in a NEW tab, fill and upload, STOP at Submit/Apply, screenshot.
   - **Google Form:** OPERATIONS #documents (account banner, ARIA listboxes, Picker upload via
     `picker_upload.py`), STOP at Submit, screenshot.
   - **Easy Apply (LinkedIn):** fill, upload, STOP at the review step, screenshot. Never complete it.
   - Evidence screenshot goes to `output/<company-slug>/`.
6. **Track:** append ONE row with `python3 {{CORE_DIR}}/scripts/sheet_append.py append '<json-row>'`
   (keys and column contract in `tracker-columns.md`; never hand-roll an append). Resume Drive column:
   `[template] <link>` for template documents, links comma-separated if CV + resume + cover letter. Put the full job
   text in `job_desc` (column I) and the source id in `comments` (column O: post url, message id, image path, draft id).
7. **Update both caches** (`seen_*.json` verdict plus `sheet_row`, `output_dir`, `processed_at`; `applied_cache.json`).

## 3. Report (every run)

A compact table: item | company | position | verdict | action taken (sheet row, draft id, staged tab,
blocked-login, not-a-job) | deadline. List every tab left open and every item that needs the user's manual
click (drafts to send, forms to submit).

## 4. Maintenance

A sheet row added outside the skill: reconcile `applied_cache.json` on the next run (the tracker wins).
