---
status: complete
phase: 12-domain-list-and-delete-commands
source: [12-01-SUMMARY.md, 12-02-SUMMARY.md, 12-03-SUMMARY.md]
started: "2026-05-07T00:00:00.000Z"
updated: "2026-05-07T00:00:00.000Z"
---

## Current Test

[testing complete]

## Tests

### 1. domain-list renders active domains
expected: Running /epistract:domain-list displays a markdown table of all active domains with columns: Name, Entity Types, Relation Types, Last Modified, Files. All currently installed active domains appear. No archived section appears when no domains are archived.
result: pass

### 2. domain-delete rejects nonexistent domain
expected: Running /epistract:domain-delete nonexistent-domain returns an error saying the domain was not found and no changes have been made. The command stops immediately (no archive/remove prompt).
result: pass

### 3. domain-delete pauses at Step 2 for action choice
expected: Running /epistract:domain-delete <real-domain-name> shows the domain name and file count, then presents two options (archive / remove) and WAITS for a response. It does not auto-advance or execute any filesystem operation.
result: pass

### 4. domain-delete cancels on unrecognized input at Step 2
expected: At the archive/remove prompt, typing anything other than "archive" or "remove" (e.g., "cancel", "no", "q") results in "Cancelled. No changes made." and the command stops with no filesystem changes.
result: pass

### 5. domain-delete requires "yes" confirmation at Step 3
expected: After selecting "archive" or "remove", a second confirmation is presented. Typing anything other than "yes" at that prompt results in "Cancelled. No changes made." and no filesystem changes occur.
result: pass

### 6. archived domains excluded from active pipeline
expected: After a domain is archived, running /epistract:domain-list shows it ONLY in the "Archived Domains" section — not in the active domains table. The domain is no longer resolved by the pipeline.
result: pass

## Summary

total: 6
passed: 6
issues: 0
pending: 0
skipped: 0

## Gaps

[none yet]
