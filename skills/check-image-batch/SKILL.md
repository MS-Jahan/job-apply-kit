---
name: check-image-batch
description: Process a batch of job-post screenshot images (paths in $ARGUMENTS or the newest JDs/pasted-batch-<date>/ folder), cross-check the tracker and local caches, and process NEW jobs end to end (template resume, email draft or staged form, tracker row; never submit). Invoke with /check-image-batch <image paths or batch folder>.
user-invocable: true
---

# Image batch job scanner

Universal rules: `{{CORE_DIR}}/OPERATIONS.md`. Per-job procedure: `{{CORE_DIR}}/references/new-job-procedure.md`.
Config keys read: `cv_source`, `templates_dir`, `sheet_id`, `drive_folder_id`, `cdp_port`, `workspace`.

## Inputs
- `$ARGUMENTS`: image paths and/or a batch folder (for example `JDs/pasted-batch-2026-01-15/`).
- Only a folder: process its `img_NN.png` files in paste order. Nothing given: use the newest `JDs/pasted-batch-*/` folder.

## Skill-specific rules
1. Application links open in NEW tabs (inventory existing tabs first). Close only tabs this run opened. Sub-agents close only pages they opened.
2. Login wall on an application link: hard stop, leave the tab open, record it.
3. **Search only when needed** (OPERATIONS #batch): if the screenshot clearly shows company, requirements and a contact or apply link, do not search. Otherwise SearXNG first, then read pages with agent-browser. No hand-written scrapers against search engines.

## Cache
Root `JDs/image-batch/`.
- `seen_posts.json`: array of `{ "image_path", "company", "position", "deadline", "apply_method": "email|link|form", "contact", "verdict": "new|applied|drafted|skipped-duplicate|expired|not-a-job", "sheet_row", "output_dir", "first_seen", "processed_at" }`.
- `applied_cache.json`: `{ "company+position": { sheet_row, date, how } }`.
- Per batch: `STATUS.md` next to the images records done, not-done and needs-search verdicts; update it as you go.

## Step 1: read the images
Read each image (the Read tool returns image attachments) and extract: company, position, deadline, required skills, apply method, contact email, whether a cover letter is required (PDF attachment or body text), and the document type (resume 1 page vs CV 2 pages per the post's wording; default resume).

## Step 2: dedup verdicts (before any work)
- Same image or same company + position already in `seen_posts.json`, `applied_cache.json`, the tracker snapshot, or a previous batch's `STATUS.md`: mark `skipped-duplicate`. One application per unique job.
- Write every verdict back to `seen_posts.json` and `STATUS.md`.

## Step 3: process NEW jobs
If the apply link or contact was not in the image, resolve it by rule 3. Then follow `{{CORE_DIR}}/references/new-job-procedure.md`. The `comments` value for the sheet row is the image path.
