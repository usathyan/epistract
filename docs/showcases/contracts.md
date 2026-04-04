# Event Contract Management

Epistract was applied to a corpus of 62 event planning contracts to demonstrate cross-domain capability. The contracts domain extracts structured knowledge about parties, obligations, deadlines, costs, venues, and service relationships — then applies epistemic analysis to detect conflicts, gaps, and risks across the entire contract landscape.

## Methodology

### Corpus

- **62 contracts** across multiple document formats
- **60 PDF files** (including large documents up to 31 MB), **1 XLS spreadsheet**, **1 EML email**
- Multi-format parsing via Kreuzberg (75+ format support with OCR fallback for scanned documents)

### Domain Schema

The contracts domain uses 11 entity types and 11 relation types designed for event planning contract analysis:

| Category | Entity Types |
|----------|-------------|
| Parties | ORGANIZATION, PERSON, VENUE |
| Obligations | OBLIGATION, DELIVERABLE, SERVICE |
| Temporal | DEADLINE, EVENT |
| Financial | COST, PAYMENT_TERM |
| Legal | CONTRACT |

Relation types capture contractual relationships: provides services to, has obligation, has deadline, specifies cost, governs, and cross-references between contracts.

### Extraction Pipeline

1. **Document parsing** — Kreuzberg extracts text from all 62 files, handling large PDFs, spreadsheets, and email formats
2. **Entity extraction** — LLM agents read each contract with domain expertise, extracting parties, obligations, deadlines, costs, and service relationships
3. **Graph construction** — sift-kg builds a deduplicated knowledge graph with entity resolution across contracts
4. **Community detection** — Louvain algorithm identifies clusters of related contracts and entities
5. **Epistemic analysis** — Domain-specific rules detect cross-contract conflicts, obligation gaps, and risk indicators

## Results

### Extraction Summary

| Metric | Value |
|--------|-------|
| Documents processed | 62 |
| Entity types | 11 |
| Relation types | 11 |
| Total nodes | 341 |
| Total edges | 663 |
| Cross-contract entities | 37 |

### Epistemic Analysis

The epistemic layer applied contract-specific rules to detect issues across the corpus:

| Finding Type | Count | Description |
|--------------|-------|-------------|
| Cross-contract conflicts | 53 | Contradictory terms, overlapping obligations, scheduling conflicts |
| Obligation gaps | -- | Missing deliverables, unassigned responsibilities |
| Risk indicators | -- | Tight deadlines, penalty clauses, exclusivity constraints |

The 53 conflicts detected represent cases where terms in one contract contradict or create tension with terms in another — the kind of cross-document insight that is difficult to surface through manual review of individual contracts.

### Knowledge Graph Structure

The graph captures the full contract landscape:

- **Party relationships** — which organizations provide services, who has obligations to whom
- **Temporal dependencies** — deadline chains, event scheduling, setup/teardown windows
- **Financial structure** — cost allocations, payment terms, penalty triggers
- **Cross-references** — 37 entities that appear across multiple contracts, enabling conflict detection

## What the Epistemic Layer Detects

Unlike simple document extraction, epistract's two-layer approach enables higher-order analysis:

1. **Conflicts** — When Contract A says one thing and Contract B says another about the same entity (e.g., overlapping exclusive service windows, contradictory setup requirements)
2. **Gaps** — Expected obligations or deliverables that are missing from the contract landscape (e.g., no contract covers a required service)
3. **Risks** — Patterns that indicate potential operational issues (e.g., tight turnaround between teardown and next setup, penalty clauses triggered by dependencies on other vendors)

## Privacy

All results shown here use aggregate statistics only. No vendor names, dollar amounts, specific contract terms, or identifying details are disclosed. The contracts domain demonstrates epistract's capability to analyze contractual relationships — the schema definitions and aggregate metrics are public, while the actual contract content remains private.

## Applicability

The contracts domain configuration can be adapted to other contract analysis scenarios:

- Corporate vendor management
- Real estate lease portfolios
- Government procurement contracts
- Construction project contracts
- Healthcare provider agreements

Each application requires only a domain schema update (entity types, relation types, epistemic rules) — the extraction pipeline and graph construction remain unchanged.
