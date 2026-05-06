// sidebar.js - Graph detail sidebar: slide-in panel for node and edge details.
// Exports: initSidebar, showNodeDetail, showEdgeDetail, hideSidebar
// SEC-01 / SIDEBAR-04: all graph data rendered via textContent — never via innerHTML.

// ---------------------------------------------------------------------------
// Module-level state
// ---------------------------------------------------------------------------
let sidebarEl = null;
let sidebarBody = null;


// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

export function initSidebar() {
    sidebarEl = document.getElementById('graph-detail-sidebar');
    if (!sidebarEl) {
        console.warn('graph-detail-sidebar element not found — sidebar.js not initialized');
        return;
    }
    sidebarBody = sidebarEl.querySelector('.graph-detail-sidebar__body');
}


export function showNodeDetail(nodeId, allNodes, allEdges, degreeMap, getEntityColor) {
    const node = allNodes.find(n => n.id === nodeId);
    if (!node) {
        _showErrorState('Unable to load details — node not found in graph. Try reloading the graph.');
        return;
    }

    const displayName = node.name || node.id;

    // Build header (replaces existing header children)
    _buildHeader(
        displayName,                          // title text
        node.entity_type || '',               // badge text
        getEntityColor(node.entity_type)      // badge color
    );

    // Build body content container
    const bodyFrag = document.createDocumentFragment();

    // --- Attributes section (degree row first per SIDEBAR-01) ---
    const attrsSection = _makeSection('Attributes');
    const attrs = node.attributes || {};
    const attrEntries = Object.entries(attrs).filter(([, v]) => v != null && v !== '');

    const degree = degreeMap[nodeId] || 0;
    attrsSection.appendChild(_makeAttrRow('Degree', String(degree)));

    if (attrEntries.length > 0) {
        for (const [k, v] of attrEntries) {
            attrsSection.appendChild(_makeAttrRow(k, String(v)));
        }
    } else {
        const empty = document.createElement('div');
        empty.className = 'graph-detail-sidebar__attr-value';
        empty.textContent = 'No attributes recorded.';
        attrsSection.appendChild(empty);
    }
    bodyFrag.appendChild(attrsSection);

    // --- Connected relations section (D-01: flat list, D-02: no cap) ---
    const relSection = _makeSection('Connected Relations');
    const connectedEdges = allEdges.filter(e => e.source === nodeId || e.target === nodeId);
    if (connectedEdges.length === 0) {
        const empty = document.createElement('div');
        empty.className = 'graph-detail-sidebar__attr-value';
        empty.textContent = 'No connected relations.';
        relSection.appendChild(empty);
    } else {
        const relList = document.createElement('ul');
        relList.className = 'graph-detail-sidebar__relations-list';
        for (const edge of connectedEdges) {
            const isSource = edge.source === nodeId;
            const otherId = isSource ? edge.target : edge.source;
            const otherNode = allNodes.find(n => n.id === otherId);

            const row = document.createElement('li');
            row.className = 'graph-detail-sidebar__relation-row';

            const typeSpan = document.createElement('span');
            typeSpan.className = 'graph-detail-sidebar__relation-type';
            typeSpan.textContent = edge.relation_type || '';
            row.appendChild(typeSpan);
            row.appendChild(document.createTextNode(' → '));
            const targetSpan = document.createElement('span');
            targetSpan.textContent = otherNode?.name || otherId || '';
            row.appendChild(targetSpan);
            relList.appendChild(row);
        }
        relSection.appendChild(relList);
    }
    bodyFrag.appendChild(relSection);

    // --- Source documents section ---
    const docsSection = _makeSection('Source Documents');
    const docs = node.source_documents || [];
    if (docs.length === 0) {
        const empty = document.createElement('div');
        empty.className = 'graph-detail-sidebar__attr-value';
        empty.textContent = 'No source documents linked.';
        docsSection.appendChild(empty);
    } else {
        for (const doc of docs) {
            const row = document.createElement('div');
            row.className = 'graph-detail-sidebar__attr-row';
            row.textContent = doc;
            docsSection.appendChild(row);
        }
    }
    bodyFrag.appendChild(docsSection);

    // --- Ask About This button (D-03: node sidebar only) ---
    const askBtn = document.createElement('button');
    askBtn.className = 'graph-detail-sidebar__ask-btn';
    askBtn.textContent = 'Ask about this';
    askBtn.addEventListener('click', () => {
        window.dispatchEvent(new CustomEvent('ask-question', {
            detail: {
                question: 'Tell me about ' + displayName + '. What are the key details and relationships?',
            },
        }));
    });
    bodyFrag.appendChild(askBtn);

    _replaceBodyContent(bodyFrag);
    _openSidebar();
}


export function showEdgeDetail(edgeId, visEdges, allNodes) {
    const edgeRecord = visEdges && visEdges.get(edgeId);
    if (!edgeRecord) {
        _showErrorState('Unable to load details — edge not found in graph. Try reloading the graph.');
        return;
    }
    const edge = edgeRecord._data || {};

    // Build header
    const titleEl = document.createElement('span');
    titleEl.className = 'graph-detail-sidebar__title';
    titleEl.style.fontFamily = 'var(--font-data)';
    titleEl.textContent = edge.relation_type || 'RELATION';

    // safeStatusClass: sanitize epistemic_status before className concatenation (T-09-02)
    const status = String(edge.epistemic_status || 'unknown').toLowerCase();
    const safeStatusClass = status.replace(/[^a-z0-9_-]/g, '');
    const badge = document.createElement('span');
    badge.className = 'epistemic-badge';
    if (safeStatusClass) {
        badge.classList.add('status-' + safeStatusClass);
    }
    badge.textContent = status;

    const closeBtn = _makeCloseButton();
    const headerEl = sidebarEl.querySelector('.graph-detail-sidebar__header');
    while (headerEl.firstChild) headerEl.removeChild(headerEl.firstChild);
    headerEl.appendChild(titleEl);
    headerEl.appendChild(badge);
    headerEl.appendChild(closeBtn);

    // Build body
    const bodyFrag = document.createDocumentFragment();

    // Source/target pair
    const sourceNode = allNodes.find(n => n.id === edge.source);
    const targetNode = allNodes.find(n => n.id === edge.target);
    const pair = document.createElement('div');
    pair.className = 'graph-detail-sidebar__pair';
    const srcEl = document.createElement('strong');
    srcEl.textContent = sourceNode?.name || edge.source || '';
    pair.appendChild(srcEl);
    pair.appendChild(document.createTextNode(' → '));
    const tgtEl = document.createElement('strong');
    tgtEl.textContent = targetNode?.name || edge.target || '';
    pair.appendChild(tgtEl);
    bodyFrag.appendChild(pair);

    // Evidence/mentions section
    const mentionsSection = _makeSection('Evidence');
    // WR-03: Use empty array when no mentions — do not fabricate a fallback object
    // from potentially-undefined edge fields (source_document, confidence, evidence).
    const mentions = Array.isArray(edge.mentions) && edge.mentions.length
        ? edge.mentions
        : [];

    if (!mentions.length) {
        const emptyEl = document.createElement('div');
        emptyEl.className = 'graph-detail-sidebar__evidence-empty';
        emptyEl.textContent = 'No evidence recorded for this relation.';
        mentionsSection.appendChild(emptyEl);
    }

    for (const m of mentions) {
        const block = document.createElement('div');
        block.className = 'graph-detail-sidebar__mention';

        const meta = document.createElement('div');
        meta.className = 'graph-detail-sidebar__mention-meta';

        const docEl = document.createElement('span');
        docEl.className = 'graph-detail-sidebar__mention-doc';
        docEl.textContent = m.source_document || '(unknown source)';
        meta.appendChild(docEl);

        const conf = typeof m.confidence === 'number' ? m.confidence : null;
        const confEl = document.createElement('span');
        confEl.className = 'graph-detail-sidebar__confidence-pill';
        confEl.textContent = conf !== null ? conf.toFixed(2) : '—';
        meta.appendChild(confEl);
        block.appendChild(meta);

        const ev = String(m.evidence || '').trim();
        if (ev) {
            const quote = document.createElement('blockquote');
            quote.className = 'graph-detail-sidebar__evidence';
            quote.textContent = ev;
            block.appendChild(quote);
        } else {
            const emptyEv = document.createElement('div');
            emptyEv.className = 'graph-detail-sidebar__evidence-empty';
            emptyEv.textContent = 'No evidence text recorded.';
            block.appendChild(emptyEv);
        }
        mentionsSection.appendChild(block);
    }
    bodyFrag.appendChild(mentionsSection);

    _replaceBodyContent(bodyFrag);
    _openSidebar();
}


export function hideSidebar() {
    sidebarEl?.classList.add('graph-detail-sidebar--closed');
}


// ---------------------------------------------------------------------------
// Private helpers
// ---------------------------------------------------------------------------

function _openSidebar() {
    sidebarEl?.classList.remove('graph-detail-sidebar--closed');
}


function _replaceBodyContent(newContent) {
    if (!sidebarBody) return;
    while (sidebarBody.firstChild) {
        sidebarBody.removeChild(sidebarBody.firstChild);
    }
    sidebarBody.appendChild(newContent);
    sidebarBody.scrollTop = 0;  // SIDEBAR-03: reset scroll on each new selection
}


function _buildHeader(titleText, badgeText, badgeColor) {
    const headerEl = sidebarEl?.querySelector('.graph-detail-sidebar__header');
    if (!headerEl) return;
    while (headerEl.firstChild) headerEl.removeChild(headerEl.firstChild);

    const titleEl = document.createElement('span');
    titleEl.className = 'graph-detail-sidebar__title';
    titleEl.textContent = titleText;

    const badge = document.createElement('span');
    badge.className = 'graph-detail-sidebar__badge entity-badge';
    badge.textContent = badgeText;
    badge.style.color = badgeColor;

    headerEl.appendChild(titleEl);
    headerEl.appendChild(badge);
    headerEl.appendChild(_makeCloseButton());
}


function _makeCloseButton() {
    const btn = document.createElement('button');
    btn.className = 'graph-detail-sidebar__close';
    btn.textContent = '×';  // × character — static literal, not graph data
    btn.setAttribute('aria-label', 'Close detail panel');
    btn.addEventListener('click', hideSidebar);
    return btn;
}


function _makeSection(labelText) {
    const section = document.createElement('div');
    section.className = 'graph-detail-sidebar__section';
    const label = document.createElement('div');
    label.className = 'graph-detail-sidebar__section-label';
    label.textContent = labelText;  // static string passed from caller
    section.appendChild(label);
    return section;
}


function _makeAttrRow(key, value) {
    const row = document.createElement('div');
    row.className = 'graph-detail-sidebar__attr-row';
    const keyEl = document.createElement('span');
    keyEl.className = 'graph-detail-sidebar__attr-key';
    keyEl.textContent = key + ':';
    const valEl = document.createElement('span');
    valEl.className = 'graph-detail-sidebar__attr-value';
    valEl.textContent = value;
    row.appendChild(keyEl);
    row.appendChild(valEl);
    return row;
}


function _showErrorState(message) {
    const errEl = document.createElement('div');
    errEl.className = 'graph-detail-sidebar__empty';
    errEl.textContent = message;  // static error strings only
    _replaceBodyContent(errEl);
    _openSidebar();
}
