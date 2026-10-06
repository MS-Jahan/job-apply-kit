# 05 — PDF generation (tectonic, fallback, page budgets)

Back to [index](index.md). Command reference: `docs/EXTERNAL_TOOLS.md` §§3.1, 3.4 (pandoc row).

## The toolchain

- **`tectonic` (primary).** One static binary, no TeX Live install. It fetches LaTeX packages on first
  use and caches them, so the first compile needs network and later ones do not. Official Windows
  builds (`-windows-msvc` / `-windows-gnu` zips) ship with every release, next to the Linux and
  macOS builds — download, unzip, put `tectonic.exe` on PATH.
- **`pdflatex` (fallback).** From a TeX Live install. Used only when `tectonic` is unavailable.
- **`pandoc` (optional).** Only for the Markdown-to-DOCX/PDF path in the deep-tailoring track.
  Official Windows installer on pandoc.org.
- **`pdfinfo` (page-budget checks).** From Poppler. Linux: `poppler-utils`. Windows: no native
  package — install via conda-forge (`conda install poppler`) or Chocolatey (`choco install
  poppler`), both of which ship `pdfinfo.exe`. If it is genuinely unavailable, `doctor.sh` flags it
  and the agent falls back to reading the PDF's page count directly; compiling itself does not need it.

## The two document systems (never mixed)

- **Workflow A — article-class templates** (`templates_dir`, built by `/create-template`): checked
  by compile + `pdfinfo` page count only.
- **Workflow B — `resume.cls` / `cv.cls`** (`skills/resume-kit/templates/`): bullets additionally pass
  through `skills/resume-kit/helpers/char_count.py`, the authoritative 1L/2L/3L length gate. Run it
  after writing each position; it tells you the rendered character count and the target band.

## Page budgets (OPERATIONS.md#format)

Resume exactly 1 page, CV exactly 2, cover letter 1. Verify after every edit:

```bash
tectonic -X compile RESUME_EXAMPLE.tex
pdfinfo RESUME_EXAMPLE.pdf | grep Pages
```

If the count is off, tune spacing/density first — never invent content to fill a page, never cut real
content to shrink it. Documents ship with zero em-dashes and pure black text.

## Two LaTeX gotchas the kit already guards

A line break (`\\`) directly before `[` is parsed as an optional length argument and fails with
`Missing number, treated as zero` — the fix is `\\{}`. A `[[TOKEN]]` immediately after `\\` has the
same problem — write `\\{}` before it. Both are covered by automated tests, but you will hit them if
you hand-edit templates.
