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

Templates in `templates_dir` are what every apply skill (`bdjobs-full-run`, `li-full-run`,
`check-li-saved`, `check-fb-saved`, `check-discord-jobs`, `check-image-batch`) picks from by default
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
   #format density rule).

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
