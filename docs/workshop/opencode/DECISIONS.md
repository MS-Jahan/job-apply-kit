# Decisions (opencode delegate run, 2026-10-08)

Design questions decided by the delegate agent per TASK.md:

1. GUIDE.md location: `docs/workshop/GUIDE.md` (TASK.md says "in docs/workshop/").
2. GUIDE structure: kept PLAN.md's 10 sections in order, added Contents links, Tip/Warning callouts, glossary (harness, skill, OAuth, debug port, dork), FAQ (10 Q&As), and a Worked example section (from 3b).
3. Slides: 25 slides total, worked-example slide is slide 17 (inside the 13-25 range) showing bdjobs_terms + 3 sample LinkedIn dorks; full lists live in GUIDE.md.
4. Slides nav: click anywhere advances (simplest for presenters); arrow keys/Space/PageUp/PageDown/Home/End also work; N toggles speaker notes.
5. No external URLs loaded by the deck (only printed as text links). Inline CSS+JS, no CDN. Works offline.
6. Verification: every path/command cited in GUIDE.md checked with ls against the repo — all 23 existed, no fixes needed.

## TASK2 redesign decisions (delegate run, 2026-10-08)

7. Tracker as a fixed global strip under the progress bar (not
   duplicated per slide): satisfies "top-of-slide tracker" visually
   on every slide and in print-with-JS, without 30x markup.
8. Addendum overrides original per-section colours: ONE green
   accent everywhere; amber only for Warning, red only for Danger.
9. Spec-mandated density exceptions: slide 11 lists all 13 setup
   steps, slide 28 lists all 7 risks — both exceed max-5-bullets,
   kept because the spec table requires those exact counts.
10. Slide 10 merges the two LinkedIn skills into one table row
    (≤5-row rule); `check-linkedin-saved` stays in notes + slide 5.
11. No `<a>` links anywhere: URLs/paths shown as plain code text
    so "no http(s) loads" holds trivially; only text mention is
    the localhost curl sample.
12. Self-check ran against headless Chrome via CDP (browser was
    not running, so started `google-chrome-stable --headless` on
    port 9222 locally); no BLOCKED.md needed.
