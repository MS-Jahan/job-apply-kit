# 07 — Template system (build once, pick automatically)

Back to [index](index.md).

## The idea

Your real CV/resume content lives in **one place per role category** (`templates_dir`), and every
apply skill picks from it automatically. No category names or file names are hard-coded in any skill.
The kit ships three fictional examples so the flow works on day one
(`./install.sh --with-examples` copies them into an empty `templates_dir`); your own set replaces
them.

## Building your set: `/create-template`

Depends only on `job-apply-core` + `humanizer` (not on the deep-tailoring `resume-kit` — separate
system, never mixed in one document). Per category it generates three documents from placeholder-only
skeletons plus a Markdown cover-letter copy:

- **CV** (exactly 2 pages): full mirror of your live CV — reorder-and-bold for the category only,
  never cut real content.
- **Resume** (exactly 1 page): condensed, category-relevant first, page filled.
- **Cover letter** (1 page): 3-paragraph structure with bracketed per-job placeholders.

Every file passes the same gates: truth (every claim traces to `cv_source`, nothing from your banned
or unproven lists), format (zero em-dashes, pure black, fixed margins), humanizer, AI-fingerprint
scan, `tectonic` compile, `pdfinfo` page count. Then the set is registered in
`<templates_dir>/INDEX.md`: one block per category with keywords, file names, page budget,
poor-fit notes and generation date. Re-run per category when your CV gains enough new material;
existing files are never silently overwritten.

## Picking automatically: the matcher

Apply skills read the index through `skills/job-apply-core/scripts/template_index.py`: it scores
categories by whole-word keyword hits against the job post, falls back to a general category on a
zero score, and expands the `.tex`/`.pdf` pair. Conceptually:

```
job post text → keyword match per INDEX category → closest RESUME_<CAT>.pdf → attach as-is
```

Because matching is index-driven, adding a new role category is just: run `/create-template` for it,
get an INDEX block, done — no skill changes.

## The other track (deep-tailoring)

`make-resume` / `make-cover-letter` / `critique` / `edit-resume` ignore `templates_dir` entirely. They generate
from scratch per job post through `resume.cls`/`cv.cls`, gated by `char_count.py`, from a knowledge
base built by `setup-extract` / `setup-build-kb`. Use on explicit request, or when a post needs a
combined skill set no single template covers.
