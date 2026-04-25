// graph.js - Graph panel: vis.js network, search, entity type toggles

const PALETTE = ['#6366f1','#f59e0b','#ef4444','#10b981','#8b5cf6','#06b6d4','#64748b','#ec4899','#f97316','#14b8a6','#a855f7','#0ea5e9'];

let ENTITY_COLORS = {};
let network = null;
let allNodes = [];
let allEdges = [];
let visNodes = null;
let visEdges = null;
let activeTypes = new Set();
let callbacks = {};
const pinnedNodes = new Set();

function getEntityColor(type) {
    if (ENTITY_COLORS[type]) return ENTITY_COLORS[type];
    // Assign from palette by alphabetical index
    const types = [...activeTypes].sort();
    const idx = types.indexOf(type);
    return PALETTE[idx >= 0 ? idx % PALETTE.length : 0];
}

export async function initGraph(opts) {
    callbacks = opts || {};
    const template = opts.template || {};
    ENTITY_COLORS = template.entity_colors || {};

    // Build toggle buttons dynamically from entity-types API
    const toggleContainer = document.getElementById('entity-toggles');
    if (toggleContainer) {
        try {
            const entityResp = await fetch('/api/graph/entity-types');
            const entityData = await entityResp.json();
            toggleContainer.innerHTML = '';
            for (const type of Object.keys(entityData.entity_types || {})) {
                activeTypes.add(type);
                const btn = document.createElement('button');
                btn.className = 'toggle-btn active';
                btn.dataset.type = type;
                btn.style.color = getEntityColor(type);
                btn.textContent = type.charAt(0) + type.slice(1).toLowerCase().replace(/_/g, ' ');
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
                toggleContainer.appendChild(btn);
            }
        } catch (e) {
            console.warn('Could not load entity types for toggles:', e);
        }
    }

    // Load graph data
    loadGraphData();

    // Search bar
    const searchInput = document.getElementById('graph-search');
    if (searchInput) {
        searchInput.addEventListener('input', () => filterGraph());
    }

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

    // Pre-compute node degree (total incoming + outgoing edges) for visual sizing.
    // Range: 8px (isolated node) to 24px (highest-degree hub). See UI-SPEC Degree-Based Node Sizing.
    const degreeMap = {};
    allEdges.forEach(e => {
        degreeMap[e.source] = (degreeMap[e.source] || 0) + 1;
        degreeMap[e.target] = (degreeMap[e.target] || 0) + 1;
    });
    const maxDegree = Math.max(...Object.values(degreeMap), 1);

    const nodes = allNodes.map(n => ({
        id: n.id,
        label: n.name || n.id,
        color: getEntityColor(n.entity_type),
        title: `${n.entity_type}: ${n.name}`,
        shape: 'dot',
        size: 8 + Math.round(((degreeMap[n.id] || 0) / maxDegree) * 16),
        font: {
            size: 12,
            color: '#1a1a1a',
            background: 'rgba(255, 255, 255, 0.85)',
        },
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
        scaling: {
            label: {
                enabled: true,
                min: 8,
                max: 14,
                maxVisible: 14,
                drawThreshold: 6,
            },
        },
        interaction: {
            hover: true,
            tooltipDelay: 200,
            multiselect: true,
            dragNodes: true,
            navigationButtons: false,
        },
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

    // Drag-to-pin: when user drops a node, pin it and apply the accent border.
    // Guard against canvas pan (params.nodes is empty for non-node drags).
    network.on('dragEnd', (params) => {
        if (!params.nodes || params.nodes.length === 0) return;
        const updates = params.nodes.map(nodeId => {
            pinnedNodes.add(nodeId);
            return {
                id: nodeId,
                fixed: { x: true, y: true },
                borderWidth: 2,
                color: {
                    border: '#4a6cf7',
                    highlight: { border: '#4a6cf7' },
                },
            };
        });
        visNodes.update(updates);
    });

    // Fit View: recenter all nodes in the viewport with a short animation.
    const fitBtn = document.getElementById('graph-fit-btn');
    if (fitBtn) {
        fitBtn.addEventListener('click', () => {
            network.fit({ animation: { duration: 400 } });
        });
    }

    // Reset Pins: unpin every pinned node and restore entity-type border color.
    const resetPinsBtn = document.getElementById('graph-reset-pins-btn');
    if (resetPinsBtn) {
        resetPinsBtn.addEventListener('click', () => {
            if (pinnedNodes.size === 0) return;
            const unfixUpdates = [...pinnedNodes].map(nodeId => {
                const node = allNodes.find(n => n.id === nodeId);
                const entityColor = getEntityColor(node?.entity_type || '');
                return {
                    id: nodeId,
                    fixed: false,
                    borderWidth: 1,
                    color: { border: entityColor, highlight: { border: entityColor } },
                };
            });
            visNodes.update(unfixUpdates);
            pinnedNodes.clear();
        });
    }

    // Close any open node popover on window resize so it does not float
    // in a stale DOM position (RESEARCH Pitfall 4).
    window.addEventListener('resize', hideNodePopover);
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
            <span class="entity-badge" style="color:${getEntityColor(node.entity_type)}">${node.entity_type}</span>
        </div>
        ${attrHtml ? `<div class="node-attrs">${attrHtml}</div>` : ''}
        ${docs.length ? `<div class="node-docs"><span class="label">Sources:</span> ${docs.join(', ')}</div>` : ''}
        <button class="ask-about-btn" onclick="window.dispatchEvent(new CustomEvent('ask-question', {detail: {question: 'Tell me about ${safeName}. What are the key details and relationships?'}}))">Ask about this</button>
    `;

    document.getElementById('graph-panel').appendChild(popover);
}

function hideNodePopover() {
    const existing = document.getElementById('node-popover');
    if (existing) existing.remove();
}
