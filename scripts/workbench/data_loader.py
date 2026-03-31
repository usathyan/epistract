"""In-memory data store for pre-extracted KG data."""
from __future__ import annotations

import json
from pathlib import Path


class WorkbenchData:
    """Load and hold all extraction pipeline output in memory."""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.graph_data: dict = {}
        self.claims_layer: dict = {}
        self.communities: dict = {}
        self.documents: list[dict] = []
        self.ingested_dir = output_dir / "ingested"
        self.corpus_dir: Path | None = None
        self.load()

    def load(self):
        """Load JSON artifacts from output directory."""
        gp = self.output_dir / "graph_data.json"
        if gp.exists():
            self.graph_data = json.loads(gp.read_text(encoding="utf-8"))

        cp = self.output_dir / "claims_layer.json"
        if cp.exists():
            self.claims_layer = json.loads(cp.read_text(encoding="utf-8"))

        cm = self.output_dir / "communities.json"
        if cm.exists():
            self.communities = json.loads(cm.read_text(encoding="utf-8"))

        # Build document list from ingested/ directory
        if self.ingested_dir.exists():
            for txt_file in sorted(self.ingested_dir.glob("*.txt")):
                self.documents.append({
                    "doc_id": txt_file.stem,
                    "filename": txt_file.name,
                    "size_bytes": txt_file.stat().st_size,
                })

        # Try to locate original corpus via triage.json
        triage_path = self.output_dir / "triage.json"
        if triage_path.exists():
            triage = json.loads(triage_path.read_text(encoding="utf-8"))
            if triage.get("documents"):
                first_doc = triage["documents"][0]
                fp = first_doc.get("file_path", "")
                if fp:
                    self.corpus_dir = Path(fp).parent

    def get_nodes(self, entity_type: str | None = None) -> list[dict]:
        """Return graph nodes, optionally filtered by entity_type."""
        nodes = self.graph_data.get("nodes", [])
        if entity_type:
            nodes = [n for n in nodes if n.get("entity_type") == entity_type.upper()]
        return nodes

    def get_edges(self) -> list[dict]:
        """Return all graph edges."""
        return self.graph_data.get("edges", [])

    def get_node_by_id(self, node_id: str) -> dict | None:
        """Find a specific node by its ID."""
        for node in self.graph_data.get("nodes", []):
            if node.get("id") == node_id:
                return node
        return None

    def get_document_text(self, doc_id: str) -> str | None:
        """Read ingested text for a document."""
        txt_path = self.ingested_dir / f"{doc_id}.txt"
        if txt_path.exists():
            return txt_path.read_text(encoding="utf-8")
        return None

    def get_document_pdf_path(self, doc_id: str) -> Path | None:
        """Try to find original PDF for a document."""
        if not self.corpus_dir or not self.corpus_dir.exists():
            return None
        # Search for matching PDF (doc_id is sanitized lowercase filename stem)
        for pdf in self.corpus_dir.rglob("*.pdf"):
            if pdf.stem.lower().replace(" ", "_").replace("-", "_") == doc_id:
                return pdf
        return None
