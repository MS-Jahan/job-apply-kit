---
name: critique
description: Critique existing resume/CV and cover letter output files (LaTeX or Markdown formats) against a JD. Deep-tailoring track (Workflow B), paired with make-resume/make-cl/edit-resume.
user-invocable: true
---

# /critique

**User input:** `$ARGUMENTS`

Parse `$ARGUMENTS`:
- Session file path (e.g., `output/Acme/session_acme_engineer.md`) → read session file, derive paths from Output Files
- File path(s) + JD source (existing format) → backward compatible
- Session name (e.g., `acme_engineer`) → find session file via derivation

---

Universal rules: `{{CORE_DIR}}/OPERATIONS.md` (#truth #format). Config keys read: `email_header`,
`## Truth gates`, `## Resume preferences`.

## Safety Rules

**Accuracy > Relevance > Impact > ATS > Brevity**

Read config.md `## Truth gates` (banned_claims, unproven_claims). Verify every claim against that table.
Check `<workspace>/SESSIONS.md` for corrections notes — do not flag corrected items as errors.
Use the email from config.md `## Identity` — flag if a different email appears in output.
FIXED sections (from `config.md` FIXED Sections) are template-locked — do not flag for editing. Flag only VARIABLE sections.

---

## Startup

Read `{{RESUME_KIT_DIR}}/reference/shared_ops.md` — Fresh Session Startup + Session File Derivation.
Read `<workspace>/SESSIONS.md` — check Active Sessions and KB corrections notes.
Read `config.md` — load Provenance Flags, FIXED Sections, email.
Find and read the session file for the files being critiqued.

**Recovery check:**
- If the CL is not DONE in the session file: "CL not yet generated. Run `/make-cl` first."
- If Critique is CURRENT: "Already critiqued (score X/100). Re-run? Waiting for confirmation."
- If Critique is STALE: "Edits made since last critique. Re-critiquing."
- If Critique is PENDING: proceed.

---

## User Input During Execution

If the user provides feedback, corrections or suggestions at any point:
1. Acknowledge it immediately.
2. If it changes scoring criteria or focus: adjust the critique accordingly.
3. Never restart — resume from the current position.

---

## Protocol

1. **Read session file** — specifically note:
   - **Company Context** → reviewer persona, "why this company".
   - **Framing Strategy** → intentional reframing decisions (flag only execution inconsistencies, not the strategy itself).
   - **Cover Letter Plan** → CL structure rationale.
   - **Critique Context** → reviewer persona, competitive landscape, domain vocabulary.
   - If the session file lacks Company Context or Critique Context: do 1-2 web searches to fill the gaps.
2. Read `{{RESUME_KIT_DIR}}/reference/critique_framework.md`.
3. Read `{{RESUME_KIT_DIR}}/support/ai_fingerprint_rules.md` — check for AI footprints, buzzwords, and banned phrases.
4. Read the resume/CV file(s) (either `.tex` or `.md`) and cover letter (if available).
5. Read the JD.
6. Read the target bundle from `resume_builder/bundles/`.
7. **Perform character/word count checks:**
   - For LaTeX: run `python3 {{RESUME_KIT_DIR}}/helpers/char_count.py -f [resume|cv] [file.tex]`.
   - For Markdown: check bullet counts, word counts, and line lengths.
8. **Compile/Format Verification:**
   - For LaTeX: compile with `tectonic -X compile` (fallback `pdflatex`) to check margins, orphans, and page budget.
   - For Markdown/DOCX: check layout, indentation, bolding, and structural cleanliness.
9. **Paper Hook Verification:** if the CL cites named papers, PIs, programs or publications, web-search to verify title, journal, year and PI affiliation. Flag factual errors as Tier 1 fixes.
10. **Perform the 8-part critique:**
    1. **Domain-Specialist Lens** (Reviewer persona, company context, JD/domain vocab, gap ranking, method transfer, competitive landscape).
    2. **Five-Perspective Read-Through** (ATS bot, 10s recruiter, 30s HR, 2min hiring manager, 10min technical reviewer).
    3. **Eight-Dimension Scoring** (ATS 15%, Summary 10%, Skills 10%, Bullets 25%, Publications 10%, Narrative 15%, Visual 5%, Credibility 10%) - target 100 points.
    4. **Interview Likelihood** (Probability + ceiling analysis).
    5. **Tiered Improvements** (Tier 1 fatal/serious, Tier 2 important, Tier 3 cosmetic).
    6. **Interview Bridge Points** (5-7 resume-to-interview talking points).
    7. **Cover Letter Critique** — 6 sub-checks: anti-patterns, tailoring, context-specific, ATS keywords,
       structural, package cohesion. **If no CL was provided:** skip the tailoring/context/structural checks;
       run package cohesion as a resume-standalone assessment (does the resume alone earn an interview) and
       note "Cover letter not provided — package cohesion not assessed."
    8. **Post-Generation Verification** (mechanical + content + structural checklists).

11. Save critique to `output/<FolderName>/critique_<name>.md`.
12. **Update session file** — add score, findings, tier 1 fixes to Critique Summary. Set status to `Critique: CURRENT`.
13. **Update memory pointer** in `<workspace>/SESSIONS.md` with the new score.

Progress: "Analyzing package... Scoring 8 dimensions... Score: 87.0/100"

### >>>>>> MANDATORY STOP <<<<<<
Present: score table + tier 1 actionable fixes + interview likelihood.
**You MUST wait for the user's explicit text response before continuing.**
If edits are needed, suggest running `/edit-resume`.

### When user approves / says "looks good" / finalizes:
Verify all expected files exist in `output/<FolderName>/`:
- Session file, resume/CV (tex/md), cover letter (tex/md), critique markdown.
- Compile artifacts if using LaTeX.
Run Finalization steps from `shared_ops.md` (renaming PDFs for submission to `FirstName_LastName_Resume.pdf`, etc.).
Confirm to user: "Package complete in output/<FolderName>/ — [list files]"
