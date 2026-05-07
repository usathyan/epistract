# Roadmap: Epistract

## Milestones

- ✅ **v1.0 FDA Product Labels Domain** — Phases 01–07 (shipped 2026-04-26)
- ✅ **v1.1 Workbench Security Hardening** — Phase 08 (shipped 2026-04-28)
- ✅ **v1.2 Workbench Graph Enhancements** — Phases 09–10 (shipped 2026-05-06)
- ✅ **v1.3 Workbench Filter Polish** — Phase 11 (shipped 2026-05-06)
- 🔄 **v1.4 Domain Management** — Phases 12–14 (in progress)

## Phases

<details>
<summary>✅ v1.0 FDA Product Labels Domain (Phases 01–07) — SHIPPED 2026-04-26</summary>

- [x] Phase 01: Domain Schema and Extraction — completed 2026-04-26
- [x] Phase 04: Domain-Aware Community Labeling — completed 2026-04-26
- [x] Phase 05: Workbench Visualization Enhancements — completed 2026-04-26
- [x] Phase 06: Structured Data Corpus Skill — completed 2026-04-26
- [x] Phase 07: FDA Showcase — completed 2026-04-26

</details>

<details>
<summary>✅ v1.1 Workbench Security Hardening (Phase 08) — SHIPPED 2026-04-28</summary>

- [x] Phase 08: Workbench Security Hardening — completed 2026-04-28

</details>

<details>
<summary>✅ v1.2 Workbench Graph Enhancements (Phases 09–10) — SHIPPED 2026-05-06</summary>

- [x] Phase 09: Graph Detail Sidebar (4/4 plans) — completed 2026-05-06
- [x] Phase 10: Graph Interaction and Filters (3/3 plans) — completed 2026-05-06

Full archive: [.planning/milestones/v1.2-ROADMAP.md](.planning/milestones/v1.2-ROADMAP.md)

</details>

---

**v1.3 Workbench Filter Polish**

- [x] **Phase 11: Relation Type Filter + Min-Degree Slider** — Completed 2026-05-06; 3/3 plans; 5/5 criteria verified

---

**v1.4 Domain Management**

- [x] **Phase 12: Domain List and Delete Commands** — Completed 2026-05-07; 3/3 plans; 6/6 UAT criteria verified
- [ ] **Phase 13: Domain Update Wizard — Core Editing** - Conversational guided-prompt wizard for editing domain.yaml, SKILL.md, and epistemic.py
- [ ] **Phase 14: Domain Update Wizard — Corpus Re-run** - Extend update wizard with corpus re-analysis to suggest schema additions

---

## Carry-Forward Notes

**Security regression baseline:** SEC-01..06 tests MUST remain green in any future milestone that touches the workbench. SEC-06 (test_sidebar_xss_dom_api) was added in v1.2 Phase 09.

**Workbench architecture constraints (v1.2 locked decisions):**
- Sidebar is `position: absolute` overlay inside `#graph-panel` — NOT a flex child
- All sidebar/graph content via DOM API (textContent/createElement) — never innerHTML with graph data
- vis.js DataSet.update() for node/edge opacity — not CSS on canvas elements
- `clearHighlight()` must be first call in `filterGraph()`

**Backlog (ready for promotion):**
- **999.1 sec-filings-domain** — Rich CONTEXT.md and DISCUSSION-LOG.md at `.planning/phases/999.1-sec-filings-domain/`. Six locked decisions D-01..D-06. Prerequisite: resolve planning-artifact rollback policy.
- **999.2 cross-scenario-knowledge-persistence** — Aspirational. Sec-filings domain would be first to exercise CIK-as-canonical-key.

---

## Phase Details

### Phase 11: Relation Type Filter + Min-Degree Slider
**Goal**: Users can filter graph edges by relation type and prune low-degree nodes, completing the filtering story alongside the existing epistemic status chips and confidence slider
**Depends on**: Phase 10 (filterGraph() single-pass architecture, module-scoped degreeMap, allEdges array)
**Requirements**: RTYPE-01, RTYPE-02, RTYPE-03, DEGREE-01, SEC-07
**Success Criteria** (what must be TRUE):
  1. User opens a compact dropdown in the filter bar and sees checkboxes for every distinct relation type in the loaded graph; unchecking a type hides those edges without affecting node visibility
  2. User clicks "Select All" or "Clear All" in the dropdown header to toggle all relation-type checkboxes in a single action
  3. User drags the "Min. total connections" slider and nodes with total degree below the threshold disappear; edges connected to hidden nodes are also suppressed
  4. All four filter dimensions (epistemic status chips, confidence slider, relation type checkboxes, min-degree slider) resolve in a single filterGraph() call with no double-render
  5. Running the security regression suite passes — SEC-07 now covers all *.js files in static/ via glob, not a hardcoded file list
**Plans**: 3 plans (11-01, 11-02, 11-03)
**UI hint**: yes

**Wave 1** — DOM/CSS Scaffolding
- 11-01: Add `#relation-type-filter` and `#min-degree-filter` to `index.html`; add CSS rules to `style.css` (RTYPE-01, RTYPE-02)

**Wave 2** *(blocked on Wave 1 completion)*
- 11-02: Module-scope state vars, hoist `maxDegree`, `buildRelationTypeDropdown()`, `initMinDegreeSlider()`, wire into `buildGraph()` in `graph.js` (RTYPE-01, RTYPE-02)

**Wave 3** *(blocked on Wave 2 completion)*
- 11-03: Extend `filterGraph()` with relation-type edge branch + min-degree node branch; SEC-07 glob fix in `test_workbench_security.py` (RTYPE-03, DEGREE-01, SEC-07)

**Cross-cutting constraints:**
- All DOM content via `textContent`/`createElement` — never `innerHTML` with graph data (SEC-01 invariant, all plans)
- Single `filterGraph()` pass — no additional `visNodes.update()` or `visEdges.update()` call (D-09, 11-02 + 11-03)
- Listener accumulation guards required on all new event listeners (WR-02 pattern, 11-02)

---

### Phase 12: Domain List and Delete Commands
**Goal**: Users can inspect all installed domains at a glance and remove unwanted domains safely — either archiving to a recoverable location or permanently deleting — with explicit confirmation before any destructive action
**Depends on**: Nothing (standalone filesystem operations, no dependency on new v1.4 phases)
**Requirements**: LIST-01, LIST-02, DEL-01, DEL-02, DEL-03, DEL-04
**Success Criteria** (what must be TRUE):
  1. User runs `/epistract:domain-list` and sees a formatted table showing every domain name, entity type count, relation type count, last-modified date, and active/archived status — including domains in `domains/_archived/`
  2. User runs `/epistract:domain-delete nonexistent-domain` and receives a clear error message identifying the missing domain by name; no filesystem operations occur
  3. User runs `/epistract:domain-delete <name>` and is prompted to choose between "archive" and "remove", then sees a confirmation listing the domain name and file count before any action executes
  4. After archiving, the domain directory moves to `domains/_archived/<name>/` and appears in `domain-list` with status "archived"; the pipeline excludes it from active domain resolution
  5. After removing, the domain directory is permanently deleted; it no longer appears in `domain-list`
**Plans**: 3 plans (12-01, 12-02, 12-03)

Plans:
- [ ] 12-01-PLAN.md — TDD: Write 8 RED unit tests for manage_domains.py and resolver exclusion
- [ ] 12-02-PLAN.md — Implement scripts/manage_domains.py and patch core/domain_resolver.py
- [ ] 12-03-PLAN.md — Create commands/domain-list.md and commands/domain-delete.md slash commands

---

### Phase 13: Domain Update Wizard — Core Editing
**Goal**: Users can run a conversational guided-prompt wizard to update any editable component of an existing domain — schema, extraction prompt, or epistemic analysis — with schema validation before any file is overwritten
**Depends on**: Phase 12 (domain existence validation pattern, domain resolution confirmed working)
**Requirements**: UPDT-01, UPDT-02, UPDT-03, UPDT-04
**Success Criteria** (what must be TRUE):
  1. User runs `/epistract:domain-update nonexistent-domain` and receives a clear error identifying the missing domain; running `/epistract:domain-update <name>` on a valid domain opens the wizard with a menu of editable components
  2. User selects "Edit schema" in the wizard, receives guided prompts to add, remove, or rename entity types and relation types, and the wizard validates schema consistency (no dangling relation endpoints, no duplicate names) before writing `domain.yaml`
  3. User selects "Edit extraction prompt" in the wizard, reviews the current `SKILL.md` content, provides a revised version via guided prompts, and the wizard writes the updated `SKILL.md`
  4. User selects "Edit epistemic analysis" in the wizard, receives guided prompts to adjust confidence tiers, evidence types, and conflict detection logic, and the wizard writes the updated `epistemic.py`
**Plans**: TBD

---

### Phase 14: Domain Update Wizard — Corpus Re-run
**Goal**: Users can trigger a corpus re-analysis from within the update wizard that surfaces schema additions as discrete per-suggestion confirmation prompts, so no change reaches disk without explicit approval
**Depends on**: Phase 13 (update wizard scaffolding, guided-prompt flow, domain validation all established)
**Requirements**: UPDT-05
**Success Criteria** (what must be TRUE):
  1. User selects "Re-run corpus analysis" in the update wizard, provides a path to new documents, and the wizard runs the corpus analyzer (equivalent to `/epistract:domain` creation flow) against those documents
  2. Wizard presents each suggested schema change (new entity type, new relation type, modified description) as a discrete confirmation prompt; user approves or rejects each suggestion individually before any file is written
  3. Only approved suggestions are written to `domain.yaml`; rejected suggestions are discarded without modifying the domain; the wizard reports a summary of accepted vs. rejected changes
**Plans**: TBD

---

## Progress Table

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 11. Relation Type Filter + Min-Degree Slider | 3/3 | Complete | 2026-05-06 |
| 12. Domain List and Delete Commands | 0/3 | Planning done | - |
| 13. Domain Update Wizard — Core Editing | 0/? | Not started | - |
| 14. Domain Update Wizard — Corpus Re-run | 0/? | Not started | - |
