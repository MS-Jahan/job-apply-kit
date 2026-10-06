# 06 — Email drafting + Drive + tracker

Back to [index](index.md). Command reference: `docs/EXTERNAL_TOOLS.md` §§6–8. Column contract:
`skills/job-apply-core/references/tracker-columns.md`.

## Email: drafted, humanized, never sent

For each approved job the agent:

1. Picks the closest template from `templates_dir` ([Templates](07-templates.md)) — used as-is.
2. Writes the body itself (no canned body with pre-claimed skills; a row without a written body is
   marked blocked, not drafted generically).
3. Runs the **`humanizer`** skill over the body — the 29-pattern AI-writing pass is a hard dependency,
   not polish.
4. Creates a **Gmail draft with the PDF attached** via `skills/job-apply-core/scripts/gmail_draft.py`
   (a thin wrapper over `jak_google.py draft`). There is no send path anywhere in the kit: no
   `drafts send`, no `messages send`, enforced by `tests/test_never_submit.py`.

Subject lines default to `Application for <position> - <name>` unless the post dictates an exact
subject. You review each draft in Gmail and click send yourself.

## Drive: upload + anyone-with-link share

The renamed template PDF goes to the configured Drive folder
(`skills/job-apply-core/scripts/jak_google.py drive-upload`), then shared anyone-with-link
(`drive-share-anyone`). The public link is what lands in the tracker's Resume Drive column with the
`[template]` prefix (meaning: template used as-is, no manual CV review needed — only the email or
form needs your eyes). Sharing outside the configured folder is refused; on the `gog` backend the
public share passes the explicit `--force` flag the CLI requires for non-interactive use.

## Tracker: one guarded append

One row per processed job (applied, drafted, staged, skipped or blocked) via
`skills/job-apply-core/scripts/sheet_append.py`:

- Exactly **15 values (columns A–O)** or it refuses; it also aborts unless the live sheet header has
  15 columns, so a hand-edited sheet cannot silently shift columns.
- Writes with **RAW** value input: JD text with commas, pipes, newlines or a leading `=` lands
  literally instead of becoming a formula or splitting cells.
- Full JD text goes in column I; column O holds extra notes only (draft id, staged-tab reference).

One-time setup creates the folder + sheet with the right headers:
`skills/job-apply-core/scripts/sheet_init.py` (prints the ids your config needs).
