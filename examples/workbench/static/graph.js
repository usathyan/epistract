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
let activeRelationTypes = new Set();      // populated by buildRelationTypeDropdown() (Phase 11)
let minDegreeThreshold = 0;               // populated by initMinDegreeSlider() (Phase 11)
let maxDegree = 0;                        // hoisted from buildGraph() local; read by initMinDegreeSlider() (Phase 11 D-10)

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
            // WR-04: clear stale entity types before re-populating so that
            // repeated initGraph calls (e.g. domain switch) do not accumulate
            // types from previous sessions, which would shift palette indices
            // and leave ghost types active in the filter Set.
            activeTypes.clear();
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
        buildEpistemicChips();
        initConfidenceSlider();
        buildRelationTypeDropdown();
        initMinDegreeSlider();
    } catch (e) {
        console.error('Failed to load graph data:', e);
        const container = document.getElementById('graph-container');
        // CR-01: use createElement/textContent instead of innerHTML (SEC-01)
        if (container) {
            const errMsg = document.createElement('p');
            errMsg.className = 'graph-placeholder';
            errMsg.textContent = 'Failed to load graph data. Please reload the page.';
            container.appendChild(errMsg);
        }
    }
}

let _btnListenersAttached = false;   // WR-02: guard fitBtn + resetPinsBtn duplicate registration
let _sliderListenerAttached = false; // WR-02: guard confidence slider duplicate registration
let _relationFilterListenerAttached = false; // WR-02: guard relation-type bulk-action listeners
let _degreeSliderListenerAttached = false;   // WR-02: guard min-degree slider duplicate registration

function buildGraph() {
    const container = document.getElementById('graph-container');
    if (!container || !window.vis) return;

    // WR-03: destroy previous network instance before creating a new one to
    // prevent canvas context leaks and competing requestAnimationFrame loops.
    if (network) {
        network.destroy();
        network = null;
    }

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
    maxDegree = Math.max(...Object.values(degreeMap), 1);

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

    // WR-02: Guard fit-view and reset-pins listeners against duplicate registration
    // on repeated buildGraph() calls (mirrors _resizeListenerAttached pattern).
    if (!_btnListenersAttached) {
        const fitBtn = document.getElementById('graph-fit-btn');
        if (fitBtn) {
            fitBtn.addEventListener('click', () => {
                network.fit({ animation: { duration: 400 } });
            });
        }

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

        _btnListenersAttached = true;
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
        // DEGREE-01: hide nodes whose total degree (degreeMap, computed at build time
        // across ALL edges, not currently visible edges) is below the threshold.
        const degreeOk = (degreeMap[n.id] || 0) >= minDegreeThreshold;
        const hidden = !(typeVisible && searchMatch && severityMatch && degreeOk);
        return { id: n.id, hidden };
    });

    visNodes.update(updates);

    // Edge visibility: epistemic status filter + confidence threshold filter (FILTER-01..03)
    // D-09: confidence slider filters edges only — node visibility is not affected here
    if (visEdges) {
        // WR-01: retrieve edge source data by ID from the DataSet record (_data field)
        // rather than correlating by positional index. vis.DataSet.getIds() does not
        // guarantee insertion order, so index-based correlation can silently apply
        // the wrong filter to the wrong edge after any DataSet mutation.
        const edgeUpdates = visEdges.getIds().map(edgeId => {
            const record = visEdges.get(edgeId);
            const e = record?._data;
            if (!e) return { id: edgeId, hidden: false };

            const status = e.epistemic_status;
            const confidence = e.confidence;

            // Epistemic filter:
            // - Edge with no status: always visible from this dimension
            // - Edge with status not in activeEpistemicStatuses: hidden (D-07: empty set hides all status-bearing edges)
            const hasStatus = status != null && status !== '';
            const epistemicHidden = hasStatus && !activeEpistemicStatuses.has(status);

            // Confidence filter:
            // - Scored edge (numeric confidence): hidden when confidence < threshold
            // - Unscored edge (null/undefined): hidden when threshold > 0.5 (D-12)
            const isScored = typeof confidence === 'number' && isFinite(confidence);
            const confidenceHidden = isScored
                ? confidence < confidenceThreshold
                : confidenceThreshold > 0.5;

            // RTYPE-03: hide edges whose relation_type is not in activeRelationTypes.
            // Edges with no relation_type field remain visible from this dimension
            // (mirrors the "hasStatus" guard for epistemic_status above).
            const hasRelType = e.relation_type != null && e.relation_type !== '';
            const relationHidden = hasRelType && !activeRelationTypes.has(e.relation_type);

            return { id: edgeId, hidden: epistemicHidden || confidenceHidden || relationHidden };
        });

        visEdges.update(edgeUpdates);
    }

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


function buildEpistemicChips() {
    const container = document.getElementById('epistemic-toggles');
    const section = document.getElementById('epistemic-filter');
    if (!container || !section) return;

    // Collect distinct non-empty epistemic_status values
    const statusSet = new Set();
    for (const edge of allEdges) {
        const s = edge.epistemic_status;
        if (s != null && s !== '') statusSet.add(s);
    }

    // D-08: hide section entirely when no epistemic data
    if (statusSet.size === 0) {
        section.style.display = 'none';
        return;
    }

    // Colour map for known epistemic statuses (from UI-SPEC.md)
    const CHIP_COLORS = {
        asserted:      { bg: '#dcfce7', text: '#166534' },
        prophetic:     { bg: '#ede9fe', text: '#5b21b6' },
        hypothesized:  { bg: '#fef3c7', text: '#92400e' },
        contested:     { bg: '#fee2e2', text: '#991b1b' },
        contradiction: { bg: '#fecaca', text: '#7f1d1d' },
        negative:      { bg: '#f3f4f6', text: '#374151' },
        speculative:   { bg: '#e0e7ff', text: '#3730a3' },
        unknown:       { bg: '#f3f4f6', text: '#6b7280' },
    };
    const FALLBACK_COLOR = { bg: '#f3f4f6', text: '#6b7280' };

    // Reset chip container and active set
    container.innerHTML = '';   // safe: clears own controlled container, not graph data
    activeEpistemicStatuses.clear();

    for (const status of [...statusSet].sort()) {
        // D-06: all chips active by default
        activeEpistemicStatuses.add(status);

        const colors = CHIP_COLORS[status] || FALLBACK_COLOR;
        const btn = document.createElement('button');
        btn.className = 'toggle-btn epistemic-chip active';
        btn.dataset.status = status;
        btn.style.backgroundColor = colors.bg;
        btn.style.color = colors.text;
        // XSS discipline: chip label via textContent only (SEC-01 / SIDEBAR-04 pattern)
        const label = status.charAt(0).toUpperCase() + status.slice(1).replace(/_/g, ' ');
        btn.textContent = label;

        btn.addEventListener('click', () => {
            if (activeEpistemicStatuses.has(status)) {
                activeEpistemicStatuses.delete(status);
                btn.classList.remove('active');
            } else {
                activeEpistemicStatuses.add(status);
                btn.classList.add('active');
            }
            filterGraph();
        });

        container.appendChild(btn);
    }
}


function initConfidenceSlider() {
    const slider = document.getElementById('confidence-slider');
    const readout = document.getElementById('confidence-value');
    if (!slider || !readout) return;

    // D-10: default at domain minimum observed confidence; if no scored edges, use 0
    let domainMin = 0;
    let foundScored = false;
    for (const edge of allEdges) {
        const c = edge.confidence;
        if (typeof c === 'number' && isFinite(c)) {
            domainMin = !foundScored ? c : Math.min(domainMin, c);
            foundScored = true;
        }
    }

    confidenceThreshold = domainMin;
    slider.value = String(domainMin);
    readout.textContent = domainMin.toFixed(2);

    // D-11: continuous 0.01 steps; update on every input event
    // WR-02: guard against duplicate registration on repeated initConfidenceSlider() calls.
    if (!_sliderListenerAttached) {
        slider.addEventListener('input', () => {
            confidenceThreshold = parseFloat(slider.value);
            readout.textContent = confidenceThreshold.toFixed(2);  // textContent only (SEC-01)
            filterGraph();
        });
        _sliderListenerAttached = true;
    }
}


// ---------------------------------------------------------------------------
// Phase 11: Relation type dropdown (RTYPE-01, RTYPE-02)
// Mirrors buildEpistemicChips() structure. Edge-only filter (RTYPE-03 wired
// in Plan 11.3 by extending filterGraph()).
// ---------------------------------------------------------------------------
function buildRelationTypeDropdown() {
    const container = document.getElementById('relation-type-panel');
    const section = document.getElementById('relation-type-filter');
    const selectAllBtn = document.getElementById('relation-select-all');
    const clearAllBtn = document.getElementById('relation-clear-all');
    if (!container || !section) return;

    // WR-04: state reset is the FIRST mutation (D-15)
    activeRelationTypes.clear();

    // Collect distinct non-empty relation_type values
    const typeSet = new Set();
    for (const edge of allEdges) {
        const t = edge.relation_type;
        if (t != null && t !== '') typeSet.add(t);
    }

    // D-04: hide section entirely when no relation_type data
    if (typeSet.size === 0) {
        section.style.display = 'none';
        return;
    }
    section.style.display = '';

    // Reset checkbox panel (clears own controlled container, no graph data)
    container.innerHTML = '';

    const sortedTypes = [...typeSet].sort();

    for (const relType of sortedTypes) {
        // D-03: all types active on load
        activeRelationTypes.add(relType);

        const row = document.createElement('label');

        const cb = document.createElement('input');
        cb.type = 'checkbox';
        cb.checked = true;
        cb.dataset.relationType = relType;   // raw snake_case value (D-07)

        const text = document.createElement('span');
        // D-06: humanize for display only — textContent (SEC-01 invariant)
        text.textContent = relType.replace(/_/g, ' ');

        row.appendChild(cb);
        row.appendChild(text);
        container.appendChild(row);

        cb.addEventListener('change', () => {
            if (cb.checked) {
                activeRelationTypes.add(relType);
            } else {
                activeRelationTypes.delete(relType);
            }
            filterGraph();
        });
    }

    // D-14 / WR-02: guard bulk-action listener registration across rebuilds.
    // Listeners re-read the panel's checkboxes at click-time so they remain
    // correct after any subsequent buildRelationTypeDropdown() rebuild.
    if (!_relationFilterListenerAttached && selectAllBtn && clearAllBtn) {
        selectAllBtn.addEventListener('click', () => {
            const panel = document.getElementById('relation-type-panel');
            if (!panel) return;
            const boxes = panel.querySelectorAll('input[type="checkbox"][data-relation-type]');
            activeRelationTypes.clear();
            boxes.forEach(box => {
                box.checked = true;
                activeRelationTypes.add(box.dataset.relationType);
            });
            filterGraph();
        });

        clearAllBtn.addEventListener('click', () => {
            // D-05: empty set hides all relation-type edges
            const panel = document.getElementById('relation-type-panel');
            if (!panel) return;
            const boxes = panel.querySelectorAll('input[type="checkbox"][data-relation-type]');
            activeRelationTypes.clear();
            boxes.forEach(box => { box.checked = false; });
            filterGraph();
        });

        _relationFilterListenerAttached = true;
    }
}


// ---------------------------------------------------------------------------
// Phase 11: Min-degree slider (DEGREE-01)
// Mirrors initConfidenceSlider() structure. Node-only filter (wired in
// Plan 11.3 by extending filterGraph() node pass).
// ---------------------------------------------------------------------------
function initMinDegreeSlider() {
    const slider = document.getElementById('min-degree-slider');
    const readout = document.getElementById('min-degree-value');
    if (!slider || !readout) return;

    // D-10: read maxDegree from module scope (set by buildGraph())
    slider.max = String(maxDegree);
    slider.min = '0';
    slider.step = '1';
    slider.value = '0';
    minDegreeThreshold = 0;
    readout.textContent = '0';   // textContent only (SEC-01)

    // WR-02: guard against duplicate registration on repeated init calls
    if (!_degreeSliderListenerAttached) {
        slider.addEventListener('input', () => {
            minDegreeThreshold = parseInt(slider.value, 10) || 0;
            readout.textContent = String(minDegreeThreshold);   // textContent only (SEC-01)
            filterGraph();
        });
        _degreeSliderListenerAttached = true;
    }
}
