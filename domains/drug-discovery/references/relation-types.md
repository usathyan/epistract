# Relation Types Quick Reference

22 relation types for the Drug Discovery extraction domain, grouped by category.

## Drug-Target Relations

| Relation | Source Types | Target Types | Symmetric | Review Required | Example |
|---|---|---|---|---|---|
| TARGETS | COMPOUND | PROTEIN, GENE | No | No | pembrolizumab → PD-1 |
| INHIBITS | COMPOUND, PROTEIN | PROTEIN, GENE, PATHWAY | No | No | sotorasib → KRAS G12C |
| ACTIVATES | COMPOUND, PROTEIN | PROTEIN, GENE, PATHWAY | No | No | trametinib → apoptosis pathway |
| BINDS_TO | COMPOUND, PROTEIN | PROTEIN | Yes | No | trastuzumab ↔ HER2 |
| HAS_MECHANISM | COMPOUND | MECHANISM_OF_ACTION | No | No | imatinib → BCR-ABL tyrosine kinase inhibition |

## Drug-Disease Relations

| Relation | Source Types | Target Types | Symmetric | Review Required | Example |
|---|---|---|---|---|---|
| INDICATED_FOR | COMPOUND | DISEASE | No | No | pembrolizumab → Non-Small Cell Lung Carcinoma |
| CONTRAINDICATED_FOR | COMPOUND | DISEASE | No | Yes | methotrexate → pregnancy |

## Drug-Clinical Relations

| Relation | Source Types | Target Types | Symmetric | Review Required | Example |
|---|---|---|---|---|---|
| EVALUATED_IN | COMPOUND | CLINICAL_TRIAL | No | No | pembrolizumab → KEYNOTE-024 |
| CAUSES | COMPOUND | ADVERSE_EVENT | No | No | doxorubicin → cardiotoxicity |

## Drug-Drug Relations

| Relation | Source Types | Target Types | Symmetric | Review Required | Example |
|---|---|---|---|---|---|
| DERIVED_FROM | COMPOUND | COMPOUND | No | No | carfilzomib → epoxomicin |
| COMBINED_WITH | COMPOUND | COMPOUND | Yes | No | nivolumab ↔ ipilimumab |

## Biology Relations

| Relation | Source Types | Target Types | Symmetric | Review Required | Example |
|---|---|---|---|---|---|
| ENCODES | GENE | PROTEIN | No | No | BRAF → BRAF kinase |
| PARTICIPATES_IN | PROTEIN, GENE | PATHWAY | No | No | RAF1 → MAPK/ERK pathway |
| IMPLICATED_IN | GENE, PROTEIN, PATHWAY, PHENOTYPE | DISEASE | No | No | BRCA1 → Breast Cancer |
| CONFERS_RESISTANCE_TO | GENE, PROTEIN, PHENOTYPE | COMPOUND | No | Yes | EGFR T790M → gefitinib |
| EXPRESSED_IN | GENE, PROTEIN | PHENOTYPE | No | No | HER2 → HER2-positive |

## Biomarker Relations

| Relation | Source Types | Target Types | Symmetric | Review Required | Example |
|---|---|---|---|---|---|
| PREDICTS_RESPONSE_TO | BIOMARKER | COMPOUND, MECHANISM_OF_ACTION | No | Yes | PD-L1 TPS ≥50% → pembrolizumab |
| DIAGNOSTIC_FOR | BIOMARKER | DISEASE | No | Yes | microsatellite instability-high → Colorectal Cancer |

## Organizational Relations

| Relation | Source Types | Target Types | Symmetric | Review Required | Example |
|---|---|---|---|---|---|
| DEVELOPED_BY | COMPOUND, CLINICAL_TRIAL | ORGANIZATION | No | No | pembrolizumab → Merck |
| PUBLISHED_IN | CLINICAL_TRIAL, COMPOUND | PUBLICATION | No | No | KEYNOTE-024 → Reck et al., 2016 |
| GRANTS_APPROVAL_FOR | REGULATORY_ACTION | COMPOUND | No | No | FDA accelerated approval → pembrolizumab |

## Fallback

| Relation | Source Types | Target Types | Symmetric | Review Required | Example |
|---|---|---|---|---|---|
| ASSOCIATED_WITH | All entity types | All entity types | Yes | No | EGFR → erlotinib resistance |

**Note:** ASSOCIATED_WITH is the fallback relation. Use it only when no more specific relation type applies.
