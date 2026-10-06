# Multi-Job Resume Tailoring - Testing Checklist

## Overview

Manual testing checklist for validating multi-job workflow functionality.

## Pre-Test Setup

- [ ] Resume library with at least 10 resumes in `resumes/` directory
- [ ] 3-5 job descriptions prepared (mix of similar and diverse roles)
- [ ] Clean test environment (no existing batches in progress)

---

## Test 1: Happy Path (3 Similar Jobs)

**Objective:** Validate complete multi-job workflow with typical use case

**Setup:**
- 3 similar job descriptions (e.g., 3 TPM roles, 3 PM roles, 3 Engineering roles)
- Resume library with 10+ resumes

**Steps:**
1. [ ] Provide 3 job descriptions
2. [ ] Verify multi-job detection triggers
3. [ ] Confirm multi-job mode
4. [ ] Complete intake (all 3 jobs collected)
5. [ ] Verify batch directory created: `resumes/batches/batch-{date}-{slug}/`
6. [ ] Verify `_batch_state.json` created with 3 jobs
7. [ ] Complete gap analysis
8. [ ] Verify `_aggregate_gaps.md` generated
9. [ ] Check gap deduplication (fewer unique gaps than total gaps)
10. [ ] Complete discovery session (answer questions for gaps)
11. [ ] Verify `_discovered_experiences.md` created
12. [ ] Check experiences tagged with job IDs
13. [ ] Approve experiences for library integration
14. [ ] Process Job 1 (INTERACTIVE mode)
    - [ ] Research phase completes
    - [ ] Success profile presented
    - [ ] Template generated and approved
    - [ ] Content matching completed and approved
    - [ ] Files generated (MD + DOCX + Report)
15. [ ] Process Job 2 (switch to EXPRESS mode)
    - [ ] Auto-proceeds through research/template/matching
    - [ ] Files generated without checkpoints
16. [ ] Process Job 3 (EXPRESS mode)
    - [ ] Completes automatically
    - [ ] Files generated
17. [ ] Batch finalization
    - [ ] `_batch_summary.md` generated
    - [ ] All 3 jobs shown with metrics
    - [ ] Review options presented
18. [ ] Approve all resumes for library
19. [ ] Verify library updated with 3 new resumes
20. [ ] Verify discovered experiences added to library

**Pass Criteria:**
- [ ] All 9 files generated (3 jobs × 3 files)
- [ ] Average JD coverage ≥ 70%
- [ ] No errors in any phase
- [ ] Time < (N × 15 min single-job time)
- [ ] Batch state shows "completed"

**Expected Time:** ~40 minutes for 3 jobs

---

## Test 2: Diverse Jobs (Low Overlap)

**Objective:** Validate detection and handling of dissimilar jobs

**Setup:**
- 3 very different job descriptions (e.g., TPM, Data Scientist, Marketing Manager)

**Steps:**
1. [ ] Provide 3 diverse job descriptions
2. [ ] Verify multi-job detection triggers
3. [ ] Complete intake
4. [ ] Run gap analysis
5. [ ] Verify diversity detection (< 40% overlap warning)
6. [ ] Verify recommendation to split batches
7. [ ] Choose to split into batches OR continue unified
8. [ ] Complete workflow

**Pass Criteria:**
- [ ] Diversity warning appears when overlap < 40%
- [ ] Options presented clearly
- [ ] User can choose to split or continue
- [ ] Workflow adapts based on choice

---

## Test 3: Incremental Batch Addition

**Objective:** Validate adding jobs to existing completed batch

**Setup:**
- Completed batch from Test 1 (3 jobs)
- 2 additional job descriptions

**Steps:**
1. [ ] Resume batch from Test 1
2. [ ] Request to add 2 more jobs
3. [ ] Verify batch loads previous state
4. [ ] Complete intake for new jobs (Job 4, Job 5)
5. [ ] Verify incremental gap analysis
6. [ ] Check that previous gaps are excluded from new analysis
7. [ ] Verify only NEW gaps identified
8. [ ] Complete incremental discovery (should be shorter)
9. [ ] Process new jobs (Job 4, Job 5)
10. [ ] Verify updated batch summary (now 5 jobs)
11. [ ] Approve new resumes

**Pass Criteria:**
- [ ] Previous jobs remain unchanged
- [ ] Only new gaps trigger discovery questions
- [ ] Time for 2 additional jobs < time for 2 from scratch
- [ ] Batch summary shows 5 jobs total
- [ ] Library updated with 2 additional resumes

**Expected Time Savings:** ~10-15 minutes vs processing 2 jobs from scratch

---

## Test 4: Pause and Resume

**Objective:** Validate batch can be paused and resumed later

**Setup:**
- Start multi-job batch with 3 jobs

**Steps:**
1. [ ] Start batch processing
2. [ ] Complete intake and gap analysis
3. [ ] Complete discovery
4. [ ] Complete Job 1 processing
5. [ ] Pause during Job 2 (say "pause")
6. [ ] Verify batch state saved
7. [ ] Verify pause message shows current state
8. [ ] End session (simulate session close)
9. [ ] Start new session
10. [ ] Resume batch (say "resume batch {id}" or "continue my batch")
11. [ ] Verify batch loads at Job 2
12. [ ] Complete Job 2 and Job 3
13. [ ] Finalize batch

**Pass Criteria:**
- [ ] Batch state accurately saved at pause
- [ ] Resume picks up at exact point (Job 2, correct phase)
- [ ] No data loss (discoveries, completed jobs intact)
- [ ] Workflow completes successfully

---

## Test 5: Error Handling - Research Failure

**Objective:** Validate graceful degradation when research fails

**Setup:**
- 3 job descriptions, one for obscure/nonexistent company

**Steps:**
1. [ ] Start batch with 3 jobs (one obscure company)
2. [ ] Complete intake and gap analysis
3. [ ] Complete discovery
4. [ ] Process Job 1 (normal company) - should succeed
5. [ ] Process Job 2 (obscure company)
6. [ ] Verify research failure detected
7. [ ] Verify warning message presented
8. [ ] Verify fallback to JD-only analysis offered
9. [ ] Choose fallback option
10. [ ] Verify Job 2 completes with JD-only analysis
11. [ ] Process Job 3 (normal company) - should succeed
12. [ ] Finalize batch

**Pass Criteria:**
- [ ] Research failure doesn't block entire batch
- [ ] Warning message clear and actionable
- [ ] Fallback options presented
- [ ] Job 2 completes successfully with degraded info
- [ ] Jobs 1 and 3 unaffected

---

## Test 6: Individual Job Review and Approval

**Objective:** Validate reviewing and approving jobs individually

**Setup:**
- Completed batch from Test 1

**Steps:**
1. [ ] Complete batch processing (3 jobs)
2. [ ] Choose "REVIEW INDIVIDUALLY" option
3. [ ] Review Job 1
    - [ ] Verify JD requirements shown
    - [ ] Verify coverage metrics shown
    - [ ] Verify discovered experiences highlighted
4. [ ] Approve Job 1
5. [ ] Review Job 2
6. [ ] Reject Job 2 (don't add to library)
7. [ ] Review Job 3
8. [ ] Request revision for Job 3
9. [ ] Make changes (e.g., "make summary shorter")
10. [ ] Re-review Job 3
11. [ ] Approve Job 3
12. [ ] Finalize batch

**Pass Criteria:**
- [ ] Job 1 added to library
- [ ] Job 2 NOT added to library
- [ ] Job 3 revised and then added to library
- [ ] Library updated with only approved jobs (Jobs 1, 3)
- [ ] Batch summary reflects individual decisions

---

## Test 7: Batch Revision

**Objective:** Validate making changes across all resumes in batch

**Setup:**
- Completed batch from Test 1

**Steps:**
1. [ ] Complete batch processing (3 jobs)
2. [ ] Choose "REVISE BATCH" option
3. [ ] Request batch-wide revision (e.g., "Emphasize leadership in all resumes")
4. [ ] Verify system identifies affected jobs (all 3)
5. [ ] Verify re-run of matching/generation for all jobs
6. [ ] Review revised resumes
7. [ ] Verify revision applied to all 3
8. [ ] Approve batch

**Pass Criteria:**
- [ ] Batch revision applied to all relevant jobs
- [ ] All resumes regenerated correctly
- [ ] Revision reflected in all final resumes
- [ ] Batch finalizes successfully

---

## Test 8: Express Mode Throughout

**Objective:** Validate EXPRESS mode with minimal user interaction

**Setup:**
- 3 similar job descriptions

**Steps:**
1. [ ] Start batch
2. [ ] Complete intake and gap analysis
3. [ ] Complete discovery
4. [ ] Choose EXPRESS mode for all jobs
5. [ ] Verify Jobs 1, 2, 3 process without checkpoints
6. [ ] Verify files generated for all jobs
7. [ ] Review all resumes in batch finalization
8. [ ] Approve all

**Pass Criteria:**
- [ ] No checkpoints during per-job processing
- [ ] All jobs complete automatically
- [ ] Quality maintained (coverage ≥ 70%)
- [ ] Time significantly faster (no waiting for approvals)

**Expected Time:** ~30-35 minutes for 3 jobs (vs ~40 with INTERACTIVE)

---

## Test 9: Remove Job Mid-Process

**Objective:** Validate removing a job during processing

**Setup:**
- Start batch with 3 jobs

**Steps:**
1. [ ] Complete intake, gap analysis, discovery
2. [ ] Complete Job 1 processing
3. [ ] Request to remove Job 2 (say "remove Job 2")
4. [ ] Verify removal confirmation
5. [ ] Verify Job 2 files archived (not deleted)
6. [ ] Verify discovered experiences remain available
7. [ ] Continue to Job 3
8. [ ] Complete Job 3
9. [ ] Finalize batch
10. [ ] Verify batch summary shows 2 jobs (Jobs 1, 3)

**Pass Criteria:**
- [ ] Job 2 removed cleanly
- [ ] No errors when continuing to Job 3
- [ ] Batch completes with 2 jobs
- [ ] Batch summary accurate

---

## Test 10: Minimal Library

**Objective:** Validate handling of small resume library

**Setup:**
- Resume library with only 2 resumes
- 3 job descriptions

**Steps:**
1. [ ] Start batch with limited library
2. [ ] Verify warning about limited library
3. [ ] Complete gap analysis
4. [ ] Verify many gaps identified (low library coverage)
5. [ ] Complete discovery (should be longer than typical)
6. [ ] Verify many new experiences discovered
7. [ ] Complete batch processing
8. [ ] Verify resumes generated despite limited starting library

**Pass Criteria:**
- [ ] Warning about limited library appears
- [ ] Discovery phase captures significant new content
- [ ] Resumes still generated successfully
- [ ] Coverage improves through discovery
- [ ] Library enriched significantly (2 → 5 resumes)

---

## Test 11: Backward Compatibility (Single-Job)

**Objective:** Ensure single-job workflow still works unchanged

**Setup:**
- Single job description (NOT multi-job)

**Steps:**
1. [ ] Provide single job description
2. [ ] Verify multi-job detection does NOT trigger
3. [ ] Verify standard single-job workflow used (from SKILL.md)
4. [ ] Complete all phases (library, research, template, matching, generation)
5. [ ] Verify single resume generated
6. [ ] Verify no batch directory created

**Pass Criteria:**
- [ ] Single-job workflow completely unchanged
- [ ] No multi-job artifacts (no batch directory, no batch state)
- [ ] Resume quality same as before multi-job feature

---

## Test 12: No Gaps Found

**Objective:** Validate handling when library already covers all requirements

**Setup:**
- Well-populated library
- 3 job descriptions with requirements matching library well

**Steps:**
1. [ ] Start batch
2. [ ] Complete intake
3. [ ] Run gap analysis
4. [ ] Verify high coverage (> 85% for all jobs)
5. [ ] Verify "no significant gaps" message
6. [ ] Verify option to skip discovery
7. [ ] Choose to skip discovery
8. [ ] Complete per-job processing
9. [ ] Finalize batch

**Pass Criteria:**
- [ ] System detects high coverage
- [ ] Option to skip discovery presented
- [ ] Batch completes successfully without discovery
- [ ] Time faster than typical (no discovery phase)

**Expected Time:** ~25 minutes for 3 jobs (vs ~40 with discovery)

---

## Regression Testing

After any changes to multi-job workflow:

- [ ] Re-run Test 1 (Happy Path)
- [ ] Re-run Test 11 (Backward Compatibility)
- [ ] Verify no existing functionality broken

---

## Performance Benchmarks

**Time Targets:**

| Scenario | Target Time | Sequential Baseline | Time Savings |
|----------|-------------|---------------------|--------------|
| 3 similar jobs | ~40 min | ~45 min (3 × 15) | ~11% |
| 5 similar jobs | ~55 min | ~75 min (5 × 15) | ~27% |
| Add 2 to existing batch | ~20 min | ~30 min (2 × 15) | ~33% |

**Quality Targets:**

- Average JD coverage: ≥ 70%
- Direct matches: ≥ 60%
- Critical gap resolution: 100%

---

## Bug Reporting Template

If any test fails, report using this template:

```markdown
## Bug Report: {Test Name} - {Failure Description}

**Test:** Test {N}: {Test Name}
**Step Failed:** Step {N}
**Expected:** {What should happen}
**Actual:** {What actually happened}
**Error Message:** {If applicable}
**Batch State:** {Current batch_state.json contents}
**Files Generated:** {List of files in batch directory}
**Reproduction Steps:**
1. {Step 1}
2. {Step 2}
...

**Environment:**
- Resume library size: {N resumes}
- Job count: {N jobs}
- Batch ID: {batch_id}
```
