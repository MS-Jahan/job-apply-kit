---
name: edit-resume
description: Edit existing resume/CV or cover letter files (LaTeX or Markdown formats) based on critique feedback and user suggestions. Deep-tailoring track (Workflow B).
user-invocable: true
---

# /edit-resume

**User input:** `$ARGUMENTS`

Parse `$ARGUMENTS`: First argument is the file path (either `.tex` or `.md` resume/CL file). Second argument is optional critique markdown path. Inline instructions are in quotes.
- `/edit-resume output/Acme/e2e_acme_resume.tex`
- `/edit-resume output/Acme/e2e_acme_resume.md "shorten summary, add Docker to skills"`
- `/edit-resume output/Acme/e2e_acme_resume.tex output/Acme/critique_acme.md`

If no instructions are provided, ask the user what to fix.

---

Universal rules: `{{CORE_DIR}}/OPERATIONS.md` (#truth #format). Config keys read: `email_header`,
`## Truth gates`, `## Resume preferences`.

## Safety Rules (ALWAYS ENFORCED)

**Accuracy > Relevance > Impact > ATS > Brevity**

Read config.md `## Truth gates` (banned_claims, unproven_claims) before editing any content. Verify every claim against that table.

- Use the email from config.md `## Identity` in all outputs.
- Source ALL bullet content from `resume_builder/experience/` files or the newly discovered experiences. Never fabricate.
- Resume bullets: verify length constraints. For LaTeX, all variable bullets must be 2L (CV: 2L/3L mix OK, check config.md `## Resume preferences` (Document Preferences)). For Markdown, ensure concise, metric-driven achievements.
- Run `python3 {{RESUME_KIT_DIR}}/helpers/char_count.py` after LaTeX edits — the tool is authoritative.

### FIXED Sections — Refuse if Asked to Edit
Check config.md `## Resume preferences` for the FIXED sections list (template-locked across all outputs —
typically education, honors, default contact headers). Say no and explain why; VARIABLE sections only
(summary, technical skills, experience bullets/headers).

---

## User Input During Execution

If the user provides feedback, corrections or suggestions at any point:
1. Acknowledge it immediately.
2. If it affects an already-applied edit: go back, fix it, re-run the char-count gate.
3. If it changes the edit plan: update the session file, adjust the remaining edits.
4. If it is a question: answer it, then continue from the current step.
5. Never restart a phase — resume from the current position.

---

## Startup

Read `{{RESUME_KIT_DIR}}/reference/shared_ops.md` — Fresh Session Startup + Session File Derivation.
Read `<workspace>/SESSIONS.md` — check Active Sessions and KB corrections notes.
Read `config.md` — load Provenance Flags, email, FIXED Sections, document preferences, tailoring preferences.
Find and read the session file for the files being edited.

**Recovery check:**
- Read the session file; check for an existing Edit N Status.
- If Edit N Status shows IN_PROGRESS: read the file, identify which edits are done, resume.
- If no edit is in progress: proceed to Phase 1.

---

## Phase 1: Load Context

Read in this order:
1. **Session file** (`output/<FolderName>/session_<name>.md`) — note Framing Strategy, Company Context, and Edit History.
2. `{{RESUME_KIT_DIR}}/reference/resume_reference.md` (for LaTeX constraints) or target templates.
3. The source file (`.tex` or `.md`) being edited.
4. Critique file (if provided in `$ARGUMENTS`).
5. JD file.
6. Record baseline metrics (pages/length, word counts, char violations, orphans, variable bullets) in the
   session file under `## Edit [N] Baseline` (scan existing Edit History sections; next N = max existing + 1,
   or 1 if none):
   ```
   ## Edit [N] Baseline
   - Pages: [N]
   - Char violations: [list or "none"]
   - Orphan violations: [list or "none"]
   - White space last page: [N lines]
   - Variable bullets: [N]
   - Rendered lines: [N]
   ```

---

## Phase 2: Diagnose & Plan Edits

Gather change requests from:
1. **User instructions** from `$ARGUMENTS` (highest priority).
2. **Critique file** (Tier 1 fixes first, then Tier 2).
3. **Auto-detected issues** (char violations, orphans, formatting inconsistencies).

Cross-check against **session file framing strategy** to maintain package consistency.

**For each change, classify:**
- **MODIFY:** Change text of existing bullet/summary/skills.
- **SWAP:** Replace one bullet with another from the experience file.
- **ADD:** Insert new bullet.
- **REMOVE:** Drop a bullet.
- **VARIANT CHANGE:** e.g., 2L → 3L.
- **FIXED:** Blocked — explain template-lock to user.

If the edit targets the **cover letter** (not the resume/CV), note this — Phase 4 uses the CL-specific
gates; load the CL path from the session file Output Files section.

### >>>>>> MANDATORY STOP — DO NOT PROCEED <<<<<<
Present numbered edit plan. Each item shows: what, why, source, classification (MODIFY/ADD/SWAP/FIXED).
**You MUST wait for the user's explicit text response before continuing.**
Proceeding without confirmation may break package consistency or overwrite custom modifications.

---

## Phase 3: Load Reference Files (only confirmed edits)

Load ONLY what the confirmed edits need:
- All edits: `{{RESUME_KIT_DIR}}/support/ai_fingerprint_rules.md` (to verify no AI footprints).
- Bullet modifications: relevant experience files under `resume_builder/experience/` and reframing guides.
- Summary rewrite: Target role bundle (S2 summary guide).
- Cover letter edits: `resume_builder/support/significance_*.md` and `cl_reference.md`.

---

## Phase 4: Execute Edits

Apply edits one section at a time. After each edited section:

1. **Gate Verification:**
   - **For LaTeX:** Run `python3 {{RESUME_KIT_DIR}}/helpers/char_count.py` after editing each section. Fix any
     OVER violations or orphans before the next section. If a bullet expansion doesn't render as expected
     (1L when targeting 2L, or 3L), adjust immediately.
   - **For Markdown:** Verify formatting syntax, bullet counts, and readability.
2. Compile or check layout:
   - For LaTeX: run `tectonic -X compile` (fallback `pdflatex`) to verify compiling.
   - For Markdown/DOCX: check structure and word counts.
3. If a change affects the cover letter, apply the CL-specific gates (word targets, hooks, cohesive claims).

Update the session file Edit N Status after each individual edit (e.g. "Edit 1 (orphan fix): DONE", "Edit 2
(Summary rewrite): IN_PROGRESS").

### Resume/CV Verification Gates
| Gate | Check | If FAIL |
|------|-------|---------|
| Char count | No OVER violations | Fix bullet before proceeding |
| Page fill | Resume: <= 3 lines white space. CV: check rendered line target | Expand/trim variable bullets |
| Page count | Matches OPERATIONS #format (resume exactly 1 page, CV exactly 2) | Trim/expand variable content |
| Orphan | 2L bullet last line >= 70% | Pad or trim |
| Title width | Position title + date fits 1 line | Shorten title |
| Compile | Clean compile | Fix LaTeX errors |

### Cover Letter Verification Gates (if the CL was edited)
| Gate | Check | If FAIL |
|------|-------|---------|
| Word count | Industry 250-300, Lab/Academic 350-450 | Trim/expand |
| Page fill | 1pg: well-filled. 2pg: page 2 >= half filled before signature | Adjust |
| Paragraph count | Industry 3, Lab/Academic 4 | Restructure |
| Anti-patterns | No generic opener, no defensive framing, no credential dump | Rewrite |
| Package cohesion | CL claims traceable to resume bullets, no contradictions | Fix |

Progress: "Editing Position 1 bullet 6 — was 184 chars, now 197..." / "Compiling... 2 pages, page fill OK"

---

## Phase 5: Update Session File & Present

1. **Append Edit History** (use the N from the Phase 1 baseline):
   ```
   ### Edit [N] ([date]): [short description]
   - Changes: [what changed]
   - Source: critique item # / user request / auto-detected
   - Verification: gates passed
   ```
2. **Compare against baseline** (Delta table for page counts, word counts, char violations, and orphans):

   | Metric | Before | After | Delta |
   |--------|--------|-------|-------|
   | Page count | [N] | [N] | [+/-] |
   | Char violations | [N] | [N] | [+/-] |
   | Orphans | [N] | [N] | [+/-] |
   | White space | [N] | [N] | [+/-] |

   Flag any metric that worsened.
3. **Update Status** — mark critique as STALE if edits were made after the last critique. Update Next command.
4. **Present** changes summary + delta table + updated output.

### >>>>>> MANDATORY STOP <<<<<<
Show results. Wait for user approval or further edits.
**You MUST wait for the user's explicit text response before continuing.**

### When user approves / says "looks good" / finalizes:
Run file organization and finalization checks from `{{RESUME_KIT_DIR}}/reference/shared_ops.md`.
Confirm package complete.
