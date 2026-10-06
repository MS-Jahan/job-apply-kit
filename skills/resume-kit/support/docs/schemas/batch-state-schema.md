# Batch State Schema

## Overview
Tracks the state of multi-job resume tailoring sessions, supporting pause/resume and incremental job additions.

## Schema

### BatchState

```json
{
  "batch_id": "batch-YYYY-MM-DD-{slug}",
  "created": "ISO 8601 timestamp",
  "current_phase": "intake|gap_analysis|discovery|per_job_processing|finalization",
  "processing_mode": "interactive|express",
  "jobs": [JobState],
  "discoveries": [DiscoveredExperience],
  "aggregate_gaps": AggregateGaps
}
```

### JobState

```json
{
  "job_id": "job-{N}",
  "company": "string",
  "role": "string",
  "jd_text": "string",
  "jd_url": "string|null",
  "priority": "high|medium|low",
  "notes": "string",
  "status": "pending|in_progress|completed|failed",
  "current_phase": "research|template|matching|generation|null",
  "coverage": "number (0-100)",
  "files_generated": "boolean",
  "requirements": ["string"],
  "gaps": [GapItem]
}
```

### DiscoveredExperience

```json
{
  "experience_id": "disc-{N}",
  "text": "string",
  "context": "string",
  "scope": "string",
  "addresses_jobs": ["job-id"],
  "addresses_gaps": ["string"],
  "confidence_improvement": {
    "gap_name": {
      "before": "number",
      "after": "number"
    }
  },
  "integrated": "boolean",
  "bullet_draft": "string"
}
```

### AggregateGaps

```json
{
  "critical_gaps": [
    {
      "gap_name": "string",
      "appears_in_jobs": ["job-id"],
      "current_best_match": "number (0-100)",
      "priority": "number"
    }
  ],
  "important_gaps": [...],
  "job_specific_gaps": [...]
}
```

### GapItem

```json
{
  "requirement": "string",
  "confidence": "number (0-100)",
  "gap_type": "critical|important|specific"
}
```
