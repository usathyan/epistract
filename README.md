# Epistract

**Turn any document corpus into a structured knowledge graph.**

Epistract is a domain-agnostic knowledge graph framework that runs as a [Claude Code](https://claude.ai/claude-code) plugin. Point it at a folder of documents, specify a domain schema, and it builds a two-layer knowledge graph: brute-force entity/relation extraction grounded to domain ontologies, then domain-specific epistemic analysis that surfaces conflicts, gaps, risks, and confidence levels across your corpus.

Ship with a pre-built domain or create your own in minutes with the domain wizard.

## The Name

From Greek **episteme** (ἐπιστήμη) — structured scientific knowledge, the highest form of knowledge in Aristotle's epistemological hierarchy — combined with **extract**. Episteme is not opinion or belief; it is knowledge grounded in evidence, demonstration, and systematic understanding. That is what this tool produces: not a bag of keywords, but a structured representation of how concepts relate to each other, traceable back to the source text.

## Quick Start

Requires [Claude Code](https://claude.ai/claude-code) and Python 3.11+.

### Path A: Use a Pre-Built Domain

Three commands to your first graph:

```
/epistract:setup
```

Install the framework and dependencies.

```
/epistract:ingest --domain drug-discovery --input ./my-papers/
```

Parse documents and extract entities/relations using the drug discovery schema.

```
/epistract:view
```

Open the interactive knowledge graph in your browser.

### Path B: Create Your Own Domain

Five steps from zero to a custom knowledge graph:

1. **Install** — `/epistract:setup`
2. **Create domain** — `/epistract:domain --input ./sample-docs/` — the wizard analyzes your documents, proposes entity types, relation types, and epistemic rules
3. **Review** — confirm the generated domain package (domain.yaml + SKILL.md + epistemic.py)
4. **Ingest** — `/epistract:ingest --domain your-domain --input ./corpus/`
5. **Explore** — `/epistract:view`

## How It Works

Epistract builds knowledge graphs in two layers. The first layer extracts brute facts — entities and relations pulled from documents by LLM agents, constrained by a domain schema grounded in established ontologies. The second layer applies epistemic analysis — domain-specific rules that detect what is asserted versus hypothesized, what contradicts across documents, what is missing, and where risks lie.

![Architecture](docs/diagrams/architecture.svg)

### Two-Layer Knowledge Graph

- **Layer 1 — Brute Facts:** Entities and relations extracted from documents via LLM agents, constrained by domain schema. Each entity is typed and grounded to domain standards. Each relation carries a confidence score and evidence passage.
- **Layer 2 — Epistemic Analysis:** Domain-specific rules detect conflicts, gaps, confidence levels, and risks across the graph. The epistemic machinery is the same regardless of domain — only the rules change.

### Domain Pluggability

New domains are added by creating a configuration package:

- `domain.yaml` — entity types, relation types, naming standards
- `SKILL.md` — extraction prompt with domain expertise
- `epistemic.py` — rules for conflict detection, gap analysis, risk scoring

No pipeline code changes required. Use the wizard (`/epistract:domain`) to auto-generate all three from a sample corpus, or create them manually.

## Pre-built Domains

| Domain | Entity Types | Relation Types | Document Formats | Description |
|--------|-------------|----------------|------------------|-------------|
| drug-discovery | 17 | 30 | PDF, DOCX, HTML, TXT | Biomedical literature analysis with molecular validation |
| contracts | 11 | 11 | PDF, XLS, EML | Event/vendor contract analysis with conflict detection |

## Showcase

### Drug Discovery Literature Analysis

Epistract was evaluated across six drug discovery research scenarios, from single-paper target validation to multi-source competitive intelligence using PubMed, Google Scholar, and Google Patents. The pipeline extracted 783 nodes and 2,230 links across all scenarios, with automatic community detection identifying therapeutic clusters, resistance mechanisms, and biomarker relationships. Molecular validation via RDKit and Biopython verified SMILES strings, sequences, CAS numbers, and NCT identifiers directly from source text.

Scenario 6 (GLP-1 Competitive Intelligence) demonstrated the largest extraction: 206 nodes and 630 links from 34 documents spanning 5 pharmaceutical companies, with patent-derived peptide sequences and chemical formulas enriching the graph beyond what literature alone provides.

[Read the full evaluation →](docs/showcases/drug-discovery.md)

### Event Contract Management

Applied to a corpus of 62 event planning contracts across multiple formats (PDF, XLS, EML). Extraction produced 341 nodes across 11 entity types and 663 edges across 11 relation types. The epistemic analysis layer detected 53 cross-contract conflicts, identified scheduling gaps, and scored vendor obligation risks — enabling event organizers to spot issues across a complex multi-vendor landscape before they become operational problems.

[Read the full evaluation →](docs/showcases/contracts.md)

## Commands Reference

| Command | Description |
|---------|-------------|
| `/epistract:setup` | Install framework and dependencies |
| `/epistract:ingest` | Parse documents and extract entities/relations into knowledge graph |
| `/epistract:build` | Rebuild graph from existing extractions (skip extraction step) |
| `/epistract:query` | Search and filter entities in the knowledge graph |
| `/epistract:export` | Export graph to GraphML, CSV, SQLite, or JSON |
| `/epistract:view` | Open interactive graph visualization in browser |
| `/epistract:validate` | Run molecular validation on extractions (RDKit, Biopython) |
| `/epistract:epistemic` | Run epistemic analysis (conflicts, gaps, risks, confidence) |
| `/epistract:domain` | Create a new domain via the interactive wizard |
| `/epistract:dashboard` | Launch web dashboard for a domain |
| `/epistract:ask` | Chat with your knowledge graph via natural language |

## Contributing / Development

### Setup

```bash
git clone https://github.com/usathyan/epistract.git
cd epistract
uv pip install -e ".[dev]"
```

### Testing

```bash
make test          # unit tests
make test-integ    # integration tests
```

### Project Structure

```
core/              # Domain-agnostic pipeline engine
domains/           # Pluggable domain configurations
examples/          # Consumer applications (workbench, telegram bot)
tests/             # Test suite
docs/              # Documentation and diagrams
```

See [CLAUDE.md](CLAUDE.md) for AI-assisted development conventions.

## Technical Documentation

- **[Adding Domains](docs/ADDING-DOMAINS.md)** — Wizard-first guide to creating new domain packages
- **[Architecture Diagrams](docs/diagrams/)** — Framework architecture, data flow, and domain package anatomy
- **[Test Scenarios](tests/MANUAL_TEST_SCENARIOS.md)** — 6 drug discovery scenarios with curated corpora
- **[Engineering Findings](tests/FINDINGS.md)** — Bugs discovered, root cause analysis, and systemic lessons

## License

MIT
