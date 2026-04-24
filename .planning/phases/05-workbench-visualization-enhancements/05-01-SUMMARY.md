---
phase: 05-workbench-visualization-enhancements
plan: "01"
subsystem: workbench-graph-panel
tags: [vis-network, graph-visualization, node-labeling, degree-sizing, multiselect]
dependency_graph:
  requires: []
  provides: [enhanced-graph-node-config, label-scaling, degree-sizing, multiselect-interaction]
  affects: [examples/workbench/static/graph.js]
tech_stack:
  added: []
  patterns: [vis-network-font-background, vis-network-scaling-label, degree-centrality-sizing]
key_files:
  created: []
  modified:
    - examples/workbench/static/graph.js
decisions:
  - "Font background uses rgba(255,255,255,0.85) not opaque white — preserves readability on light BG, degrades gracefully on dark-mode"
  - "degreeMap clamped with Math.max(...values, 1) to prevent division-by-zero on edgeless graphs"
  - "Node dot size grep check conflict noted — font.size:12 from Task 1 causes grep -c 'size: 12' to return 1 not 0; semantic goal met"
metrics:
  duration: "~3 minutes"
  completed: "2026-04-24"
  tasks_completed: 2
  tasks_total: 2
  files_modified: 1
---

# Phase 05 Plan 01: Graph Panel Visual Legibility Summary

**One-liner:** Node label halo (rgba white background), auto-hide at zoom-out (drawThreshold 6px), degree-based size range 8-24px, and explicit multiselect/dragNodes/navigationButtons interaction block added to `buildGraph()` via pure vis-network configuration.

---

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Upgrade node font to 12px with rgba halo and add label scaling | 4252e6e | examples/workbench/static/graph.js |
| 2 | Add degree-based node sizing (8-24px range) and explicit interaction block | f24a43f | examples/workbench/static/graph.js |

---

## What Was Built

### Task 1: Label Halo + Scaling

Replaced the per-node `font: { size: 11, color: '#333' }` with:

```javascript
font: {
    size: 12,
    color: '#1a1a1a',
    background: 'rgba(255, 255, 255, 0.85)',
},
```

Added `scaling.label` to the global options block:

```javascript
scaling: {
    label: {
        enabled: true,
        min: 8,
        max: 14,
        maxVisible: 14,
        drawThreshold: 6,
    },
},
```

Labels have a semi-transparent white halo for legibility against dark edges, and auto-disappear when the rendered font size drops below 6px (far zoom-out).

### Task 2: Degree-Based Sizing + Multiselect

Pre-computed a `degreeMap` before `allNodes.map(...)`:

```javascript
const degreeMap = {};
allEdges.forEach(e => {
    degreeMap[e.source] = (degreeMap[e.source] || 0) + 1;
    degreeMap[e.target] = (degreeMap[e.target] || 0) + 1;
});
const maxDegree = Math.max(...Object.values(degreeMap), 1);
```

Replaced hardcoded node dot `size: 12` with degree formula:

```javascript
size: 8 + Math.round(((degreeMap[n.id] || 0) / maxDegree) * 16),
```

Expanded `interaction` in options:

```javascript
interaction: {
    hover: true,
    tooltipDelay: 200,
    multiselect: true,
    dragNodes: true,
    navigationButtons: false,
},
```

---

## Deviations from Plan

### Minor Grep Check Conflict (documentation artifact only)

The Task 2 acceptance criteria includes:
> `grep -c "size: 12," returns 0` (old hardcoded size removed)

This check returns `1` because Task 1 legitimately added `font: { size: 12, ... }` per its own spec. The old node dot `size: 12` was correctly replaced by the degree formula on a separate line. The grep cannot distinguish between font size and shape size. The semantic goal is fully achieved; the check wording assumed the only occurrence of `size: 12` would be the old shape size, which was written before Task 1 added the font size. No code change needed.

---

## Known Stubs

None. All node config values are computed from live graph data (`allEdges`, `allNodes`). No placeholders, hardcoded empty arrays, or TODO markers introduced.

---

## Threat Flags

None. No new network endpoints, auth paths, file access patterns, or schema changes introduced. All node data originates from the same-origin `/api/graph` endpoint. The `degreeMap` computation uses array values already loaded before `buildGraph()` is called — no new trust boundary.

---

## Self-Check

### Files exist

- [x] `examples/workbench/static/graph.js` — modified (confirmed via grep checks during execution)

### Commits exist

- [x] 4252e6e — Task 1: font halo + scaling
- [x] f24a43f — Task 2: degree sizing + interaction block

## Self-Check: PASSED
