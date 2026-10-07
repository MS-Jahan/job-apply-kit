---
name: resume-kit
description: Shared reference, templates and helpers for the deep-tailoring resume skills (make-resume, make-cover-letter, critique, edit-resume, setup-extract, setup-build-kb). Not used directly; installed automatically as their dependency.
---

# resume-kit

Shared data for the deep-tailoring track (job-apply-core OPERATIONS.md#documents calls this Workflow B).
Not a standalone skill — it has no workflow of its own. The six resume skills depend on it and reference
its contents as `{{RESUME_KIT_DIR}}/...`.

```
reference/    session startup, char-limit budgets, CL rules, critique framework (resume_reference.md,
              critical_rules.md, cl_reference.md, critique_framework.md, session_file_template.md,
              shared_ops.md)
support/      skills taxonomy format, branching questions, matching strategies, multi-job workflow,
              research prompts, AI-fingerprint rules, design docs under support/docs/
templates/    resume.cls, cv.cls, coverletter_template.tex, resume_template.tex/.md, cv_template.tex
helpers/      char_count.py (authoritative bullet length checker), test_char_count.py
examples/     fictional example session, bundle, experience and extraction files (Workflow B format)
```

Generated, per-user knowledge-base files (`experience/`, `bundles/`, `support/skills_taxonomy.md`,
`support/pub_metadata.md`, `support/achievement_reframing_guide.md`, `support/significance_*.md`) are
NOT part of this folder — they live under `<workspace>/resume_builder/`, built by `/setup-extract` and
`/setup-build-kb` from `cv_source`, and are never shipped.
