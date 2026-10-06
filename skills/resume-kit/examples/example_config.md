# Configuration

> Edit this file with your personal details. Every skill reads this file.

---

## Personal Info

- **Name:** Jordan Chen
- **Degree suffix:** Ph.D.
- **Email:** jordan.chen@email.com
- **Phone:** +1 5551234567
- **Location:** Richland, WA 99354
- **LinkedIn:** linkedin.com/in/jordanchen
- **Google Scholar:** scholar.google.com/citations?user=XXXXXXXXX
- **ORCID:** orcid.org/0000-0002-XXXX-XXXX
- **Website:**

---

## Document Preferences

- **Resume pages:** 2
- **CV pages:** 5
- **Resume bullet variant:** 2L (all variable bullets are 2-line)
- **CV bullet variant:** 2L/3L mix
- **Skills config (resume):** 4-3-2-2-2 (13 lines, 5 groups)
- **Skills config (CV):** 4-4-3-3-3 (17 lines, 5 groups)
- **Immigration line:** Yes | "Authorized to work in the United States"

---

## Provenance Flags

Track the publication status of your work. Skills check this table before every output.

| Item | Status | Correct Framing |
|------|--------|----------------|
| Enzyme solvent tolerance paper (Chen, Yamamoto, Holmberg) | under review at Proteins | "under review" -- never say "published" |
| Screening pipeline tool | unpublished internal tool | "computational infrastructure I developed" -- never imply peer-reviewed |
| Stability database preprint | preprint on bioRxiv, not yet submitted | "preprint" -- do not say "published" or "under review" |

---

## KB Corrections Log

Verified errors to never re-introduce. Add entries as you catch mistakes.

| Correction | Details |
|-----------|---------|
| Transfer learning framework credit | Co-developed with M. Rivera. Always use "Co-developed", never "Developed" alone. |
| ESM-2 stability prediction accuracy | 0.82 Spearman (not 0.85). Confirmed in published Table 2. |

---

## Role Types

Define the role types you're targeting. Each gets a bundle during setup.

| Role Name | Target Employers | Tier | Bundle File |
|-----------|-----------------|------|-------------|
| Academic | R1 research universities, teaching-focused colleges | 1 | bundle_academic.md |
| Industry R&D | Biotech/pharma companies | 2 | bundle_industry_rd.md |

**Tier guide:** 1 = strongest evidence, full portfolio | 2 = strong with targeted emphasis | 3 = viable with careful framing

---

## Role-Type Decision Tree

Customize this to map JD keywords to your role types.

| If JD mentions... | Primary profile | Secondary (hybrid) |
|-------------------|----------------|-------------------|
| tenure-track, faculty, assistant professor, teaching | Academic | -- |
| university, department, graduate students, NSF, NIH | Academic | Industry R&D |
| ML, machine learning, data science, R&D | Industry R&D | Academic |
| protein engineering, drug discovery, biologics | Academic | Industry R&D |
| pharma, biotech, clinical pipeline, GMP | Industry R&D | -- |

---

## FIXED Sections

List template sections that should NEVER be modified during generation.
These are copied verbatim from your template every time.

- Education
- Publications (CV)
- Honors & Awards
- Header block (name, contact, links)
- Undergraduate Research Experience (2 bullets, never changes)

---

## Output Rules

- **Email in all outputs:** jordan.chen@email.com
- **Resume package:** 2 pages + 1-page cover letter
- **CV package:** 5 pages + 1-2 page cover letter
- **Output .tex files ONLY** -- user compiles locally
