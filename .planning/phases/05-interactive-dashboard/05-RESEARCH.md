# Phase 5: Interactive Dashboard - Research

**Researched:** 2026-03-31
**Domain:** FastAPI web application, Claude Sonnet chat integration, vis.js graph visualization, vanilla HTML/JS frontend
**Confidence:** HIGH

## Summary

Phase 5 builds the Sample Contract Analysis Workbench -- a FastAPI-powered web application with three components: (1) a chat-first interface backed by Claude Sonnet for natural-language contract analysis, (2) an interactive vis.js knowledge graph browser, and (3) a source document viewer with citation linking. The workbench reads pre-built artifacts (graph_data.json, claims_layer.json, communities.json, ingested/*.txt) from the extraction pipeline output directory.

The technology decisions are locked: FastAPI backend, vanilla HTML/JS frontend (no framework), vis.js for graph visualization (already bundled), Claude Sonnet via Anthropic API for chat, SSE streaming for response delivery. The phase also includes expanding the contract domain schema with organizational entity types (COMMITTEE, PERSON, EVENT, STAGE, ROOM) extracted from the Master planning document.

**Primary recommendation:** Structure as 4-5 plans: (1) domain schema expansion, (2) FastAPI backend with API endpoints + data loading, (3) chat interface with Claude streaming, (4) graph panel + source viewer frontend, (5) integration wiring + synthetic test fixtures.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** FastAPI backend + vanilla HTML/JS frontend. Python API server proxies Claude API calls, serves the HTML app, serves source documents and KG data. No additional web framework dependencies beyond FastAPI.
- **D-02:** Single-page web application served by FastAPI. Not a static HTML file -- the chat interface requires a live backend for Claude API calls.
- **D-03:** Claude Sonnet as the chat LLM model. Balances speed, cost, and reasoning quality for a personal analysis tool with frequent queries.
- **D-04:** ANTHROPIC_API_KEY provided via environment variable. Matches existing codebase convention for LLM access.
- **D-05:** Chat-first layout with collapsible side panels (Graph, Sources). Chat is the main column; side panels expand on click.
- **D-06:** Separate extract-then-serve workflow. Run extraction pipeline first, then launch workbench server pointing at output directory.
- **D-07:** Personal tool, localhost only. No authentication, no multi-user support.
- **D-08:** Session-only chat history. No persistence between server restarts. No database required.
- **D-09:** Full KG + relevant doc chunks as context for every chat question.
- **D-10:** Starter prompts on first load (4-6 suggested questions), then free-form input.
- **D-11:** Rich markdown responses with tables, bullet lists, and inline citations.
- **D-12:** Chat-based what-if reasoning.
- **D-13:** Senior contract analyst persona ("Sample Contract Analyst"). No personal name.
- **D-14:** Honest boundary + redirect for out-of-scope questions.
- **D-15:** Cost estimation capability from extracted contract data.
- **D-16:** Interactive vis.js network graph with search bar + entity type toggles + severity filter.
- **D-17:** Double-click to recenter on node neighborhood.
- **D-18:** Extracted text display from ingested/*.txt files with section highlighting.
- **D-19:** Inline citation links open Sources panel scrolled to referenced section.
- **D-20:** Add new entity types to domain.yaml: COMMITTEE, PERSON, EVENT/PROGRAM, STAGE, ROOM. Add new relation types.
- **D-21:** Programs/events are KG nodes linked to contracts.
- **D-22:** Committees and people are KG nodes.
- **D-23:** Schema expansion as first plan in Phase 5.
- **D-24:** SME reasoning from KG + contract text for volunteer-vs-union-labor questions.
- **D-25:** Clean professional visual design per UI-SPEC color/typography tokens.
- **D-26:** Synthetic fixtures for automated tests. Mock Claude API responses.
- **D-27:** v1 essential: Chat + Graph panel + Source viewer.
- **D-28:** Deferred to v1.1: Dedicated Risk panel.

### Claude's Discretion
- Starter prompt question selection (which 4-6 questions best showcase capabilities)
- Graph layout algorithm and physics settings for vis.js
- Source panel search/navigation UX details
- System prompt engineering for the SME persona
- FastAPI project structure (single file vs. modular)
- Exact API endpoint design beyond core routes
- HTML/CSS implementation details within the visual direction specified

### Deferred Ideas (OUT OF SCOPE)
- Dedicated Risk Panel (v1.1)
- Telegram chat interface (v2)
- Persistent what-if scenarios
- Multi-user access / sharing
- Persistent chat history
- Committee-oriented dashboard views (PRES-01)
- Source provenance drill-down (PRES-02, PRES-03)

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DASH-01 | Interactive web interface displays the contract knowledge graph with filterable views | FastAPI serves HTML SPA; vis.js renders graph from graph_data.json; entity type toggles + severity filter provide filtering; search bar enables node name filtering |
| DASH-02 | Users can explore entities by type (parties, obligations, deadlines, costs) with tabular and graph views | Chat provides tabular exploration via markdown tables in responses; graph panel provides visual exploration; entity type toggle buttons switch visibility by type |

</phase_requirements>

## Project Constraints (from CLAUDE.md)

- **Package management:** `uv` for Python dependencies, not pip directly
- **Linting:** `ruff check` and `ruff format`
- **Testing:** `pytest`
- **Python:** 3.11+
- **Paths:** Use `pathlib.Path` throughout, not `os.path`
- **Error handling:** Optional deps wrapped in try/except with availability flags
- **JSON:** `indent=2` for all JSON output
- **Naming:** snake_case functions/variables, SCREAMING_SNAKE_CASE constants
- **CLI pattern:** `sys.argv` parsing (no argparse)
- **Makefile:** Must have standard targets including `help`, `test`, `lint`, `format`, `run`

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | 0.135.2 | HTTP API server, serves SPA + API endpoints | Locked decision D-01. Async-native, Pydantic integration, auto-docs |
| uvicorn | 0.42.0 | ASGI server for FastAPI | Standard FastAPI production server. Already installed locally (0.35.0) |
| anthropic | 0.87.0 | Claude Sonnet API client with streaming | Locked decision D-03/D-04. Official Python SDK with `.messages.stream()` |
| sse-starlette | 3.3.4 | Server-Sent Events for chat streaming | W3C SSE spec implementation for Starlette/FastAPI. Enables incremental markdown rendering |
| vis.js | 9.1.2 | Network graph visualization | Already bundled in `lib/vis-9.1.2/`. Reuse per D-16, existing pyvis pattern |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Pydantic | >=2.5 | Request/response models for API | Already in project deps. Natural fit for FastAPI endpoint validation |
| httpx | 0.28.1 | Async HTTP test client | FastAPI test client uses httpx. For automated API tests |
| PyYAML | >=6.0 | Parse expanded domain.yaml | Already in project deps. For schema expansion plan |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| sse-starlette | FastAPI native SSE (0.135+) | FastAPI 0.135 added built-in SSE support via `EventSourceResponse`. Could use native if upgrading to 0.135+, but sse-starlette is more battle-tested and works with older FastAPI |
| Vanilla HTML/JS | React/Vue/Svelte | Locked decision D-01 -- no frontend framework. Vanilla is simpler for this scope |
| vis.js | D3.js, Cytoscape.js | vis.js already bundled and used by pyvis viewer. No reason to switch |

**Installation:**
```bash
uv pip install fastapi uvicorn anthropic sse-starlette httpx
```

**Note:** FastAPI 0.135.2 has built-in SSE support (`from fastapi.responses import EventSourceResponse`). If installing 0.135+, sse-starlette may be optional. However, sse-starlette provides additional features (keep-alive pings, reconnection headers) that are useful for long-running chat streams.

## Architecture Patterns

### Recommended Project Structure

```
scripts/
  workbench/
    __init__.py
    server.py           # FastAPI app, startup, mount static
    api_chat.py         # POST /api/chat -> SSE stream
    api_graph.py        # GET /api/graph, GET /api/graph/node/{id}
    api_sources.py      # GET /api/sources, GET /api/sources/{doc_id}
    api_pdf.py          # GET /api/pdf/{doc_id} -> serves original PDF
    data_loader.py      # Load graph_data.json, claims_layer.json, etc. at startup
    system_prompt.py    # SME persona prompt construction
    static/
      index.html        # Single-page application
      style.css         # All styles per UI-SPEC tokens
      app.js            # Main application logic
      chat.js           # Chat panel: messages, streaming, markdown rendering
      graph.js          # Graph panel: vis.js setup, search, filters
      sources.js        # Source panel: document list, text viewer, highlighting
scripts/
  launch_workbench.py   # CLI entry point: python launch_workbench.py <output_dir> [--port 8000]
```

### Pattern 1: Data Loading at Startup

**What:** Load all KG data files once at server startup, keep in memory. The graph is read-only during workbench session.
**When to use:** Always -- the output directory is a snapshot from the extraction pipeline.
**Example:**
```python
# data_loader.py
from pathlib import Path
import json

class WorkbenchData:
    """In-memory store for pre-extracted KG data."""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.graph_data: dict = {}
        self.claims_layer: dict = {}
        self.communities: dict = {}
        self.documents: list[dict] = []
        self.load()

    def load(self):
        gp = self.output_dir / "graph_data.json"
        if gp.exists():
            self.graph_data = json.loads(gp.read_text(encoding="utf-8"))
        cp = self.output_dir / "claims_layer.json"
        if cp.exists():
            self.claims_layer = json.loads(cp.read_text(encoding="utf-8"))
        # ... communities, document list from ingested/
```

### Pattern 2: SSE Streaming for Chat

**What:** Use Server-Sent Events to stream Claude responses token-by-token to the browser.
**When to use:** For the `/api/chat` endpoint.
**Example:**
```python
# api_chat.py
from anthropic import Anthropic
from sse_starlette.sse import EventSourceResponse
import json

client = Anthropic()  # reads ANTHROPIC_API_KEY from env

async def chat_stream(question: str, context: str):
    """Stream Claude response as SSE events."""
    async def event_generator():
        with client.messages.stream(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=build_system_prompt(context),
            messages=[{"role": "user", "content": question}],
        ) as stream:
            for text in stream.text_stream:
                yield {"data": json.dumps({"type": "text", "content": text})}
        yield {"data": json.dumps({"type": "done"})}
    return EventSourceResponse(event_generator())
```

### Pattern 3: Vanilla JS Module Organization

**What:** Separate JS files for each panel, loaded as ES modules.
**When to use:** For the frontend SPA.
**Example:**
```html
<!-- index.html -->
<script type="module" src="/static/app.js"></script>
```
```javascript
// app.js
import { initChat } from './chat.js';
import { initGraph } from './graph.js';
import { initSources } from './sources.js';

document.addEventListener('DOMContentLoaded', () => {
    initChat();
    initGraph();
    initSources();
});
```

### Pattern 4: Citation Linking (Chat -> Source Panel)

**What:** Claude responses include `[Contract Name]` citations. Frontend parses these into clickable links that open the Sources panel and scroll to the referenced document/section.
**When to use:** For D-11 and D-19.
**Example:**
```javascript
// chat.js - post-process rendered markdown
function linkifyCitations(html) {
    // Match [Document Name] patterns
    return html.replace(/\[([^\]]+)\]/g, (match, name) => {
        const docId = nameToDocId(name);
        if (docId) {
            return `<a href="#" class="citation-link" data-doc="${docId}">${match}</a>`;
        }
        return match;
    });
}
```

### Pattern 5: Context Assembly for Claude

**What:** Build a system prompt that includes the full KG summary + claims layer + matched source text chunks.
**When to use:** For every chat request per D-09.
**Key consideration:** graph_data.json for 62+ contracts could be large. Must measure token count and potentially summarize (entity counts by type, top findings, community labels) rather than dumping raw JSON if it exceeds context limits.
**Example:**
```python
# system_prompt.py
def build_system_prompt(data: WorkbenchData) -> str:
    """Assemble system prompt with KG context."""
    parts = [PERSONA_PROMPT]  # D-13 analyst persona

    # Summarize KG structure
    nodes = data.graph_data.get("nodes", [])
    by_type = {}
    for n in nodes:
        t = n.get("entity_type", "UNKNOWN")
        by_type.setdefault(t, []).append(n)
    parts.append(format_kg_summary(by_type))

    # Include claims layer (conflicts, gaps, risks)
    parts.append(format_claims(data.claims_layer))

    # Full node details as structured data
    parts.append(json.dumps(nodes, indent=2))

    return "\n\n".join(parts)
```

### Anti-Patterns to Avoid

- **WebSocket for chat streaming:** SSE is simpler, unidirectional (server->client is all we need), and works without reconnection logic. Chat requests go via POST, responses stream via SSE. Do not use WebSocket.
- **Embedding original PDFs in the browser:** D-18 explicitly says "No embedded PDF rendering." Show extracted text, link to original PDF in new tab.
- **Custom markdown renderer:** Use a lightweight JS markdown library or the browser's built-in capabilities. Do not hand-roll markdown parsing.
- **Database for chat history:** D-08 says session-only. Keep messages in JS array in the browser. Lost on page reload -- that is intentional.
- **Building a REST API for every graph operation:** The graph data is loaded once. Serve it as a single JSON blob; let the frontend filter/search client-side. Minimize API roundtrips.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Markdown rendering in chat | Custom markdown parser | marked.js (CDN) or showdown.js (CDN) | Tables, code blocks, lists -- tons of edge cases |
| SSE protocol | Custom chunked response | sse-starlette EventSourceResponse | Keep-alive, reconnection, W3C spec compliance |
| Graph visualization | Custom SVG/canvas renderer | vis.js (already bundled) | Physics simulation, zoom/pan, node selection all built-in |
| Code highlighting in chat | Custom syntax highlighter | Omit for v1; markdown tables sufficient | Not needed for contract analysis responses |

**Key insight:** The frontend is vanilla HTML/JS but should still use CDN-loaded micro-libraries for markdown rendering. Parsing markdown with regex is a classic hand-rolling trap.

## Common Pitfalls

### Pitfall 1: Claude Context Window Overflow
**What goes wrong:** Full graph_data.json for 62+ contracts with all node attributes could exceed Claude Sonnet's context window (200K tokens), especially when combined with source text chunks.
**Why it happens:** D-09 says "full KG + relevant doc chunks as context." Raw JSON for hundreds of entities/relations is verbose.
**How to avoid:** Measure graph_data.json size at startup. If >50K tokens, use a summarized format: entity names grouped by type, key attributes only, community labels. Include full claims_layer.json (smaller). For source chunks, retrieve only relevant ones per query using keyword matching against the question.
**Warning signs:** Chat responses are slow or truncated; API errors mentioning token limits.

### Pitfall 2: SSE Connection Drops During Long Responses
**What goes wrong:** Browser closes the SSE connection after ~30 seconds of inactivity, or proxies/firewalls timeout.
**Why it happens:** Keep-alive not configured; Claude may have pauses between tokens during complex reasoning.
**How to avoid:** sse-starlette sends keep-alive pings by default (every 15s). Ensure ping interval is configured. On the frontend, handle reconnection gracefully -- show "reconnecting" state if connection drops.
**Warning signs:** Responses appear truncated mid-sentence.

### Pitfall 3: Synchronous Anthropic Client in Async FastAPI
**What goes wrong:** Using the synchronous `Anthropic()` client blocks the event loop, freezing all other requests.
**Why it happens:** FastAPI is async, but `client.messages.stream()` is synchronous by default.
**How to avoid:** Use `AsyncAnthropic()` client with `async with client.messages.stream(...)` for non-blocking streaming. Or run the synchronous client in a thread pool via `asyncio.to_thread()`.
**Warning signs:** The server becomes unresponsive during chat responses; graph/source API calls hang while chat is streaming.

### Pitfall 4: vis.js Performance with Large Graphs
**What goes wrong:** vis.js becomes sluggish or freezes with >500 nodes due to physics simulation.
**Why it happens:** The contract KG for 62+ documents could have hundreds of nodes and thousands of edges.
**How to avoid:** Disable physics after initial stabilization (`network.once('stabilized', () => network.setOptions({physics: false}))`). Use `barnesHut` solver (default, most efficient). Implement node hiding via entity type toggles to reduce visible nodes. Consider showing only a subset (e.g., first 200 nodes) with a "show more" control.
**Warning signs:** Browser tab becomes unresponsive when opening graph panel.

### Pitfall 5: Markdown Citation Parsing Conflicts
**What goes wrong:** `[Contract Name]` citation format collides with markdown link syntax `[text](url)`.
**Why it happens:** Standard markdown treats `[text]` as potential link text.
**How to avoid:** Post-process rendered HTML rather than raw markdown. After markdown rendering, find remaining `[text]` patterns that weren't converted to links, and convert them to citation links. Or use a distinctive citation format in the system prompt (e.g., `[[Contract Name]]` double brackets).
**Warning signs:** Citations render as broken links or disappear from rendered output.

### Pitfall 6: Static File Serving Path Resolution
**What goes wrong:** FastAPI's `StaticFiles` mount doesn't find the HTML/CSS/JS files when the server is launched from a different working directory.
**Why it happens:** Relative paths resolve from CWD, not from the script location.
**How to avoid:** Use `Path(__file__).parent / "static"` for the static files directory. This follows existing codebase convention of `pathlib.Path(__file__).parent` for relative imports.
**Warning signs:** 404 errors for all static assets.

## Code Examples

### FastAPI App Skeleton

```python
# Source: FastAPI official docs + project conventions
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path

app = FastAPI(title="Sample Contract Analysis Workbench")

STATIC_DIR = Path(__file__).parent / "static"

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Serve index.html at root
@app.get("/")
async def root():
    from fastapi.responses import FileResponse
    return FileResponse(STATIC_DIR / "index.html")
```

### Anthropic Streaming with AsyncAnthropic

```python
# Source: anthropic SDK docs, messages_stream.py example
from anthropic import AsyncAnthropic

client = AsyncAnthropic()  # reads ANTHROPIC_API_KEY from env

async def stream_chat(system: str, user_message: str):
    async with client.messages.stream(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": user_message}],
    ) as stream:
        async for text in stream.text_stream:
            yield text
```

### vis.js Network Setup

```javascript
// Source: vis.js docs + existing lib/vis-9.1.2/
const container = document.getElementById('graph-container');
const data = { nodes: new vis.DataSet(nodes), edges: new vis.DataSet(edges) };
const options = {
    physics: {
        solver: 'barnesHut',
        barnesHut: { gravitationalConstant: -3000, springLength: 150 },
        stabilization: { iterations: 100 }
    },
    nodes: { shape: 'dot', font: { size: 12 } },
    edges: { arrows: 'to', smooth: { type: 'continuous' } },
    interaction: { hover: true, tooltipDelay: 200 }
};
const network = new vis.Network(container, data, options);

// Disable physics after stabilization for performance
network.once('stabilized', () => {
    network.setOptions({ physics: false });
});
```

### SSE Event Source in Browser

```javascript
// Source: W3C EventSource spec
async function sendMessage(question) {
    const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, history: chatHistory })
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        // Parse SSE events from buffer
        const lines = buffer.split('\n');
        buffer = lines.pop();
        for (const line of lines) {
            if (line.startsWith('data: ')) {
                const data = JSON.parse(line.slice(6));
                if (data.type === 'text') appendToMessage(data.content);
                if (data.type === 'done') finalizeMessage();
            }
        }
    }
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| FastAPI StreamingResponse for SSE | FastAPI 0.135+ native EventSourceResponse OR sse-starlette | FastAPI 0.135.0 (2025) | Built-in SSE support, but sse-starlette still more feature-rich |
| Synchronous Anthropic client | AsyncAnthropic with async streaming | anthropic SDK 0.20+ | Non-blocking streaming critical for FastAPI async |
| anthropic `completion()` API | `messages.stream()` API | 2024 | Messages API is the current standard; Completions deprecated |

**Deprecated/outdated:**
- `anthropic.Anthropic().completions.create()` -- use `messages.create()` or `messages.stream()`
- `from starlette.responses import StreamingResponse` for SSE -- use `sse-starlette` or FastAPI native SSE

## Open Questions

1. **Graph data size vs. Claude context window**
   - What we know: Claude Sonnet has 200K token context. Graph for 62+ contracts is of unknown size.
   - What's unclear: Whether raw graph_data.json fits within context limits alongside system prompt and source chunks.
   - Recommendation: Measure at startup, implement tiered context (summary vs. full) with a threshold around 50K tokens for graph data.

2. **Markdown rendering library choice**
   - What we know: Need tables, lists, code blocks, bold/italic at minimum. No build step (vanilla JS).
   - What's unclear: Whether marked.js or showdown.js is better for CDN-loaded use without build tools.
   - Recommendation: Use marked.js via CDN -- smaller, faster, widely used. ~28KB minified.

3. **Multi-turn chat context management**
   - What we know: D-08 says session-only history. System prompt includes full KG context.
   - What's unclear: How to handle multi-turn conversations without exceeding token limits (KG context + growing chat history).
   - Recommendation: Include last N messages (e.g., 10) in the messages array. Truncate oldest messages when total approaches limit.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.11+ | All | Yes | 3.11.0 | -- |
| uvicorn | Server | Yes | 0.35.0 | -- |
| anthropic SDK | Chat | Yes | 0.55.0 | -- |
| vis.js | Graph panel | Yes | 9.1.2 (bundled) | -- |
| FastAPI | Server | No (not installed in env) | -- | Install via uv |
| sse-starlette | Chat streaming | No | -- | Install via uv, or use FastAPI 0.135+ native SSE |
| httpx | Tests | No | -- | Install via uv |
| marked.js | Markdown rendering | No (CDN) | -- | Load from CDN at runtime |

**Missing dependencies with no fallback:**
- FastAPI, sse-starlette, httpx must be installed via `uv pip install`

**Missing dependencies with fallback:**
- marked.js loaded from CDN, no install needed. Fallback: showdown.js CDN or basic innerHTML (degraded)

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (existing) |
| Config file | none (uses pytest defaults, run from project root) |
| Quick run command | `python -m pytest tests/test_workbench.py -x -v` |
| Full suite command | `python -m pytest tests/ -v` |

### Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DASH-01 | Web interface serves and graph data API returns filterable nodes | unit + integration | `python -m pytest tests/test_workbench.py::test_graph_api -x` | No -- Wave 0 |
| DASH-02 | Entity type filtering returns correct subsets | unit | `python -m pytest tests/test_workbench.py::test_entity_filter -x` | No -- Wave 0 |
| D-20 | Domain schema has new entity/relation types | unit | `python -m pytest tests/test_workbench.py::test_schema_expansion -x` | No -- Wave 0 |
| D-09 | Chat endpoint returns streaming response with KG context | integration | `python -m pytest tests/test_workbench.py::test_chat_stream -x` | No -- Wave 0 |
| D-26 | Tests use synthetic fixtures, mock Claude API | unit | `python -m pytest tests/test_workbench.py -x` | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/test_workbench.py -x -v`
- **Per wave merge:** `python -m pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_workbench.py` -- covers DASH-01, DASH-02, D-09, D-20, D-26
- [ ] `tests/fixtures/sample_graph_data.json` -- synthetic KG data for tests
- [ ] `tests/fixtures/sample_claims_layer.json` -- synthetic claims data for tests
- [ ] `tests/fixtures/sample_ingested/` -- sample .txt files for source viewer tests
- [ ] Install: `uv pip install fastapi uvicorn anthropic sse-starlette httpx`

## Sources

### Primary (HIGH confidence)
- PyPI registry -- verified versions: FastAPI 0.135.2, uvicorn 0.42.0, anthropic 0.87.0, sse-starlette 3.3.4, httpx 0.28.1
- Existing codebase -- `lib/vis-9.1.2/vis-network.min.js` bundled, `scripts/run_sift.py` graph data patterns
- `skills/contract-extraction/domain.yaml` -- current schema to expand
- `05-CONTEXT.md` and `05-UI-SPEC.md` -- locked decisions and visual contract

### Secondary (MEDIUM confidence)
- [FastAPI SSE docs](https://fastapi.tiangolo.com/tutorial/server-sent-events/) -- native SSE support in 0.135+
- [Anthropic SDK streaming example](https://github.com/anthropics/anthropic-sdk-python/blob/main/examples/messages_stream.py) -- `messages.stream()` pattern
- [Anthropic streaming docs](https://platform.claude.com/docs/en/build-with-claude/streaming) -- SSE streaming protocol

### Tertiary (LOW confidence)
- marked.js CDN availability and exact bundle size -- based on general web knowledge, needs verification at implementation time

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries verified on PyPI, versions confirmed, vis.js already bundled
- Architecture: HIGH -- FastAPI + SSE + vis.js is well-established pattern, project conventions clear from prior phases
- Pitfalls: HIGH -- context overflow, async client, vis.js performance are well-documented issues
- Schema expansion: HIGH -- domain.yaml structure is well-understood from Phase 1

**Research date:** 2026-03-31
**Valid until:** 2026-04-30 (stable libraries, locked decisions)
