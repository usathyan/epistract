# Epistemic Briefing

## Executive Summary

- The knowledge graph is **dominated by `asserted` claims** (394 of 395 relations), with a single unclassified relation — suggesting either a highly curated corpus or a systematic gap in epistemic tagging that warrants audit before downstream decision-making.
- **No `prophetic`, `hypothesized`, `speculative`, `contested`, or `contradictions` statuses are recorded** in the graph, which is atypical for a corpus spanning 10 trials across multiple phases; this absence is itself a finding and likely reflects incomplete annotation rather than genuine consensus.
- The graph is **outcome-heavy** (65 Outcome nodes across 10 trials) but **intervention-light** (16 Intervention nodes), indicating that endpoint language is well-captured while the mechanistic and compound-level detail needed for cross-trial comparability may be underrepresented.
- **Cohort and population stratification** (13 Cohort nodes, 10 Population nodes) is present but not yet linked to divergent outcome signals in the current annotation — a critical gap for any subgroup-level efficacy or safety inference.
- With only 2 `TrialPhase` nodes recorded against 10 trials, **phase-based evidence grading cannot be applied uniformly** across the corpus; several efficacy claims may be sourced from Phase 1/2 data and should be treated as `low_evidence` or `medium_evidence` until phase attribution is completed.

---

## Prophetic Claim Landscape

**No relations are explicitly tagged `prophetic` in the current graph.** However, the structural profile of the corpus — 10 documents including what appear to be patent or regulatory submissions (10 `DOCUMENT` nodes) — creates a high prior probability that prophetic language exists but has not been surfaced.

Specific areas where prophetic claims would be expected and should be reviewed:

- **Compound class / mechanism claims**: With only 5 `Biomarker` nodes and 16 `Intervention` nodes, any language asserting that a compound "is expected to inhibit," "may be prepared by," or "would demonstrate activity against" a biomarker target is likely present in the source documents but collapsed into `asserted` status during ingestion. This is a tagging artifact risk, not a confirmed absence.
- **Dosing and formulation language**: Patent-family documents routinely contain prophetic examples (e.g., "a dose of X mg/kg may be administered"). Without explicit `prophetic` tagging, these forward-looking claims are indistinguishable from empirically validated dosing data in the current graph.
- **Combination therapy projections**: Given the one-to-many mapping between Interventions and Compounds expected in combination regimens, any claim about synergistic efficacy of a combination not yet tested in a completed Phase 3 trial should be flagged prophetic. The graph does not currently surface this distinction.

**Recommended action**: Re-annotate all `DOCUMENT` nodes of type patent or preclinical report with `prophetic` status on any relation not directly supported by a completed trial endpoint readout.

---

## Contested Claims & Contradictions

**No `contested` or `contradictions` relations are recorded in the graph.** Given the breadth of 10 trials and 6 conditions, this is statistically unlikely to reflect genuine scientific consensus and more likely reflects:

1. **Single-source annotation**: If each claim was extracted from one document without cross-referencing competing trial results, contradictions would not be captured.
2. **Absence of head-to-head trial data** in the corpus (see Coverage Gaps below), which would be the primary mechanism for generating `contradictions` tags.
3. **Outcome node proliferation without synthesis**: 65 Outcome nodes across 10 trials suggests granular endpoint capture, but without a synthesis layer comparing directionally opposing results across trials, contradictions remain latent.

One structural tension worth flagging: the combination of **outcome-heavy annotation with minimal phase tagging** means that a Phase 1 signal and a Phase 3 null result for the same compound-condition pair could coexist in the graph as two `asserted` claims with no contradiction flag. This is a material risk for any analyst using the graph to support regulatory or investment decisions.

---

## Coverage Gaps

**Phase attribution**: Only 2 `TrialPhase` nodes are recorded for 10 trials. At minimum, 8 trials lack explicit phase annotation in the graph. This makes it impossible to apply the `high_evidence` / `medium_evidence` / `low_evidence` tiering framework systematically. Every efficacy claim in the graph should be considered **ungraded** until phase is confirmed for all trials.

**Companion diagnostics and biomarker-to-trial linkage**: With 5 `Biomarker` nodes and 6 `Condition` nodes, the graph likely underrepresents biomarker-stratified enrollment criteria. For oncology or precision medicine trials, the absence of explicit biomarker-positive/negative cohort splits means subgroup efficacy claims cannot be validated. No companion diagnostic (`CDx`) entities are present.

**Head-to-head comparisons**: No cross-trial comparative relations are recorded. For any condition covered by multiple trials in the graph, the absence of a structured comparator arm or indirect treatment comparison (ITC) node means the graph cannot support comparative effectiveness claims.

**Safety and adverse event outcomes**: The 65 Outcome nodes appear to skew toward efficacy endpoints based on the graph profile. Explicit safety outcome nodes (e.g., treatment-emergent adverse events, dose-limiting toxicities, serious adverse event rates) are not surfaced as a distinct category. Post-market safety signals are entirely absent — expected for recently approved products but should be noted explicitly.

**Sponsor and investigator coverage**: Only 3 `Sponsor` nodes are recorded across 10 trials. Either multiple trials share sponsors (plausible for a focused portfolio) or sponsor attribution is incomplete. Investigator nodes are absent entirely, removing the ability to assess site-level or PI-level bias.

**Enrollment data**: The graph summary does not confirm whether enrollment figures are populated for all 10 trials. Missing enrollment counts prevent application of the ≥300 threshold required for `high_evidence` classification.

**Arm-level granularity**: 13 Cohort nodes for 10 trials suggests some trials have multiple arms captured, but it is unclear whether all randomized arms (including placebo/comparator) are represented. Control arm outcome data is essential for any relative efficacy claim.

---

## Recommended Follow-Ups

1. **Complete phase annotation for all 10 trials**: Pull CT.gov records for each NCT ID in the graph and populate `TrialPhase` nodes. Reclassify all efficacy relations using the `high_evidence` / `medium_evidence` / `low_evidence` tier once phase and enrollment are confirmed.

2. **Re-run epistemic tagging with `prophetic` and `hypothesized` passes**: Apply NLP or manual review to all 10 `DOCUMENT` nodes — particularly any patents or preclinical reports — to surface forward-looking language currently collapsed into `asserted`. Flag any compound-efficacy relation not anchored to a completed trial primary endpoint.

3. **Audit the single unclassified relation**: Identify which entity pair carries the unclassified epistemic status and determine whether it represents a data extraction failure, a genuinely ambiguous claim, or a placeholder. This is a low-effort, high-signal task.

4. **Build a cross-trial outcome matrix**: For each Condition node, map all associated trials, their phases, primary endpoints (verbatim), and directional results into a markdown comparison table. This will surface latent contradictions currently invisible in the flat `asserted` annotation.

5. **Add biomarker-stratified cohort splits**: For each Biomarker node, verify whether any trial enrolled biomarker-selected populations and create explicit Cohort → Biomarker → Outcome chains. This is prerequisite for any precision medicine claim in the graph.

6. **Verify enrollment counts against CT.gov**: Confirm whether the ≥300 enrollment threshold is met for any trial currently treated as `high_evidence`. If enrollment data is absent for any trial, flag all associated efficacy claims as **ungraded** pending verification.

7. **Introduce safety outcome nodes**: Re-extract adverse event, tolerability, and discontinuation data from source documents and add as distinct Outcome nodes with `safety` typing. Cross-reference against any available post-market pharmacovigilance data for approved compounds in the graph.