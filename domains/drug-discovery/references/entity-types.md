# Entity Types Quick Reference

13 entity types for the Drug Discovery extraction domain.

| Type | Description | Naming Standard | Key Attributes | Example |
|---|---|---|---|---|
| COMPOUND | Small molecules, biologics, drug candidates, approved drugs, chemical probes | INN name (prefer over brand/code) | modality, development_stage, aliases | pembrolizumab |
| GENE | Genes, genetic loci, alleles, genomic variants | HGNC symbol | variant, alteration_type | BRAF V600E |
| PROTEIN | Receptors, enzymes, ion channels, protein complexes | UniProt canonical name | protein_class, domain | PD-1 |
| DISEASE | Medical conditions, syndromes, disease classifications | MeSH term | subtype, stage | HER2-positive Breast Cancer |
| MECHANISM_OF_ACTION | Pharmacological mechanisms by which compounds exert effects | Established terminology (noun phrase) | mechanism_class, selectivity | CDK4/6 inhibition |
| CLINICAL_TRIAL | Registered clinical studies (interventional or observational) | Trial name / NCT ID | phase, design, primary_endpoint, population | KEYNOTE-024 (NCT02142738) |
| PATHWAY | Signaling, metabolic, or regulatory cascades | KEGG/Reactome standard name | pathway_type | MAPK/ERK pathway |
| BIOMARKER | Measurable indicators for diagnosis, prognosis, or treatment response | Standard abbreviation | biomarker_class, threshold, assay | PD-L1 TPS ≥50% |
| ADVERSE_EVENT | Drug-induced side effects, toxicities, safety signals | MedDRA Preferred Term | severity (CTCAE grade), frequency | Grade 3 hepatotoxicity |
| ORGANIZATION | Pharma companies, biotech firms, regulatory agencies, institutions | Common recognized name | org_type | Merck, FDA |
| PUBLICATION | Journal articles, clinical study reports, patents, regulatory filings | Author et al. Year | pmid, doi, publication_type, journal | Mok et al., 2019 |
| REGULATORY_ACTION | Approvals, designations, label changes, safety communications | Agency + action type | action_type, agency, date | FDA accelerated approval |
| PHENOTYPE | Observable biological traits, expression states, patient characteristics | HPO term where applicable | phenotype_type | microsatellite instability |

## Disambiguation Quick Reference

| Ambiguity | Rule | Example |
|---|---|---|
| GENE vs PROTEIN | Use GENE for genomic locus, mutation, expression, coding sequence. Use PROTEIN for binding, catalytic activity, structure, post-translational modification. When ambiguous (e.g. "EGFR"): prefer PROTEIN if discussing binding/inhibition, GENE if discussing expression/mutation. | "EGFR T790M mutation" → GENE; "EGFR inhibitor binding" → PROTEIN |
| COMPOUND vs MECHANISM_OF_ACTION | Named drugs/molecules are COMPOUND. Pharmacological action phrases are MECHANISM_OF_ACTION. | "nivolumab" → COMPOUND; "PD-1 inhibition" → MECHANISM_OF_ACTION |
| DISEASE vs PHENOTYPE | DISEASE = classifiable medical condition with diagnostic criteria. PHENOTYPE = observable trait or biomarker state. | "Type 2 Diabetes Mellitus" → DISEASE; "insulin resistance" → PHENOTYPE |
| ADVERSE_EVENT vs DISEASE | ADVERSE_EVENT = condition caused by a drug or treatment. DISEASE = condition being treated or studied independently of drug exposure. | "drug-induced hepatotoxicity" → ADVERSE_EVENT; "hepatitis C" → DISEASE |
| BIOMARKER vs PHENOTYPE | BIOMARKER = measurable clinical indicator used for decision-making. PHENOTYPE = the underlying biological state. | "PD-L1 TPS ≥50%" → BIOMARKER; "PD-L1 high expression" → PHENOTYPE |
