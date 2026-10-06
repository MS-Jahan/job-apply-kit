# 04 — Job searching (what each scanning skill owns)

Back to [index](index.md).

## The scanners (save/find-only vs end-to-end)

| Skill | Source | Does it apply? |
|---|---|---|
| `bdjobs-full-run` | BDJobs search pages | Yes — portal Apply (the one authorized exception) or Gmail draft, + tracker row |
| `li-full-run` | LinkedIn **post search** results | Stages only — Gmail draft or form left at Submit, + tracker row |
| `linkedin-job-search` | LinkedIn post search | No — saves matching posts only; `check-li-saved` processes them later |
| `check-li-saved` | LinkedIn **saved posts** page | Stages only (draft or form at Submit), + tracker row |
| `check-fb-saved` | Facebook saved items | Stages only, + tracker row |
| `check-discord-jobs` | Discord job channels | Stages only, + tracker row |
| `check-image-batch` | Pasted job-post screenshots | Stages only, + tracker row |

`li-full-run` and `check-li-saved` overlap on purpose but never collide: the first owns post-search
results, the second owns the saved-posts page. They share one contract file,
`JDs/linkedin-saved/applied_cache.json` (documented in
`skills/job-apply-core/references/shared-caches.md`), so a job found by either is never processed
twice. Duplicate protection everywhere else works the same way: per-source `seen_*.json` caches plus
a tracker-snapshot check before any work starts.

## How a run flows (all end-to-end scanners)

1. **Extract** — scroll the source, collect items (links, titles, post text) into a run folder.
2. **Verdict** — mark each `new`, `applied`, `drafted`, `skipped-duplicate`, `expired` or `not-a-job`
   against the caches and the tracker. Write verdicts back *before* opening anything.
3. **Process NEW only** — pick the closest template automatically ([Templates](07-templates.md)),
   then follow `skills/job-apply-core/references/new-job-procedure.md`: humanized email body or form
   fill, Drive upload, tracker row, staged (never submitted) with screenshot evidence.

## Personal tuning lives in the config, not in the skills

Experience cap, salary floors, on-site location whitelist, remote-ok flag, and the BDJobs/LinkedIn
search-term lists are config keys with neutral defaults — the same skill behaves differently for
different users without code changes. Missing salary floors are a hard error, not a silent default.

## Search only when needed

If a post already shows the company, the requirements and a contact or apply link, the agent does not
search further. Otherwise: SearXNG first, then page reads via `agent-browser`. Nobody hand-writes
scrapers against search-engine result pages.
