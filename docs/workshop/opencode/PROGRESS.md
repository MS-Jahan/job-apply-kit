# Progress summary (opencode delegate run, 2026-10-08)

All PLAN.md boxes ticked (1-9 + 3b). No BLOCKED.md needed — nothing blocked.

## Deliverables

1. `docs/workshop/GUIDE.md` — beginner-friendly rewrite of `docs/workshop/PLAN.md`.
   Sections 1-10 (all facts kept), Contents links, Tip/Warning callouts,
   glossary (harness, skill, OAuth, debug port, dork), 10-question FAQ,
   Worked example section copied exactly from `docs/workshop/example-config.md`
   (search lists verbatim, placeholders only, no personal data).
2. `docs/workshop/slides/index.html` — one self-contained file, inline CSS+JS,
   no CDN, works offline. 25 slides following PLAN.md Appendix A.
   Arrow-key/Space/click navigation, slide counter, dark theme, big fonts,
   speaker notes on every slide (press N). Slide 17 = worked example.

## Verification

- All 23 paths/commands cited in GUIDE.md checked with ls — all exist, no fixes.
- Headless parse of index.html: 25 slides, 25 notes, 0 external src/href, 0 CDN refs,
  nav + counter + notes toggle present.
- Design decisions logged in `docs/workshop/opencode/DECISIONS.md`.
- Rules kept: nothing touched outside docs/workshop/ (+ opencode/ tracking files),
  no secrets, no commit/push.
