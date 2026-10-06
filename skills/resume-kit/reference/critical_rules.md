# Critical Rules — Compact Re-Read

> Quick reference for Phase 2 generation. Full rules in `resume_reference.md`.

## Character Limits

**Resume (10pt, textwidth=7.5in):**

| Target Lines | Rendered Char Range | HARD MAX | Orphan Threshold |
|-------|---------------|---------|------------------|
| 1 line | 105-111 chars | 117 | -- |
| 2 lines | 189-205 chars | 218 | Last line >= 78 chars |

**CV (11pt, textwidth=7.5in):**

| Target Lines | Rendered Char Range | HARD MAX | Orphan Threshold |
|-------|---------------|---------|------------------|
| 1 line | 88-93 chars | 101 | -- |
| 2 lines | 168-182 chars | 190 | Last line >= 65 chars |
| 3 lines | 250-268 chars | 280 | Last line >= 65 chars |

### Variant Naming

| Variant | Document | Lines | Target Range | HARD MAX | Orphan | Word Target |
|---------|----------|-------|-------------|----------|--------|-------------|
| Resume-1L | 1/2-page resume | 1 | 105-111 | 117 | -- | ~13 words |
| Resume-2L | 2-page resume | 2 | 189-205 | 218 | >= 78 | ~23-25 words |
| CV-2L | 5-page CV | 2 | 168-182 | 190 | >= 65 | ~21-22 words |
| CV-3L | 5-page CV | 3 | 250-268 | 280 | >= 65 | ~31-32 words |

## Bold Width Penalty

Resume (10pt): Effective limit = 119 - (0.5 x bold_char_count)
CV (11pt): Effective limit = 91 - (0.25 x bold_char_count)

## Orphan Rule

Multi-line bullet last rendered line must fill >= 70% of line width.
Resume 2L: last line >= 78 chars. CV 2L: >= 65 chars. CV 3L: >= 65 chars.

## FIXED Sections — NEVER Modify

All FIXED sections (internships, education, publications, honors/awards, header block) are set in the template.
NEVER change: \vspace values, \geometry settings, .cls formatting, header layout.
Only modify VARIABLE sections: Summary, Technical Skills, Experience bullets/headers.

## Provenance Flags

See your `config.md` (`## Truth gates`: `banned_claims`, `unproven_claims`) for your project-specific provenance flags. Common patterns:

| Item Status | Rule |
|-------------|------|
| Under review | State journal name: "under review at [Journal]" |
| Unpublished | No specific numbers or publication claims |
| Internal/proprietary | "infrastructure I developed" — not peer-reviewed |
| Preprint only | Always flag provenance |

## LaTeX Notation Quick-Ref

| Item | Correct LaTeX | Wrong | Rendered |
|------|--------------|-------|----------|
| Chemical formulas | `\ce{H2O}` | `H2O`, `H$_2$O` | H₂O |
| Superscript labels | `X$^2$Y` | `X2Y` | X²Y |
| R² values | `R$^2$=0.99` | `R^2`, `R2` | R² |
| Greek letters | `$\alpha$-phase` | `alpha-phase` | α-phase |
| Approximately | `$\sim$64` | `~64` (LaTeX non-breaking space!) | ~64 |

CRITICAL: ~ in LaTeX = non-breaking space. Use $\sim$ for "approximately."

## KB Corrections

See your `config.md` (`## Resume preferences`) for your project-specific corrections log. Always check before generation to avoid re-introducing known errors.

## Budget Reminder

Resume: ~20 variable bullets (exact count depends on skills config + immigration line). CV: 19-21 bullets, 45 rendered lines.
Resume bullets: ALL 2L. CV bullets: 2L/3L mix OK.
**CV Page 1 rule:** First bullet of first experience MUST be 2L. A 3L first bullet overflows page 1.
