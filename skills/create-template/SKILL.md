---
name: create-template
description: Generate the user's own CV, resume and cover-letter templates per role category from their live CV, store them in templates_dir, and register them in INDEX.md so the apply skills pick them up automatically. Invoke with /create-template [category ...].
user-invocable: true
---

# /create-template

Universal rules: `{{CORE_DIR}}/OPERATIONS.md` (#sources #truth #format #documents). Config keys read:
`cv_source`, `projects_source`, `templates_dir`, `banned_claims`, `unproven_claims`, identity keys.
Depends on `job-apply-core` and `humanizer` only — NOT on `resume-kit` (that is the separate,
`resume.cls`-based deep-tailoring track; this skill uses its own article-class skeleton in `assets/`
and the two systems are never mixed in one document, OPERATIONS #format).

## Purpose

Templates in `templates_dir` are what every apply skill (`bdjobs-full-run`, `linkedin-full-run`,
`check-linkedin-saved`, `check-facebook-saved`, `check-discord-jobs`, `check-image-batch`) picks from by default
(OPERATIONS #documents: template-first, no customization unless asked). This skill is how a user builds
that set in the first place, and how they refresh it as their CV changes. It is not run per job post —
run it once per role category, and again when the live CV gains enough new material to warrant it.

## Inputs

- `$ARGUMENTS`: optional category names. Empty: propose categories (see Step 2).

## Workflow

### Step 1: load facts
Fetch `cv_source` (and `projects_source` if set). Stop and tell the user if unreachable
(OPERATIONS #sources). Snapshot to `.cache/profile/<date>/` so later steps share one fact base.

### Step 2: propose categories
Cluster the live CV's stack into 4-10 role categories (for example: a primary language plus its
common frameworks, a frontend stack, a mobile stack, a generalist full-stack category). Add any
category the user names explicitly. Confirm the list with the user before generating anything.

For each category, record:
- **keywords**: terms a job post in this category would use (for the template matcher).
- **primary stack**: skills/projects to bold and lead with.
- **secondary stack**: skills to keep, unbolded, after the primary group (never erase cross-domain
  breadth — OPERATIONS #format density rule and `{{CORE_DIR}}/references/new-job-procedure.md`).
- **lead projects**: the 2-3 projects most relevant to this category.

### Step 3: generate the three documents per category
Base skeletons: `{{SKILL_DIR}}/assets/CV_SKELETON.tex`, `RESUME_SKELETON.tex`, `CL_SKELETON.tex`. Copy
each to `<templates_dir>/CV_<CAT>.tex`, `RESUME_<CAT>.tex`, `CL_<CAT>.tex` and fill every `[[TOKEN]]`:

- **CV** (2 pages): full mirror of the live CV — every section, every project, every certification.
  Category tailoring is reorder-and-bold ONLY (lead with the category's projects and skills); never cut
  real content to fit page budget (tune spacing instead).
- **Resume** (1 page): condensed, high-density, JD-relevant content first (OPERATIONS #format).
- **Cover letter**: 3-paragraph industry structure with bracketed placeholders for company-specific
  details (`[[COMPANY_NAME]]`, `[[TARGET_ROLE]]`, etc.) to be filled per job, not per category.

Also produce a `.md` copy of the cover letter (`CL_<CAT>.md`) for the Markdown/DOCX path.

### Step 4: gates (every generated file)
1. **Truth gates** (OPERATIONS #truth): every claim traces to `cv_source`; nothing from
   `banned_claims` appears; nothing from `unproven_claims` is claimed (it may appear as willingness-
   to-learn language in the cover letter only).
2. **Format** (OPERATIONS #format): zero em-dashes, pure black text, margins as shipped in the
   skeleton.
3. **Humanizer**: run on the summary, bullets and cover-letter prose before compiling.
4. **AI-fingerprint scan**: no banned buzzwords, no generic AI phrasing.
5. **Compile**: `tectonic -X compile` (fallback `pdflatex`) each `.tex` file.
6. **Page count**: `pdfinfo <file>.pdf | grep Pages` — CV exactly 2, resume exactly 1, cover letter 1.
   If it fails, adjust spacing/density first; never invent content to fill a page, never cut real
   content to shrink it.
7. **Last-page fill**: the CV's page 2 and the resume should end with minimal blank space (OPERATIONS
   #format density rule). Measure, don't eyeball: `pdftotext -bbox <file>.pdf -` gives every
   `<word ... yMax="...">`; bottom whitespace = page height minus max yMax (minus the bottom
   margin). Targets: resume and CV page 2 content whitespace at most ~70pt; cover letter at most
   ~130pt (letters conventionally run 70-80% of a page — fill with substance, never pad).
   Fill order is content first, spacing second: expand the summary (max 3 sentences), broaden
   project blurbs to 2-3 lines each from source facts, add one or two secondary (even
   less-relevant) projects when the relevant pool is exhausted, add extra certification lines,
   and keep the CV's Extracurriculars section (it is part of the live source mirror). Only then
   tune `\linespread` (stay at or under ~1.26), `itemsep`, `titlespacing`. Never invent content
   to fill a page, never cut real content to shrink one. Naming: a 1-page document is a resume;
   only a multi-page document is called a CV.

### Step 4b: cover-letter density
Letters use the sender letterhead block (name, location, contact, links), a `[[WHY_COMPANY]]`
per-job slot appended to paragraph 1, three proof paragraphs with metrics, a concrete close, and
an `Enclosed with this letter: my resume.` line; `.md` mirrors `.tex` exactly (placeholders stay
raw in `.md`, `\_`-escaped in `.tex` so they compile — see Production notes). Top/bottom margins
0.75in, sides 1in.

## Production notes (learned 2026-10-07, keep updated)

- **Never use `\color` (or any xcolor command) in the CL skeleton** — it ships without xcolor and
  compilation fails with `Undefined control sequence`. The same holds for any package not in the
  skeleton preamble: check before using.
- **CL placeholders must be `\_`-escaped in `.tex`** (`[[COMPANY\_NAME]]` renders identically in
  the PDF; raw `_` is fatal in LaTeX text mode). Keep raw `[[COMPANY_NAME]]` in the `.md` copy.
  Per-application fill must match the escaped form in `.tex`.
- **Token sweep after generation**: `grep -c "\[\[" templates/*.tex` — CV/resume files must show 0;
  CL files show only the intended per-job placeholders.
- **tectonic parallel runs collide** writing the format file (`format-file write` failure). Compile
  serially (one file per command, or retry on failure) — the failure is transient and unrelated to
  sources. Never run two `tectonic -X compile` processes at once.
- **Keep the compiled PDFs.** `INDEX.md` references `.pdf` files and the apply skills attach them;
  do not delete PDFs after verification.
- **Windows shell discipline**: run all kit and compile commands in Git Bash, never PowerShell
  (PowerShell mangles quoting, pipes like `tail`, and stderr). Set `PYTHONUTF8=1` (or
  `PYTHONIOENCODING=utf-8`) before any Python script whose output may contain non-ASCII
  (`--help` texts and error paths contain unicode arrows).
- **Google Docs sources**: the `/edit` canvas snapshots near-empty — always rewrite
  `.../document/d/<id>/...` to `.../document/d/<id>/mobilebasic` and read `innerText` there.
  `.../export?format=txt` triggers a download instead of navigation; prefer the mobilebasic view.
- **Truth in paraphrase**: stay close to source verbs and mechanics. Do not add unstated release
  mechanics (e.g. "staged rollouts", "store assets") to a Play-release claim, and do not add
  forward-looking promises (e.g. documenting for the next developer) that the source never states.
  Metrics stay exact; cross-stack claims stay inside the source's skill lists.

### Step 5: register in the index
Create or update `<templates_dir>/INDEX.md`, one block per category (format below). Never silently
overwrite an existing category's entry or files: if `CV_<CAT>.tex` already exists, write
`CV_<CAT>_new.tex` alongside it and ask the user before replacing.

```
## <CATEGORY>
- **keywords:** comma list used to match a job post
- **cv:** CV_<CAT>.tex / .pdf
- **resume:** RESUME_<CAT>.tex / .pdf
- **cover_letter:** CL_<CAT>.tex / .md / .pdf
- **page_budget:** cv 2, resume 1, cl 1
- **avoid_for:** short note on roles this category is a poor fit for
- **generated:** <date> from <cv_source>
```

The apply skills read this file through `{{CORE_DIR}}/scripts/template_index.py` — no category name or
file name is hard-coded anywhere else in the kit.

### Step 6: report
Show the user a table: category | files generated | gate results | any warnings. If `templates_dir`
was empty before this run, mention that the apply skills can now use it immediately.

## Boundaries

This skill never applies anywhere, never sends or drafts anything, and never touches Drive (archiving
templates to Drive is a separate, optional step under OPERATIONS #tracking).
