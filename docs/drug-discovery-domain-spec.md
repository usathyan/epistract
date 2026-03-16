# Drug Discovery Domain Schema — Design Specification

**Status:** DRAFT — awaiting review
**Date:** 2026-03-16
**Purpose:** Production-grade domain schema for sift-kg, grounded in established biomedical ontologies, optimized for extracting structured knowledge from PubMed, bioRxiv/medRxiv, regulatory filings, and patent literature into a knowledge graph suitable for RAG retrieval.

---

## 1. Design Principles

1. **Ontology-grounded** — Every entity type and relation type maps to one or more established biomedical ontologies (Biolink Model, ChEBI, Gene Ontology, MeSH, Disease Ontology, MedDRA). This ensures interoperability with external knowledge bases and future cross-referencing.

2. **LLM-extractable** — Entity and relation types must have clear linguistic signals in scientific text. Types that require deep domain inference or that are ambiguous in natural language are avoided or simplified.

3. **RAG-optimized** — The graph structure supports the query patterns a drug discovery scientist actually uses: "What targets this disease?", "What are the safety signals for this compound?", "What clinical evidence exists?", "What biomarkers predict response?"

4. **Closed-schema with escape hatch** — Entity types and relation types are a closed set enforced during extraction. `ASSOCIATED_WITH` serves as a fallback for relations that don't fit defined types, signaling gaps in the schema that should be addressed.

5. **Source provenance preserved** — Every extraction links back to the source document and passage (inherited from sift-kg core), critical for scientific claims that must be verifiable.

6. **Nomenclature standards enforced** — Extraction hints guide the LLM to use INN drug names, HGNC gene symbols, MeSH disease terms, and other canonical forms.

7. **Hybrid extraction for molecular identifiers** — SMILES, InChI, nucleotide sequences, amino acid sequences, and other character-exact molecular notations require a two-phase approach: LLM-based detection followed by deterministic extraction and validation. LLMs alone cannot guarantee character-perfect reproduction of structural notation.

---

## 2. Ontology Alignment Map

Each entity type is grounded in established standards. This table documents the alignment so that extracted entities can be cross-referenced to external databases.

| Entity Type | Primary Ontology | Secondary Ontologies | ID Prefixes |
|---|---|---|---|
| COMPOUND | Biolink: `Drug`, `ChemicalEntity` | ChEBI, DrugBank, ChEMBL, UNII, PubChem | CHEBI:, DRUGBANK:, CHEMBL:, PUBCHEM: |
| GENE | Biolink: `Gene` | HGNC, NCBI Gene, Ensembl | HGNC:, NCBIGene:, ENSEMBL: |
| PROTEIN | Biolink: `Protein` | UniProtKB, PDB, InterPro | UniProtKB:, PDB:, PR: |
| DISEASE | Biolink: `Disease` | MeSH, Disease Ontology, ICD-11, OMIM, Orphanet | MESH:, DOID:, ICD:, OMIM: |
| PATHWAY | Biolink: `Pathway` | KEGG, Reactome, WikiPathways, GO (BP) | KEGG:, REACT:, GO: |
| MECHANISM_OF_ACTION | Biolink: `MolecularActivity` | ChEBI (role), MeSH (pharmacological action) | CHEBI: (role), MESH: |
| CLINICAL_TRIAL | No Biolink equivalent | ClinicalTrials.gov | NCT, EUCTR, ISRCTN |
| BIOMARKER | Biolink: `ChemicalEntity` or `Gene` | BEST (FDA/NIH taxonomy) | — |
| ADVERSE_EVENT | Biolink: `DiseaseOrPhenotypicFeature` | MedDRA, CTCAE | MedDRA:, CTCAE: |
| ORGANIZATION | Biolink: `Agent` | ROR, GRID, Wikidata | ROR:, GRID: |
| PUBLICATION | Biolink: `InformationContentEntity` | PubMed, DOI | PMID:, DOI: |
| REGULATORY_ACTION | No Biolink equivalent | FDA Orange Book, EMA | — |
| PHENOTYPE | Biolink: `PhenotypicFeature` | HPO, MP | HP:, MP: |
| METABOLITE | Biolink: `SmallMolecule` | ChEBI, HMDB, KEGG Compound | CHEBI:, HMDB:, KEGG: |
| CELL_OR_TISSUE | Biolink: `AnatomicalEntity`, `Cell` | Cell Ontology (CL), Uberon, BRENDA Tissue | CL:, UBERON:, BTO: |
| PROTEIN_DOMAIN | Biolink: `ProteinDomain` | InterPro, Pfam, SMART, PROSITE | IPR:, PF:, SM: |
| SEQUENCE_VARIANT | Biolink: `SequenceVariant` | ClinVar, dbSNP, COSMIC | ClinVar:, dbSNP:, COSMIC: |

---

## 3. Entity Types (23)

### 3.1 COMPOUND

**What it captures:** Any chemical or biological therapeutic agent — approved drugs, drug candidates, chemical probes, biologics, vaccines, gene therapies, cell therapies, ADCs, radiopharmaceuticals.

**Biolink alignment:** `biolink:Drug` (approved) / `biolink:ChemicalEntity` (general)

**Naming conventions:**
- Use INN (International Nonproprietary Name) as canonical name when available: "pembrolizumab" not "Keytruda"
- Record brand names, development codes (e.g., MK-3475, BNT162b2), and chemical names as attributes
- For biologics: use the nonproprietary name stem conventions (-mab, -nib, -lib, -tide, etc.)
- For combination products, extract each component as a separate COMPOUND entity

**Key attributes to extract:**
- `modality`: small molecule | monoclonal antibody | ADC | bispecific antibody | CAR-T | mRNA | siRNA/ASO | gene therapy | peptide | vaccine | radiopharmaceutical
- `development_stage`: preclinical | IND | Phase I | Phase II | Phase III | approved | withdrawn | discontinued
- `brand_names`: list of trade names
- `development_codes`: list of company codes
- `route_of_administration`: oral | IV | SC | IM | intrathecal | topical | inhaled
- `chemical_class`: where applicable (e.g., "tyrosine kinase inhibitor", "PD-1 antibody")

**Extraction hints for LLM:**
- Look for INN names, brand names, company development codes (letter-number patterns like AZD9291, BMS-986016)
- Include small molecules AND biologics — monoclonal antibodies (-mab), ADCs, bispecific antibodies, CAR-T cells, mRNA therapeutics, gene therapies, peptides, vaccines
- For combination regimens (e.g., "nivolumab + ipilimumab"), extract each drug as a separate entity
- Capture the modality and development stage when mentioned
- If only a brand name is given, use it but note it as a brand name in attributes

### 3.2 GENE

**What it captures:** Genes, genetic loci, gene fusions, specific mutations/variants. The unit of heredity, not the protein product.

**Biolink alignment:** `biolink:Gene`

**Naming conventions:**
- Use official HGNC symbols: EGFR, TP53, BRCA1, ALK (not "epidermal growth factor receptor gene")
- Mutations: append to gene symbol — BRAF V600E, KRAS G12C, EGFR T790M
- Fusions: use standard notation — EML4-ALK, BCR-ABL, NTRK fusion
- Copy number: ERBB2 amplification, MYC amplification

**Key attributes:**
- `variant`: specific mutation (V600E, G12C, T790M, exon 19 deletion)
- `alteration_type`: mutation | fusion | amplification | deletion | loss-of-function | gain-of-function | rearrangement
- `germline_or_somatic`: germline | somatic | unknown
- `chromosome_location`: when mentioned

**Extraction hints:**
- Use official HGNC gene symbols in UPPERCASE italics-free form
- Distinguish gene mentions from protein mentions: "EGFR gene" or "EGFR mutation" → GENE; "EGFR protein" or "EGFR receptor" → PROTEIN
- When text is ambiguous (just says "EGFR"), prefer GENE if discussing mutations/genomics, PROTEIN if discussing drug binding/signaling
- Capture the specific variant or alteration when mentioned
- Gene fusions should be extracted as a single GENE entity with the fusion notation (e.g., "EML4-ALK")

### 3.3 PROTEIN

**What it captures:** Specific proteins, including drug targets discussed at the protein level — receptors, enzymes, ion channels, transporters, signaling molecules, structural proteins, antibodies (endogenous).

**Biolink alignment:** `biolink:Protein`

**Naming conventions:**
- Use standard protein names from UniProt: "programmed death-1" → PD-1, "epidermal growth factor receptor" → EGFR protein
- Enzyme names follow EC nomenclature conventions where applicable
- Receptor subtypes: use standard abbreviations (5-HT2A, mGluR5, CB1)

**Key attributes:**
- `protein_class`: receptor | enzyme | ion channel | transporter | signaling molecule | structural | transcription factor
- `uniprot_id`: when identifiable
- `post_translational_modifications`: phosphorylation, ubiquitination, glycosylation
- `isoform`: when specified

**Extraction hints:**
- Distinguish PROTEIN from GENE: "p53 protein levels" → PROTEIN; "TP53 mutations" → GENE
- Include receptors (PD-1, HER2, VEGFR), enzymes (CDK4/6, PI3Kα, mTOR), ion channels, GPCRs
- When a target is discussed in the context of drug binding or protein function, use PROTEIN
- When a target is discussed in the context of genomic analysis or mutations, use GENE

### 3.4 DISEASE

**What it captures:** Diseases, conditions, syndromes, indications. Includes molecular subtypes when they define distinct therapeutic approaches.

**Biolink alignment:** `biolink:Disease`

**Naming conventions:**
- Use precise clinical terminology: "non-small cell lung cancer" not "lung cancer" (unless the text truly means all lung cancers)
- Include molecular subtypes: "HER2-positive breast cancer", "EGFR-mutant NSCLC", "Ph+ chronic myeloid leukemia"
- Use MeSH-preferred terms when possible
- Rare diseases: include both the common name and the formal name

**Key attributes:**
- `subtype`: molecular or histological subtype
- `stage`: when mentioned (Stage IIIB, metastatic, locally advanced, early-stage)
- `icd_code`: ICD-10/11 code if identifiable
- `orphan_status`: whether it qualifies as an orphan/rare disease
- `prevalence`: when mentioned

**Extraction hints:**
- Extract the most specific disease form mentioned — "metastatic castration-resistant prostate cancer" not just "prostate cancer"
- Include molecular subtypes as part of the disease name when they define the indication (HER2+ breast cancer is a distinct indication from triple-negative breast cancer)
- Distinguish the disease entity from the patient population (the disease is the entity, not "patients with...")
- Capture staging, line of therapy context as attributes, not as part of the entity name

### 3.5 MECHANISM_OF_ACTION

**What it captures:** Pharmacological mechanisms by which drugs exert their effects. These are conceptual entities that span multiple drugs and targets.

**Biolink alignment:** `biolink:MolecularActivity`, ChEBI role ontology

**Naming conventions:**
- Use established pharmacological terminology: "selective CDK4/6 inhibition", "PD-1/PD-L1 checkpoint blockade", "KRAS G12C covalent inhibition"
- Be specific: "allosteric inhibition" not just "inhibition"; "immune checkpoint blockade" not just "immunotherapy"
- For novel mechanisms, use the terminology from the source text

**Key attributes:**
- `mechanism_class`: inhibition | activation | blockade | degradation | modulation | depletion | conjugation | gene silencing | gene editing
- `selectivity`: selective | pan- | dual | multi-targeted
- `reversibility`: reversible | irreversible | covalent

**Extraction hints:**
- Look for terms like "inhibitor", "agonist", "antagonist", "blocker", "modulator", "degrader", "checkpoint blockade"
- This is the HOW of drug action — a conceptual entity, not a specific drug
- "CDK4/6 inhibition" is a MECHANISM_OF_ACTION; "palbociclib" is a COMPOUND that HAS_MECHANISM of CDK4/6 inhibition
- Distinguish from the target (which is what the mechanism acts ON) — the mechanism describes the pharmacological action

### 3.6 CLINICAL_TRIAL

**What it captures:** Clinical studies evaluating therapeutic interventions in humans. The trial itself as a registered entity.

**Biolink alignment:** No direct Biolink equivalent (closest: `biolink:ClinicalIntervention`)

**Naming conventions:**
- Use trial name/acronym when available: KEYNOTE-024, DESTINY-Breast03, CheckMate-067
- Include NCT number as an attribute
- For unnamed trials, use "Phase [X] trial of [compound] in [indication]"

**Key attributes:**
- `nct_id`: ClinicalTrials.gov identifier (NCTxxxxxxxx)
- `phase`: Phase I | Phase I/II | Phase II | Phase III | Phase IV | Phase 0
- `design`: randomized | open-label | double-blind | single-arm | basket | umbrella | platform | adaptive
- `primary_endpoint`: PFS | OS | ORR | DLT | safety | DOR | CR rate
- `comparator`: standard of care, placebo, active comparator
- `sample_size`: number of patients enrolled
- `status`: recruiting | active | completed | terminated | suspended
- `sponsor`: sponsoring organization

**Key results attributes (when reported):**
- `primary_result`: e.g., "median PFS 18.7 months vs 10.4 months"
- `hazard_ratio`: e.g., "HR 0.51 (95% CI 0.39-0.67)"
- `p_value`: statistical significance
- `overall_response_rate`: percentage

**Extraction hints:**
- Capture trial acronyms/names (KEYNOTE, CheckMate, DESTINY, PACIFIC, IMpower, CROWN, etc.)
- Look for NCT numbers (NCTxxxxxxxx pattern)
- Extract phase, design, and primary endpoint
- When results are reported, capture the key efficacy numbers (HR, ORR, median PFS/OS)
- Distinguish between the trial entity and its results — the trial is a CLINICAL_TRIAL entity; the results are attributes or separate FINDING-type relations

### 3.7 PATHWAY

**What it captures:** Biological signaling pathways, metabolic pathways, and major cellular processes that are targets of therapeutic intervention or implicated in disease.

**Biolink alignment:** `biolink:Pathway`

**Naming conventions:**
- Use established pathway names: "MAPK/ERK signaling pathway", "PI3K/AKT/mTOR pathway", "Wnt/β-catenin pathway"
- For cellular processes: "apoptosis", "autophagy", "DNA damage repair", "cell cycle regulation"
- Immune pathways: "PD-1/PD-L1 checkpoint axis", "CTLA-4 checkpoint pathway", "cGAS-STING pathway"

**Key attributes:**
- `pathway_database`: KEGG | Reactome | WikiPathways | GO
- `pathway_id`: database-specific identifier when identifiable
- `pathway_type`: signaling | metabolic | immune | DNA repair | cell cycle | apoptotic | developmental

**Extraction hints:**
- Look for named signaling cascades and their components
- Include immune regulatory pathways relevant to immunotherapy
- Capture DNA damage repair pathways (HRD, MMR) relevant to PARP inhibitors and immunotherapy
- Major metabolic pathways (glycolysis, oxidative phosphorylation) when relevant to cancer metabolism

### 3.8 BIOMARKER

**What it captures:** Measurable biological indicators used for patient stratification, treatment selection, diagnosis, prognosis, or monitoring. Follows the FDA/NIH BEST (Biomarkers, EndpointS, and other Tools) framework.

**Biolink alignment:** Context-dependent — a biomarker can be a `Gene`, `Protein`, or `ChemicalEntity` in Biolink; the biomarker role is captured by the relation type.

**Naming conventions:**
- Use standard abbreviations: PD-L1, TMB, MSI-H/dMMR, HER2, BRCA1/2
- Include the measurement context: "PD-L1 TPS" (not just "PD-L1"), "TMB-high" (not just "TMB")
- For companion diagnostics, include the test name when mentioned

**Key attributes:**
- `biomarker_class`: predictive | prognostic | diagnostic | monitoring | safety | pharmacodynamic | susceptibility (per BEST framework)
- `analyte_type`: genomic | proteomic | transcriptomic | metabolomic | circulating | imaging
- `measurement_method`: IHC | FISH | NGS | PCR | ctDNA | liquid biopsy
- `threshold`: cutoff value when mentioned (e.g., "TPS ≥50%", "TMB ≥10 mut/Mb")
- `companion_diagnostic`: name of approved CDx test

**Extraction hints:**
- Extract biomarkers that are used for treatment decisions, not every measured variable
- Include PD-L1 expression (TPS, CPS), TMB, MSI-H/dMMR, HRD, specific mutations as biomarkers
- Capture the biomarker class (predictive vs prognostic) when the text distinguishes them
- Note companion diagnostic tests (FoundationOne CDx, Dako 22C3, Ventana SP263)
- Thresholds and cutoffs are critical — extract them when mentioned

### 3.9 ADVERSE_EVENT

**What it captures:** Drug side effects, toxicities, safety signals, dose-limiting toxicities, and immune-related adverse events.

**Biolink alignment:** `biolink:DiseaseOrPhenotypicFeature` (when adverse event is modeled as a phenotype)

**Naming conventions:**
- Use MedDRA preferred terms when recognizable: "immune-mediated colitis" not "gut inflammation from the drug"
- Use CTCAE grade notation: "Grade 3 hepatotoxicity"
- For class effects, name the class: "immune-related adverse events (irAEs)"

**Key attributes:**
- `severity`: Grade 1-5 (CTCAE) or mild | moderate | severe | life-threatening | fatal
- `frequency`: very common (≥10%) | common (1-10%) | uncommon (0.1-1%) | rare (<0.1%)
- `seriousness`: serious | non-serious
- `organ_system`: SOC (System Organ Class) from MedDRA
- `management`: dose reduction | dose interruption | discontinuation | corticosteroids | supportive care
- `is_dose_limiting`: boolean
- `is_black_box_warning`: boolean

**Extraction hints:**
- Use MedDRA preferred terms when the text uses recognizable medical terminology
- Capture CTCAE grades and frequencies
- Distinguish treatment-emergent AEs from disease-related symptoms
- Note immune-related adverse events (irAEs) specifically — they are a major concern in immunotherapy
- Extract management strategies when described
- Look for boxed warnings, REMS, and class-effect safety signals

### 3.10 ORGANIZATION

**What it captures:** Pharmaceutical companies, biotech firms, academic medical centers, CROs, CMOs, regulatory agencies, funding bodies, standards organizations.

**Biolink alignment:** `biolink:Agent`

**Naming conventions:**
- Use the most widely recognized name: "Roche" not "F. Hoffmann-La Roche AG" (but capture full legal name as attribute)
- For subsidiaries, extract both parent and subsidiary as separate entities
- Regulatory agencies: FDA, EMA, PMDA, NMPA, Health Canada, TGA

**Key attributes:**
- `org_type`: pharma | biotech | CRO | CMO | academic | regulatory_agency | funding_body | diagnostics
- `headquarters`: location
- `ticker_symbol`: when relevant

### 3.11 PUBLICATION

**What it captures:** Scientific papers, review articles, regulatory documents, and other published references that are discussed substantively (not just cited).

**Biolink alignment:** `biolink:InformationContentEntity`

**Naming conventions:**
- Use "Author et al., Year" format or the paper title
- Include PMID and DOI as attributes when identifiable

**Key attributes:**
- `pmid`: PubMed ID
- `doi`: Digital Object Identifier
- `journal`: journal name
- `year`: publication year
- `publication_type`: original research | review | meta-analysis | case report | editorial | guideline | regulatory document | patent

### 3.12 REGULATORY_ACTION

**What it captures:** Regulatory decisions, designations, and milestones — FDA approvals, EMA marketing authorizations, breakthrough therapy designations, orphan drug designations, clinical holds, complete response letters.

**Naming conventions:**
- Be specific about the type: "FDA accelerated approval" not just "approval"
- Include the date and indication in attributes

**Key attributes:**
- `action_type`: approval | accelerated approval | breakthrough therapy designation | fast track | priority review | orphan drug designation | clinical hold | complete response letter | REMS | label update | biosimilar approval
- `agency`: FDA | EMA | PMDA | NMPA | Health Canada | TGA
- `date`: date of action
- `indication`: specific approved indication
- `conditions`: post-marketing requirements, confirmatory trial requirements
- `label_sections`: boxed warning, contraindications

### 3.13 PHENOTYPE

**What it captures:** Observable biological characteristics, cellular phenotypes, and disease manifestations that are not adverse events but are biologically relevant — tumor characteristics, immune phenotypes, resistance phenotypes, biomarker expression patterns.

**Biolink alignment:** `biolink:PhenotypicFeature`

**Naming conventions:**
- Use HPO terms when applicable for clinical phenotypes
- For tumor phenotypes: "microsatellite instability", "homologous recombination deficiency", "tumor-infiltrating lymphocytes"

**Key attributes:**
- `phenotype_type`: molecular | cellular | tissue | organism | clinical
- `measurement`: how it's assessed

**Extraction hints:**
- Extract phenotypes that are biologically meaningful for drug discovery — tumor mutational burden, immune infiltration, expression signatures
- Distinguish phenotypes from diseases (a phenotype is an observable feature; a disease is a diagnosed condition)
- Resistance phenotypes are critical: "acquired resistance to osimertinib via C797S mutation"

### 3.14 METABOLITE

**What it captures:** Endogenous small molecules, substrates, products, cofactors, neurotransmitters, hormones, and second messengers. Distinct from COMPOUND (which captures exogenous therapeutic agents).

**Biolink alignment:** `biolink:SmallMolecule`, `biolink:ChemicalEntity`

**Ontology grounding:**
- ChEBI: Chemical Entities of Biological Interest (primary — the OBO Foundry standard for biochemical entities)
- HMDB: Human Metabolome Database (metabolite-specific)
- KEGG Compound: biochemical compounds in metabolic pathways

**Naming conventions:**
- Use IUPAC or common biochemical names: "ATP" not "adenosine 5'-triphosphate" (but capture the full name as an attribute)
- Neurotransmitters: dopamine, serotonin (5-HT), glutamate, GABA, acetylcholine
- Hormones: estradiol, testosterone, cortisol, insulin, thyroxine
- Second messengers: cAMP, IP3, DAG, calcium ions
- Metabolic intermediates: pyruvate, lactate, acetyl-CoA, succinate
- Lipid mediators: prostaglandin E2, leukotriene B4, sphingosine-1-phosphate

**Key attributes:**
- `metabolite_class`: amino acid | nucleotide | lipid | carbohydrate | cofactor | neurotransmitter | hormone | second messenger | vitamin | electrolyte
- `chebi_id`: ChEBI identifier when identifiable
- `role`: substrate | product | cofactor | inhibitor | activator | signaling molecule
- `endogenous`: true (distinguishes from exogenous drugs)

**Extraction hints:**
- Extract endogenous molecules that participate in drug-relevant biology — substrates of drug-targeted enzymes, products of inhibited pathways, neurotransmitters modulated by CNS drugs
- Do NOT extract metabolites as COMPOUND — COMPOUND is for exogenous therapeutic agents. "Dopamine" is a METABOLITE; "levodopa" is a COMPOUND
- Exception: when an endogenous molecule is used therapeutically (e.g., insulin, cortisol as hydrocortisone), extract it as COMPOUND with a note
- Amino acids as individual entities only when discussed as signaling molecules, enzyme substrates, or in the context of mutations (otherwise they're substructure of proteins)

### 3.15 CELL_OR_TISSUE

**What it captures:** Cell types, tissue types, organs, anatomical structures, and microenvironment contexts where genes are expressed, proteins function, or drugs act.

**Biolink alignment:** `biolink:AnatomicalEntity`, `biolink:Cell`, `biolink:CellularComponent`

**Ontology grounding:**
- Cell Ontology (CL): standardized cell type terms (CL:0000084 = T cell)
- Uberon: cross-species anatomical ontology (UBERON:0002107 = liver)
- BRENDA Tissue Ontology (BTO): enzyme source tissues
- Gene Ontology Cellular Component (GO:CC): subcellular locations (GO:0005634 = nucleus)

**Naming conventions:**
- Cell types: use Cell Ontology preferred names — "CD8-positive T cell", "natural killer cell", "macrophage", "hepatocyte"
- Tissues/organs: use Uberon terms — "liver", "cerebral cortex", "bone marrow", "pancreas"
- Tumor contexts: "tumor microenvironment", "tumor-infiltrating lymphocytes"
- Subcellular: "cell membrane", "nucleus", "mitochondria", "endoplasmic reticulum", "cytoplasm"

**Key attributes:**
- `entity_subtype`: cell_type | tissue | organ | subcellular_compartment | tumor_microenvironment | cell_line
- `cell_ontology_id`: CL: identifier when applicable
- `uberon_id`: UBERON: identifier when applicable
- `species`: human | mouse | rat | in vitro (for cell lines)

**Extraction hints:**
- Extract cell types that are functionally relevant to drug action — immune cells for immunotherapy, hepatocytes for drug metabolism, tumor cells for oncology
- Include cell lines when discussed as experimental models (HeLa, A549, MCF-7, HEK293) — mark with `entity_subtype: cell_line`
- Subcellular compartments matter for drug delivery and target accessibility — "membrane-bound receptor", "nuclear target", "mitochondrial toxicity"
- The tumor microenvironment (TME) is a critical concept in immuno-oncology — extract it as a distinct entity
- For expression patterns: "HER2 is overexpressed in breast epithelial cells" → creates EXPRESSED_IN relation

### 3.16 PROTEIN_DOMAIN

**What it captures:** Functional domains, structural motifs, binding sites, catalytic regions, and regulatory elements within proteins. These are the functional units that drugs interact with.

**Biolink alignment:** `biolink:ProteinDomain`

**Ontology grounding:**
- InterPro: integrative protein signature database (IPR000719 = protein kinase domain)
- Pfam: protein families database (PF00069 = protein kinase domain)
- SMART: Simple Modular Architecture Research Tool
- PROSITE: protein domains, families, and functional sites

**Naming conventions:**
- Use established domain names: "kinase domain", "SH2 domain", "PDZ domain", "bromodomain", "zinc finger domain"
- Binding sites: "ATP-binding pocket", "substrate-binding cleft", "allosteric site"
- Active sites: "catalytic triad", "DFG motif" (in kinases)
- Structural motifs: "death domain", "RING finger", "WD40 repeat"

**Key attributes:**
- `domain_type`: catalytic | binding | regulatory | structural | interaction
- `interpro_id`: InterPro identifier
- `pfam_id`: Pfam identifier
- `parent_protein`: the protein this domain belongs to (captured via PART_OF relation)
- `druggability`: druggable | difficult-to-drug | undruggable (when discussed)

**Extraction hints:**
- Extract domains when they are the specific site of drug interaction — "binds to the kinase domain of EGFR", "targets the bromodomain of BRD4"
- Important for understanding selectivity: a drug may inhibit the kinase domain of one protein but not another
- Allosteric sites are increasingly important drug targets — extract them when discussed
- Protein-protein interaction interfaces are emerging drug targets — extract as domains when named
- Do NOT extract every domain mentioned in a protein structure paper — focus on domains discussed in the context of drug interaction, disease mechanism, or functional significance

### 3.17 SEQUENCE_VARIANT

**What it captures:** Specific genetic or protein sequence alterations — point mutations, insertions, deletions, frameshifts, splice variants, copy number alterations, and structural variants. The variant as a discrete molecular entity, distinct from the gene it affects.

**Biolink alignment:** `biolink:SequenceVariant`

**Ontology grounding:**
- ClinVar: clinical significance of variants (pathogenic, benign, VUS)
- dbSNP: single nucleotide polymorphisms (rs identifiers)
- COSMIC: somatic mutations in cancer
- HGVS nomenclature: standard variant notation

**Naming conventions:**
- Use HGVS protein-level notation when available: p.V600E, p.G12C, p.T790M
- For well-known variants, the common short form is acceptable: BRAF V600E, KRAS G12C
- Gene fusions use standard notation: EML4-ALK, BCR-ABL1, ROS1 fusion
- Copy number: ERBB2 amplification, CDKN2A homozygous deletion
- Use rs identifiers for SNPs when mentioned: rs1801133

**Key attributes:**
- `hgvs_notation`: HGVS standard notation (e.g., NM_004333.6:c.1799T>A for BRAF V600E)
- `variant_type`: missense | nonsense | frameshift | splice_site | insertion | deletion | amplification | fusion | rearrangement | copy_number_loss
- `functional_consequence`: gain-of-function | loss-of-function | dominant-negative | neomorphic | unknown
- `clinical_significance`: pathogenic | likely pathogenic | VUS | likely benign | benign (per ClinVar)
- `allele_frequency`: population frequency when mentioned
- `somatic_or_germline`: somatic | germline | both
- `associated_gene`: the gene harboring this variant
- `dbsnp_id`: rs identifier when available
- `cosmic_id`: COSMIC identifier for somatic mutations

**Extraction hints:**
- Extract variants that are discussed as drug targets, resistance mechanisms, biomarkers, or disease drivers — not every variant in a WES/WGS study
- Common actionable variants: BRAF V600E, KRAS G12C, EGFR T790M, EGFR L858R, ALK fusions, NTRK fusions, PIK3CA H1047R, IDH1 R132H
- Resistance mutations are critical: EGFR C797S (resistance to osimertinib), BCR-ABL T315I (resistance to imatinib)
- Distinguish the variant (SEQUENCE_VARIANT) from the gene (GENE) — "BRAF" is a GENE; "BRAF V600E" is a SEQUENCE_VARIANT in that gene
- When text says "EGFR-mutant NSCLC" without specifying the variant, extract EGFR as GENE with variant attribute "mutant" rather than creating a SEQUENCE_VARIANT

**Design rationale — why separate from GENE:**
In the initial schema, variants were captured as attributes on GENE entities. This is insufficient for production use because:
1. The same variant (e.g., BRAF V600E) appears across multiple diseases and drugs — it needs to be a first-class node for graph traversal
2. Resistance variants (EGFR C797S) need their own CONFERS_RESISTANCE_TO relations
3. Actionable variants drive treatment selection — they need PREDICTS_RESPONSE_TO relations
4. ClinVar/COSMIC cross-referencing requires variant-level identifiers, not gene-level

---

## Molecular Biology Linkage Framework

This section documents how the fundamental molecular biology concepts connect through the schema, grounded in Gene Ontology (GO), Sequence Ontology (SO), Protein Ontology (PRO), and Relation Ontology (RO).

### The Central Dogma Chain

```
GENE ──ENCODES──→ PROTEIN ──HAS_DOMAIN──→ PROTEIN_DOMAIN
  │                   │                         │
  │                   │                    (drug binding site)
  │                   │
  ├──HAS_VARIANT──→ SEQUENCE_VARIANT ──CONFERS_RESISTANCE_TO──→ COMPOUND
  │                   │
  │                   └──PREDICTS_RESPONSE_TO (as BIOMARKER)──→ COMPOUND
  │
  ├──PARTICIPATES_IN──→ PATHWAY
  │                       │
  │                       └──IMPLICATED_IN──→ DISEASE
  │
  └──EXPRESSED_IN──→ CELL_OR_TISSUE
```

### Protein Function Chain

```
PROTEIN ──PARTICIPATES_IN──→ PATHWAY ──IMPLICATED_IN──→ DISEASE
   │           │
   │           └── contains METABOLITE as substrates/products
   │
   ├──BINDS_TO──→ PROTEIN (protein-protein interaction)
   │
   ├──PHOSPHORYLATES──→ PROTEIN (kinase→substrate signaling)
   │
   ├──FORMS_COMPLEX_WITH──→ PROTEIN (multi-subunit complexes)
   │
   ├──HAS_DOMAIN──→ PROTEIN_DOMAIN (functional regions)
   │
   ├──EXPRESSED_IN──→ CELL_OR_TISSUE (tissue-specific expression)
   │
   └──LOCALIZED_TO──→ CELL_OR_TISSUE (subcellular location)
```

### Drug Action Chain

```
COMPOUND ──TARGETS──→ PROTEIN ──HAS_DOMAIN──→ PROTEIN_DOMAIN
   │          │                     (specific binding site)
   │          │
   │          ├──INHIBITS──→ PROTEIN/PATHWAY
   │          ├──ACTIVATES──→ PROTEIN/PATHWAY
   │          └──BINDS_TO──→ PROTEIN (physical interaction)
   │
   ├──HAS_MECHANISM──→ MECHANISM_OF_ACTION
   │
   ├──INDICATED_FOR──→ DISEASE
   │
   ├──EVALUATED_IN──→ CLINICAL_TRIAL
   │
   ├──CAUSES──→ ADVERSE_EVENT
   │
   ├──METABOLIZED_BY──→ PROTEIN (CYP enzymes)
   │                      │
   │                      └──EXPRESSED_IN──→ CELL_OR_TISSUE (liver hepatocytes)
   │
   └──PRODUCES_METABOLITE──→ METABOLITE (active/toxic metabolites)
```

### Ontology Cross-Reference Map

This map shows how each entity type's extracted names can be resolved to standard ontology identifiers for linking to external knowledge bases:

| Entity Type | Primary Resolution Database | Resolution Strategy | Example |
|---|---|---|---|
| COMPOUND | ChEBI → DrugBank → ChEMBL | INN name lookup → synonym matching | "pembrolizumab" → CHEMBL3137343 |
| GENE | HGNC → NCBI Gene → Ensembl | HGNC symbol exact match | "EGFR" → HGNC:3236 |
| PROTEIN | UniProtKB → PDB | Gene symbol + species → canonical entry | "EGFR protein" → UniProtKB:P00533 |
| DISEASE | MeSH → Disease Ontology → OMIM | MeSH preferred term matching | "non-small cell lung cancer" → MESH:D002289 |
| PATHWAY | KEGG → Reactome → GO (BP) | Pathway name fuzzy matching | "MAPK/ERK pathway" → KEGG:hsa04010 |
| METABOLITE | ChEBI → HMDB → KEGG Compound | Chemical name matching | "ATP" → CHEBI:15422 |
| CELL_OR_TISSUE | Cell Ontology → Uberon | Cell type name matching | "CD8+ T cell" → CL:0000625 |
| PROTEIN_DOMAIN | InterPro → Pfam | Domain name matching | "kinase domain" → IPR000719 |
| SEQUENCE_VARIANT | ClinVar → dbSNP → COSMIC | HGVS notation + gene context | "BRAF V600E" → ClinVar:13961 |
| ADVERSE_EVENT | MedDRA | Preferred term matching | "hepatotoxicity" → MedDRA:10019851 |
| BIOMARKER | Context-dependent (gene/protein/chemical) | Analyte name → source ontology | "PD-L1 TPS" → gene CD274 → HGNC:17635 |

### Amino Acid Context

Amino acids are NOT a separate entity type. They are captured contextually through:

1. **SEQUENCE_VARIANT attributes** — mutations specify amino acid changes: V600E = valine→glutamic acid at position 600. The `hgvs_notation` attribute carries the full amino acid substitution information.

2. **PROTEIN_DOMAIN attributes** — active site residues are captured as domain attributes: "catalytic triad (Ser195, His57, Asp102)" is an attribute of the serine protease catalytic domain.

3. **METABOLITE entities** — individual amino acids extracted as METABOLITE when discussed as signaling molecules (e.g., glutamate as a neurotransmitter, tryptophan in the kynurenine pathway) or metabolic substrates.

4. **Relation evidence fields** — binding site residues captured in evidence: "compound X forms hydrogen bonds with Lys745 and Met793 in the EGFR kinase domain."

**Rationale:** Extracting every amino acid mention as a separate entity would create massive node proliferation with limited navigational value. The three-pronged approach (variant notation, domain attributes, evidence text) preserves the information without cluttering the graph.

---

## 4. Relation Types (46)

### 4.1 Drug–Target Pharmacology

| Relation | Description | Source Types | Target Types | Biolink Alignment |
|---|---|---|---|---|
| **TARGETS** | Compound acts on a molecular target (general) | COMPOUND | PROTEIN, GENE | `biolink:target_for` (inverse) |
| **INHIBITS** | Compound or protein inhibits a target, pathway, or process | COMPOUND, PROTEIN | PROTEIN, GENE, PATHWAY | `biolink:negatively_regulates` |
| **ACTIVATES** | Compound or protein activates a target, pathway, or process | COMPOUND, PROTEIN | PROTEIN, GENE, PATHWAY | `biolink:positively_regulates` |
| **BINDS_TO** | Physical binding interaction (compound-protein, protein-protein) | COMPOUND, PROTEIN | PROTEIN | `biolink:physically_interacts_with` |
| **HAS_MECHANISM** | Compound operates through a specific mechanism of action | COMPOUND | MECHANISM_OF_ACTION | `biolink:has_molecular_activity` |

**Extraction guidance:**
- TARGETS is the general drug→target relation. Use INHIBITS or ACTIVATES when the text specifies the pharmacological direction.
- BINDS_TO is for physical interaction evidence (binding affinity, crystal structure, co-IP). It's more specific than TARGETS.
- Capture potency data (IC50, EC50, Ki, Kd) as attributes on the relation evidence field.

### 4.2 Drug–Disease

| Relation | Description | Source Types | Target Types | Biolink Alignment |
|---|---|---|---|---|
| **INDICATED_FOR** | Compound is indicated, studied, or approved for a disease | COMPOUND | DISEASE | `biolink:treats` |
| **CONTRAINDICATED_FOR** | Compound is contraindicated for a condition | COMPOUND | DISEASE | `biolink:contraindicated_for` |

**Extraction guidance:**
- INDICATED_FOR covers the full spectrum: approved indication, under investigation, preclinical evidence of efficacy
- Capture line of therapy (1L, 2L, adjuvant, neoadjuvant, maintenance) and patient subpopulation in the evidence field
- CONTRAINDICATED_FOR requires `review_required: true` — these are safety-critical

### 4.3 Drug–Clinical

| Relation | Description | Source Types | Target Types | Biolink Alignment |
|---|---|---|---|---|
| **EVALUATED_IN** | Compound is evaluated in a clinical trial | COMPOUND | CLINICAL_TRIAL | — |
| **CAUSES** | Compound causes an adverse event | COMPOUND | ADVERSE_EVENT | `biolink:has_adverse_event` |

**Extraction guidance:**
- EVALUATED_IN captures the compound→trial relationship. The trial entity carries the results.
- CAUSES should include frequency and severity in the evidence field when available.
- For combination regimens, create EVALUATED_IN for each compound individually.

### 4.4 Drug–Drug

| Relation | Description | Source Types | Target Types | Biolink Alignment |
|---|---|---|---|---|
| **DERIVED_FROM** | Compound is structurally derived from or successor to another | COMPOUND | COMPOUND | `biolink:derives_from` |
| **COMBINED_WITH** | Compounds used in therapeutic combination | COMPOUND | COMPOUND | — |
| **INTERACTS_WITH** | Pharmacological drug-drug interaction | COMPOUND | COMPOUND | `biolink:interacts_with` |

**Extraction guidance:**
- DERIVED_FROM: "next-generation", "analog of", "derivative of", "backup compound to"
- COMBINED_WITH: for combination therapy regimens. Direction doesn't matter (symmetric).
- INTERACTS_WITH: pharmacokinetic (CYP-mediated) or pharmacodynamic interactions. Include clinical significance.

### 4.5 Biology

| Relation | Description | Source Types | Target Types | Biolink Alignment |
|---|---|---|---|---|
| **ENCODES** | Gene encodes a protein | GENE | PROTEIN | `biolink:has_gene_product` |
| **PARTICIPATES_IN** | Protein or gene participates in a pathway | PROTEIN, GENE | PATHWAY | `biolink:participates_in` |
| **IMPLICATED_IN** | Gene, protein, pathway, or phenotype implicated in disease | GENE, PROTEIN, PATHWAY, PHENOTYPE | DISEASE | `biolink:gene_associated_with_condition` |
| **CONFERS_RESISTANCE_TO** | Mutation or mechanism confers resistance to a compound | GENE, PROTEIN, PHENOTYPE | COMPOUND | — |

**Extraction guidance:**
- ENCODES is the canonical gene→protein relationship. Only extract when the text explicitly discusses this relationship.
- PARTICIPATES_IN captures pathway membership. Source is the component, target is the pathway.
- IMPLICATED_IN covers genetic associations, functional studies, and GWAS findings. Include evidence strength.
- CONFERS_RESISTANCE_TO is critical for drug discovery — captures resistance mechanisms. `review_required: true`.

### 4.6 Biomarker Relations

| Relation | Description | Source Types | Target Types | Biolink Alignment |
|---|---|---|---|---|
| **PREDICTS_RESPONSE_TO** | Biomarker predicts response or resistance to therapy | BIOMARKER | COMPOUND, MECHANISM_OF_ACTION | `biolink:biomarker_for` |
| **DIAGNOSTIC_FOR** | Biomarker is diagnostic or prognostic for a disease | BIOMARKER | DISEASE | `biolink:biomarker_for` |

**Extraction guidance:**
- PREDICTS_RESPONSE_TO: "companion diagnostic", "predictive biomarker", "associated with sensitivity/resistance"
- DIAGNOSTIC_FOR: prognostic and diagnostic biomarkers for disease
- Both require `review_required: true` — biomarker claims need careful validation
- Capture the directionality (positive = response, negative = resistance) in the evidence field

### 4.7 Organizational & Publication

| Relation | Description | Source Types | Target Types | Biolink Alignment |
|---|---|---|---|---|
| **DEVELOPED_BY** | Compound or trial developed/sponsored by organization | COMPOUND, CLINICAL_TRIAL | ORGANIZATION | — |
| **PUBLISHED_IN** | Trial results or findings published in a publication | CLINICAL_TRIAL, COMPOUND | PUBLICATION | — |

### 4.8 Regulatory

| Relation | Description | Source Types | Target Types | Biolink Alignment |
|---|---|---|---|---|
| **GRANTS_APPROVAL_FOR** | Regulatory action applies to a compound | REGULATORY_ACTION | COMPOUND | — |

### 4.9 Fallback

| Relation | Description | Source Types | Target Types | Biolink Alignment |
|---|---|---|---|---|
| **ASSOCIATED_WITH** | General association — use ONLY when no specific relation applies | any | any | `biolink:associated_with` |

**If many relations land on ASSOCIATED_WITH, the schema is missing a relation type that the data needs.**

### 4.10 Molecular Biology Relations (NEW)

These relations capture the fundamental molecular biology linkages that connect genes, proteins, variants, domains, metabolites, cells, and tissues.

| Relation | Description | Source Types | Target Types | Biolink Alignment | RO/GO Reference |
|---|---|---|---|---|---|
| **EXPRESSED_IN** | Gene or protein is expressed in a cell type, tissue, or organ | GENE, PROTEIN | CELL_OR_TISSUE | `biolink:expressed_in` | RO:0002206 |
| **LOCALIZED_TO** | Protein is localized to a subcellular compartment or anatomical site | PROTEIN | CELL_OR_TISSUE | `biolink:located_in` | RO:0001025 |
| **HAS_VARIANT** | Gene harbors a specific sequence variant | GENE | SEQUENCE_VARIANT | `biolink:has_sequence_variant` | — |
| **HAS_DOMAIN** | Protein contains a functional domain | PROTEIN | PROTEIN_DOMAIN | `biolink:has_part` | BFO:0000051 |
| **METABOLIZED_BY** | Compound is metabolized by an enzyme (protein) | COMPOUND | PROTEIN | `biolink:is_substrate_of` | RO:0002233 |
| **PRODUCES_METABOLITE** | Enzymatic reaction or drug metabolism produces a metabolite | COMPOUND, PROTEIN | METABOLITE | `biolink:has_metabolite` | RO:0002234 |
| **SUBSTRATE_OF** | Metabolite is a substrate of an enzyme or pathway | METABOLITE | PROTEIN, PATHWAY | `biolink:is_substrate_of` | RO:0002233 |
| **PHOSPHORYLATES** | Kinase phosphorylates a substrate protein (activating or inactivating) | PROTEIN | PROTEIN | `biolink:affects` | GO:0006468 |
| **FORMS_COMPLEX_WITH** | Proteins form a multi-subunit complex | PROTEIN | PROTEIN | `biolink:physically_interacts_with` | GO:0065003 |
| **REGULATES_EXPRESSION** | Transcription factor or epigenetic modifier regulates gene expression | PROTEIN, COMPOUND | GENE | `biolink:regulates` | RO:0002211 |

**Extraction guidance for molecular biology relations:**

- **EXPRESSED_IN**: Critical for understanding tissue-specific drug effects. "EGFR is highly expressed in NSCLC cells" creates PROTEIN(EGFR) → EXPRESSED_IN → CELL_OR_TISSUE(NSCLC cells). Captures both normal expression and disease-specific overexpression. Include expression level (high, low, absent, overexpressed) in the evidence field.

- **LOCALIZED_TO**: Protein subcellular localization determines drug accessibility. "PD-L1 is expressed on the cell surface" → PROTEIN(PD-L1) → LOCALIZED_TO → CELL_OR_TISSUE(cell membrane). Distinct from EXPRESSED_IN (which is tissue-level, not subcellular).

- **HAS_VARIANT**: Links genes to their clinically relevant variants. "EGFR harbors the T790M resistance mutation" → GENE(EGFR) → HAS_VARIANT → SEQUENCE_VARIANT(T790M). The variant entity then participates in its own relations (CONFERS_RESISTANCE_TO, PREDICTS_RESPONSE_TO).

- **HAS_DOMAIN**: Links proteins to their functional domains. "The kinase domain of EGFR is the binding site for erlotinib" → PROTEIN(EGFR) → HAS_DOMAIN → PROTEIN_DOMAIN(kinase domain). Enables queries like "what drugs target the bromodomain?"

- **METABOLIZED_BY**: Drug metabolism by CYP enzymes. "Tamoxifen is metabolized by CYP2D6 to its active metabolite endoxifen" → COMPOUND(tamoxifen) → METABOLIZED_BY → PROTEIN(CYP2D6). Critical for drug-drug interaction prediction and pharmacogenomics.

- **PRODUCES_METABOLITE**: Drug metabolism products. "CYP2D6 converts tamoxifen to endoxifen" → COMPOUND(tamoxifen) → PRODUCES_METABOLITE → METABOLITE(endoxifen). Or for endogenous pathways: PROTEIN(aromatase) → PRODUCES_METABOLITE → METABOLITE(estradiol).

- **SUBSTRATE_OF**: Metabolite-enzyme relationships in pathways. "Pyruvate is a substrate of lactate dehydrogenase" → METABOLITE(pyruvate) → SUBSTRATE_OF → PROTEIN(LDH). Important for understanding metabolic targets.

- **PHOSPHORYLATES**: Kinase signaling cascades. "MEK phosphorylates ERK" → PROTEIN(MEK) → PHOSPHORYLATES → PROTEIN(ERK). Captures the signaling chain that drugs interrupt.

- **FORMS_COMPLEX_WITH**: Multi-protein complexes relevant to drug targets. "PD-1 forms a complex with PD-L1" → PROTEIN(PD-1) → FORMS_COMPLEX_WITH → PROTEIN(PD-L1). Symmetric relation.

- **REGULATES_EXPRESSION**: Transcription factor and epigenetic regulation. "MYC upregulates expression of CDK4" → PROTEIN(MYC) → REGULATES_EXPRESSION → GENE(CDK4). Also covers drug effects: "HDAC inhibitor X increases expression of tumor suppressor Y" → COMPOUND → REGULATES_EXPRESSION → GENE.

### 4.11 Extended RAG Query Patterns (Molecular Biology)

| Query Pattern | Graph Traversal |
|---|---|
| "Where is HER2 expressed?" | PROTEIN(HER2) → EXPRESSED_IN → CELL_OR_TISSUE |
| "What domains does EGFR have?" | PROTEIN(EGFR) → HAS_DOMAIN → PROTEIN_DOMAIN |
| "What variants of KRAS are clinically relevant?" | GENE(KRAS) → HAS_VARIANT → SEQUENCE_VARIANT |
| "What enzyme metabolizes tamoxifen?" | COMPOUND(tamoxifen) → METABOLIZED_BY → PROTEIN |
| "What does CYP3A4 metabolize?" | PROTEIN(CYP3A4) ← METABOLIZED_BY ← COMPOUND |
| "What proteins interact with PD-1?" | PROTEIN(PD-1) → FORMS_COMPLEX_WITH/BINDS_TO → PROTEIN |
| "What phosphorylates ERK?" | PROTEIN(ERK) ← PHOSPHORYLATES ← PROTEIN |
| "What genes does MYC regulate?" | PROTEIN(MYC) → REGULATES_EXPRESSION → GENE |
| "What metabolites are produced by drug X?" | COMPOUND(X) → PRODUCES_METABOLITE → METABOLITE |
| "In what subcellular compartment is target Y located?" | PROTEIN(Y) → LOCALIZED_TO → CELL_OR_TISSUE |
| "What is the full signaling cascade from EGFR to cell proliferation?" | PROTEIN(EGFR) → PHOSPHORYLATES → PROTEIN(RAS) → ACTIVATES → PROTEIN(RAF) → PHOSPHORYLATES → PROTEIN(MEK) → ... → PATHWAY(cell proliferation) |

---

## 5. Relation Properties

Every relation extracted by sift-kg carries these fields (inherited from core):

| Property | Type | Purpose |
|---|---|---|
| `confidence` | float 0.0-1.0 | How clearly the text supports this relation |
| `evidence` | string | Direct quote from source text |
| `source_document` | string | Document ID |
| `support_count` | int | Number of independent mentions (after canonicalization) |
| `support_documents` | list[string] | All documents mentioning this relation |

For drug discovery, confidence scoring should follow these guidelines:
- **0.9-1.0**: Explicitly stated with strong evidence ("pembrolizumab is a PD-1 inhibitor approved for...")
- **0.7-0.9**: Clearly implied with supporting evidence ("treatment with X resulted in tumor regression, suggesting it targets Y pathway")
- **0.5-0.7**: Reasonable inference but indirect ("compound X, which acts similarly to Y inhibitors...")
- **< 0.5**: Speculative or very indirect — these should be flagged for review

---

## 6. System Context Prompt

The `system_context` field in the domain YAML is injected into every extraction prompt. For drug discovery, it must orient the LLM to:

1. **Scientific rigor** — Extract only explicitly stated facts, not inferences
2. **Nomenclature standards** — INN, HGNC, MeSH preferred terms
3. **Disambiguation rules** — Gene vs Protein, Target vs Mechanism, Disease vs Phenotype
4. **Document type awareness** — Different extraction strategies for research articles, reviews, regulatory documents, patent claims
5. **Confidence calibration** — What warrants high vs low confidence in pharmaceutical literature

See Section 8 for the full system_context text.

---

## 7. Review-Required Relations

These relation types carry `review_required: true` and are automatically flagged in `relation_review.yaml` for human verification:

| Relation | Why Review Required |
|---|---|
| CONTRAINDICATED_FOR | Safety-critical claim |
| PREDICTS_RESPONSE_TO | Biomarker-treatment associations need validation |
| DIAGNOSTIC_FOR | Diagnostic claims need evidence strength assessment |
| CONFERS_RESISTANCE_TO | Resistance mechanisms have major clinical implications |

---

## 8. Full Domain YAML — system_context

```
You are analyzing drug discovery and pharmaceutical research documents
to build a scientifically rigorous knowledge graph. Your extractions
will be used in a production RAG system where accuracy is paramount.

DOCUMENT TYPE AWARENESS:
- Research articles (PubMed/bioRxiv): Extract findings with their
  statistical evidence. Note whether findings are from in vitro, in
  vivo (animal), or human studies.
- Clinical trial reports: Extract trial design, endpoints, and results.
  Capture hazard ratios, response rates, and p-values.
- Review articles: Extract consensus knowledge and note conflicting
  evidence across studies.
- Regulatory documents: Extract approval decisions, indications,
  safety warnings, and label changes.
- Patent filings: Extract compound structures, claimed mechanisms,
  and therapeutic applications. Note that patent claims are aspirational.

NOMENCLATURE STANDARDS:
- Drugs: Use INN (International Nonproprietary Name) as the canonical
  name. Record brand names and development codes as attributes.
- Genes: Use official HGNC symbols (EGFR, TP53, BRCA1). Mutations
  use protein-level notation (V600E, G12C, T790M).
- Proteins: Use standard names from UniProt. Distinguish from genes.
- Diseases: Use MeSH-preferred terms. Include molecular subtypes when
  they define distinct therapeutic approaches.
- Adverse events: Use MedDRA preferred terms. Include CTCAE grades.
- Biomarkers: Use standard abbreviations (PD-L1, TMB, MSI-H).

DISAMBIGUATION RULES:
- GENE vs PROTEIN: "EGFR mutation" → GENE; "EGFR receptor" → PROTEIN.
  When text is ambiguous, use GENE for genomic context, PROTEIN for
  functional/pharmacological context.
- COMPOUND vs MECHANISM_OF_ACTION: "pembrolizumab" is a COMPOUND;
  "PD-1 checkpoint blockade" is a MECHANISM_OF_ACTION.
- DISEASE vs PHENOTYPE: "NSCLC" is a DISEASE; "high tumor mutational
  burden" is a PHENOTYPE (or BIOMARKER if used for treatment selection).
- ADVERSE_EVENT vs DISEASE: "hepatotoxicity from drug X" is an
  ADVERSE_EVENT; "hepatitis B" is a DISEASE.

MOLECULAR BIOLOGY DISAMBIGUATION:
- GENE vs SEQUENCE_VARIANT: "BRAF" is a GENE; "BRAF V600E" is a
  SEQUENCE_VARIANT. Extract both and link with HAS_VARIANT.
- PROTEIN vs PROTEIN_DOMAIN: "EGFR" is a PROTEIN; "EGFR kinase
  domain" is a PROTEIN_DOMAIN. Link with HAS_DOMAIN.
- COMPOUND vs METABOLITE: Exogenous therapeutic agents are COMPOUND;
  endogenous molecules are METABOLITE. "Dopamine" used therapeutically
  → COMPOUND; "dopamine" as neurotransmitter → METABOLITE.
- CELL_OR_TISSUE covers cell types (T cell), tissues (liver),
  organs (brain), subcellular compartments (nucleus), and cell lines
  (HeLa). Use the entity_subtype attribute to distinguish.
- PATHWAY vs individual proteins: "PI3K/AKT/mTOR pathway" is a
  PATHWAY entity. "PI3K", "AKT", "mTOR" are individual PROTEIN
  entities that PARTICIPATE_IN that pathway.
- EXPRESSED_IN vs LOCALIZED_TO: EXPRESSED_IN is tissue/cell-level
  ("HER2 is expressed in breast cancer cells"). LOCALIZED_TO is
  subcellular ("PD-L1 on cell surface"). Both use CELL_OR_TISSUE
  as target but capture different biological levels.

AMINO ACID HANDLING:
- Do NOT extract individual amino acids as separate entities
- Capture amino acid changes within SEQUENCE_VARIANT notation:
  V600E means valine→glutamic acid at position 600
- Capture binding site residues in relation evidence text:
  "binds to Lys745 in the ATP-binding pocket"
- Extract amino acids as METABOLITE only when discussed as
  signaling molecules (glutamate) or metabolic substrates
  (tryptophan in kynurenine pathway)

POST-TRANSLATIONAL MODIFICATIONS:
- Phosphorylation events between proteins use PHOSPHORYLATES relation
- Other PTMs (ubiquitination, acetylation, SUMOylation, glycosylation)
  are captured as attributes on PROTEIN entities
- When a drug modulates a PTM (e.g., HDAC inhibitor affects
  acetylation), use REGULATES_EXPRESSION or INHIBITS as appropriate

CONFIDENCE CALIBRATION:
- 0.9-1.0: Explicitly stated, primary finding, strong statistical evidence
- 0.7-0.9: Clearly supported but secondary or from non-primary endpoints
- 0.5-0.7: Reasonable inference, indirect evidence, or from preclinical data
- <0.5: Speculative, from case reports, or unconfirmed
```

---

## 9. RAG Query Pattern Coverage

The schema is designed to support these high-value drug discovery query patterns:

| Query Pattern | Graph Traversal |
|---|---|
| "What drugs target KRAS G12C?" | GENE(KRAS G12C) ← TARGETS ← COMPOUND |
| "What are the clinical results for pembrolizumab in NSCLC?" | COMPOUND(pembrolizumab) → EVALUATED_IN → CLINICAL_TRIAL; COMPOUND → INDICATED_FOR → DISEASE(NSCLC) |
| "What biomarkers predict response to checkpoint inhibitors?" | MECHANISM_OF_ACTION(checkpoint blockade) ← PREDICTS_RESPONSE_TO ← BIOMARKER |
| "What adverse events does sotorasib cause?" | COMPOUND(sotorasib) → CAUSES → ADVERSE_EVENT |
| "What resistance mechanisms exist for osimertinib?" | COMPOUND(osimertinib) ← CONFERS_RESISTANCE_TO ← GENE/PROTEIN |
| "Compare safety profiles of CDK4/6 inhibitors" | MECHANISM_OF_ACTION(CDK4/6 inhibition) ← HAS_MECHANISM ← COMPOUND → CAUSES → ADVERSE_EVENT |
| "What pathways are implicated in triple-negative breast cancer?" | DISEASE(TNBC) ← IMPLICATED_IN ← PATHWAY |
| "Who developed this drug and what trials are ongoing?" | COMPOUND → DEVELOPED_BY → ORGANIZATION; COMPOUND → EVALUATED_IN → CLINICAL_TRIAL |
| "What companion diagnostics exist for this indication?" | COMPOUND → INDICATED_FOR → DISEASE; BIOMARKER → PREDICTS_RESPONSE_TO → COMPOUND |
| "What is the mechanism of action of drug X?" | COMPOUND → HAS_MECHANISM → MECHANISM_OF_ACTION; COMPOUND → TARGETS/INHIBITS/ACTIVATES → PROTEIN |

---

## 10. Symmetric Relations

| Relation | Symmetric? | Rationale |
|---|---|---|
| COMBINED_WITH | Yes | Combination therapy is bidirectional |
| INTERACTS_WITH | Yes | Drug interactions are mutual |
| BINDS_TO | Yes | Binding is mutual (though affinity may differ) |
| FORMS_COMPLEX_WITH | Yes | Protein complex formation is mutual |
| ASSOCIATED_WITH | Yes | General association has no directionality |
| All others | No | Have clear source→target semantics |

---

## 11. What This Schema Does NOT Cover (Future Extensions)

| Area | Rationale for Exclusion |
|---|---|
| Protein 3D structure details | PDB/AlphaFold data requires structural bioinformatics tooling, not NLP |
| Detailed ADME/PK parameters | Cmax, AUC, half-life are best as COMPOUND attributes, not entities |
| Epigenomic landscape | CpG methylation, histone marks too granular for document extraction |
| Patient-level data | PHI/HIPAA concerns; different data model needed |
| Pricing / market data | Separate domain; financial not scientific |
| Manufacturing / CMC | Process chemistry is a distinct domain |
| Patent claim analysis | Legal interpretation requires separate tooling |
| Pharmacokinetics (ADME) | Best captured as compound attributes, not separate entities |
| Single-cell omics data | Too granular for document-level extraction |
| Chemical structure data | SMILES/InChI require chemical informatics tooling, not NLP |

These can be added as domain extensions or companion schemas.

---

## 12. Validation Criteria

The schema should be validated against:

1. **Coverage test**: Extract from 5-10 representative PubMed abstracts spanning oncology, immunology, rare disease, and neuroscience. Verify that ≥90% of scientifically meaningful entities map to defined types.

2. **Precision test**: Review extracted relations for accuracy. Target ≥85% precision for high-confidence (>0.8) extractions.

3. **Disambiguation test**: Feed text with ambiguous gene/protein mentions and verify correct classification rate.

4. **Ontology mapping test**: Verify that extracted entity names can be mapped to standard identifiers (ChEBI, HGNC, MeSH) at ≥70% rate.

5. **RAG retrieval test**: Run the 10 query patterns from Section 9 against a built graph and verify meaningful subgraphs are returned.

6. **Molecular biology linkage test**: Verify that gene→protein→domain chains and signaling cascades (PHOSPHORYLATES chains) form connected subgraphs, not isolated nodes.

7. **Variant resolution test**: Feed articles discussing well-known actionable variants (BRAF V600E, KRAS G12C, EGFR T790M) and verify they're extracted as SEQUENCE_VARIANT entities linked to their parent GENE via HAS_VARIANT.

---

## 13. Biomedical Ontology Ecosystem Reference

This section documents the full ontology ecosystem the schema is designed to interoperate with. These are the authoritative sources for entity resolution and cross-referencing.

### Chemical/Drug Ontologies

| Ontology | Coverage | Maintained By | Use in Schema |
|---|---|---|---|
| **ChEBI** (Chemical Entities of Biological Interest) | ~65,000 molecular entities with roles, classes, relationships | EMBL-EBI / OBO Foundry | Primary chemical classification. COMPOUND and METABOLITE entities map here. ChEBI roles (inhibitor, agonist) inform MECHANISM_OF_ACTION. |
| **DrugBank** | ~15,000 drugs with targets, pathways, interactions | University of Alberta | Drug-target and drug-drug interaction validation. COMPOUND entities cross-reference here. |
| **ChEMBL** | ~2.4M compounds with bioactivity data | EMBL-EBI | Compound bioactivity validation. IC50/EC50 data validates TARGETS/INHIBITS relations. |
| **UNII** (Unique Ingredient Identifier) | FDA substance registry | FDA | Regulatory identification for COMPOUND entities. |
| **ATC** (Anatomical Therapeutic Chemical) | WHO drug classification | WHO | Therapeutic class hierarchy for MECHANISM_OF_ACTION grouping. |

### Gene/Protein Ontologies

| Ontology | Coverage | Maintained By | Use in Schema |
|---|---|---|---|
| **HGNC** (HUGO Gene Nomenclature Committee) | ~43,000 human gene symbols | EMBL-EBI | **Canonical naming standard** for GENE entities. Every gene must use HGNC symbol. |
| **Gene Ontology (GO)** | 3 sub-ontologies: Molecular Function, Biological Process, Cellular Component | GO Consortium | PATHWAY entities align to GO:BP. PROTEIN functional annotations align to GO:MF. CELL_OR_TISSUE subcellular locations align to GO:CC. |
| **UniProtKB** | ~570,000 reviewed human protein entries | UniProt Consortium | **Canonical reference** for PROTEIN entities. Provides domain annotations, PTMs, function. |
| **InterPro** | ~40,000 protein domain/family signatures | EMBL-EBI | PROTEIN_DOMAIN entities map here. Integrates Pfam, SMART, PROSITE, CDD. |
| **Pfam** | ~20,000 protein families | EMBL-EBI | Specific domain family identifiers for PROTEIN_DOMAIN. |
| **Protein Ontology (PRO)** | Protein forms, modifications, complexes | PIR/Georgetown | Modified protein forms (phospho-ERK, ubiquitinated p53). Informs PTM attributes. |
| **Sequence Ontology (SO)** | Types of genomic features | OBO Foundry | SEQUENCE_VARIANT type classification (SO:0001583 = missense_variant). |

### Disease Ontologies

| Ontology | Coverage | Maintained By | Use in Schema |
|---|---|---|---|
| **MeSH** (Medical Subject Headings) | ~30,000 descriptors | NLM (National Library of Medicine) | **Primary naming standard** for DISEASE entities. All PubMed articles are MeSH-indexed. |
| **Disease Ontology (DO)** | ~12,000 disease terms with relationships | OBO Foundry | Disease classification hierarchy. DISEASE entities map here. |
| **ICD-11** | WHO disease classification | WHO | Clinical coding for DISEASE entities. |
| **OMIM** | ~9,000 genetic diseases | Johns Hopkins | Genetic disease associations. Links GENE → DISEASE via IMPLICATED_IN. |
| **Orphanet** | ~7,000 rare diseases | INSERM | Rare/orphan disease identification for DISEASE entities. |
| **HPO** (Human Phenotype Ontology) | ~18,000 clinical phenotype terms | Monarch Initiative | PHENOTYPE entity naming standard. Clinical manifestations. |

### Clinical and Safety Ontologies

| Ontology | Coverage | Maintained By | Use in Schema |
|---|---|---|---|
| **MedDRA** | ~80,000 medical terms for regulatory | ICH (International Council for Harmonisation) | **Standard terminology** for ADVERSE_EVENT entities. PT (Preferred Term) level. |
| **CTCAE** | Adverse event severity grading | NCI | ADVERSE_EVENT severity attributes (Grade 1-5). |
| **BEST** (Biomarkers, EndpointS, and other Tools) | Biomarker classification framework | FDA/NIH | BIOMARKER entity classification (predictive, prognostic, diagnostic). |
| **ClinicalTrials.gov schema** | Trial registration data model | NLM | CLINICAL_TRIAL entity attributes (phase, design, endpoints, NCT ID). |

### Variant Databases

| Database | Coverage | Maintained By | Use in Schema |
|---|---|---|---|
| **ClinVar** | Clinical significance of variants | NCBI | SEQUENCE_VARIANT clinical significance classification (pathogenic/benign/VUS). |
| **dbSNP** | ~700M SNPs | NCBI | rs identifiers for SEQUENCE_VARIANT entities. |
| **COSMIC** | Somatic mutations in cancer | Sanger Institute | Cancer-specific variant identifiers. Somatic SEQUENCE_VARIANT entities. |
| **gnomAD** | Population allele frequencies | Broad Institute | Allele frequency attributes on SEQUENCE_VARIANT. |
| **HGVS nomenclature** | Variant naming standard | HGVS | **Canonical notation** for SEQUENCE_VARIANT: c. (coding), p. (protein), g. (genomic). |

### Pathway and Process Databases

| Database | Coverage | Maintained By | Use in Schema |
|---|---|---|---|
| **KEGG** | ~500 reference pathways | Kanehisa Labs | PATHWAY entity identifiers. Metabolic and signaling pathways. |
| **Reactome** | ~2,600 human pathways | EMBL-EBI/ORCF | Detailed pathway models. PATHWAY and PROTEIN participation. |
| **WikiPathways** | ~3,000 community pathways | WikiPathways Foundation | Additional pathway coverage. |

### Anatomical and Cell Ontologies

| Ontology | Coverage | Maintained By | Use in Schema |
|---|---|---|---|
| **Cell Ontology (CL)** | ~2,700 cell types | OBO Foundry | CELL_OR_TISSUE entity naming for cell types (CL:0000084 = T cell). |
| **Uberon** | Cross-species anatomy | OBO Foundry | CELL_OR_TISSUE entity naming for tissues/organs (UBERON:0002107 = liver). |
| **BRENDA Tissue Ontology** | Enzyme source tissues | TU Braunschweig | Tissue expression context for EXPRESSED_IN relations. |

### Relation Ontology Grounding

All relations in this schema are grounded in the OBO Relation Ontology (RO) and/or Biolink predicates where possible:

| Schema Relation | RO ID | Biolink Predicate | GO Process (if applicable) |
|---|---|---|---|
| ENCODES | RO:0002205 | `has_gene_product` | — |
| EXPRESSED_IN | RO:0002206 | `expressed_in` | — |
| LOCALIZED_TO | RO:0001025 | `located_in` | — |
| PARTICIPATES_IN | RO:0000056 | `participates_in` | — |
| INHIBITS | RO:0002212 | `negatively_regulates` | — |
| ACTIVATES | RO:0002213 | `positively_regulates` | — |
| BINDS_TO | RO:0002436 | `physically_interacts_with` | — |
| TARGETS | — | `target_for` (inverse) | — |
| PHOSPHORYLATES | — | `affects` | GO:0006468 (protein phosphorylation) |
| FORMS_COMPLEX_WITH | — | `physically_interacts_with` | GO:0065003 (protein-containing complex assembly) |
| REGULATES_EXPRESSION | RO:0002211 | `regulates` | GO:0010468 (regulation of gene expression) |
| METABOLIZED_BY | RO:0002233 | `is_substrate_of` | — |
| PRODUCES_METABOLITE | RO:0002234 | `has_metabolite` | — |
| SUBSTRATE_OF | RO:0002233 | `is_substrate_of` | — |
| IMPLICATED_IN | — | `gene_associated_with_condition` | — |
| INDICATED_FOR | — | `treats` | — |
| CAUSES | — | `has_adverse_event` | — |
| HAS_VARIANT | — | `has_sequence_variant` | — |
| HAS_DOMAIN | BFO:0000051 | `has_part` | — |
| DERIVED_FROM | — | `derives_from` | — |
| CONFERS_RESISTANCE_TO | — | — | — |
| PREDICTS_RESPONSE_TO | — | `biomarker_for` | — |

---

## 14. Schema Summary Statistics

| Category | Count |
|---|---|
| Entity types | 23 |
| Relation types | 46 |
| Review-required relations | 6 |
| Symmetric relations | 6 |
| Ontologies aligned to | 45+ |
| RAG query patterns covered | 30+ |
| Biolink predicates mapped | 24 |
| RO relations grounded | 12 |
| Regex validation patterns | 12 |
| Required validation libraries | RDKit, Biopython (optional deps) |

---

## 15. Specialty Domain Extensions

### 15.1 Statistical Genetics & GWAS

Drug discovery increasingly relies on genetic evidence from GWAS, Mendelian randomization, PheWAS, and burden tests to validate targets and predict drug safety.

**Additional Entity Types:**

#### GENETIC_ASSOCIATION

**What it captures:** Statistical associations between genetic variants/loci and traits or diseases — GWAS hits, eQTL signals, pQTL signals, Mendelian randomization results.

**Biolink alignment:** `biolink:VariantToDiseaseAssociation`, `biolink:VariantToPhenotypicFeatureAssociation`

**Ontology grounding:**
- GWAS Catalog (EFO-based trait mapping)
- EFO (Experimental Factor Ontology) for trait terms
- OpenTargets genetics pipeline

**Naming conventions:**
- Name by locus and trait: "PCSK9 locus–LDL cholesterol association"
- For GWAS hits: include lead SNP, p-value, effect size, and population
- For eQTL/pQTL: include tissue context and target gene/protein

**Key attributes:**
- `study_type`: GWAS | exome_sequencing | Mendelian_randomization | eQTL | pQTL | PheWAS | burden_test | fine_mapping
- `p_value`: statistical significance (e.g., 5e-8)
- `effect_size`: odds ratio, beta coefficient, hazard ratio
- `confidence_interval`: 95% CI bounds
- `sample_size`: number of individuals
- `population`: ancestry/ethnicity of study population (European, East Asian, African, multi-ethnic)
- `lead_snp`: rs identifier of the lead variant
- `locus`: genomic region (e.g., 9p21.3, 1q23.3)
- `trait_efo_id`: EFO trait identifier
- `replication_status`: replicated | not replicated | meta-analysis

**Extraction hints:**
- Extract GWAS findings when they involve drug targets or disease biology — not every association in a GWAS paper
- Capture the evidence strength: genome-wide significant (p < 5×10⁻⁸) vs suggestive (p < 1×10⁻⁵)
- Mendelian randomization results provide causal inference — flag these as higher-value evidence
- eQTL/pQTL data links variants to gene expression changes in specific tissues — extract the tissue context
- OpenTargets uses genetic evidence to score drug targets — these scores can inform confidence

**Additional Relations for Statistical Genetics:**

| Relation | Description | Source Types | Target Types | Biolink Alignment |
|---|---|---|---|---|
| **GENETICALLY_ASSOCIATED_WITH** | Variant/locus shows statistical association with trait/disease | SEQUENCE_VARIANT, GENE, GENETIC_ASSOCIATION | DISEASE, PHENOTYPE | `biolink:gene_associated_with_condition` |
| **MODULATES_EXPRESSION_OF** | Variant affects expression level of a gene (eQTL) | SEQUENCE_VARIANT | GENE | `biolink:affects_expression_of` |
| **MODULATES_PROTEIN_LEVEL_OF** | Variant affects protein abundance (pQTL) | SEQUENCE_VARIANT | PROTEIN | `biolink:affects` |
| **CAUSAL_FOR** | Mendelian randomization evidence for causal relationship | GENE, PROTEIN | DISEASE, PHENOTYPE | `biolink:causes` |

**Extraction guidance:**
- GENETICALLY_ASSOCIATED_WITH is for statistical associations. Include p-value and effect size in evidence.
- MODULATES_EXPRESSION_OF is specifically for eQTL findings — include tissue context.
- CAUSAL_FOR requires Mendelian randomization or other causal inference evidence — `review_required: true`.
- Distinguish genetic association (statistical) from functional validation (mechanistic). Association alone does not establish causation.

### 15.2 Proteomics & Protein Science

Drug discovery proteomics encompasses mass spectrometry-based protein identification, protein-protein interaction networks, structural biology, and targeted protein degradation.

**Additional Entity Type:**

#### PROTEIN_COMPLEX

**What it captures:** Multi-protein assemblies that function as single units — proteasome, ribosome, spliceosome, chromatin remodeling complexes, signaling complexes, antibody-antigen complexes.

**Biolink alignment:** `biolink:MacromolecularComplex`

**Ontology grounding:**
- Gene Ontology Cellular Component (GO:CC) — protein complexes (GO:0032991)
- Complex Portal (EBI) — curated protein complexes
- PDB — structural data for complexes

**Naming conventions:**
- Use established complex names: "26S proteasome", "PRC2 complex", "cohesin complex", "TFIID"
- For transient complexes: name by components ("PD-1/PD-L1 complex", "EGFR/HER2 heterodimer")

**Key attributes:**
- `complex_type`: stable | transient | obligate | non-obligate
- `subunit_count`: number of protein subunits
- `complex_portal_id`: EBI Complex Portal identifier
- `pdb_id`: PDB structure identifier when available
- `molecular_weight`: when discussed

**Extraction hints:**
- Extract complexes that are drug targets (proteasome for bortezomib, PRC2 for tazemetostat)
- Include signaling complexes when they're the functional unit of drug action
- Antibody-target complexes relevant to biologic drug development
- DNA/RNA-protein complexes when they're the target of gene therapy or antisense approaches

**Additional Relations for Proteomics:**

| Relation | Description | Source Types | Target Types |
|---|---|---|---|
| **SUBUNIT_OF** | Protein is a subunit of a complex | PROTEIN | PROTEIN_COMPLEX |
| **CLEAVES** | Protease cleaves a substrate protein | PROTEIN | PROTEIN |
| **UBIQUITINATES** | E3 ligase ubiquitinates a substrate (relevant to PROTACs/degraders) | PROTEIN | PROTEIN |
| **DEGRADES** | Compound or protein degrades a target protein (PROTAC, molecular glue) | COMPOUND, PROTEIN | PROTEIN |

**Extraction guidance:**
- SUBUNIT_OF: "BRD4 is a component of the super-elongation complex" → PROTEIN(BRD4) → SUBUNIT_OF → PROTEIN_COMPLEX(SEC).
- CLEAVES: relevant for protease drug targets. "Caspase-3 cleaves PARP" → PROTEIN(caspase-3) → CLEAVES → PROTEIN(PARP).
- UBIQUITINATES: critical for PROTAC drug design. "CRBN ubiquitinates IKZF1" → PROTEIN(CRBN) → UBIQUITINATES → PROTEIN(IKZF1).
- DEGRADES: for targeted protein degradation therapeutics. "ARV-110 degrades the androgen receptor" → COMPOUND(ARV-110) → DEGRADES → PROTEIN(AR).

### 15.3 Genomics & Transcriptomics

Coverage for large-scale genomic and transcriptomic technologies used in drug discovery.

**Additional Entity Type:**

#### GENE_SIGNATURE

**What it captures:** Multi-gene expression signatures, gene panels, and molecular classifiers used for patient stratification, response prediction, and disease subtyping.

**Biolink alignment:** No direct equivalent — closest is `biolink:GeneGroupingMixin`

**Ontology grounding:**
- MSigDB (Molecular Signatures Database) — curated gene sets
- GSEA (Gene Set Enrichment Analysis) — pathway-level signatures
- Oncotype DX, MammaPrint, Foundation CDx — commercial panels

**Naming conventions:**
- Named signatures: "Oncotype DX recurrence score", "PAM50 subtype classifier", "tumor inflammation signature (TIS)"
- Unnamed signatures: describe by function — "18-gene T-cell inflammation signature", "interferon-gamma response signature"

**Key attributes:**
- `signature_type`: expression | mutation | methylation | copy_number | multi-omic
- `gene_count`: number of genes in the signature
- `application`: subtyping | prognosis | prediction | diagnosis
- `platform`: RNA-seq | microarray | NanoString | NGS panel
- `validated`: clinically validated | research-use only

**Extraction hints:**
- Extract gene signatures that are used for clinical decision-making or drug development stratification
- Distinguish single-gene biomarkers (BIOMARKER entity) from multi-gene signatures (GENE_SIGNATURE entity)
- Capture the application context — is this signature used for patient selection, prognosis, or subtyping?
- Note whether the signature has clinical validation (CLIA/CAP certified) or is research-grade

**Additional Relations for Genomics:**

| Relation | Description | Source Types | Target Types |
|---|---|---|---|
| **MEMBER_OF** | Gene is a member of a gene signature or panel | GENE | GENE_SIGNATURE |
| **CLASSIFIES** | Gene signature classifies a disease subtype or predicts an outcome | GENE_SIGNATURE | DISEASE, PHENOTYPE |
| **ENRICHED_IN** | Pathway or process is enriched in a gene signature or cellular context | PATHWAY | GENE_SIGNATURE, CELL_OR_TISSUE, DISEASE |

### 15.4 Immunology & Immuno-oncology

Critical for the large and growing immunotherapy drug space.

**Entities already covered:** PROTEIN (immune checkpoints, cytokines), CELL_OR_TISSUE (immune cell types), MECHANISM_OF_ACTION (checkpoint blockade, CAR-T, BiTE), PATHWAY (immune signaling), BIOMARKER (PD-L1, TMB, MSI-H).

**Key immunological concepts captured through existing entities:**
- Immune checkpoints: PD-1, PD-L1, CTLA-4, LAG-3, TIM-3, TIGIT → PROTEIN
- Cytokines: IL-2, IFN-γ, TNF-α, IL-6, TGF-β → METABOLITE (when endogenous) or COMPOUND (when therapeutic, e.g., aldesleukin)
- Immune cell subtypes: CD8+ T cells, Tregs, MDSCs, M1/M2 macrophages, NK cells → CELL_OR_TISSUE
- Immune pathways: T cell activation, antigen presentation, complement cascade → PATHWAY
- Immune phenotypes: "hot" vs "cold" tumors, immune desert, immune excluded → PHENOTYPE

**Additional immunology-specific relation guidance:**
- Cytokine signaling: METABOLITE(IL-2) → ACTIVATES → PROTEIN(IL-2 receptor) → ACTIVATES → PATHWAY(JAK/STAT signaling) → ACTIVATES → CELL_OR_TISSUE(T cell proliferation)
- Checkpoint blockade: COMPOUND(pembrolizumab) → BINDS_TO → PROTEIN(PD-1) → disrupts → PROTEIN(PD-1) FORMS_COMPLEX_WITH PROTEIN(PD-L1)
- CAR-T: COMPOUND(tisagenlecleucel) → TARGETS → PROTEIN(CD19) → EXPRESSED_IN → CELL_OR_TISSUE(B cells)

### 15.5 Epigenetics & Gene Regulation

**Entities already covered:** PROTEIN (epigenetic enzymes — HDACs, BRDs, EZH2, DNMTs, KDMs), MECHANISM_OF_ACTION (epigenetic modulation), GENE (target genes), COMPOUND (epigenetic drugs).

**Key epigenetic concepts mapped to existing entities:**
- Writers: HMTs (EZH2, DOT1L), DNMTs (DNMT1, DNMT3A), HATs → PROTEIN
- Erasers: HDACs, KDMs (KDM5A, KDM6A), TET enzymes → PROTEIN
- Readers: BRD4, TRIM33, chromodomain proteins → PROTEIN
- Marks: H3K27me3, H3K4me3, 5-methylcytosine → captured as attributes on relations or in evidence text
- REGULATES_EXPRESSION relation handles the functional consequence: PROTEIN(EZH2) → REGULATES_EXPRESSION → GENE(CDKN2A)

### 15.6 Pharmacogenomics

The intersection of genetics and drug response — how genetic variation affects drug efficacy and safety.

**Covered through existing entities and relations:**
- Pharmacogene variants: CYP2D6 poor metabolizer, DPYD deficiency → SEQUENCE_VARIANT
- Drug metabolism enzymes: CYP2D6, CYP3A4, UGT1A1, DPYD → PROTEIN
- Drug-variant associations: SEQUENCE_VARIANT → PREDICTS_RESPONSE_TO → COMPOUND
- Metabolism: COMPOUND → METABOLIZED_BY → PROTEIN(CYP enzyme)

**Key pharmacogenomic query patterns:**

| Query | Traversal |
|---|---|
| "What CYP enzymes metabolize this drug?" | COMPOUND → METABOLIZED_BY → PROTEIN |
| "What variants affect response to tamoxifen?" | COMPOUND(tamoxifen) ← PREDICTS_RESPONSE_TO ← BIOMARKER/SEQUENCE_VARIANT |
| "Is CYP2D6 PM status relevant for this drug?" | SEQUENCE_VARIANT(CYP2D6 *4) → PREDICTS_RESPONSE_TO → COMPOUND; COMPOUND → METABOLIZED_BY → PROTEIN(CYP2D6) |
| "What are the DPYD considerations for fluoropyrimidines?" | GENE(DPYD) → HAS_VARIANT → SEQUENCE_VARIANT → PREDICTS_RESPONSE_TO → COMPOUND(5-FU); COMPOUND → CAUSES → ADVERSE_EVENT(DPD-deficiency toxicity) |

---

## 16. Molecular Identifier Extraction (SMILES, Sequences, Patent Notation)

### 16.1 The Problem

Drug discovery documents — especially patents, chemical biology papers, and biologic drug filings — contain character-exact molecular identifiers that are critical for compound identification:

| Notation Type | Example | Use Case |
|---|---|---|
| **SMILES** | `CC(=O)Oc1ccccc1C(=O)O` | Chemical structure (aspirin) |
| **InChI** | `InChI=1S/C9H8O4/c1-6(10)...` | IUPAC structure identifier |
| **InChIKey** | `BSYNRYMUTXBXSQ-UHFFFAOYSA-N` | Hashed structure fingerprint |
| **IUPAC name** | `2-acetoxybenzoic acid` | Systematic chemical name |
| **Markush** | Generic R-group structures in patent claims | Patent compound families |
| **DNA sequence** | `ATCGATCGATCG` | Nucleotide sequences |
| **RNA sequence** | `AUGCUAGCUAGC` | mRNA, siRNA, guide RNA |
| **Amino acid sequence (1-letter)** | `MTEYKLVVVGAGGVGKSALT` | Protein/peptide sequences |
| **Amino acid sequence (3-letter)** | `Met-Thr-Glu-Tyr-Lys-Leu-Val` | Protein/peptide sequences |
| **HELM** | `PEPTIDE1{A.C.T.G.C}$$$$` | Complex biopolymers (ADCs, peptide-drug conjugates) |
| **Antibody CDR** | `GYTFTSYWIE` (VH-CDR1) | Antibody drug sequences |
| **CRISPR guide** | `GAGUCCGAGCAGAAGAAGAA` | Gene editing targets |

**The fundamental challenge:** LLMs are probabilistic token predictors. They **cannot reliably reproduce** character-exact notation like SMILES strings. A single transposition, missing parenthesis, or wrong ring closure number produces a completely different (or invalid) molecule. This is not a prompt engineering problem — it's a fundamental limitation of autoregressive language models for exact string reproduction.

### 16.2 Hybrid Extraction Architecture

The solution is a two-phase pipeline:

```
Phase 1: LLM Detection                    Phase 2: Deterministic Extraction + Validation
┌─────────────────────┐                   ┌──────────────────────────────────┐
│ LLM reads document  │                   │ Regex patterns extract exact     │
│ chunk and identifies │──── outputs ────→│ strings from source text at      │
│ that molecular       │   entity with    │ character positions identified    │
│ notation EXISTS at   │   location hint  │ by LLM                           │
│ approximate location │                   │                                  │
└─────────────────────┘                   │ Validation:                      │
                                          │ • RDKit: SMILES → mol object     │
                                          │ • Biopython: sequence validity   │
                                          │ • PubChem: structure lookup      │
                                          │ • UniProt: sequence BLAST        │
                                          └──────────────────────────────────┘
```

**Phase 1 — LLM Detection (in sift-kg extraction prompt):**
The LLM identifies that a molecular identifier is present and extracts:
- The entity it belongs to (which COMPOUND or GENE or PROTEIN)
- The type of notation (SMILES, sequence, InChI, etc.)
- An approximate quote from the text containing the notation
- The context explaining what the structure/sequence represents

**Phase 2 — Post-Processing Validation (new sift-kg module):**
A deterministic post-processor:
1. Scans the original source text at the location indicated by the LLM
2. Uses regex patterns to extract the exact notation string
3. Validates using domain-specific libraries
4. Attaches validated notation as a high-confidence attribute on the entity

### 16.3 New Entity Types for Molecular Identifiers

#### CHEMICAL_STRUCTURE

**What it captures:** A chemical structure notation — the molecular identity of a compound, independent of its name. Critical for patents where a compound may have no name, only a structure.

**Biolink alignment:** `biolink:ChemicalEntity` (with structural representation)

**Ontology grounding:**
- PubChem: canonical SMILES, InChI, InChIKey
- ChEBI: InChI-based chemical identity
- ChEMBL: canonical SMILES
- CAS Registry: CAS numbers

**Key attributes:**
- `smiles`: SMILES string (canonical form preferred)
- `smiles_isomeric`: isomeric SMILES with stereochemistry
- `inchi`: InChI string
- `inchikey`: InChIKey hash (27 characters, deterministic)
- `iupac_name`: systematic IUPAC name
- `molecular_formula`: e.g., C9H8O4
- `molecular_weight`: in daltons
- `cas_number`: CAS registry number
- `notation_type`: SMILES | InChI | IUPAC | Markush | SELFIES | other
- `validated`: boolean — whether the notation was validated by RDKit/cheminformatics
- `validation_method`: RDKit | PubChem_lookup | manual
- `canonical_smiles`: RDKit-canonicalized SMILES (for deduplication)

**Extraction hints for LLM:**
- SMILES strings appear as character sequences with atoms (C, N, O, S, P, F, Cl, Br, I), bonds (=, #, :), branches (parentheses), rings (digits), and stereochemistry (@, /, \)
- InChI strings start with "InChI=" prefix — unambiguous pattern
- InChIKey is always 27 characters in format XXXXXXXXXXXXXX-YYYYYYYYYY-Z
- IUPAC names follow systematic nomenclature: numbered, substituted chemical names
- In patents: structures often appear in claims, examples sections, and Markush definitions
- When you detect a SMILES/InChI/sequence, quote the EXACT surrounding text — do not attempt to reproduce the notation yourself
- Flag the entity as `requires_validation: true`

**Patent-specific guidance:**
- Patent claims often define compound families via Markush notation with R-groups
- "Example 1", "Example 2" sections contain specific compound instances with measured activity
- Table sections list compounds with SMILES, activity data, and selectivity
- Extract the compound-structure pairing even if you cannot reproduce the SMILES exactly — quote the text location

#### NUCLEOTIDE_SEQUENCE

**What it captures:** DNA or RNA sequences that define therapeutic molecules (siRNA, ASO, mRNA, CRISPR guides), diagnostic probes, or gene constructs.

**Biolink alignment:** `biolink:NucleicAcidEntity`

**Ontology grounding:**
- NCBI GenBank: nucleotide sequences
- NCBI RefSeq: reference sequences
- Sequence Ontology (SO): sequence feature types

**Key attributes:**
- `sequence`: the nucleotide sequence string (validated characters only: A, T/U, G, C, and IUPAC ambiguity codes)
- `sequence_type`: DNA | RNA | mRNA | siRNA | ASO | sgRNA | shRNA | miRNA | aptamer | primer | probe
- `length`: sequence length in nucleotides
- `target_gene`: gene this sequence targets (for siRNA, ASO, CRISPR)
- `target_region`: mRNA region targeted (3'UTR, coding, splice junction)
- `modifications`: chemical modifications (2'-OMe, 2'-MOE, phosphorothioate, LNA)
- `strand`: sense | antisense | guide | passenger
- `genbank_accession`: GenBank accession number
- `validated`: boolean — whether sequence was validated
- `validation_method`: character_check | BLAST | manual

**Extraction hints for LLM:**
- DNA sequences: continuous strings of A, T, G, C (≥10 characters, often 18-30 for oligos, hundreds-thousands for gene constructs)
- RNA sequences: contain U instead of T — A, U, G, C
- siRNA: typically 19-25 nucleotides, often presented as sense/antisense pair
- CRISPR guide RNA: typically 20 nucleotides + PAM sequence context
- ASO: typically 15-25 nucleotides with chemical modifications noted
- mRNA: can be very long (thousands of nucleotides) — extract key regions or reference the sequence ID
- Sequences in patents often appear in sequence listings (WIPO ST.26 XML format) and claim definitions
- When you detect a sequence, quote the EXACT text — do not attempt to reproduce the sequence yourself

#### PEPTIDE_SEQUENCE

**What it captures:** Amino acid sequences that define therapeutic peptides, antibody CDR regions, protein fragments, or engineered proteins.

**Biolink alignment:** `biolink:Polypeptide`

**Ontology grounding:**
- UniProtKB: protein sequences
- IMGT: antibody sequences (immunogenetics)
- PDB: structural sequences

**Key attributes:**
- `sequence`: amino acid sequence (1-letter code)
- `sequence_3letter`: 3-letter code notation when used
- `sequence_type`: peptide | CDR | VH | VL | scFv | Fab | linker | signal_peptide | fusion_protein | cyclic_peptide
- `length`: number of amino acid residues
- `cdr_region`: CDR-H1 | CDR-H2 | CDR-H3 | CDR-L1 | CDR-L2 | CDR-L3 (for antibodies)
- `modifications`: non-natural amino acids, PEGylation, cyclization, stapling, D-amino acids
- `parent_protein`: protein this sequence derives from
- `uniprot_id`: UniProt accession for full-length proteins
- `imgt_id`: IMGT identifier for antibody sequences
- `validated`: boolean
- `validation_method`: character_check | UniProt_BLAST | manual

**Extraction hints for LLM:**
- 1-letter amino acid codes: continuous strings of standard amino acids (A, R, N, D, C, E, Q, G, H, I, L, K, M, F, P, S, T, W, Y, V)
- 3-letter codes: Met-Thr-Glu-Tyr-Lys... (hyphen or space separated)
- Antibody CDR sequences: typically 5-20 amino acids, labeled as CDR-H1/H2/H3 or CDR-L1/L2/L3 following IMGT or Kabat numbering
- Peptide drugs: typically 5-50 amino acids, may include D-amino acids (noted in lowercase) or non-natural amino acids
- In patents: antibody sequences appear in detailed description with chain definitions (heavy chain SEQ ID NO: 1, light chain SEQ ID NO: 2)
- Cyclic peptides: noted with cyclization chemistry (disulfide, head-to-tail, stapled)

### 16.4 Relations for Molecular Identifiers

| Relation | Description | Source Types | Target Types |
|---|---|---|---|
| **HAS_STRUCTURE** | Compound has a defined chemical structure | COMPOUND | CHEMICAL_STRUCTURE |
| **HAS_SEQUENCE** | Compound, gene, or protein has a defining sequence | COMPOUND, GENE, PROTEIN | NUCLEOTIDE_SEQUENCE, PEPTIDE_SEQUENCE |
| **SEQUENCE_SIMILARITY_TO** | Sequence is similar to another sequence (homology) | PEPTIDE_SEQUENCE, NUCLEOTIDE_SEQUENCE | PEPTIDE_SEQUENCE, NUCLEOTIDE_SEQUENCE |
| **TARGETS_SEQUENCE** | siRNA/ASO/CRISPR guide targets a specific nucleotide sequence | COMPOUND | NUCLEOTIDE_SEQUENCE |

### 16.5 Patent Document Handling

Patents are a critical source for drug discovery KGs but have unique structural challenges:

**Patent document sections and what to extract:**

| Section | What to Extract | Entity Types |
|---|---|---|
| **Title & Abstract** | Compound class, target, indication | COMPOUND, PROTEIN, DISEASE, MECHANISM_OF_ACTION |
| **Claims (independent)** | Core Markush structure, genus claims | CHEMICAL_STRUCTURE, COMPOUND |
| **Claims (dependent)** | Specific substituents, preferred embodiments | CHEMICAL_STRUCTURE attributes |
| **Detailed Description** | Target biology, mechanism rationale | PROTEIN, PATHWAY, DISEASE relations |
| **Examples / Specific Embodiments** | Named compounds with SMILES, activity data | COMPOUND, CHEMICAL_STRUCTURE with IC50/EC50 |
| **Biological Examples** | Assay results, in vivo data | COMPOUND → INHIBITS/ACTIVATES → PROTEIN with potency |
| **Sequence Listing (ST.26)** | DNA, RNA, protein sequences with SEQ ID NOs | NUCLEOTIDE_SEQUENCE, PEPTIDE_SEQUENCE |
| **Tables** | SAR data, compound lists, selectivity panels | COMPOUND attributes, TARGETS relations |

**Patent-specific extraction rules:**
1. **Markush claims** are NOT individual compounds — extract as CHEMICAL_STRUCTURE with `notation_type: Markush` and note the R-group definitions
2. **"Example N" compounds** ARE specific compounds — extract each with its own COMPOUND entity and CHEMICAL_STRUCTURE
3. **SEQ ID NO references** — extract the referenced sequence from the sequence listing, not from inline text
4. **Prophetic examples** (starting with "would", "could", "is expected to") — lower confidence (0.4-0.6), flag as prophetic in attributes
5. **Priority claims and patent families** — extract as PUBLICATION entities with patent number, filing date, priority date

**Patent identifiers to capture as PUBLICATION attributes:**
- Patent number (US 11,234,567 B2)
- Application number (US 2021/0123456 A1)
- PCT number (WO 2021/123456)
- Priority date
- Filing date
- Assignee (→ DEVELOPED_BY → ORGANIZATION)
- Inventor names

### 16.6 Regex Patterns for Post-Processing Validation

These patterns enable the deterministic Phase 2 extraction from source text:

```python
# SMILES — atoms, bonds, branches, rings, stereochemistry
SMILES_PATTERN = r'[A-Z][a-z]?(?:[\(\)\[\]=#@+\-\\\/\.:0-9]|[A-Z][a-z]?)*(?:\.[A-Z][a-z]?(?:[\(\)\[\]=#@+\-\\\/\.:0-9]|[A-Z][a-z]?)*)*'
# More precise: must contain at least one bond or ring notation
SMILES_STRICT = r'(?<!\w)(?:[A-IK-Z][a-z]?(?:[\(\)\[\]=#@+\-\\\/\.:0-9]|[A-IK-Z][a-z]?){3,})(?!\w)'

# InChI — always starts with "InChI="
INCHI_PATTERN = r'InChI=1S?/[A-Za-z0-9\.\+\-\(\)/,;?]+'

# InChIKey — exactly 27 characters in specific format
INCHIKEY_PATTERN = r'[A-Z]{14}-[A-Z]{10}-[A-Z]'

# DNA sequence — continuous A/T/G/C, ≥10 characters
DNA_PATTERN = r'(?<![A-Z])[ATGC]{10,}(?![A-Z])'

# RNA sequence — continuous A/U/G/C, ≥10 characters
RNA_PATTERN = r'(?<![A-Z])[AUGC]{10,}(?![A-Z])'

# Amino acid sequence (1-letter) — ≥8 characters, standard AA codes
AA_1LETTER_PATTERN = r'(?<![A-Z])[ARNDCEQGHILKMFPSTWYV]{8,}(?![A-Z])'

# Amino acid sequence (3-letter) — hyphen-separated triplets
AA_3LETTER_PATTERN = r'(?:Ala|Arg|Asn|Asp|Cys|Glu|Gln|Gly|His|Ile|Leu|Lys|Met|Phe|Pro|Ser|Thr|Trp|Tyr|Val)(?:[-\s](?:Ala|Arg|Asn|Asp|Cys|Glu|Gln|Gly|His|Ile|Leu|Lys|Met|Phe|Pro|Ser|Thr|Trp|Tyr|Val)){2,}'

# CAS number — digits-digits-digit pattern
CAS_PATTERN = r'\b\d{2,7}-\d{2}-\d\b'

# Patent number patterns
US_PATENT = r'US\s*\d{1,3},?\d{3},?\d{3}\s*[AB]\d?'
PCT_PATENT = r'WO\s*\d{4}/\d{5,6}'
US_APPLICATION = r'US\s*\d{4}/\d{7}\s*A\d'

# SEQ ID NO reference
SEQ_ID_PATTERN = r'SEQ\s*ID\s*NO:?\s*\d+'

# NCT trial number
NCT_PATTERN = r'NCT\d{8}'
```

### 16.7 Validation Pipeline (Implementation Spec)

```python
# Proposed post-processing validation module
# sift_kg/validate/molecular.py

class MolecularValidator:
    """Validates and canonicalizes molecular identifiers extracted from text."""

    def validate_smiles(self, smiles: str) -> dict:
        """Validate SMILES using RDKit, return canonical form + properties."""
        # rdkit.Chem.MolFromSmiles(smiles) → None if invalid
        # Canonical SMILES for deduplication
        # Molecular formula, MW, InChI, InChIKey computed
        ...

    def validate_sequence(self, seq: str, seq_type: str) -> dict:
        """Validate nucleotide/amino acid sequence."""
        # Check valid characters
        # For protein: all 20 standard amino acids
        # For DNA: A, T, G, C (+ IUPAC ambiguity codes)
        # For RNA: A, U, G, C
        # Compute length, GC content (nucleotide), MW estimate
        ...

    def lookup_structure(self, identifier: str) -> dict:
        """Cross-reference structure against PubChem/ChEBI."""
        # InChIKey lookup in PubChem REST API
        # Returns CID, synonyms, known activity data
        ...

    def extract_from_text(self, text: str, hint_location: str) -> list[dict]:
        """Extract molecular identifiers from raw text using regex patterns."""
        # Apply all regex patterns from Section 16.6
        # Return list of {type, value, start_pos, end_pos, validated}
        ...
```

**Required dependencies:**
- `rdkit-pypi` — SMILES validation and canonicalization (~50MB)
- `biopython` — sequence validation and analysis (~20MB)
- Both are optional dependencies: `pip install sift-kg[cheminformatics]`

### 16.8 Updated Ontology Alignment for Molecular Identifiers

| Entity Type | Primary Ontology | Secondary Ontologies | ID Prefixes |
|---|---|---|---|
| CHEMICAL_STRUCTURE | PubChem (canonical SMILES, InChI) | ChEBI, ChEMBL, CAS | PUBCHEM:, CAS:, InChIKey: |
| NUCLEOTIDE_SEQUENCE | NCBI GenBank | RefSeq, Sequence Ontology | GenBank:, RefSeq:, SO: |
| PEPTIDE_SEQUENCE | UniProtKB | PDB, IMGT | UniProtKB:, PDB:, IMGT: |

### 16.9 Hybrid Validation System Architecture

This section specifies the full architecture for integrating RDKit, Biopython, and external database lookups into the sift-kg extraction pipeline.

#### System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    sift-kg Extraction Pipeline                       │
│                                                                     │
│  ┌──────────┐    ┌──────────────┐    ┌─────────────────────────┐   │
│  │ Document  │    │  LLM-based   │    │ Molecular Validation    │   │
│  │ Ingest    │───→│  Entity &    │───→│ Post-Processor          │   │
│  │ (existing)│    │  Relation    │    │ (NEW module)            │   │
│  │           │    │  Extraction  │    │                         │   │
│  └──────────┘    │  (existing)  │    │ ┌─────────────────────┐ │   │
│                  └──────────────┘    │ │ 1. Pattern Scanner   │ │   │
│                         │            │ │    (regex on source  │ │   │
│                         │            │ │    text chunks)      │ │   │
│                         ▼            │ └────────┬────────────┘ │   │
│                  ┌──────────────┐    │          │              │   │
│                  │ Extraction   │    │ ┌────────▼────────────┐ │   │
│                  │ JSON output  │───→│ │ 2. Structure        │ │   │
│                  │ (per doc)    │    │ │    Validators        │ │   │
│                  └──────────────┘    │ │                     │ │   │
│                                     │ │  ┌───────────────┐  │ │   │
│                                     │ │  │ RDKit         │  │ │   │
│                                     │ │  │ • SMILES→mol  │  │ │   │
│                                     │ │  │ • Canonicalize│  │ │   │
│                                     │ │  │ • InChI/Key   │  │ │   │
│                                     │ │  │ • MW, formula │  │ │   │
│                                     │ │  │ • Fingerprint │  │ │   │
│                                     │ │  └───────────────┘  │ │   │
│                                     │ │  ┌───────────────┐  │ │   │
│                                     │ │  │ Biopython     │  │ │   │
│                                     │ │  │ • Seq validate│  │ │   │
│                                     │ │  │ • BLAST lookup│  │ │   │
│                                     │ │  │ • Translation │  │ │   │
│                                     │ │  │ • GC content  │  │ │   │
│                                     │ │  └───────────────┘  │ │   │
│                                     │ └────────┬────────────┘ │   │
│                                     │          │              │   │
│                                     │ ┌────────▼────────────┐ │   │
│                                     │ │ 3. Database Lookup  │ │   │
│                                     │ │    (optional)       │ │   │
│                                     │ │  • PubChem REST API │ │   │
│                                     │ │  • UniProt API      │ │   │
│                                     │ │  • ChEBI API        │ │   │
│                                     │ └────────┬────────────┘ │   │
│                                     │          │              │   │
│                                     │ ┌────────▼────────────┐ │   │
│                                     │ │ 4. Enrichment       │ │   │
│                                     │ │    • Attach valid   │ │   │
│                                     │ │      structures to  │ │   │
│                                     │ │      COMPOUND nodes │ │   │
│                                     │ │    • Create         │ │   │
│                                     │ │      CHEMICAL_      │ │   │
│                                     │ │      STRUCTURE,     │ │   │
│                                     │ │      SEQUENCE nodes │ │   │
│                                     │ │    • Add cross-refs │ │   │
│                                     │ └─────────────────────┘ │   │
│                                     └─────────────────────────┘   │
│                                                │                   │
│                                                ▼                   │
│                                     ┌─────────────────────┐       │
│                                     │ Enriched Extraction  │       │
│                                     │ JSON (per doc)       │       │
│                                     └─────────────────────┘       │
└─────────────────────────────────────────────────────────────────────┘
```

#### Component Specifications

**Component 1: Pattern Scanner** (`sift_kg/validate/scanner.py`)

```python
# Scans source text chunks and extraction JSON to find molecular identifiers
# Input: original source text + LLM extraction result
# Output: list of candidate molecular identifiers with positions

class PatternScanner:
    """Scan document text for molecular identifier patterns."""

    PATTERNS = {
        'smiles': (SMILES_STRICT, 'CHEMICAL_STRUCTURE'),
        'inchi': (INCHI_PATTERN, 'CHEMICAL_STRUCTURE'),
        'inchikey': (INCHIKEY_PATTERN, 'CHEMICAL_STRUCTURE'),
        'cas': (CAS_PATTERN, 'CHEMICAL_STRUCTURE'),
        'dna_seq': (DNA_PATTERN, 'NUCLEOTIDE_SEQUENCE'),
        'rna_seq': (RNA_PATTERN, 'NUCLEOTIDE_SEQUENCE'),
        'aa_1letter': (AA_1LETTER_PATTERN, 'PEPTIDE_SEQUENCE'),
        'aa_3letter': (AA_3LETTER_PATTERN, 'PEPTIDE_SEQUENCE'),
        'seq_id_no': (SEQ_ID_PATTERN, 'reference'),
        'nct': (NCT_PATTERN, 'CLINICAL_TRIAL'),
        'patent_us': (US_PATENT, 'PUBLICATION'),
        'patent_pct': (PCT_PATENT, 'PUBLICATION'),
    }

    def scan(self, text: str) -> list[PatternMatch]:
        """Find all molecular identifier patterns in text."""
        ...

    def correlate_with_extraction(
        self,
        matches: list[PatternMatch],
        extraction: DocumentExtraction,
    ) -> list[EnrichedEntity]:
        """Match found patterns to LLM-extracted entities."""
        # Link SMILES to the nearest COMPOUND entity
        # Link sequences to the nearest GENE/PROTEIN/COMPOUND
        ...
```

**Component 2: Structure Validators** (`sift_kg/validate/chemistry.py`, `sift_kg/validate/sequences.py`)

```python
# Chemistry validation (requires rdkit-pypi)
class ChemistryValidator:
    """Validate and enrich chemical structures using RDKit."""

    def validate_smiles(self, smiles: str) -> ValidationResult:
        """Parse SMILES, return canonical form + computed properties."""
        from rdkit import Chem
        from rdkit.Chem import Descriptors, inchi

        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return ValidationResult(valid=False, error="Invalid SMILES")

        return ValidationResult(
            valid=True,
            canonical_smiles=Chem.MolToSmiles(mol),  # canonical form
            inchi=inchi.MolToInchi(mol),
            inchikey=inchi.MolToInchiKey(mol),
            molecular_formula=Chem.rdMolDescriptors.CalcMolFormula(mol),
            molecular_weight=Descriptors.ExactMolWt(mol),
            num_atoms=mol.GetNumAtoms(),
            num_rings=Chem.rdMolDescriptors.CalcNumRings(mol),
            num_rotatable_bonds=Descriptors.NumRotatableBonds(mol),
            logp=Descriptors.MolLogP(mol),  # Lipinski parameter
            hbd=Descriptors.NumHDonors(mol),  # H-bond donors
            hba=Descriptors.NumHAcceptors(mol),  # H-bond acceptors
            tpsa=Descriptors.TPSA(mol),  # Topological polar surface area
        )

    def canonical_deduplicate(self, smiles_list: list[str]) -> dict[str, str]:
        """Map SMILES variants to canonical forms for deduplication."""
        # Different SMILES can encode the same molecule
        # RDKit canonical SMILES resolves this
        ...

    def compute_similarity(self, smiles1: str, smiles2: str) -> float:
        """Tanimoto similarity between two molecules (Morgan fingerprints)."""
        ...

    def lipinski_check(self, smiles: str) -> dict:
        """Rule of 5 compliance check for drug-likeness."""
        ...

# Sequence validation (requires biopython)
class SequenceValidator:
    """Validate and analyze nucleotide and amino acid sequences."""

    def validate_nucleotide(self, seq: str, seq_type: str = "DNA") -> ValidationResult:
        """Validate DNA/RNA sequence."""
        from Bio.Seq import Seq
        from Bio.SeqUtils import gc_fraction

        valid_dna = set("ATGCNRYWSMKHBVD")  # IUPAC
        valid_rna = set("AUGCNRYWSMKHBVD")

        charset = valid_rna if seq_type == "RNA" else valid_dna
        invalid = set(seq.upper()) - charset
        if invalid:
            return ValidationResult(valid=False, error=f"Invalid characters: {invalid}")

        bio_seq = Seq(seq)
        return ValidationResult(
            valid=True,
            length=len(seq),
            gc_content=gc_fraction(bio_seq),
            complement=str(bio_seq.complement()),
            reverse_complement=str(bio_seq.reverse_complement()),
            translation=str(bio_seq.translate()) if len(seq) % 3 == 0 else None,
        )

    def validate_protein(self, seq: str) -> ValidationResult:
        """Validate amino acid sequence."""
        valid_aa = set("ACDEFGHIKLMNPQRSTVWY*X")
        invalid = set(seq.upper()) - valid_aa
        if invalid:
            return ValidationResult(valid=False, error=f"Invalid amino acids: {invalid}")

        from Bio.SeqUtils.ProtParam import ProteinAnalysis
        analysis = ProteinAnalysis(seq)
        return ValidationResult(
            valid=True,
            length=len(seq),
            molecular_weight=analysis.molecular_weight(),
            isoelectric_point=analysis.isoelectric_point(),
            aromaticity=analysis.aromaticity(),
            instability_index=analysis.instability_index(),
            gravy=analysis.gravy(),  # hydrophobicity
        )

    def detect_sequence_type(self, seq: str) -> str:
        """Auto-detect if sequence is DNA, RNA, or protein."""
        seq = seq.upper().replace(" ", "").replace("-", "")
        if set(seq) <= set("ATGCN"):
            return "DNA"
        if set(seq) <= set("AUGCN"):
            return "RNA"
        if set(seq) <= set("ACDEFGHIKLMNPQRSTVWYX*"):
            return "protein"
        return "unknown"
```

**Component 3: Database Lookup** (`sift_kg/validate/lookup.py`)

```python
class DatabaseLookup:
    """Cross-reference molecular identifiers against public databases."""

    async def pubchem_by_inchikey(self, inchikey: str) -> dict | None:
        """Look up compound in PubChem by InChIKey."""
        # GET https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/inchikey/{key}/JSON
        # Returns CID, synonyms, molecular properties
        ...

    async def pubchem_by_name(self, name: str) -> dict | None:
        """Look up compound in PubChem by name."""
        # GET https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{name}/JSON
        ...

    async def uniprot_by_sequence(self, sequence: str) -> dict | None:
        """BLAST sequence against UniProt to find matching protein."""
        # POST to UniProt BLAST API
        ...

    async def chembl_by_smiles(self, smiles: str) -> dict | None:
        """Look up compound in ChEMBL by SMILES similarity."""
        # GET https://www.ebi.ac.uk/chembl/api/data/similarity/{smiles}/70
        ...
```

**Component 4: Pipeline Integration** (`sift_kg/validate/pipeline.py`)

```python
class MolecularValidationPipeline:
    """Orchestrates molecular identifier validation as a post-processing step."""

    def __init__(
        self,
        enable_chemistry: bool = True,    # RDKit
        enable_sequences: bool = True,     # Biopython
        enable_lookup: bool = False,       # External DB queries (slower)
    ):
        self.scanner = PatternScanner()
        self.chem = ChemistryValidator() if enable_chemistry else None
        self.seq = SequenceValidator() if enable_sequences else None
        self.lookup = DatabaseLookup() if enable_lookup else None

    def process_extraction(
        self,
        extraction: DocumentExtraction,
        source_text: str,
    ) -> DocumentExtraction:
        """
        Post-process an extraction result:
        1. Scan source text for molecular identifiers
        2. Validate found patterns
        3. Link to LLM-extracted entities
        4. Create new entities for orphan identifiers
        5. Attach validated attributes
        """
        # Step 1: Scan source text
        matches = self.scanner.scan(source_text)

        # Step 2: Validate
        for match in matches:
            if match.pattern_type in ('smiles', 'inchi') and self.chem:
                match.validation = self.chem.validate_smiles(match.value)
            elif match.pattern_type in ('dna_seq', 'rna_seq') and self.seq:
                match.validation = self.seq.validate_nucleotide(match.value)
            elif match.pattern_type in ('aa_1letter',) and self.seq:
                match.validation = self.seq.validate_protein(match.value)

        # Step 3: Correlate with LLM-extracted entities
        enriched = self.scanner.correlate_with_extraction(matches, extraction)

        # Step 4: Create CHEMICAL_STRUCTURE / SEQUENCE entities for valid matches
        # Step 5: Link to parent COMPOUND/GENE/PROTEIN via HAS_STRUCTURE/HAS_SEQUENCE

        return enriched_extraction
```

#### Dependency Management

```toml
# pyproject.toml additions
[project.optional-dependencies]
cheminformatics = [
    "rdkit-pypi>=2023.9.1",     # SMILES validation, canonicalization, properties
]
bioinformatics = [
    "biopython>=1.83",           # Sequence validation, analysis, BLAST
]
molecular = [
    "sift-kg[cheminformatics]",
    "sift-kg[bioinformatics]",
]
all = [
    "sift-kg[embeddings]",
    "sift-kg[ocr]",
    "sift-kg[molecular]",
]
```

#### CLI Integration

```bash
# Extraction with molecular validation enabled
sift extract ./patents/ --validate-molecules          # auto-detect available validators
sift extract ./papers/ --validate-chemistry           # RDKit only
sift extract ./sequences/ --validate-sequences        # Biopython only
sift extract ./patents/ --validate-molecules --lookup  # include PubChem/UniProt lookups (slower)

# Or set in sift.yaml
# validation:
#   chemistry: true
#   sequences: true
#   database_lookup: false
```

---

## 17. Complete Entity Type Summary

| # | Entity Type | Biolink Category | Key Ontologies | Description |
|---|---|---|---|---|
| 1 | COMPOUND | Drug, ChemicalEntity | ChEBI, DrugBank, ChEMBL | Exogenous therapeutic agents |
| 2 | GENE | Gene | HGNC, NCBI Gene | Genes, genetic loci |
| 3 | PROTEIN | Protein | UniProtKB, PDB | Proteins, receptors, enzymes |
| 4 | DISEASE | Disease | MeSH, DO, ICD-11 | Diseases, conditions, indications |
| 5 | MECHANISM_OF_ACTION | MolecularActivity | ChEBI role | Pharmacological mechanisms |
| 6 | CLINICAL_TRIAL | — | ClinicalTrials.gov | Clinical studies |
| 7 | PATHWAY | Pathway | KEGG, Reactome, GO:BP | Signaling/metabolic pathways |
| 8 | BIOMARKER | Context-dependent | BEST framework | Measurable indicators for Dx/Rx |
| 9 | ADVERSE_EVENT | DiseaseOrPhenotypicFeature | MedDRA, CTCAE | Drug side effects, toxicities |
| 10 | ORGANIZATION | Agent | ROR, GRID | Companies, agencies, institutions |
| 11 | PUBLICATION | InformationContentEntity | PubMed, DOI | Scientific papers, documents |
| 12 | REGULATORY_ACTION | — | FDA, EMA | Approvals, designations |
| 13 | PHENOTYPE | PhenotypicFeature | HPO, MP | Observable characteristics |
| 14 | METABOLITE | SmallMolecule | ChEBI, HMDB, KEGG | Endogenous small molecules |
| 15 | CELL_OR_TISSUE | AnatomicalEntity, Cell | CL, Uberon, GO:CC | Cells, tissues, organs, compartments |
| 16 | PROTEIN_DOMAIN | ProteinDomain | InterPro, Pfam | Functional protein regions |
| 17 | SEQUENCE_VARIANT | SequenceVariant | ClinVar, dbSNP, COSMIC | Mutations, SNPs, fusions |
| 18 | GENETIC_ASSOCIATION | VariantToDiseaseAssociation | GWAS Catalog, EFO | GWAS hits, eQTL, MR results |
| 19 | PROTEIN_COMPLEX | MacromolecularComplex | Complex Portal, GO:CC | Multi-protein assemblies |
| 20 | GENE_SIGNATURE | — | MSigDB | Multi-gene expression panels |
| 21 | CHEMICAL_STRUCTURE | ChemicalEntity | PubChem, ChEBI, CAS | SMILES, InChI, InChIKey, IUPAC |
| 22 | NUCLEOTIDE_SEQUENCE | NucleicAcidEntity | GenBank, RefSeq, SO | DNA/RNA sequences |
| 23 | PEPTIDE_SEQUENCE | Polypeptide | UniProtKB, IMGT, PDB | Amino acid sequences, CDRs |

## 18. Complete Relation Type Summary

| # | Relation | Source Types | Target Types | Symmetric | Review Required |
|---|---|---|---|---|---|
| 1 | TARGETS | COMPOUND | PROTEIN, GENE | No | No |
| 2 | INHIBITS | COMPOUND, PROTEIN | PROTEIN, GENE, PATHWAY | No | No |
| 3 | ACTIVATES | COMPOUND, PROTEIN | PROTEIN, GENE, PATHWAY | No | No |
| 4 | BINDS_TO | COMPOUND, PROTEIN | PROTEIN | Yes | No |
| 5 | HAS_MECHANISM | COMPOUND | MECHANISM_OF_ACTION | No | No |
| 6 | INDICATED_FOR | COMPOUND | DISEASE | No | No |
| 7 | CONTRAINDICATED_FOR | COMPOUND | DISEASE | No | **Yes** |
| 8 | EVALUATED_IN | COMPOUND | CLINICAL_TRIAL | No | No |
| 9 | CAUSES | COMPOUND | ADVERSE_EVENT | No | No |
| 10 | DERIVED_FROM | COMPOUND | COMPOUND | No | No |
| 11 | COMBINED_WITH | COMPOUND | COMPOUND | Yes | No |
| 12 | INTERACTS_WITH | COMPOUND | COMPOUND | Yes | No |
| 13 | ENCODES | GENE | PROTEIN | No | No |
| 14 | PARTICIPATES_IN | PROTEIN, GENE | PATHWAY | No | No |
| 15 | IMPLICATED_IN | GENE, PROTEIN, PATHWAY, PHENOTYPE | DISEASE | No | No |
| 16 | CONFERS_RESISTANCE_TO | GENE, PROTEIN, PHENOTYPE, SEQUENCE_VARIANT | COMPOUND | No | **Yes** |
| 17 | PREDICTS_RESPONSE_TO | BIOMARKER, SEQUENCE_VARIANT, GENE_SIGNATURE | COMPOUND, MECHANISM_OF_ACTION | No | **Yes** |
| 18 | DIAGNOSTIC_FOR | BIOMARKER, GENE_SIGNATURE | DISEASE | No | **Yes** |
| 19 | DEVELOPED_BY | COMPOUND, CLINICAL_TRIAL | ORGANIZATION | No | No |
| 20 | PUBLISHED_IN | CLINICAL_TRIAL, COMPOUND | PUBLICATION | No | No |
| 21 | GRANTS_APPROVAL_FOR | REGULATORY_ACTION | COMPOUND | No | No |
| 22 | EXPRESSED_IN | GENE, PROTEIN | CELL_OR_TISSUE | No | No |
| 23 | LOCALIZED_TO | PROTEIN | CELL_OR_TISSUE | No | No |
| 24 | HAS_VARIANT | GENE | SEQUENCE_VARIANT | No | No |
| 25 | HAS_DOMAIN | PROTEIN | PROTEIN_DOMAIN | No | No |
| 26 | METABOLIZED_BY | COMPOUND | PROTEIN | No | No |
| 27 | PRODUCES_METABOLITE | COMPOUND, PROTEIN | METABOLITE | No | No |
| 28 | SUBSTRATE_OF | METABOLITE | PROTEIN, PATHWAY | No | No |
| 29 | PHOSPHORYLATES | PROTEIN | PROTEIN | No | No |
| 30 | FORMS_COMPLEX_WITH | PROTEIN | PROTEIN | Yes | No |
| 31 | REGULATES_EXPRESSION | PROTEIN, COMPOUND | GENE | No | No |
| 32 | GENETICALLY_ASSOCIATED_WITH | SEQUENCE_VARIANT, GENE, GENETIC_ASSOCIATION | DISEASE, PHENOTYPE | No | No |
| 33 | MODULATES_EXPRESSION_OF | SEQUENCE_VARIANT | GENE | No | No |
| 34 | CAUSAL_FOR | GENE, PROTEIN | DISEASE, PHENOTYPE | No | **Yes** |
| 35 | SUBUNIT_OF | PROTEIN | PROTEIN_COMPLEX | No | No |
| 36 | CLEAVES | PROTEIN | PROTEIN | No | No |
| 37 | UBIQUITINATES | PROTEIN | PROTEIN | No | No |
| 38 | DEGRADES | COMPOUND, PROTEIN | PROTEIN | No | No |
| 39 | MEMBER_OF | GENE | GENE_SIGNATURE | No | No |
| 40 | CLASSIFIES | GENE_SIGNATURE | DISEASE, PHENOTYPE | No | No |
| 41 | ENRICHED_IN | PATHWAY | GENE_SIGNATURE, CELL_OR_TISSUE, DISEASE | No | No |
| 42 | HAS_STRUCTURE | COMPOUND | CHEMICAL_STRUCTURE | No | No |
| 43 | HAS_SEQUENCE | COMPOUND, GENE, PROTEIN | NUCLEOTIDE_SEQUENCE, PEPTIDE_SEQUENCE | No | No |
| 44 | SEQUENCE_SIMILARITY_TO | PEPTIDE_SEQUENCE, NUCLEOTIDE_SEQUENCE | PEPTIDE_SEQUENCE, NUCLEOTIDE_SEQUENCE | Yes | No |
| 45 | TARGETS_SEQUENCE | COMPOUND | NUCLEOTIDE_SEQUENCE | No | No |
| 46 | ASSOCIATED_WITH | any | any | Yes | No |
