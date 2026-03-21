---
name: session-start
description: Run at the start of every Claude Code session. Checks progress, services, blockers, and recommends next steps.
---

# Session Start Checklist

Run this at the beginning of every work session.

## Step 1 — Read Progress
Read `.claude/docs/progress.md` to understand:
- Current phase and status
- What's completed
- Open blockers
- Key numbers

## Step 2 — Check Services
Run `/service-health` to verify all Docker containers are running.

## Step 3 — Check Pipeline
Run `dvc status` to see if any pipeline stages are stale.

## Step 4 — Check Git State
Run `git status` and `git log --oneline -5` to see current branch and recent commits.

## Step 5 — Recommend Next Steps
Based on the progress tracker, identify the next 2-3 tasks to work on.
Present them in priority order with the specific commands or files involved.

## Output Format
```
Session Start Summary
═══════════════════════
Phase: [current phase]
Branch: [current branch]
Services: [X/8 healthy]
Pipeline: [stale/up-to-date]

Next Steps:
1. [highest priority task]
2. [second task]
3. [third task]

Blockers: [any open blockers]
```
