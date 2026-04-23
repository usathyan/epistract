---
name: clinicaltrials-extraction
description: >
  Use when extracting entities and relations from ClinicalTrials.gov
  protocol documents, IRB submissions, clinical study reports, trial
  publications, or any document discussing trial designs, interventions,
  conditions, sponsors, and outcomes. Activates for documents containing
  NCT numbers, phase designations (Phase 1/2/3), or trial protocol
  sections (Primary Endpoint, Inclusion/Exclusion Criteria, Arms).
version: 1.0.0
---

# Clinical Trials Extraction Skill

## CRITICAL: NCT ID Capture Directive

For any Trial entity, the `name` field MUST be the NCT identifier
(format: `NCT` followed by 8 digits, e.g. `NCT04303780`) when one is
present in the document. Study acronyms ("CodeBreaK 200"), sponsor-assigned
codes ("AMG 510 study"), and descriptive titles ("Phase 3 study of
sotorasib in NSCLC") go into `attributes.trial_acronym` or
`attributes.descriptive_title` — NEVER into `name`.

If no NCT ID is present, fall back to the study acronym. Only use a
descriptive title as `name` as a last resort, and set `confidence` <= 0.6.

This rule exists because the post-build enrichment step resolves Trial
nodes against ClinicalTrials.gov via their NCT ID. Nodes without an NCT
ID cannot be enriched.

## Output Format

Return a `DocumentExtraction` JSON envelope. The `document_id` field is
REQUIRED. All entities and relations are lists of objects.

```json
{
  "document_id": "nct04303780_protocol",
  "entities": [
    {
      "name": "NCT04303780",
      "entity_type": "Trial",
      "confidence": 0.95,
      "context": "Phase 3 CodeBreaK 200 trial evaluating sotorasib vs docetaxel",
      "attributes": {
        "trial_acronym": "CodeBreaK 200",
        "study_type": "Interventional"
      }
    },
    {
      "name": "sotorasib",
      "entity_type": "Compound",
      "confidence": 0.95,
      "context": "AMG 510; KRAS G12C inhibitor evaluated as experimental arm",
      "attributes": {
        "inn": "sotorasib",
        "sponsor_code": "AMG 510"
      }
    }
  ],
  "relations": [
    {
      "source_entity": "NCT04303780",
      "target_entity": "sotorasib",
      "relation_type": "tests",
      "confidence": 0.95,
      "evidence": "Trial NCT04303780 evaluates sotorasib in the experimental arm"
    }
  ]
}
```

## Field Requirements

### Entity fields
- `name` (required): Canonical identifier. For Trial, use NCT ID. For Compound, use INN. For Condition, use MeSH term.
- `entity_type` (required): Must match one of the 12 types in domain.yaml exactly (case-sensitive).
- `confidence` (required): Float 0.0–1.0. See Confidence Calibration section.
- `context` (required): Short excerpt or paraphrase from the source document justifying extraction.
- `attributes` (optional): Dict of domain-specific metadata (e.g. `trial_acronym`, `sponsor_code`, `phase`, `dose`).

### Relation fields
- `source_entity` (required): `name` value of the source entity.
- `target_entity` (required): `name` value of the target entity.
- `relation_type` (required): Must match one of the 10 relation types in domain.yaml exactly (case-sensitive).
- `confidence` (required): Float 0.0–1.0.
- `evidence` (required): Short quote or paraphrase from the document supporting the relation.

## Entity Types

### Trial

A clinical trial identified by its NCT registry ID. NCT IDs follow the format
`NCT` followed by exactly 8 digits (e.g. `NCT04303780`). Always use the NCT ID
as the canonical `name` when present. Capture the study acronym and descriptive
title in attributes.

```json
{
  "name": "NCT04303780",
  "entity_type": "Trial",
  "confidence": 0.98,
  "context": "CodeBreaK 200 (NCT04303780): a global Phase 3 randomized controlled trial",
  "attributes": {
    "trial_acronym": "CodeBreaK 200",
    "descriptive_title": "Study to Compare AMG 510 With Docetaxel in NSCLC",
    "study_type": "Interventional",
    "status": "Active, not recruiting"
  }
}
```

### Intervention

A procedure, behavioral intervention, device use, or non-drug therapy (i.e., not a
drug or biologic) being studied in the trial. An intervention that IS a drug or
biologic gets BOTH a Compound entity (with INN as name) AND an Intervention entity
(with the arm label as name), linked by the `tests` relation from the Trial.

```json
{
  "name": "sotorasib 960 mg QD oral",
  "entity_type": "Intervention",
  "confidence": 0.92,
  "context": "Experimental arm: sotorasib 960 mg administered orally once daily",
  "attributes": {
    "dose": "960 mg",
    "schedule": "QD",
    "route": "oral"
  }
}
```

### Condition

The disease, disorder, or indication being studied. Prefer MeSH disease terms as
the canonical name. Include disease subtypes and staging information when specified.

```json
{
  "name": "Non-Small Cell Lung Carcinoma",
  "entity_type": "Condition",
  "confidence": 0.97,
  "context": "Patients with previously treated advanced NSCLC with KRAS G12C mutation",
  "attributes": {
    "mesh_term": "Carcinoma, Non-Small-Cell Lung",
    "subtype": "KRAS G12C-mutant",
    "staging": "Advanced"
  }
}
```

### Sponsor

Organization funding or running the trial — pharmaceutical companies, academic
medical centers, CROs, or government agencies. Use the most widely recognized
organization name.

```json
{
  "name": "Amgen",
  "entity_type": "Sponsor",
  "confidence": 0.98,
  "context": "Sponsored by Amgen Inc., a multinational biopharmaceutical company",
  "attributes": {
    "role": "Industry sponsor",
    "country": "United States"
  }
}
```

### Investigator

Principal investigator or key study personnel named in the protocol or publication.
Use the full name as listed. Capture institution and role in attributes.

```json
{
  "name": "Melissa L. Johnson",
  "entity_type": "Investigator",
  "confidence": 0.95,
  "context": "Principal investigator: Dr. Melissa L. Johnson, Sarah Cannon Research Institute",
  "attributes": {
    "role": "Principal Investigator",
    "institution": "Sarah Cannon Research Institute"
  }
}
```

### Outcome

A primary, secondary, or exploratory outcome measure — the endpoint being assessed.
Include the endpoint category (primary/secondary/exploratory) in attributes.

```json
{
  "name": "overall survival",
  "entity_type": "Outcome",
  "confidence": 0.97,
  "context": "Primary endpoint: overall survival (OS) assessed by BIRC review",
  "attributes": {
    "endpoint_type": "Primary",
    "assessment_method": "BIRC review"
  }
}
```

### Compound

A small molecule, biologic, or drug candidate under investigation. Prefer the
International Nonproprietary Name (INN) as the canonical `name`. Record sponsor
codes, brand names, and chemical names in attributes. Compound nodes are candidates
for PubChem enrichment during `--enrich`.

```json
{
  "name": "sotorasib",
  "entity_type": "Compound",
  "confidence": 0.98,
  "context": "Sotorasib (AMG 510), a first-in-class KRAS G12C covalent inhibitor",
  "attributes": {
    "inn": "sotorasib",
    "sponsor_code": "AMG 510",
    "drug_class": "KRAS G12C inhibitor",
    "mechanism": "Covalent irreversible KRAS G12C inhibition"
  }
}
```

### Biomarker

A measurable indicator used for patient selection, stratification, or response
assessment. Capture threshold, measurement method, and biomarker category in
attributes when available.

```json
{
  "name": "KRAS G12C",
  "entity_type": "Biomarker",
  "confidence": 0.98,
  "context": "Eligible patients must have KRAS G12C mutation confirmed by local testing",
  "attributes": {
    "biomarker_type": "Genomic",
    "gene": "KRAS",
    "variant": "G12C",
    "use": "Patient selection (inclusion criterion)"
  }
}
```

### Cohort

A specific arm or group within the trial. Each study arm becomes a Cohort entity.
Name = arm label (e.g. 'Arm A: sotorasib 960 mg QD'). Attributes capture `dose`,
`schedule`, `population_size`.

```json
{
  "name": "Arm A: sotorasib 960 mg QD",
  "entity_type": "Cohort",
  "confidence": 0.95,
  "context": "Arm A: sotorasib 960 mg orally once daily; n=171",
  "attributes": {
    "arm_label": "Arm A",
    "dose": "960 mg",
    "schedule": "QD",
    "route": "oral",
    "population_size": 171
  }
}
```

### Population

The inclusion/exclusion-defined patient population for the trial. Captures the
eligibility criteria as a single entity representing who the trial targets.

```json
{
  "name": "Previously treated KRAS G12C-mutant NSCLC patients",
  "entity_type": "Population",
  "confidence": 0.92,
  "context": "Adults with advanced NSCLC, KRAS G12C mutation, 1-2 prior lines of therapy",
  "attributes": {
    "age_group": "Adult",
    "prior_treatment": "1-2 prior lines",
    "performance_status": "ECOG 0-1"
  }
}
```

### TrialPhase

The regulatory phase designation. Normalize phase values to exactly one of:
`Phase 1`, `Phase 2`, `Phase 2/3`, `Phase 3`, `Phase 4`, `Observational`.
Map 'I' -> `Phase 1`, 'II' -> `Phase 2`, 'III' -> `Phase 3`, 'IV' -> `Phase 4`.
Do not use Roman numerals or non-standard designations in the `name` field.

```json
{
  "name": "Phase 3",
  "entity_type": "TrialPhase",
  "confidence": 0.99,
  "context": "Phase 3, randomized, open-label, multicenter study",
  "attributes": {
    "design": "Randomized controlled trial",
    "blinding": "Open-label"
  }
}
```

### Site

A clinical study site — specific hospital, clinic, or country listed as a trial
location. Use the most specific available name (institution name preferred over
city/country alone).

```json
{
  "name": "Sarah Cannon Research Institute",
  "entity_type": "Site",
  "confidence": 0.90,
  "context": "Study sites include Sarah Cannon Research Institute, Nashville, TN",
  "attributes": {
    "city": "Nashville",
    "state": "TN",
    "country": "United States"
  }
}
```

## Relation Types

### tests

**Source:** Trial | **Target:** Compound or Intervention

A Trial tests a Compound or Intervention. Use this relation to connect the trial
to each experimental treatment arm. For drug interventions, create separate `tests`
relations to both the Compound (INN name) and the Intervention (arm label).

```json
{
  "source_entity": "NCT04303780",
  "target_entity": "sotorasib",
  "relation_type": "tests",
  "confidence": 0.98,
  "evidence": "NCT04303780 evaluates sotorasib 960 mg QD as experimental treatment"
}
```

### treats

**Source:** Compound or Intervention | **Target:** Condition

A Compound or Intervention treats a Condition. Use for established or investigational
therapeutic use. Distinguish from `investigates` (Trial->Condition).

```json
{
  "source_entity": "sotorasib",
  "target_entity": "Non-Small Cell Lung Carcinoma",
  "relation_type": "treats",
  "confidence": 0.93,
  "evidence": "Sotorasib evaluated for treatment of previously treated NSCLC"
}
```

### sponsored_by

**Source:** Trial | **Target:** Sponsor

A Trial is sponsored or funded by a Sponsor. Every Trial with a named sponsor in
the protocol MUST produce a `sponsored_by` relation.

```json
{
  "source_entity": "NCT04303780",
  "target_entity": "Amgen",
  "relation_type": "sponsored_by",
  "confidence": 0.98,
  "evidence": "Sponsored by Amgen Inc."
}
```

### has_outcome

**Source:** Trial | **Target:** Outcome

A Trial has a specified Outcome endpoint. Capture primary, secondary, and key
exploratory endpoints. Create one `has_outcome` relation per distinct endpoint.

```json
{
  "source_entity": "NCT04303780",
  "target_entity": "overall survival",
  "relation_type": "has_outcome",
  "confidence": 0.97,
  "evidence": "Primary endpoint: overall survival assessed by BIRC"
}
```

### uses_biomarker

**Source:** Trial | **Target:** Biomarker

A Trial uses a Biomarker for patient selection, stratification, or response
assessment. Include inclusion-criterion biomarkers and pharmacodynamic markers.

```json
{
  "source_entity": "NCT04303780",
  "target_entity": "KRAS G12C",
  "relation_type": "uses_biomarker",
  "confidence": 0.98,
  "evidence": "KRAS G12C mutation required for enrollment"
}
```

### enrolls

**Source:** Trial | **Target:** Population or Cohort

A Trial enrolls a specific Population (inclusion/exclusion-defined) or Cohort
(arm-specific subgroup). Create one `enrolls` relation per arm (Cohort) and one
for the overall patient Population.

```json
{
  "source_entity": "NCT04303780",
  "target_entity": "Previously treated KRAS G12C-mutant NSCLC patients",
  "relation_type": "enrolls",
  "confidence": 0.95,
  "evidence": "Enrolled adults with advanced NSCLC with KRAS G12C mutation"
}
```

### investigates

**Source:** Trial | **Target:** Condition

A Trial investigates a Condition (the disease under study). Use for the primary
disease indication. Distinct from `treats` which links Compound/Intervention to Condition.

```json
{
  "source_entity": "NCT04303780",
  "target_entity": "Non-Small Cell Lung Carcinoma",
  "relation_type": "investigates",
  "confidence": 0.98,
  "evidence": "CodeBreaK 200 investigates KRAS G12C-mutant NSCLC"
}
```

### targets

**Source:** Compound | **Target:** Biomarker

A Compound targets a Biomarker (molecular target). Use when the mechanism of action
involves specific binding to or modulation of a measurable molecular entity.

```json
{
  "source_entity": "sotorasib",
  "target_entity": "KRAS G12C",
  "relation_type": "targets",
  "confidence": 0.98,
  "evidence": "Sotorasib covalently and irreversibly binds KRAS G12C"
}
```

### is_phase

**Source:** Trial | **Target:** TrialPhase

A Trial is of a given TrialPhase. Every stated phase MUST produce an `is_phase`
relation from the Trial to the matching TrialPhase entity. Use normalized phase
names (Phase 1, Phase 2, Phase 2/3, Phase 3, Phase 4, Observational).

```json
{
  "source_entity": "NCT04303780",
  "target_entity": "Phase 3",
  "relation_type": "is_phase",
  "confidence": 0.99,
  "evidence": "Phase 3, randomized, open-label study"
}
```

### co_intervention

**Source:** Compound or Intervention | **Target:** Compound or Intervention

Two Interventions or Compounds are co-administered in the same Cohort. Use for
combination therapy arms where multiple agents are administered together.

```json
{
  "source_entity": "nivolumab",
  "target_entity": "ipilimumab",
  "relation_type": "co_intervention",
  "confidence": 0.95,
  "evidence": "Combination arm: nivolumab 3 mg/kg + ipilimumab 1 mg/kg Q3W"
}
```

## Confidence Calibration

| Tier | Range | When to Use |
|------|-------|-------------|
| Explicit | 0.9–1.0 | Directly stated with a clear citation (e.g. "NCT04303780", stated phase, named sponsor) |
| Supported | 0.7–0.89 | Strongly supported by context but not directly quoted (e.g. inferred from arm label) |
| Inferred | 0.5–0.69 | Inferred from indirect evidence or background knowledge |
| Speculative | < 0.5 | Speculative; flag for review; do not use if NCT ID is absent and title is vague |

## Quality Checks

Before returning your extraction, verify:

- Every Trial with an NCT ID in the source document MUST be captured as a Trial entity with name == NCT ID.
- Every named Compound MUST be captured as a Compound entity with the INN as canonical name.
- Every stated phase MUST produce an `is_phase` relation from the Trial to the matching TrialPhase.
- Every Sponsor named in the protocol MUST produce a `sponsored_by` relation from the Trial.
- Every primary endpoint MUST produce a `has_outcome` relation.
- Biomarkers used for patient selection MUST appear as Biomarker entities and linked via `uses_biomarker`.
- Drug interventions MUST appear as BOTH a Compound entity AND an Intervention entity (the arm label), connected via a `tests` relation from the Trial.
- TrialPhase names MUST be normalized: use `Phase 1`, `Phase 2`, `Phase 2/3`, `Phase 3`, `Phase 4`, or `Observational` — never Roman numerals.
- No duplicate entities: if the same NCT ID appears multiple times, extract only one Trial entity.
- Missing NCT ID: if no NCT ID is found, set Trial confidence <= 0.6 and use the study acronym as the name with a note in context.
