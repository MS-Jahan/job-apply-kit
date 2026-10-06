# BDJobs site notes

Reference material for `bdjobs-full-run`, kept from the earlier hand-driven skills (job search and
apply-saved) that the scripted pipeline replaced. Use it when a script needs debugging or a step has
to be done by hand.

## Login state (important)

`https://bdjobs.com` may show "Sign In" while a valid `mybdjobs.bdjobs.com` jobseeker-panel session
exists (separate domains; the session cookies live on `.bdjobs.com` but the public header does not
always hydrate). A Save click that redirects to `signin?tp=sj&sys=save/<id>` therefore does NOT always
mean you are logged out.

Reliable probe: open `https://mybdjobs.bdjobs.com/jobseeker-panel/saved-jobs?lang=en` in a new tab.
If it shows the candidate's name and the saved list, the session is live; go back to the job page and
click Save again. A redirect to a sign-in page there is a real login wall (the scripts auto-login from
the `.env` file; without it, hard stop).

## Search page

- Listing URL: `https://bdjobs.com/h/jobs`. The search box has the placeholder "Search for Jobs...";
  type the term with the native value setter plus `input` events (Angular), then Enter. Wait at least
  7 seconds for the results to re-render.
- Result cards are `app-job-card` elements: title, company, location, experience, deadline (some
  fields missing on some cards). The job id comes from the link `/h/details/<id>?ln=1`.
- Every card carries a deadline such as `13 Oct 2026`. Compare with `TZ=Asia/Dhaka date`; an expired
  deadline means skip, and stop paginating that term.
- Pagination: use the trusted-click path in `bd1_scrape.py` (synthetic scrolling alone is unreliable).

## Save semantics (detail page)

- Button text "Save" = not saved yet: click it. "Saved", "Already saved" or "Unsave" = already saved:
  do not click, record `already-saved`.
- Success signal: the button list changes from `["Apply Now","Save"]` to `["Apply Now"]`.
- Early-stop heuristic from the hand-driven version: more than 3 already-saved jobs in a row means the
  rest of that term was handled in an earlier run.
- Verify at the saved-jobs panel after a batch.

## Apply-method triage (per saved job)

- An email address in the posting = email path (template as-is, humanized body, Gmail draft).
- An outside application link (company site, Google Form, portal) = link path: fill and upload, stop at
  the final Submit, screenshot to `output/<company-slug>/`.
- The BDJobs "Apply" button available = BDJobs path: click Apply. A form with questions: fill it and
  STAGE (do not submit). Only a custom-CV upload field and no questions: attach the CV and complete the
  apply (the authorized exception in SKILL.md rule 2).
- Expired deadline: skip and record. Login wall: stop, leave the tab open, record.

## Apply form (what actually works)

The apply-online page is an Angular form. Known gotchas:
1. **Salary input.** There are usually two inputs with `placeholder="e.g. 50000"` (a hidden current
   salary and a visible expected salary). Fill the VISIBLE one. A synthetic `input` event with the
   native value setter works for most jobs.
2. **Trusted events.** When the synthetic fill leaves submit disabled, use real CDP input events
   (`type_salary.py`, `Input.dispatchMouseEvent`). Synthetic KeyboardEvent objects do not satisfy
   Angular validation.
3. **Salary-warning modal.** After submit a modal may say the expected salary is higher than the
   position's range, with [Apply Anyway] and [Change Salary]. Clicking Apply Anyway is authorized for
   this skill only (see SKILL.md rule 2).
4. **Ground truth.** After any batch, check the applied-jobs panel
   (`https://mybdjobs.bdjobs.com/jobseeker-panel/applied-jobs?lang=en`: the "Total Job Found" count and
   the company names). An UNCONFIRMED result from a script can be a false negative; the panel is right.
5. **Forms that reset.** A listing whose form resets on every submit attempt, regardless of method, goes
   to the email path.

## Google Forms reached from BDJobs links

Follow OPERATIONS #accounts (account banner, switch account, re-check after reload) and #documents
(dropdowns are ARIA listboxes; file upload goes through the Picker iframe: `picker_upload.py`).
