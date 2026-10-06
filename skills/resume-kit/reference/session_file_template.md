# Session File Template

Every JD gets a persistent session file: `output/<FolderName>/session_<name>.md`

## Template

```markdown
# Session: [Company] [Role Title]

## JD Info
- **File:** JDs/[file].txt
- **Role:** [title]
- **Company:** [company] ([context])
- **Bundle:** [role_type]
- **Format:** [Resume/CV] ([N]-page, [cls]) + [N]-page cover letter
- **Salary/Details:** [if available]

## JD Analysis
### Requirements
| # | Requirement | Match | Evidence |
|---|-------------|-------|----------|
| 1 | ... | Direct/Bridge/Gap | ... |

### ATS Keywords
- **ML/AI:** ...
- **Domain:** ...
- **Methods:** ...
- **Tools:** ...
- **Soft Skills:** ...

### Gap Assessment
- **Direct:** [list]
- **Bridge:** [list with confidence]
- **Gap:** [list -- what we can't claim]

## Company Context
- **Mission:** ...
- **This role:** Why it exists, what success looks like
- **Culture:** ...
- **"Why them" angle:** ...

## Framing Strategy
- **Lead narrative:** ...
- **Reframing map:** [domain term] → [JD term]
- **Emphasize:** ...
- **Downplay:** ...
- **CL hooks:** ...
- **User directives:** ...

## Critique Context (captured in Phase 0, used in /critique)
- **Reviewer persona:** Who reads this? Their title, daily work, what impresses/bores them
- **Competitive landscape:** Who else applies? What does the "obvious fit" have that we don't?
- **Domain vocabulary:** What terms separate insider from outsider at THIS company?

## Cover Letter Plan
- **Institution type:** Industry / National Lab / Academic
- **Paragraph count:** [N] paragraphs, [word count target]
- **P1 hook:** [specific product/paper/program to reference]
- **P2-P3 evidence:** [which achievements to highlight, how to frame]
- **Domain pivot:** [methodology bridge sentence, if pivoting]
- **Jargon level:** HR-safe / Technical / Academic
- **"Why them" hook:** [specific connection to their work]

## Bullet Plan

Note: Any FIXED positions (e.g., internships) are not included in this plan.

### Position 1 ([N] bullets, [N] rendered lines)
| # | ID | Achievement | Variant | Lines | Rationale |
|---|-----|------------|---------|-------|-----------|

### Position 2 ([N] bullets, [N] rendered lines)
[same table]

### Position 3 ([N] bullets, [N] rendered lines)
[same table]

**Budget:** [N] variable bullets, [N] rendered lines vs target [N]

## Output Files
- Resume/CV: `output/<FolderName>/e2e_<name>_[resume|cv].tex`
- Cover Letter: `output/<FolderName>/e2e_<name>_cover_letter.tex`
- Critique: `output/<FolderName>/critique_<name>.md`

## Critique Summary
- **Score:** [N]/100
- **Key findings:** ...
- **Tier 1 fixes:** ...

## Edit History
### Edit [N] ([date]): [description]
- Changes: ...
- Source: [critique item # / user request / auto-detected]
- Verification: [gates passed]

## Status
- Phase 0: [PENDING | DONE]
- Phase 1: [PENDING | DONE (N bullets confirmed)]
- Phase 2 Resume:
  - Summary: [PENDING | DONE]
  - Skills: [PENDING | DONE]
  - Position 1 ([N] bullets): [PENDING | DONE | IN_PROGRESS]
  - Position 2 ([N] bullets): [PENDING | DONE | IN_PROGRESS]
  - Position 3 ([N] bullets): [PENDING | DONE | IN_PROGRESS]
  - Compile: [PENDING | DONE]
- Cover Letter: [PENDING | IN_PROGRESS | DONE]
- Critique: [PENDING | IN_PROGRESS | CURRENT (score) | STALE]
- **Next:** [exact command to copy after /clear]
- **Next CL:** /make-cl output/<FolderName>/session_<name>.md
- **Next Critique:** /critique output/<FolderName>/session_<name>.md
```

## Context Efficiency Notes

- Session 1 (resume): resume_reference.md + critical_rules.md re-read + experience files + bundle + support files + template. Peak depends on knowledge base size.
- Session 2 (CL): cl_reference.md + significance files (if available) + session file + resume .tex + bundle S5. Much lighter context.
- Session 3 (critique): critique_framework.md + session file + both .tex + bundle. Moderate context.
- Folder created in Phase 0 — all files go to output/<FolderName>/ from the start.
