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
                            // Render markdown incrementally (D-11)
                            assistantDiv.innerHTML = renderMarkdown(fullResponse);
                            messages.scrollTop = messages.scrollHeight;
                        } else if (data.type === 'error') {
                            assistantDiv.innerHTML = `<div class="error-msg">${data.content}</div>`;
                        } else if (data.type === 'done') {
                            // Final render with citation linking
                            assistantDiv.innerHTML = linkifyCitations(renderMarkdown(fullResponse));
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
    // Use marked.js (loaded via CDN) for markdown rendering (D-11)
    if (typeof marked !== 'undefined') {
        return marked.parse(text);
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
// Model selector: fetches /api/models, populates <select>, persists to
// localStorage under key `epistract_model`. Hidden when <=1 model available
// (Azure Foundry single-deployment case) per RESEARCH Pitfall 4.
// ---------------------------------------------------------------------------
export async function loadModelSelector() {
    const modelSelect = document.getElementById('model-select');
    if (!modelSelect) return;
    try {
        const resp = await fetch('/api/models');
        if (!resp.ok) {
            modelSelect.style.display = 'none';
            return;
        }
        const data = await resp.json();
        if (!data.models || data.models.length <= 1) {
            // Foundry single-deployment OR no provider configured.
            modelSelect.style.display = 'none';
            return;
        }
        // Populate options
        data.models.forEach(m => {
            const opt = document.createElement('option');
            opt.value = m.id;
            opt.textContent = m.label;
            modelSelect.appendChild(opt);
        });
        // Restore persisted selection — validate against current list
        // (per RESEARCH Pitfall 3 — provider switch must not leak stale IDs).
        const saved = localStorage.getItem('epistract_model');
        if (saved && data.models.some(m => m.id === saved)) {
            modelSelect.value = saved;
        }
        modelSelect.style.display = '';
        modelSelect.addEventListener('change', () => {
            localStorage.setItem('epistract_model', modelSelect.value);
        });
    } catch (_e) {
        modelSelect.style.display = 'none';
    }
}
