# Help center

New to the kit? Read this page, then follow the path that matches what you want to do. Every page
below links back here. Command reference stays in `docs/EXTERNAL_TOOLS.md`; universal agent rules live
in `skills/job-apply-core/OPERATIONS.md`.

## Two paths

- **Tailor-only (no accounts, no browser).** You want tailored resumes, CVs and cover letters for
  specific posts. Install the resume skills, set up the config, optionally build the knowledge base.
  Needs: Python, a PDF toolchain. See [Prerequisites](01-prerequisites.md) and
  [PDF generation](05-pdf-generation.md).
- **Full apply automation.** The agent also scans job sources, drafts emails and stages applications
  for your review. Needs everything above plus: Node, a debug browser, `agent-browser`, and a Google
  backend. See [Browser setup](03-browser-setup.md) and [Google setup](02-google-setup.md).

Run `./doctor.sh --mode tailor` or `--mode apply` at any point — it tells you exactly what is missing
for your path. On native Windows, run the Python entry points directly (`python install.py`,
`python doctor.py`); see [Compatibility](08-compatibility.md).

## Module map

| Module | Page | Skills involved |
|---|---|---|
| config.md: every key, per-job flow, refresh rules | [00-config](00-config.md) | all (config-first, every run) |
| Prerequisites (Python, Node, accounts) | [01-prerequisites](01-prerequisites.md) | all |
| Google auth + Gmail/Drive/Sheets backend | [02-google-setup](02-google-setup.md) ([Cloud Console walkthrough](02-cloud-console.md)) | every apply skill, via `job-apply-core` |
| Debug browser + agent-browser + MCP fallback | [03-browser-setup](03-browser-setup.md) | every search/apply skill |
| Job searching (BDJobs, LinkedIn, saved lists, screenshots) | [04-job-search](04-job-search.md) | `bdjobs-full-run`, `li-full-run`, `linkedin-job-search`, `check-li-saved`, `check-fb-saved`, `check-discord-jobs`, `check-image-batch` |
| PDF generation (tectonic, page budgets) | [05-pdf-generation](05-pdf-generation.md) | `create-template`, `make-resume`, `make-cl` |
| Email drafting + Drive + tracker | [06-email-and-tracking](06-email-and-tracking.md) | every apply skill, via `job-apply-core` |
| Template system (build once, pick automatically) | [07-templates](07-templates.md) | `create-template`, every apply skill |
| OS compatibility (Windows, WSL2, VM) | [08-compatibility](08-compatibility.md) | — |

## The one rule

Fill it in, stage it at the final Submit/Apply button, stop. Every email is a Gmail draft, never
sent. The single documented exception (BDJobs's own portal Apply button) lives only in
`bdjobs-full-run`. Nothing in these pages changes that.
