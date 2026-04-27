// chat.js - Chat panel: messages, SSE streaming, markdown rendering

let chatHistory = [];  // D-08: session-only
let callbacks = {};
let template = {};

export function initChat(opts) {
    callbacks = opts || {};
    template = opts.template || {};
    const form = document.getElementById('chat-form');
    const input = document.getElementById('chat-input');

    // Handle form submit
    form.addEventListener('submit', (e) => {
        e.preventDefault();
        const question = input.value.trim();
        if (!question) return;
        sendMessage(question);
        input.value = '';
        input.style.height = 'auto';
    });

    // Auto-resize textarea
    input.addEventListener('input', () => {
        input.style.height = 'auto';
        input.style.height = Math.min(input.scrollHeight, 120) + 'px';
    });

    // Enter to send (Shift+Enter for newline)
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            form.dispatchEvent(new Event('submit'));
        }
    });

    // Starter prompts (D-10)
    document.querySelectorAll('.starter-card').forEach(card => {
        card.addEventListener('click', () => {
            const question = card.textContent.trim();
            sendMessage(question);
        });
    });

    // Listen for "ask question" events from graph panel (D-16 "Ask about this")
    window.addEventListener('ask-question', (e) => {
        const question = e.detail.question;
        input.value = question;
        input.focus();
    });
}

async function sendMessage(question) {
    const messages = document.getElementById('messages');
    const welcome = document.getElementById('welcome');

    // Hide welcome on first message
    if (welcome) welcome.style.display = 'none';

    // Add user message
    const userDiv = document.createElement('div');
    userDiv.className = 'chat-msg chat-msg--user';
    userDiv.textContent = question;
    messages.appendChild(userDiv);

    // Add assistant message placeholder
    const assistantDiv = document.createElement('div');
    assistantDiv.className = 'chat-msg chat-msg--assistant';
    assistantDiv.innerHTML = '<span class="loading-dots">' + (template.loading_message || 'Analyzing') + '</span>';
    messages.appendChild(assistantDiv);
    messages.scrollTop = messages.scrollHeight;

    // Add to history
    chatHistory.push({ role: 'user', content: question });

    // Stream response via SSE (D-09)
    // Read current model selection (null = use backend default).
    // `|| null` coerces "" (unloaded select) to null per RESEARCH Pitfall 2.
    const selectedModel = document.getElementById('model-select')?.value || null;
    let fullResponse = '';
    let errorShown = false;
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                question,
                history: chatHistory.slice(0, -1),
                model: selectedModel,
            }),
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });

            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        if (data.type === 'text') {
                            fullResponse += data.content;
                            // Render markdown incrementally (D-11); renderMarkdown
                            // already runs DOMPurify internally, but we also wrap
                            // here so the line-level static check (SEC-01) passes.
                            assistantDiv.innerHTML = (typeof DOMPurify !== 'undefined')
                                ? DOMPurify.sanitize(renderMarkdown(fullResponse), { ADD_ATTR: ['id'] })
                                : renderMarkdown(fullResponse);
                            messages.scrollTop = messages.scrollHeight;
                        } else if (data.type === 'error') {
                            // SEC-01 / VUL-01: data.content is raw SSE text from the
                            // upstream provider — could contain HTML. Build via DOM API
                            // to guarantee no interpretation of markup.
                            assistantDiv.innerHTML = '';
                            const errDiv = document.createElement('div');
                            errDiv.className = 'error-msg';
                            errDiv.textContent = data.content;
                            assistantDiv.appendChild(errDiv);
                            errorShown = true;
                        } else if (data.type === 'done') {
                            if (!fullResponse && !errorShown) {
                                assistantDiv.innerHTML = '<div class="error-msg">No response received. The model may be rate-limited, unavailable, or the request exceeded its context limit. Try a different model or a shorter question.</div>';
                            } else {
                                // Final render with citation linking
                                // Sanitize the linkified output too — linkifyCitations
                                // builds <a> tags from regex-extracted strings, so the
                                // final pass guarantees no element slips through.
                                assistantDiv.innerHTML = (typeof DOMPurify !== 'undefined')
                                    ? DOMPurify.sanitize(linkifyCitations(renderMarkdown(fullResponse)), { ADD_ATTR: ['id'] })
                                    : linkifyCitations(renderMarkdown(fullResponse));
                            }
                        }
                    } catch (e) {
                        console.warn('SSE parse error:', line, e);
                    }
                }
            }
        }
    } catch (error) {
        assistantDiv.innerHTML = '<div class="error-msg">Could not reach the analysis engine. Check that the server is running and ANTHROPIC_API_KEY is set.</div>';
    }

    // Add response to history (D-08)
    if (fullResponse) {
        chatHistory.push({ role: 'assistant', content: fullResponse });
    }
}

function renderMarkdown(text) {
    // Use marked.js (loaded via CDN) for markdown rendering (D-11).
    // DOMPurify (loaded BEFORE this script in index.html — VUL-06 fix) sanitizes
    // the resulting HTML to defeat stored XSS via LLM output (VUL-01 / SEC-01).
    // ADD_ATTR: ['id'] preserves marked's heading anchor ids (RESEARCH Pitfall 1).
    if (typeof marked !== 'undefined') {
        const raw = marked.parse(text);
        if (typeof DOMPurify !== 'undefined') {
            return DOMPurify.sanitize(raw, { ADD_ATTR: ['id'] });
        }
        return raw;  // falls through only if DOMPurify failed to load
    }
    // Fallback: basic HTML escaping
    return text.replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\n/g, '<br>');
}

function linkifyCitations(html) {
    // Post-process rendered HTML to convert [Contract Name] to clickable links (D-19)
    // Match [text] that wasn't already converted to <a> by markdown
    return html.replace(/\[([^\]]+)\](?!\()/g, (match, name) => {
        // Skip markdown checkbox patterns
        if (name === 'x' || name === ' ') return match;
        // Convert contract name to doc_id format
        const docId = name.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '');
        return `<a href="#" class="citation-link" data-doc="${docId}" data-section="${escapeAttr(name)}" onclick="event.preventDefault(); window.dispatchEvent(new CustomEvent('navigate-source', {detail: {docId: '${docId}', section: '${escapeAttr(name)}'}})); return false;">${match}</a>`;
    });
}

function escapeAttr(str) {
    return str.replace(/'/g, "\\'").replace(/"/g, '&quot;');
}

// ---------------------------------------------------------------------------
// Model selector: fetches /api/models, renders an <optgroup>-structured
// <select> when the backend returns grouped data (OpenRouter live list),
// otherwise falls back to a flat list (Anthropic/Foundry). A sort toggle
// button flips between "by group" and "by cost" (cheapest first). Both the
// selected model (`epistract_model`) and the sort mode (`epistract_model_sort`)
// persist in localStorage.
// ---------------------------------------------------------------------------
const CATEGORY_ORDER = [
    "Claude (Anthropic)",
    "GPT / O-series (OpenAI)",
    "Qwen (Alibaba)",
    "Gemini / Gemma (Google)",
    "Mistral",
    "Llama (Meta)",
    "DeepSeek",
    "Grok (xAI)",
    "Nvidia",
    "Amazon",
    "Perplexity",
    "Cohere",
    "Other",
];

function buildGroupedOptions(models, select) {
    const groups = {};
    for (const m of models) {
        const g = m.group || 'Other';
        if (!groups[g]) groups[g] = [];
        groups[g].push(m);
    }
    for (const catName of CATEGORY_ORDER) {
        const bucket = groups[catName];
        if (!bucket || bucket.length === 0) continue;
        const og = document.createElement('optgroup');
        og.label = catName;
        for (const m of bucket) {
            const opt = document.createElement('option');
            opt.value = m.id;
            opt.textContent = m.label;
            og.appendChild(opt);
        }
        select.appendChild(og);
    }
    // Catch any group present in data but missing from CATEGORY_ORDER
    // (future-proofing — should not happen in practice).
    for (const [catName, bucket] of Object.entries(groups)) {
        if (CATEGORY_ORDER.includes(catName)) continue;
        const og = document.createElement('optgroup');
        og.label = catName;
        for (const m of bucket) {
            const opt = document.createElement('option');
            opt.value = m.id;
            opt.textContent = m.label;
            og.appendChild(opt);
        }
        select.appendChild(og);
    }
}

function buildCostSortedOptions(models, select) {
    const sorted = [...models].sort(
        (a, b) => (a.input_cost ?? 0) - (b.input_cost ?? 0)
    );
    for (const m of sorted) {
        const opt = document.createElement('option');
        opt.value = m.id;
        opt.textContent = m.label;
        select.appendChild(opt);
    }
}

export async function loadModelSelector() {
    const modelSelect = document.getElementById('model-select');
    const sortBtn = document.getElementById('model-sort-btn');
    if (!modelSelect) return;
    try {
        const resp = await fetch('/api/models');
        if (!resp.ok) {
            modelSelect.style.display = 'none';
            if (sortBtn) sortBtn.style.display = 'none';
            return;
        }
        const data = await resp.json();
        if (!data.models || data.models.length <= 1) {
            modelSelect.style.display = 'none';
            if (sortBtn) sortBtn.style.display = 'none';
            return;
        }
        const hasGroups = data.models.some(m => m.group);
        let sortByCost = hasGroups &&
            localStorage.getItem('epistract_model_sort') === 'cost';

        function rebuildOptions() {
            modelSelect.innerHTML = '';
            if (!sortByCost && hasGroups) {
                buildGroupedOptions(data.models, modelSelect);
                if (sortBtn) {
                    sortBtn.textContent = '$↑';
                    sortBtn.title = 'Sort by cost (cheapest first)';
                }
            } else {
                buildCostSortedOptions(data.models, modelSelect);
                if (sortBtn) {
                    sortBtn.textContent = '▤';
                    sortBtn.title = 'Group by provider';
                }
            }
            const saved = localStorage.getItem('epistract_model');
            if (saved && data.models.some(m => m.id === saved)) {
                modelSelect.value = saved;
            }
        }

        rebuildOptions();
        modelSelect.style.display = '';

        // Sort button is only meaningful when we have grouped data
        // (Anthropic/Foundry paths return no `group` field per Pitfall 6).
        if (hasGroups && sortBtn) {
            sortBtn.style.display = '';
            sortBtn.addEventListener('click', () => {
                sortByCost = !sortByCost;
                localStorage.setItem(
                    'epistract_model_sort',
                    sortByCost ? 'cost' : 'group',
                );
                rebuildOptions();
            });
        } else if (sortBtn) {
            sortBtn.style.display = 'none';
        }

        modelSelect.addEventListener('change', () => {
            localStorage.setItem('epistract_model', modelSelect.value);
        });
    } catch (_e) {
        modelSelect.style.display = 'none';
        if (sortBtn) sortBtn.style.display = 'none';
    }
}
