# Job Schema

## Overview
Represents a single job application within a multi-job batch.

## Lifecycle States

```
pending → in_progress → completed
                     ↓
                   failed
```

## Phase Progression

Within `in_progress` status:
1. research
2. template
3. matching
4. generation

## Required Fields

- job_id: Unique identifier within batch
- company: Company name
- role: Job title
- jd_text: Job description text

## Optional Fields

- jd_url: Source URL if scraped
- priority: User-assigned priority
- notes: User notes about this job
- requirements: Extracted after intake
- gaps: Identified after gap analysis
- coverage: Calculated after matching
- files_generated: Set true after generation

## Example

```json
{
  "job_id": "job-1",
  "company": "Microsoft",
  "role": "Principal PM - 1ES",
  "jd_text": "We are seeking...",
  "jd_url": "https://careers.microsoft.com/...",
  "priority": "high",
  "notes": "Internal referral from Alice",
  "status": "completed",
  "current_phase": null,
  "coverage": 85,
  "files_generated": true,
  "requirements": [
    "Kubernetes experience",
    "CI/CD pipeline management",
    "Cross-functional leadership"
  ],
  "gaps": []
}
```
