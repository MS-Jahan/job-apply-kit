---
name: setup-build-kb
description: Synthesize extractions and existing resumes into experience files, bundles, and support files for resume tailoring. Builds the knowledge base the deep-tailoring track (make-resume/make-cover-letter/critique/edit-resume) reads from.
user-invocable: true
---

# /setup-build-kb

**User input:** `$ARGUMENTS`

Parse `$ARGUMENTS`:
- Empty → full build (all phases)
- Phase number (e.g., `3`) → resume from that phase
- "experience" / "bundles" / "skills" / "pubs" / "reframing" / "significance" → run only that component
- "status" → show what's built and what's missing

---

Universal rules: `{{CORE_DIR}}/OPERATIONS.md` (#sources). Config keys read: `cv_source`, `## Identity`,
`## Resume preferences` (library path, role types, bullet variant defaults). Output lives under
`<workspace>/resume_builder/` and `<workspace>/knowledge_base/` — gitignored, rebuilt from `cv_source`
plus any local extractions/resumes, never shipped.

## Startup

1. Read `<workspace>/SESSIONS.md` — check for KB correction notes from prior sessions
2. Read `config.md` — load:
   - Personal Info (positions, institutions, dates)
   - Tailoring Preferences (library path, e.g. `resumes/`)
   - Role Types table (defines which bundles to create)
   - Provenance Flags (propagate to all KB files)
   - Document Preferences (bullet variant defaults)
3. Check inputs:
   - Scan `knowledge_base/extractions/*.md` and `resumes/*.md`
   - Read `knowledge_base/extractions/_INVENTORY.md` (if exists)
4. Scan `resume_builder/` to see what's already built

**Pre-flight check:**
- If both `resumes/` and `knowledge_base/extractions/` are empty: "No resumes or extractions found. Put existing markdown resumes in `resumes/` or run `/setup-extract` on your papers." Stop.

Progress: "Found [N] extractions and [M] resume files. Building unified knowledge base..."

---

## Phase 0: Library Ingestion (resumes/*.md)

**Goal:** Extract experience, roles, bullets, and skills from existing markdown resumes.

**Process:**
1. Scan the resume library directory (configured in config.md `## Resume preferences` (Tailoring Preferences), defaults to `resumes/`).
2. Read and parse each markdown resume:
   - Extract positions, titles, companies, locations, and dates.
   - For each position, extract the bullets and skills.
   - Classify bullet lengths (using `char_count.py` or length thresholds) into 1L, 2L, or 3L.
   - Group identical/similar bullets across resumes to avoid duplicates.
3. Keep track of which resume files each bullet came from.

---

## Phase 1: Build Experience Files

**Goal:** Create one experience file per position, merging paper extractions and markdown resume bullets.

**Read:** All extractions + parsed resume data from Phase 0.

**For each position** (from config.md `## Identity`, or found in extractions/resumes):
1. Create/update `resume_builder/experience/experience_<position_key>.md` where `<position_key>` is derived from company/institution name (lowercase, underscores).
2. Group all paper extractions and parsed resume bullets belonging to this position.
3. Format the experience file as follows:

```markdown
# Experience: [Position Title] — [Institution]
## [Date Range]

### Cross-Position Section
[Brief narrative connecting this position's work to the user's broader trajectory]
[CL framing content — how this position fits the career arc]

---

### Achievement [ID]: [Short Title]
**Source:** [extraction_filename.md or resume_filename.md]
**User's role:** [e.g., first author / sole contributor / developer]
**Status:** [published / under review / internal / N/A]

**Context:** [1-2 sentences explaining what challenge this addressed and why it matters]

**Bullet variants:**
- **2L:** [Full 2-line bullet text — STAR format, ~180-210 rendered characters]
- **3L:** [Full 3-line bullet text — for CV use, ~270-310 rendered characters]
- **1L:** [Condensed 1-line version — ~90-110 rendered characters, for tight budgets]

**Key skills:** [comma-separated list of skills this achievement demonstrates]
**ATS keywords:** [domain-specific terms an ATS might scan for]
**Reframing notes:** [how to emphasize different aspects for different role types]

---
[Repeat for all achievements/bullets from papers and resumes]
```

*Note on bullet variants:* If importing a resume bullet that only has one length, automatically generate the other variants (1L, 2L, 3L) using Claude's reframing capabilities, keeping them strictly truthful to the original.

### >>>>>> MANDATORY STOP — DO NOT PROCEED <<<<<<
Present the experience file(s) — show achievement count per position, total bullet variants, and sources.
Ask user to review: "Are the groupings correct? Any achievements missing or misattributed?"
**You MUST wait for the user's explicit text response before continuing.**

---

## Phase 2: Build Skills Taxonomy

**Goal:** Create a categorized inventory of all technical skills from extractions and resumes.

**Read:** Experience files built in Phase 1.

**Build/Update** `resume_builder/support/skills_taxonomy.md` using the standard format:
- Count unique skills.
- Categorize skills (e.g. Computational Methods, Machine Learning, Programming & Software, Product Management).
- Assign weight (HIGH/MED/LOW) and proficiency evidence based on publications and resume mentions.

Progress: "Built taxonomy — [N] skills across [M] categories"

---

## Phase 3: Build Publication Metadata

**Goal:** Structured publication data for resume/CV generation.

**Read:** Extractions + `config.md` Provenance Flags.

**Build** `resume_builder/support/pub_metadata.md`:
- List all publications with details (authors, year, journal, status, key topic).
- Group by: First-Author / Co-First, Contributing Author, Under Review / In Prep.

Progress: "Pub metadata — [N] first-author, [M] contributing, [K] under review"

---

## Phase 4: Build Achievement Reframing Guide

**Goal:** Per-achievement significance lines + framing directives for each role type.

**Read:** Experience files + config.md `## Resume preferences` (Role Types).

**Build** `resume_builder/support/achievement_reframing_guide.md` using the standard format:
- Define significance broad sentence for each achievement.
- Map emphasis (HIGH/MED/LOW), lead verb, and framing angle for each target role type in `config.md`.

### >>>>>> MANDATORY STOP — DO NOT PROCEED <<<<<<
Present the reframing guide summary — show which achievements are HIGH for which role types.
Ask user: "Does this priority mapping look right for your target roles?"
**You MUST wait for the user's explicit text response before continuing.**

---

## Phase 5: Build Bundles

**Goal:** One bundle per role type from `config.md`, with 5 sections each.

**Read:** Experience files + Skills Taxonomy + Reframing Guide + config.md `## Resume preferences` (Role Types).

**For each role type**, create `resume_builder/bundles/bundle_<role_type>.md`:
- **S1: Role Profile & Priority Matrix** (HIGH/MEDIUM/LOW priority achievement IDs).
- **S2: Summary Guide** (Headlines, building blocks, terminology).
- **S3: Achievement Reframing Map** (Framing angle and key metric per ID).
- **S4: Skills Guide** (Bold tools, must-include, nice-to-have, omit).
- **S5: Cover Letter Guide** (Opening hook, narrative thread, why them).

Progress: "Building bundle for [role type] — [N] HIGH priority achievements, [M] bold tools"

---

## Phase 6: Build Significance Research Files

**Goal:** Field context for cover letters — NOT for resume bullets.

**For each position**, create `resume_builder/support/significance_<position_key>.md` with broad challenge description, competing approaches, and why it matters.

---

## Final: Status Report

After all phases complete (or after the requested subset), present:

### KB Build Status
| Component | File | Status | Items |
|-----------|------|--------|-------|
| Experience files | `experience/*.md` | [DONE/MISSING] | [N achievements] |
| Skills taxonomy | `support/skills_taxonomy.md` | [DONE/MISSING] | [N skills] |
| Pub metadata | `support/pub_metadata.md` | [DONE/MISSING] | [N pubs] |
| Reframing guide | `support/achievement_reframing_guide.md` | [DONE/MISSING] | [N entries] |
| Bundles | `bundles/bundle_*.md` | [DONE/MISSING] | [N bundles] |
| Significance | `support/significance_*.md` | [DONE/MISSING] | [N files] |

### Ready for Tailoring?
- [ ] At least 1 experience file with 5+ achievements
- [ ] Skills taxonomy with 20+ skills
- [ ] At least 1 bundle matching a target role type

If all checked: "Knowledge base is ready. Save a JD to `JDs/` and run `/make-resume JDs/<filename>.txt`"

### >>>>>> MANDATORY STOP <<<<<<
Present status report. Wait for user confirmation.
**You MUST wait for the user's explicit text response before continuing.**
