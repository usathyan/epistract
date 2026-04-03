// graph.js - Graph panel: vis.js network, search, entity type toggles

const ENTITY_COLORS = {
    PARTY: '#6366f1', OBLIGATION: '#f59e0b', DEADLINE: '#ef4444',
    COST: '#10b981', SERVICE: '#8b5cf6', VENUE: '#06b6d4',
    CLAUSE: '#64748b', COMMITTEE: '#ec4899', PERSON: '#f97316',
    EVENT: '#14b8a6', STAGE: '#a855f7', ROOM: '#0ea5e9',
};

let network = null;
let allNodes = [];
let allEdges = [];
let visNodes = null;
let visEdges = null;
let activeTypes = new Set(Object.keys(ENTITY_COLORS));
let callbacks = {};

export function initGraph(opts) {
    callbacks = opts || {};

    // Load graph data
    loadGraphData();

    // Search bar
    const searchInput = document.getElementById('graph-search');
    if (searchInput) {
        searchInput.addEventListener('input', () => filterGraph());
    }

    // Entity type toggles
    document.querySelectorAll('.toggle-btn[data-type]').forEach(btn => {
        const type = btn.dataset.type;
        btn.classList.add('active');
        btn.style.color = ENTITY_COLORS[type] || '#666';
        btn.addEventListener('click', () => {
            if (activeTypes.has(type)) {
                activeTypes.delete(type);
                btn.classList.remove('active');
            } else {
                activeTypes.add(type);
                btn.classList.add('active');
            }
            filterGraph();
        });
    });

    // Severity filter
    const severityFilter = document.getElementById('severity-filter');
    if (severityFilter) {
        severityFilter.addEventListener('change', () => filterGraph());
    }

    // Resize handler for when panel opens
    window.addEventListener('graph-panel-opened', () => {
        if (network) {
            setTimeout(() => network.fit(), 100);
        }
    });
}

async function loadGraphData() {
    try {
        const resp = await fetch('/api/graph');
        const data = await resp.json();
        allNodes = data.nodes || [];
        allEdges = data.edges || [];

        // Load claims data for severity filtering
        try {
            const claimsResp = await fetch('/api/graph/claims');
            window._claimsData = await claimsResp.json();
        } catch (e) {
            window._claimsData = null;
        }

        buildGraph();
    } catch (e) {
        console.error('Failed to load graph data:', e);
        const container = document.getElementById('graph-container');
        if (container) container.innerHTML = '<p class="graph-placeholder">No entities match the current filters. Try broadening your search or toggling entity types.</p>';
    }
}

function buildGraph() {
    const container = document.getElementById('graph-container');
    if (!container || !window.vis) return;

    // Clear placeholder
    container.innerHTML = '';

    const nodes = allNodes.map(n => ({
        id: n.id,
        label: n.name || n.id,
        color: ENTITY_COLORS[n.entity_type] || '#999',
        title: `${n.entity_type}: ${n.name}`,
        shape: 'dot',
        size: 12,
        font: { size: 11, color: '#333' },
        _data: n,
    }));

    const edges = allEdges.map(e => ({
        from: e.source,
        to: e.target,
        label: e.relation_type,
        arrows: 'to',
        font: { size: 9, color: '#888' },
        smooth: { type: 'continuous' },
        _data: e,
    }));

    visNodes = new vis.DataSet(nodes);
    visEdges = new vis.DataSet(edges);

    const options = {
        physics: {
            solver: 'barnesHut',
            barnesHut: { gravitationalConstant: -3000, springLength: 150 },
            stabilization: { iterations: 100 },
        },
        interaction: { hover: true, tooltipDelay: 200 },
    };

    network = new vis.Network(container, { nodes: visNodes, edges: visEdges }, options);

    // Disable physics after stabilization (research pitfall 4)
    network.once('stabilized', () => {
        network.setOptions({ physics: false });
    });

    // Click node -> show popover (D-16)
    network.on('click', (params) => {
        if (params.nodes.length > 0) {
            showNodePopover(params.nodes[0], params.pointer.DOM);
        } else {
            hideNodePopover();
        }
    });

    // Double-click -> recenter on neighborhood (D-17)
    network.on('doubleClick', (params) => {
        if (params.nodes.length > 0) {
            const nodeId = params.nodes[0];
            const connectedNodes = network.getConnectedNodes(nodeId);
            network.fit({ nodes: [nodeId, ...connectedNodes], animation: { duration: 500 } });
        }
    });
}

function filterGraph() {
    if (!visNodes) return;

    const searchTerm = (document.getElementById('graph-search')?.value || '').toLowerCase();
    const severityFilter = document.getElementById('severity-filter')?.value || 'all';

    // Build set of node IDs involved in claims of selected severity
    let severityNodeIds = null;  // null means no filter (show all)
    if (severityFilter !== 'all' && window._claimsData) {
        severityNodeIds = new Set();
        const claims = window._claimsData;
        for (const section of ['conflicts', 'gaps', 'risks']) {
            for (const item of (claims[section] || [])) {
                if ((item.severity || '').toLowerCase() === severityFilter.toLowerCase()) {
                    // Collect affected entity IDs
                    if (item.entity_a) severityNodeIds.add(item.entity_a);
                    if (item.entity_b) severityNodeIds.add(item.entity_b);
                    for (const eid of (item.affected_entities || [])) {
                        severityNodeIds.add(eid);
                    }
                }
            }
        }
    }

    // Update node visibility
    const updates = allNodes.map(n => {
        const typeVisible = activeTypes.has(n.entity_type);
        const searchMatch = !searchTerm || (n.name || '').toLowerCase().includes(searchTerm);
        const severityMatch = !severityNodeIds || severityNodeIds.has(n.id);
        const hidden = !(typeVisible && searchMatch && severityMatch);
        return { id: n.id, hidden };
    });

    visNodes.update(updates);

    // Show empty state if all hidden
    const visibleCount = updates.filter(u => !u.hidden).length;
    const container = document.getElementById('graph-container');
    const emptyMsg = container?.querySelector('.graph-empty-msg');
    if (visibleCount === 0 && !emptyMsg) {
        const msg = document.createElement('p');
        msg.className = 'graph-placeholder graph-empty-msg';
        msg.textContent = 'No entities match the current filters. Try broadening your search or toggling entity types.';
        container?.appendChild(msg);
    } else if (visibleCount > 0 && emptyMsg) {
        emptyMsg.remove();
    }
}

function showNodePopover(nodeId, position) {
    const node = allNodes.find(n => n.id === nodeId);
    if (!node) return;

    hideNodePopover();

    const popover = document.createElement('div');
    popover.className = 'node-popover';
    popover.id = 'node-popover';
    popover.style.left = position.x + 'px';
    popover.style.top = position.y + 'px';

    const attrs = node.attributes || {};
    const docs = node.source_documents || [];

    let attrHtml = '';
    for (const [k, v] of Object.entries(attrs)) {
        if (v) attrHtml += `<div><span class="label">${k}:</span> <span class="data">${v}</span></div>`;
    }

    const safeName = (node.name || node.id).replace(/'/g, "\\'").replace(/"/g, '&quot;');

    popover.innerHTML = `
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
            <strong>${node.name || node.id}</strong>
            <span class="entity-badge" style="color:${ENTITY_COLORS[node.entity_type] || '#666'}">${node.entity_type}</span>
        </div>
        ${attrHtml ? `<div class="node-attrs">${attrHtml}</div>` : ''}
        ${docs.length ? `<div class="node-docs"><span class="label">Sources:</span> ${docs.join(', ')}</div>` : ''}
        <button class="ask-about-btn" onclick="window.dispatchEvent(new CustomEvent('ask-question', {detail: {question: 'Tell me about ${safeName}. What contracts mention it and what are the key obligations?'}}))">Ask about this</button>
    `;

    document.getElementById('graph-panel').appendChild(popover);
}

function hideNodePopover() {
    const existing = document.getElementById('node-popover');
    if (existing) existing.remove();
}
