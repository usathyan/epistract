// sources.js - Source panel: document list, text viewer, citation highlighting

let documents = [];
let currentDocId = null;

export function initSources() {
    loadDocumentList();

    // Listen for citation navigation from chat (D-19)
    window.addEventListener('navigate-source', (e) => {
        const { docId, section } = e.detail;
        openDocument(docId, section);
    });

    // Esc key closes sources panel (per UI-SPEC: "Esc returns to chat")
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            const sidePanel = document.getElementById('side-panel');
            if (sidePanel.classList.contains('open')) {
                sidePanel.classList.remove('open');
                document.getElementById('chat-input')?.focus();
            }
        }
    });
}

async function loadDocumentList() {
    try {
        const resp = await fetch('/api/sources');
        const data = await resp.json();
        documents = data.documents || [];
        renderDocumentList();
    } catch (e) {
        console.error('Failed to load document list:', e);
    }
}

function renderDocumentList() {
    const list = document.getElementById('doc-list');
    if (!list) return;

    if (documents.length === 0) {
        list.innerHTML = '<li class="doc-list-empty">No documents found. Run the extraction pipeline first.</li>';
        return;
    }

    list.innerHTML = documents.map(doc => {
        const safeDocId = doc.doc_id.replace(/'/g, "\\'");
        const displayName = doc.display_name || doc.filename || doc.doc_id;
        return `
        <li>
            <button class="doc-list-item" data-doc="${doc.doc_id}" onclick="window.dispatchEvent(new CustomEvent('navigate-source', {detail: {docId: '${safeDocId}'}}))">
                <span class="doc-name">${displayName}</span>
                <span class="doc-size">${formatSize(doc.size_bytes)}</span>
            </button>
        </li>`;
    }).join('');
}

async function openDocument(docId, highlightSection) {
    const viewer = document.getElementById('source-text');
    if (!viewer) return;

    // Try exact match first, then fuzzy match
    let matchedDocId = docId;
    const exactMatch = documents.find(d => d.doc_id === docId);
    if (!exactMatch) {
        // Fuzzy match: find doc whose ID contains keywords from docId
        const keywords = docId.split('_').filter(w => w.length > 2);
        const fuzzy = documents.find(d =>
            keywords.some(kw => d.doc_id.includes(kw))
        );
        if (fuzzy) matchedDocId = fuzzy.doc_id;
    }

    viewer.innerHTML = '<p class="loading">Loading document...</p>';
    currentDocId = matchedDocId;

    // Highlight active doc in list
    document.querySelectorAll('.doc-list-item').forEach(item => {
        item.classList.toggle('active', item.dataset.doc === matchedDocId);
    });

    try {
        const resp = await fetch(`/api/sources/${matchedDocId}`);
        const data = await resp.json();

        if (data.error) {
            viewer.innerHTML = `<p class="error-msg">${data.error}</p>`;
            return;
        }

        let text = escapeHtml(data.text);

        // Highlight section if provided (D-19)
        if (highlightSection) {
            const searchTerms = highlightSection.split(/\s+/).filter(w => w.length > 3);
            for (const term of searchTerms) {
                const regex = new RegExp(`(${escapeRegex(term)})`, 'gi');
                text = text.replace(regex, '<mark class="source-highlight">$1</mark>');
            }
        }

        viewer.innerHTML = `<pre class="source-viewer">${text}</pre>`;

        // Show PDF link
        const pdfLink = document.getElementById('pdf-link');
        if (pdfLink) {
            pdfLink.href = `/api/sources/pdf/${matchedDocId}`;
            pdfLink.style.display = 'inline';
        }

        // Scroll to first highlight
        const firstMark = viewer.querySelector('mark');
        if (firstMark) {
            firstMark.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    } catch (e) {
        viewer.innerHTML = '<p class="error-msg">Failed to load document.</p>';
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function escapeRegex(str) {
    return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function formatSize(bytes) {
    if (!bytes) return '';
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}
