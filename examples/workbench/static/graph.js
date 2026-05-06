import { initSidebar, showNodeDetail, showEdgeDetail, hideSidebar } from './sidebar.js';

// graph.js - Graph panel: vis.js network, search, entity type toggles

const PALETTE = ['#6366f1','#f59e0b','#ef4444','#10b981','#8b5cf6','#06b6d4','#64748b','#ec4899','#f97316','#14b8a6','#a855f7','#0ea5e9'];

let ENTITY_COLORS = {};
let network = null;
let allNodes = [];
let allEdges = [];
let degreeMap = {};          // hoisted for sidebar and Phase 10 neighbourhood highlight
let visNodes = null;
let visEdges = null;
let activeTypes = new Set();
let callbacks = {};
const pinnedNodes = new Set();
let _resizeListenerAttached = false;
let highlightedNodeId = null;             // currently highlighted node; null = no highlight active
let activeEpistemicStatuses = new Set();  // populated by buildEpistemicChips() (plan 03)
let confidenceThreshold = 0;             // populated by initConfidenceSlider() (plan 03)

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
            if (!entityResp.ok) {
                throw new Error(`Entity-types API returned ${entityResp.status} ${entityResp.statusText}`);
            }
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
        if (!resp.ok) {
            throw new Error(`Graph API returned ${resp.status} ${resp.statusText}`);
        }
        const data = await resp.json();
        allNodes = data.nodes || [];
        allEdges = data.edges || [];

        // Load claims data for severity filtering
        try {
            const claimsResp = await fetch('/api/graph/claims');
            if (!claimsResp.ok) {
                throw new Error(`Claims API returned ${claimsResp.status} ${claimsResp.statusText}`);
            }
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

    // WR-04: Close sidebar before rebuilding so stale content is not shown
    // alongside newly rebuilt graph data.
    hideSidebar();

    // Clear placeholder
    container.innerHTML = '';

    // Pre-compute node degree (total incoming + outgoing edges) for visual sizing.
    // Range: 8px (isolated node) to 24px (highest-degree hub). See UI-SPEC Degree-Based Node Sizing.
    degreeMap = {};
    allEdges.forEach(e => {
        degreeMap[e.source] = (degreeMap[e.source] || 0) + 1;
        degreeMap[e.target] = (degreeMap[e.target] || 0) + 1;
    });
    const maxDegree = Math.max(...Object.values(degreeMap), 1);

    const nodes = allNodes.map(n => {
        // CR-01: Build tooltip as an HTMLElement so vis.js renders it via DOM
        // rather than innerHTML, preventing XSS from untrusted node data.
        const tooltipEl = document.createElement('div');
        tooltipEl.textContent = `${n.entity_type}: ${n.name}`;
        return {
            id: n.id,
            label: n.name || n.id,
            color: getEntityColor(n.entity_type),
            title: tooltipEl,
            shape: 'dot',
            size: 8 + Math.round(((degreeMap[n.id] || 0) / maxDegree) * 16),
            font: {
                size: 12,
                color: '#1a1a1a',
                background: 'rgba(255, 255, 255, 0.85)',
            },
            _data: n,
        };
    });

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
    initSidebar();

    // Disable physics after stabilization (research pitfall 4)
    network.once('stabilized', () => {
        network.setOptions({ physics: false });
    });

    // Click node -> highlight neighbourhood + sidebar; click edge -> sidebar only;
    // canvas background -> clear highlight + close sidebar. (D-01..D-04)
    network.on('click', (params) => {
        if (params.nodes.length > 0) {
            const nodeId = params.nodes[0];

            // D-02: second click on already-highlighted node clears dim; sidebar stays open
            if (highlightedNodeId === nodeId) {
                clearHighlight();
                showNodeDetail(nodeId, allNodes, allEdges, degreeMap, getEntityColor);
                return;
            }

            // D-01: highlight this node's 1-hop neighbourhood; dim everything else
            clearHighlight();
            highlightedNodeId = nodeId;

            const neighbourIds = new Set(network.getConnectedNodes(nodeId));
            neighbourIds.add(nodeId);

            const connectedEdgeIds = new Set(network.getConnectedEdges(nodeId));

            // Dim non-neighbourhood nodes to opacity 0.15
            const nodeDims = visNodes.getIds()
                .filter(id => !neighbourIds.has(id))
                .map(id => ({ id, opacity: 0.15 }));
            if (nodeDims.length) visNodes.update(nodeDims);

            // Dim non-neighbourhood edges to opacity 0.15
            const edgeDims = visEdges.getIds()
                .filter(id => !connectedEdgeIds.has(id))
                .map(id => ({ id, color: { opacity: 0.15 } }));
            if (edgeDims.length) visEdges.update(edgeDims);

            // Open sidebar (Phase 09 unchanged)
            showNodeDetail(nodeId, allNodes, allEdges, degreeMap, getEntityColor);

        } else if (params.edges && params.edges.length > 0) {
            // D-04: edge click — sidebar only, no neighbourhood dim
            showEdgeDetail(params.edges[0], visEdges, allNodes);
        } else {
            // D-03: canvas background click — clear highlight AND close sidebar
            clearHighlight();
            hideSidebar();
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

    // Close sidebar on window resize so it does not float
    // in a stale DOM position (RESEARCH Pitfall 4).
    // CR-02: Guard against accumulating duplicate listeners on repeated buildGraph() calls.
    if (!_resizeListenerAttached) {
        window.addEventListener('resize', hideSidebar);
        _resizeListenerAttached = true;
    }
}

function filterGraph() {
    if (!visNodes) return;
    clearHighlight();

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

function clearHighlight() {
    if (!visNodes || !visEdges) return;
    const nodeRestores = visNodes.getIds().map(id => ({ id, opacity: 1.0 }));
    const edgeRestores = visEdges.getIds().map(id => ({ id, color: { opacity: 1.0 } }));
    visNodes.update(nodeRestores);
    visEdges.update(edgeRestores);
    highlightedNodeId = null;
}

