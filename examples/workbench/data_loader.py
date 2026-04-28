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

        # Load triage.json for original filenames
        triage_map: dict[str, dict] = {}
        triage_path = self.output_dir / "triage.json"
        if triage_path.exists():
            triage = json.loads(triage_path.read_text(encoding="utf-8"))
            for doc in triage.get("documents", []):
                triage_map[doc.get("doc_id", "")] = doc
            if triage.get("documents"):
                fp = triage["documents"][0].get("file_path", "")
                if fp:
                    self.corpus_dir = Path(fp).parent

        # Build document list from ingested/ directory
        if self.ingested_dir.exists():
            for txt_file in sorted(self.ingested_dir.glob("*.txt")):
                doc_id = txt_file.stem
                triage_info = triage_map.get(doc_id, {})
                original_path = triage_info.get("file_path", "")
                original_name = (
                    Path(original_path).name if original_path else txt_file.name
                )
                self.documents.append(
                    {
                        "doc_id": doc_id,
                        "filename": original_name,
                        "display_name": original_name.rsplit(".", 1)[0]
                        if original_name
                        else doc_id,
                        "original_path": original_path,
                        "size_bytes": txt_file.stat().st_size,
                        "original_size": triage_info.get(
                            "chars", txt_file.stat().st_size
                        ),
                    }
                )

    def get_nodes(self, entity_type: str | None = None) -> list[dict]:
        """Return graph nodes, optionally filtered by entity_type."""
        nodes = self.graph_data.get("nodes", [])
        if entity_type:
            nodes = [n for n in nodes if n.get("entity_type") == entity_type.upper()]
        return nodes

    def get_edges(self) -> list[dict]:
        """Return all graph edges (sift-kg uses 'links' key)."""
        return self.graph_data.get("links", self.graph_data.get("edges", []))

    def get_node_by_id(self, node_id: str) -> dict | None:
        """Find a specific node by its ID."""
        for node in self.graph_data.get("nodes", []):
            if node.get("id") == node_id:
                return node
        return None

    def get_document_text(self, doc_id: str) -> str | None:
        """Read ingested text for a document.

        Returns None if doc_id is empty, contains traversal markers, or resolves
        outside ingested_dir. Defense-in-depth: a string-level reject (`..`, `/`,
        `\\`) catches the obvious cases; a `Path.resolve().relative_to()` check
        catches edge cases like symlinks and URL-encoded equivalents.
        """
        if not doc_id or ".." in doc_id or "/" in doc_id or "\\" in doc_id:
            return None
        txt_path = self.ingested_dir / f"{doc_id}.txt"
        try:
            txt_path.resolve().relative_to(self.ingested_dir.resolve())
        except ValueError:
            return None
        if txt_path.exists():
            return txt_path.read_text(encoding="utf-8")
        return None

    def get_document_pdf_path(self, doc_id: str) -> Path | None:
        """Try to find original PDF for a document.

        Same containment guard as get_document_text — even though rglob is
        inherently contained to corpus_dir, we reject obvious traversal payloads
        early so callers see consistent behavior across both lookups.
        """
        if not doc_id or ".." in doc_id or "/" in doc_id or "\\" in doc_id:
            return None
        if not self.corpus_dir or not self.corpus_dir.exists():
            return None
        # Search for matching PDF (doc_id is sanitized lowercase filename stem)
        for pdf in self.corpus_dir.rglob("*.pdf"):
            if pdf.stem.lower().replace(" ", "_").replace("-", "_") == doc_id:
                return pdf
        return None
