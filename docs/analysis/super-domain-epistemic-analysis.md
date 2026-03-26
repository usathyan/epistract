# Epistemic Super Domains in Drug Discovery Knowledge Graphs

*Inspired by Eric Little's [LinkedIn post](https://www.linkedin.com/posts/eric-little-71b2a0b_pleased-to-announce-that-i-will-be-speaking-activity-7442581339096313856-wEFc) on reasoning with knowledge graphs and Super Domains.*

**See also:** [Addendum — POC Implementation & Validation Results](super-domain-addendum.md)

---

## Context

Eric's proposal introduces **Super Domains** as an ontological layer above base domains to manage **epistemic facts** — hypotheses, conjectures, and conditional statements that are true only under certain conditions, at certain times, or from certain perspectives. This addresses a fundamental limitation of reification and RDF*, which annotate at the individual triple level and cause scalability problems in large graphs.

We tested this hypothesis empirically against **6 knowledge graphs** built by Epistract (a Claude Code-based extraction system) from drug discovery literature: PubMed abstracts, bioRxiv preprints, FDA documents, and patent filings. The graphs contain a combined **1,400+ relations** across **600+ entities**.

**Key question:** Does literature-derived KG construction inherently produce epistemic facts that require Super Domain treatment?

**Answer:** Yes — unambiguously. Below is the evidence.

---

## 1. The Problem: Epistemic Facts Are Everywhere in Scientific KGs

Our extraction pipeline assigns confidence scores (0.0–1.0) to every relation, calibrated by evidence type, document type, hedging language, and study design. This is effectively **triple-level annotation** — exactly what Eric identifies as insufficient.

Here's what we found when we examined what those scores actually encode:

### 1.1 Confidence Scores Are a Lossy Proxy for Epistemic Status

| Confidence Range | What It Actually Encodes | Count (S1+S6) | Example |
|---|---|---|---|
| 0.95–1.0 | Explicit statement, replicated evidence | ~480 | "APOE is the major genetic risk factor for AD" |
| 0.7–0.89 | Supported but hedged; consensus without proof | ~120 | "CSF biomarkers provide insight into **potentially predominant** mechanisms" |
| 0.5–0.69 | Indirect evidence; preliminary; speculative | ~18 | "GLP-1 analogues **may be used** for alcohol use disorder" |
| < 0.5 | Negative results; prophetic patent examples | ~4 | "**No association** was observed for rs592297" |

The problem: a relation at confidence 0.55 could be:
- A **hypothesis** from a review paper (speculative mechanism)
- A **prophetic example** from a patent (unproven compound)
- A **negative result** (absence of evidence)
- A **conditional finding** (true only in a subpopulation)

These are fundamentally different epistemic categories, but they collapse into the same numeric range. A triple-level annotation cannot distinguish them.

### 1.2 Graph-Level Hypotheses Are Not Capturable as Individual Triples

**Example: The Complement Activation Hypothesis (Scenario 1)**

Three relations together form a mechanistic hypothesis about Alzheimer's disease:

```
complement membrane attack complex → HAS_MECHANISM → complement-mediated neuronal lysis
    Evidence: "The presence of the MAC in AD neurones suggests complement mediated neuronal lysis"

complement-mediated neuronal lysis → IMPLICATED_IN → Alzheimer disease
    Evidence: "complement mediated neuronal lysis may be a consequence of this struggle"

complement system → PARTICIPATES_IN → neuroinflammation
    Evidence: "complement activation in AD pathology"
```

Each triple carries hedging language ("suggests", "may be"). But the epistemic unit is the **entire 3-relation pattern**: the hypothesis that complement activation drives neuronal death in AD. Annotating each triple individually misses the fact that they stand or fall together as a coherent conjecture.

This is exactly what Eric describes as **graph-level sets of inference** that reification cannot handle.

---

## 2. Five Categories of Epistemic Facts Found in Our Graphs

### Category A: Hypothesized Mechanisms (graph-level conjectures)

Clusters of relations that together propose a mechanism. Not individually uncertain — uncertain *as a group*.

| Hypothesis | Relations | Source | Status |
|---|---|---|---|
| Complement-mediated neuronal lysis in AD | 3 relations (MAC → lysis → AD) | pmid_21167244 | Proposed |
| PICALM mediates Aβ clearance via clathrin endocytosis | 4 relations (PICALM → clathrin → endocytosis → Aβ) | pmid_21300948 | Supported by CSF biomarkers |
| Viral etiology of AD (HSV-1) | 2 relations (HSV-1 → proposed contributor → AD) | pmid_21167244 | Proposed |
| GLP-1 neuroprotection via insulin signaling | 3 relations (semaglutide → GLP1R → neuroprotection → PD) | pmid_35650449 | Pre-clinical only |

**Super Domain treatment:** Each hypothesis becomes a named container holding its member triples, with `status: proposed|supported|refuted`, `perspective: <author group>`, and `valid_if: <conditions>`.

### Category B: Conflicting Evidence (perspective-dependent truth)

The same relation extracted from multiple sources with **opposing conclusions**.

**Flagship example — PICALM rs3851179 allele direction (Scenario 1):**

| Source | Finding | Confidence |
|---|---|---|
| pmid_26611835 (meta-analysis) | Allele T → **13% increased risk** of AD | 0.95 |
| pmid_31385771 (meta-analysis) | Allele A → **decreased risk** of AD (OR=0.88) | 0.95 |

Both are meta-analyses. Both report high confidence. Both cannot be simultaneously true in the same population. The KG aggregates them into a single relation with composite confidence 0.997 — **which masks the contradiction entirely**.

**Super Domain treatment:** Two competing epistemic claims, each containing the same base relation but from different perspectives. The contradiction is structural, not numeric.

**Additional conflict — rs541458:**

| Source | Finding | Confidence |
|---|---|---|
| pmid_26611835 | **No significant association** | 0.50 |
| pmid_31385771 | **Inversely associated** (OR=0.86, Caucasians only) | 0.95 |

A negative result (no association) vs. a positive population-specific result. The negative finding is itself an epistemic fact — absence of evidence in one meta-analysis, presence in another with a population constraint.

### Category C: Patent Claims vs. Paper Evidence (document-type epistemic signatures)

Patents and papers have fundamentally different epistemic signatures:

| Feature | Patent Language | Paper Language |
|---|---|---|
| Tense | Present/future ("is expected to", "may be modified") | Past ("demonstrated", "reported") |
| Uncertainty acknowledgment | Absent (legal claim structure) | Explicit ("remains unproven", "preliminary") |
| Evidence stage | Not specified (intentionally) | Explicitly stated (pre-clinical, Phase 2, meta-analysis) |
| Prophetic examples | Common ("potentially below 10 pM EC50") | Rare |

**Concrete example — GLP-1R activation (Scenario 6):**

| Source | Claim | Evidence Stage |
|---|---|---|
| Patent 01 (Novo Nordisk) | semaglutide ACTIVATES GLP1R (conf=1.0) | Approved drug, validated |
| Patent 05 (Pfizer) | danuglipron ACTIVATES GLP1R via allosteric mechanism (conf=0.97) | Phase 2/3, partially discontinued |
| Patent 06 (Hanmi) | 102 triple agonist variants ACTIVATE GLP1R+GIPR+GCGR (conf=0.95) | Theoretical (peptide designs) |
| pmid_38858523 | retatrutide ACTIVATES GLP1R (conf=0.999) | Phase 2 demonstrated, Phase 3 ongoing |

All four have confidence > 0.95. But their epistemic status ranges from **validated** (approved drug) to **theoretical** (102 unsyntheiszed variants). Triple-level confidence cannot distinguish these.

**Super Domain treatment:** Patent claims and paper evidence occupy different epistemic layers. A patent's "for treating obesity" is a legal claim contingent on clinical success; a paper's "demonstrated 17.3% weight loss" is an empirical observation. Same base relation, different epistemic containers.

### Category D: Temporal State Transitions (time-scoped truth)

Drug development stages are inherently temporal:

```
2020: semaglutide → INDICATED_FOR → obesity (confidence: 0.85, Phase 3 trial)
2021: semaglutide → INDICATED_FOR → obesity (confidence: 0.99, FDA approved)
2024: semaglutide → INDICATED_FOR → NASH (confidence: 0.60, pre-clinical evidence)
2025: semaglutide → INDICATED_FOR → Parkinson's (confidence: 0.55, animal models)
```

Today we flatten all of these into the same graph. The approved indication and the speculative one coexist without temporal or evidence-stage separation.

**Super Domain treatment:** Each time-point/evidence-stage is a scoped layer. The base domain contains only the established fact (approved for obesity). The Super Domain contains the evolving claims (NASH: Phase 2, Parkinson's: pre-clinical).

### Category E: Negative Results (epistemic facts about absence)

Negative findings are genuine epistemic contributions:

| Variant | Finding | Confidence | Epistemic Status |
|---|---|---|---|
| rs592297 | "No association was observed" | 0.40 | Absence of evidence |
| rs2373115 (GAB2) | "No significant association" | 0.50 | Refuted (in this population) |
| rs541458 | "No significant association" (one study) | 0.50 | Contested |

We extract these at low confidence, but they're not uncertain — they're certain statements about absence. A confidence of 0.40 for "no association was observed" is misleading; the observation itself is high-confidence, but the *relation* (association) doesn't hold.

**Super Domain treatment:** Negative results are first-class epistemic claims: "Under conditions X, with sample size N, relation R was not observed." This is qualitatively different from a low-confidence positive claim.

---

## 3. Prevalence Across 6 Scenarios

| Scenario | Domain | Total Relations | Epistemic Patterns | Dominant Category |
|---|---|---|---|---|
| S1: PICALM/Alzheimer's | Neurogenetics | ~220 | 12 | B (conflicting allele effects), A (mechanistic hypotheses) |
| S2: KRAS G12C Landscape | Oncology | ~180 | 26 | A (resistance mechanisms — conjectural) |
| S3: Rare Disease | Rare disease | ~150 | 12 | D (evolving diagnostic criteria), C (biomarker predictivity) |
| S4: Immuno-oncology | Immunotherapy | ~200 | 19 | A (biomarker-response hypotheses) |
| S5: Cardiovascular | Cardiology | ~190 | 22 | D (evolving guidelines), E (negative trial results) |
| S6: GLP-1 CI | Metabolic/CI | ~630 | 18+ | C (patent vs. paper), D (temporal drug development) |

**Every scenario** contains epistemic facts. The proportion varies by domain: genetics-heavy scenarios (S1, S2) produce more Category B (conflicting evidence); patent-heavy scenarios (S6) produce more Category C (document-type signatures); clinical scenarios (S4, S5) produce more Category D (temporal) and E (negative results).

---

## 4. Proposed Test: Extraction-Time Epistemic Tagging (Approach C)

We propose extending our extraction model with epistemic metadata:

```python
class ExtractedRelation(BaseModel):
    # Existing fields
    relation_type: str          # e.g., INHIBITS, INDICATED_FOR
    source_entity: str
    target_entity: str
    confidence: float           # 0.0-1.0 (existing calibration)
    evidence: str               # Verbatim source quote

    # NEW: Epistemic metadata
    epistemic_status: str = "asserted"
        # asserted | hypothesized | conditional | speculative | prophetic | negative
    claim_group: str | None = None
        # Groups relations into named hypotheses
        # e.g., "complement_activation_hypothesis"
    valid_if: str | None = None
        # Conditions for truth
        # e.g., "PICALM rs3851179 risk allele carriers"
    temporal_scope: str | None = None
        # When this is/was true
        # e.g., "pre-clinical 2024" or "FDA approved 2021"
    perspective: str | None = None
        # Who asserts this
        # e.g., "Smith et al. 2024" or "Patent US11,234,567 (Novo Nordisk)"
```

A post-processing skill (`/epistract-claims`) would then:

1. Read tagged extractions
2. Group relations sharing the same `claim_group` into named `EPISTEMIC_CLAIM` entities
3. Detect contradictions (same entities, opposing evidence)
4. Output a `claims_layer.json` — the Super Domain — alongside the base `graph_data.json`

This separates **brute facts** (base domain, high-confidence asserted relations) from **epistemic facts** (Super Domain, everything else) without changing the base graph structure.

---

## 5. Discussion Points for Eric

1. **Does the `claim_group` field adequately capture graph-level inference patterns?** We're grouping relations by a shared label, but Eric's Super Domain implies richer structure — e.g., ordering within the pattern, conditional dependencies between member triples.

2. **How should contradictions be represented?** We found cases where the *same* relation has high-confidence evidence in *both* directions (rs3851179: risk allele in one meta-analysis, protective in another). Is this two competing Super Domain entries? Or a single entry with a `contested` status?

3. **Patent epistemic status**: Patents have a unique epistemic signature — forward-looking, prophetic, legally claimed. Should this be a distinct epistemic category, or does it fold into `conditional`/`speculative`?

4. **Negative results**: "No association was observed" is a high-confidence statement about absence. How does the Super Domain handle facts about what *isn't* true? Is a negative result a Super Domain entry, or does it belong in the base domain as a constraint?

5. **Scalability**: Eric's talk addresses scalability problems with triple-level annotation. Our `claim_group` approach would create ~50-100 epistemic claim containers per scenario. Does this scale better than annotating each of the 1,400+ relations individually?

6. **Temporal layering**: Drug development naturally creates temporal Super Domains (pre-clinical → Phase 1 → Phase 2 → approved → withdrawn). Should each stage be a separate Super Domain layer, or should temporal scoping be an attribute within a single layer?

---

## 6. Raw Data: Selected Evidence Quotes

### Hedging Language (Hypothesized Mechanisms)

> "The presence of the complement membrane attack complex in AD neurones **suggests** complement mediated neuronal lysis" — pmid_21167244, conf=0.9

> "complement mediated neuronal lysis **may be** a consequence of this struggle" — pmid_21167244, conf=0.85

> "CSF biomarker analyses provide a first insight into the **potentially predominant** pathogenetic mechanisms" — pmid_21300948, conf=0.8

> "GWASs have identified several genes that **might be potential** risk factors for AD" — pmid_24729694, conf=0.85

> "GLP-1 analogues **may be used** for the treatment of alcohol use disorder" — pmid_37192005, conf=0.75

> "In osteoarthritis, **they appear to reduce** inflammation and cartilage degradation" — pmid_40726115, conf=0.7

### Conflicting Evidence

> "The **allele T** of rs3851179 in PICALM was associated with a **13% increase** in the risk of AD" — pmid_26611835, conf=0.95

> "**A carriers** of rs3851179 were associated with a **decreased risk** of AD (OR = 0.88)" — pmid_31385771, conf=0.95

### Patent Prophetic Language

> "Performance characteristics include EC50 values **potentially below 10 pM** on both receptors" — Patent 08 (GLP-1/Amylin co-agonist)

> "The peptides **may be modified** with fatty acid conjugation or PEGylation at lysine residues" — Patent 06 (Hanmi triple agonist)

> "Unlike peptide-based GLP-1 receptor agonists, these are orally bioavailable nonpeptide small molecules that activate the GLP-1 receptor through an **allosteric mechanism**" — Patent 05 (Pfizer)

### Negative Results

> "**No association** was observed for rs592297" — pmid_26611835, conf=0.4

> "no **significant association** between PICALM rs541458 (C > T) and AD" — pmid_26611835, conf=0.5

### Self-Acknowledged Epistemic Gaps

> "Although these agents provide beneficial effects for MASH, their **efficacy in promoting fibrosis regression remains unproven**" — pmid_39663847

> "Larger-scale trials are needed to confirm these findings. Most current findings come from **animal studies or small human trials**" — pmid_40726115

---

## Summary

Scientific literature produces epistemic facts at every scale — from individual hedged assertions to multi-relation mechanistic hypotheses to cross-paper contradictions. Our analysis of 6 drug discovery KGs (1,400+ relations) confirms that:

1. **Triple-level confidence scores are a lossy proxy** — they collapse distinct epistemic categories (hypothesis, prophetic claim, negative result, conditional finding) into a single number
2. **Graph-level inference patterns exist** and cannot be captured by annotating individual triples — mechanistic hypotheses span 3-5 relations that stand or fall together
3. **Conflicting evidence is structural, not numeric** — the rs3851179 example shows two equally confident meta-analyses reporting opposite allele effects, invisible to a composite confidence score
4. **Document type determines epistemic signature** — patents and papers make fundamentally different kinds of claims about the same entities and relations
5. **Temporal evolution is inherent to drug discovery KGs** — the same drug-indication relation changes epistemic status from speculative (pre-clinical) to established (FDA approval) over time

Eric's Super Domain proposal provides an engineering home for all five of these patterns. Our proposed Approach C (extraction-time tagging + post-processing into claim containers) offers a lightweight path to test this in practice.

---

*Analysis generated from Epistract knowledge graphs built with Claude Code. All evidence quotes are verbatim from source documents (PubMed, bioRxiv, USPTO patents).*
