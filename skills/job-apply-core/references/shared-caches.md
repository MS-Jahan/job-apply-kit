# Shared caches and run-state contract

All paths are relative to the workspace (config `workspace`). Skills read and write these; none of
them ships in the kit.

| Path | Owner | Shape / purpose |
|---|---|---|
| `JDs/tracker/sheet_snapshot_<date>.md`, `sheet_raw_<date>.json` | core `sheet_snapshot.py` | read-only copy of the tracker; the dedup fact base for a session |
| `.cache/profile/<date>/` | every skill that touches candidate facts | snapshot of `cv_source` / `projects_source` content for the day |
| `JDs/<source>/applied_cache.json` | each source skill | `{ "company+position": { "sheet_row": N, "date": "...", "how": "..." } }` |
| `JDs/<source>/seen_*.json` | each source skill | per-item verdicts (`new`, `applied`, `drafted`, `skipped-duplicate`, `expired`, `not-a-job`) so nothing is opened twice |
| `JDs/linkedin-saved/seen_posts.json` | `check-li-saved` only | saved-post verdicts (post_url, title, company, position, verdict, sheet_row, ...) |
| `JDs/linkedin-saved/seen.json` | `li-full-run` only | post-search sweep verdicts (post_url, verdict, first_seen, processed_at) |
| `JDs/linkedin-saved/applied_cache.json` | `check-li-saved` AND `li-full-run` | SHARED: `{ "company+position": { sheet_row, date, how } }`. Both skills read it before acting and add entries after; neither may delete the other's entries. Keep the shape stable |
| `JDs/<source>/<date>/` | the run that created it | run state (CSV, logs, decisions, reports) |
| `JDs/pasted-batch-<date>/` | `check-image-batch` | images + `STATUS.md` |
| `output/<company-slug>/` | any apply skill | per-job files, evidence screenshots |
| `SESSIONS.md` | the agent | session log |

Rules:
- Update the cache for a job before doing work on it, and again when the outcome is known.
- If a tracker row was added outside a skill, reconcile `applied_cache.json` on the next run.
- A cache entry never overrides the live tracker: when they disagree, the tracker wins.
