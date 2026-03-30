#!/usr/bin/env python3
"""End-to-end contract extraction orchestrator.

Chains document chunking, chunk-extraction merge, entity resolution, and
graph construction into a single pipeline call.

Usage:
    python extract_contracts.py <output_dir> [--domain contract] [--skip-chunking] [--skip-graph]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Optional Rich progress
# ---------------------------------------------------------------------------
try:
    from rich.console import Console

    _console = Console(stderr=True)
    HAS_RICH = True
except ImportError:
    HAS_RICH = False


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


def extract_and_build(
    output_dir: Path,
    domain_name: str = "contract",
    skip_chunking: bool = False,
    skip_graph: bool = False,
) -> dict:
    """Run the full contract extraction pipeline.

    Steps:
        1. Chunking -- split ingested documents at clause boundaries.
        2. Extraction merge -- merge per-chunk extraction JSONs.
        3. Entity resolution -- normalize party names, resolve aliases.
        4. Graph build -- invoke sift-kg to construct the knowledge graph.

    Args:
        output_dir: Root output directory (must contain triage.json or ingested/).
        domain_name: Domain name for schema resolution (default: contract).
        skip_chunking: Skip Step 1 if chunks already exist.
        skip_graph: Skip Step 4 (graph construction).

    Returns:
        Stats dict with counts for each step.
    """
    output_dir = Path(output_dir)
    stats: dict = {
        "documents_chunked": 0,
        "extractions_merged": 0,
        "names_normalized": 0,
        "graph_built": False,
    }

    # ------------------------------------------------------------------
    # Step 1: Chunking
    # ------------------------------------------------------------------
    if not skip_chunking:
        from chunk_document import chunk_document_to_files

        triage_path = output_dir / "triage.json"
        if triage_path.exists():
            triage = json.loads(triage_path.read_text(encoding="utf-8"))
            docs = [
                d for d in triage.get("documents", [])
                if d.get("extraction_readiness_score", 0) > 0
            ]
        else:
            # Fallback: look for .txt files in ingested/
            ingested = output_dir / "ingested"
            if ingested.exists():
                docs = [
                    {"doc_id": f.stem}
                    for f in sorted(ingested.glob("*.txt"))
                ]
            else:
                docs = []

        if not docs:
            if HAS_RICH:
                _console.print("[yellow]No documents found for chunking[/yellow]")
            return stats

        for doc in docs:
            doc_id = doc["doc_id"]
            try:
                chunk_document_to_files(doc_id, output_dir)
                stats["documents_chunked"] += 1
            except Exception as exc:
                if HAS_RICH:
                    _console.print(f"[red]Chunking failed for {doc_id}: {exc}[/red]")

    # ------------------------------------------------------------------
    # Step 2: Extraction merge (placeholder for agent-dispatched extraction)
    # ------------------------------------------------------------------
    from build_extraction import write_extraction
    from entity_resolution import merge_chunk_extractions

    ingested = output_dir / "ingested"
    if ingested.exists():
        for chunk_dir in sorted(ingested.glob("*_chunks")):
            doc_id = chunk_dir.name.replace("_chunks", "")
            extraction_path = output_dir / "extractions" / f"{doc_id}.json"

            # Skip if final extraction already exists
            if extraction_path.exists():
                continue

            # Collect chunk-level extraction JSONs written by extraction agents
            chunk_extractions = []
            for ef in sorted(chunk_dir.glob("extraction_*.json")):
                chunk_extractions.append(json.loads(ef.read_text(encoding="utf-8")))

            if chunk_extractions:
                merged = merge_chunk_extractions(chunk_extractions, doc_id)
                write_extraction(
                    doc_id,
                    str(output_dir),
                    merged["entities"],
                    merged["relations"],
                    chunks_processed=merged["chunks_processed"],
                    domain_name=domain_name,
                )
                stats["extractions_merged"] += 1

    # ------------------------------------------------------------------
    # Step 3: Entity resolution
    # ------------------------------------------------------------------
    from entity_resolution import preprocess_extractions

    res = preprocess_extractions(output_dir)
    stats["names_normalized"] = res.get("names_normalized", 0)

    # ------------------------------------------------------------------
    # Step 4: Graph build
    # ------------------------------------------------------------------
    if not skip_graph:
        try:
            from run_sift import cmd_build

            cmd_build(str(output_dir), domain_name=domain_name)
            stats["graph_built"] = True
        except SystemExit:
            pass  # cmd_build may sys.exit on import error
        except Exception as exc:
            if HAS_RICH:
                _console.print(f"[red]Graph build failed: {exc}[/red]")

    return stats


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_contracts.py <output_dir> [--domain name] [--skip-chunking] [--skip-graph]", file=sys.stderr)
        sys.exit(1)

    out = Path(sys.argv[1])
    if not out.exists():
        print(f"Error: directory {out} does not exist", file=sys.stderr)
        sys.exit(1)

    domain = "contract"
    if "--domain" in sys.argv:
        domain = sys.argv[sys.argv.index("--domain") + 1]

    result = extract_and_build(
        out,
        domain_name=domain,
        skip_chunking="--skip-chunking" in sys.argv,
        skip_graph="--skip-graph" in sys.argv,
    )
    print(json.dumps(result, indent=2))
