---
phase: 05-interactive-dashboard
plan: 03
subsystem: api
tags: [claude, sse, streaming, anthropic, chat, fastapi]

requires:
  - phase: 05-02
    provides: FastAPI server with data loader and API endpoints
provides:
  - Chat SSE streaming endpoint with Claude Sonnet
  - SME persona system prompt assembler with KG context
  - Source document keyword matching for per-query context
affects: [05-04]

tech-stack:
  added: [sse-starlette, anthropic (optional)]
  patterns: [SSE streaming via EventSourceResponse, async generator for streaming, optional import with availability flag]

key-files:
  created:
    - scripts/workbench/system_prompt.py
    - scripts/workbench/api_chat.py
  modified:
    - scripts/workbench/server.py
    - tests/test_workbench.py

key-decisions:
  - "AsyncAnthropic with try/except ImportError pattern for optional anthropic SDK"
  - "50K token threshold for conditional full JSON inclusion in system prompt"
  - "Last 10 messages history limit for multi-turn context management"

patterns-established:
  - "SSE streaming pattern: async generator yielding JSON-encoded data dicts"
  - "Mock testing pattern: inject MockClient via monkeypatch when SDK not installed"

requirements-completed: [DASH-01, DASH-02]

duration: 3min
completed: 2026-03-31
---

# Phase 05 Plan 03: Chat Endpoint Summary

**Claude Sonnet SSE chat endpoint with Sample Contract Analyst persona, full KG context injection, and mock-based test**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-31T23:49:32Z
- **Completed:** 2026-03-31T23:52:51Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- System prompt assembler turns Claude into Sample Contract Analyst with union labor, cost estimation, and citation guidelines
- POST /api/chat endpoint streams Claude responses via SSE with full KG context and multi-turn history
- Mock chat test validates endpoint wiring without requiring live Anthropic API key

## Task Commits

Each task was committed atomically:

1. **Task 1: Build system prompt assembler** - `cf1b968` (feat)
2. **Task 2: Create chat SSE endpoint, wire server, add test** - `cc113d2` (feat)

## Files Created/Modified
- `scripts/workbench/system_prompt.py` - SME persona prompt and KG context assembly
- `scripts/workbench/api_chat.py` - SSE streaming chat endpoint with AsyncAnthropic
- `scripts/workbench/server.py` - Added chat_router and has_api_key to health endpoint
- `tests/test_workbench.py` - Added test_chat_stream_mock with monkeypatched AsyncAnthropic

## Decisions Made
- AsyncAnthropic wrapped in try/except ImportError with HAS_ANTHROPIC flag (consistent with project convention for optional dependencies)
- 50K token threshold for system prompt: includes full node JSON if under 50K estimated tokens, otherwise summarized format
- Last 10 messages from history included in each request to limit token usage while preserving multi-turn context

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed mock test for missing anthropic SDK**
- **Found during:** Task 2 (mock chat test)
- **Issue:** monkeypatch.setattr failed because AsyncAnthropic attribute doesn't exist when anthropic SDK isn't installed
- **Fix:** Set attribute directly on module before monkeypatch to handle missing import case
- **Files modified:** tests/test_workbench.py
- **Verification:** test_chat_stream_mock passes, all 13 workbench tests pass
- **Committed in:** cc113d2 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Necessary fix for test to work without anthropic SDK installed. No scope creep.

## Issues Encountered
- sse-starlette was already installed in the project venv but system python was being used initially; resolved by using the project venv python explicitly

## User Setup Required
None - chat endpoint gracefully handles missing ANTHROPIC_API_KEY by returning an error SSE event.

## Next Phase Readiness
- Chat endpoint ready for frontend integration in Plan 04
- System prompt assembler provides full KG context for Claude reasoning
- All 13 workbench tests pass

---
*Phase: 05-interactive-dashboard*
*Completed: 2026-03-31*
