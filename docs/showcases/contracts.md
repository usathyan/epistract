# Event Contract Management — Cross-Domain Demonstration

The `contracts` domain demonstrates that epistract is truly cross-domain: **the same pipeline runs against a different schema and produces a knowledge graph with different epistemic rules**. The drug-discovery and contracts domains share zero extraction or build code — only the YAML configuration, SKILL.md prompt, and `epistemic.py` rules differ.

This page describes the contracts domain package shipped in this repository (`domains/contracts/`). The package is a **schema scaffold** — it defines the entity types, relation types, extraction prompt, and epistemic rules, but does **not** include a sample corpus. Bring your own contracts to reproduce the cross-domain story.

## What Ships in `domains/contracts/`

```
domains/contracts/
├── domain.yaml          # 11 entity types, 11 relation types
├── SKILL.md             # extraction prompt + naming standards
├── references/          # entity-type and relation-type reference docs
├── epistemic.py         # cross-contract conflict detection rules
└── workbench/
    └── template.yaml    # workbench title, persona, entity colors, starter questions
```

## Domain Schema

The contracts domain uses 11 entity types and 11 relation types designed for event/vendor contract analysis:

| Category | Entity Types |
|----------|-------------|
| Parties | PARTY, PERSON, COMMITTEE |
| Obligations | OBLIGATION, SERVICE, DELIVERABLE |
| Temporal | DEADLINE, EVENT |
| Financial | COST, PAYMENT_TERM |
| Spaces | VENUE, ROOM, STAGE |
| Legal | CLAUSE |

Relation types capture contractual structure: **OBLIGATES**, **PROVIDES**, **COSTS**, **DEPENDS_ON**, **RESTRICTS**, **CONFLICTS_WITH**, **RELATED_TO**, plus event-specific links for committees, persons, and physical spaces. See `domains/contracts/references/` for the full reference documentation.

## Pipeline (Same as Drug Discovery)

```
/epistract:ingest ./my-contracts/ --output ./contracts-output --domain contracts
/epistract:epistemic ./contracts-output
/epistract:dashboard ./contracts-output --domain contracts
```

1. **Document parsing** — Kreuzberg extracts text from PDF, XLS, EML, and 75+ other formats with OCR fallback for scanned documents
2. **Entity extraction** — `epistract:extractor` subagents read each contract using `domains/contracts/SKILL.md` and emit entities/relations as `DocumentExtraction` JSON
3. **Graph construction** — `sift-kg` builds a deduplicated knowledge graph with entity resolution across contracts using domain-specific canonical naming
4. **Community detection** — Louvain algorithm identifies clusters of related vendors, obligations, and deadlines
5. **Epistemic analysis** — `domains/contracts/epistemic.py` detects cross-contract conflicts, obligation gaps, and risk indicators

## What the Epistemic Layer Detects

Unlike simple document extraction, epistract's two-layer approach enables higher-order analysis specific to contract portfolios:

1. **Conflicts** — When Contract A says one thing and Contract B says another about the same entity. Examples: overlapping exclusive service windows ("Vendor X has exclusive catering rights" vs. "Vendor Y is approved for premium suite catering"), contradictory setup requirements, scheduling collisions on shared rooms.
2. **Gaps** — Expected obligations or deliverables that are missing from the contract landscape. Examples: no contract covers a required service, an event date has no labor agreement, a venue requires insurance but no certificate is on file.
3. **Risks** — Patterns that indicate potential operational issues. Examples: tight turnaround between teardown and next setup, penalty clauses triggered by dependencies on other vendors, missing force majeure language for a critical service.

## Cross-Domain Story

The contracts domain is the proof point that epistract's framework is genuinely domain-agnostic:

| Layer | Drug Discovery | Contracts | Shared? |
|---|---|---|---|
| Document parsing | Kreuzberg | Kreuzberg | ✅ |
| Extraction agent | `epistract:extractor` | `epistract:extractor` | ✅ |
| Graph builder | `sift-kg.run_build` | `sift-kg.run_build` | ✅ |
| Community detection | Louvain | Louvain | ✅ |
| Viewer | `graph.html` | `graph.html` | ✅ |
| Workbench | `examples/workbench/` | `examples/workbench/` | ✅ |
| **Schema** (entity + relation types) | 17 / 30 | 11 / 11 | ❌ — domain-specific |
| **SKILL.md** (extraction prompt) | drug-discovery domain expertise | contract domain expertise | ❌ — domain-specific |
| **Epistemic rules** | RDKit/Biopython validation, prophetic-claim detection | Cross-contract conflict detection, obligation gap analysis, risk scoring | ❌ — domain-specific |
| **Workbench template** | drug-discovery persona | contract-analyst persona | ❌ — domain-specific |

**Adding a third domain (legal briefs, scientific datasets, regulatory filings, real estate leases, anything) requires only writing the four domain-specific files. Pipeline code is unchanged.**

## Applicability — Where This Schema Reuses

The contracts domain configuration can be adapted to many contractual analysis scenarios with minimal schema changes:

- Corporate vendor management portfolios
- Real estate lease landscapes
- Government procurement contracts
- Construction project subcontract chains
- Healthcare provider agreements
- SaaS terms-of-service comparison

Each application requires only a domain schema update (entity types, relation types, epistemic rules) — the extraction pipeline and graph construction remain unchanged. Use `/epistract:domain --input ./sample-docs/` to auto-generate a starter domain package from a sample corpus.

## Privacy Note

This public branch ships the contracts domain *package* (schema, prompt, rules) but **does not include any sample contract documents or extracted graphs**. The page above describes capabilities, not specific content. To reproduce the cross-domain story, point `/epistract:ingest` at your own contract corpus.
