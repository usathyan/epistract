#!/usr/bin/env python3
"""Tests for the multi-project CLI: registry, hybrid index, and graph retrieval.

Run: python -m pytest tests/test_multiproject.py -v
"""

import json
from pathlib import Path

import pytest

from core import cli
from core import graph_retrieval
from core import index_db
from core import registry
from core.registry import ProjectError


@pytest.fixture
def home(tmp_path, monkeypatch):
    """Isolate EPISTRACT_HOME and clear any inherited project selection."""
    monkeypatch.setenv("EPISTRACT_HOME", str(tmp_path / "home"))
    monkeypatch.delenv("EPISTRACT_PROJECT", raising=False)
    return tmp_path


@pytest.fixture
def project(home, tmp_path):
    return registry.init_project("demo", root=tmp_path / "demo", domain="contracts")


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


def test_init_creates_registry_and_manifest(home, tmp_path):
    project = registry.init_project(
        "alpha", root=tmp_path / "alpha", domain="contracts"
    )
    assert project["domain"] == "contracts"
    assert (Path(project["root"]) / ".epistract" / "project.json").exists()
    assert (Path(project["root"]) / "corpus").is_dir()
    assert registry.get_project("alpha")["name"] == "alpha"


def test_init_rejects_duplicate(project):
    with pytest.raises(ProjectError, match="already exists"):
        registry.init_project("demo", root=project["root"])


def test_init_rejects_bad_name(home):
    with pytest.raises(ProjectError, match="Invalid project name"):
        registry.init_project("bad name!")


def test_resolve_by_cwd_walkup(project):
    nested = Path(project["root"]) / "corpus"
    resolved = registry.resolve_project(cwd=nested)
    assert resolved["name"] == "demo"


def test_resolve_prefers_explicit_name(project, home, tmp_path):
    registry.init_project("other", root=tmp_path / "other")
    resolved = registry.resolve_project("other", cwd=project["root"])
    assert resolved["name"] == "other"


def test_resolve_env_project(project, monkeypatch):
    monkeypatch.setenv("EPISTRACT_PROJECT", "demo")
    assert registry.resolve_project(cwd="/tmp")["name"] == "demo"


def test_delete_keeps_files_by_default(project):
    root = Path(project["root"])
    registry.delete_project("demo")
    assert "demo" not in registry.load_registry()["projects"]
    assert (root / ".epistract" / "project.json").exists()


def test_delete_purge_removes_state(project):
    root = Path(project["root"])
    registry.delete_project("demo", purge=True)
    assert not (root / ".epistract").exists()


# ---------------------------------------------------------------------------
# Sources
# ---------------------------------------------------------------------------


def test_add_files_dedup_by_hash(project, tmp_path):
    a = tmp_path / "a.txt"
    a.write_text("hello world")
    b = tmp_path / "b.txt"
    b.write_text("hello world")  # same content -> duplicate
    report = registry.add_files(project, [a, b])
    assert len(report["added"]) == 1
    assert len(report["skipped_duplicate"]) == 1
    reloaded = registry.get_project("demo")
    assert len(reloaded["manifest"]["sources"]) == 1


def test_add_files_reports_missing(project, tmp_path):
    report = registry.add_files(project, [tmp_path / "nope.txt"])
    assert report["missing"] and not report["added"]


def test_add_url_uses_fetcher(project):
    report = registry.add_url(
        project, "https://example.com/doc.txt", fetcher=lambda url: b"content here"
    )
    assert report["status"] == "added"
    assert Path(report["file"]).read_bytes() == b"content here"


def test_default_fetcher_rejects_non_http():
    with pytest.raises(ProjectError, match="scheme"):
        registry._default_fetcher("file:///etc/passwd")
    with pytest.raises(ProjectError, match="scheme"):
        registry._default_fetcher("ftp://example.com/x")


def test_load_registry_corrupt_json(home):
    path = registry._registry_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{not valid json")
    with pytest.raises(ProjectError, match="registry.json"):
        registry.load_registry()


# ---------------------------------------------------------------------------
# Index & search
# ---------------------------------------------------------------------------


def _seed_corpus(project):
    corpus = registry.corpus_dir(project)
    (corpus / "doc1.txt").write_text(
        "Semaglutide is a GLP-1 receptor agonist used for type 2 diabetes.\n\n"
        "It reduces blood glucose and promotes weight loss in clinical trials."
    )
    (corpus / "doc2.txt").write_text(
        "Tirzepatide is a dual GIP and GLP-1 receptor agonist. "
        "Trials show significant weight reduction versus semaglutide."
    )


def test_index_and_search_chunks(project):
    _seed_corpus(project)
    stats = index_db.index_project(project)
    assert len(stats["indexed"]) == 2
    assert stats["chunks"] >= 2

    results = index_db.search_index(project, "semaglutide weight loss", k=5)
    assert results["chunks"], "expected chunk hits"
    assert any("doc1.txt" in c["doc_id"] for c in results["chunks"])


def test_index_is_incremental(project):
    _seed_corpus(project)
    index_db.index_project(project)
    second = index_db.index_project(project)
    assert second["indexed"] == []
    assert second["skipped"] == 2


def test_index_reconciles_deleted_docs(project):
    _seed_corpus(project)
    index_db.index_project(project)
    (registry.corpus_dir(project) / "doc2.txt").unlink()
    stats = index_db.index_project(project)
    assert stats["removed"] == 1, f"expected 1 removed doc, got {stats}"
    db = index_db.open_index(project)
    doc_ids = {row[0] for row in db.execute("SELECT doc_id FROM documents")}
    chunk_docs = {row[0] for row in db.execute("SELECT doc_id FROM chunks_fts")}
    db.close()
    assert not any("doc2.txt" in d for d in doc_ids), f"stale doc rows: {doc_ids}"
    assert not any("doc2.txt" in d for d in chunk_docs), "stale chunk rows remain"


def test_index_picks_up_changes(project):
    _seed_corpus(project)
    index_db.index_project(project)
    (registry.corpus_dir(project) / "doc1.txt").write_text(
        "Completely new content about insulin."
    )
    third = index_db.index_project(project)
    assert any("doc1.txt" in d for d in third["indexed"])


def test_search_indexes_entities_from_graph(project):
    graph = {
        "nodes": [
            {"id": "n1", "name": "Semaglutide", "entity_type": "Compound"},
            {"id": "n2", "name": "GLP-1 Receptor", "entity_type": "Protein"},
        ],
        "links": [{"source": "n1", "target": "n2"}],
    }
    (Path(project["root"]) / "graph_data.json").write_text(json.dumps(graph))
    stats = index_db.index_project(project)
    assert stats["entities"] == 2
    results = index_db.search_index(project, "semaglutide", k=5)
    assert any(e["name"] == "Semaglutide" for e in results["entities"])
    typed = index_db.search_index(project, "semaglutide", k=5, entity_type="Protein")
    assert all(e["entity_type"] == "Protein" for e in typed["entities"])


# ---------------------------------------------------------------------------
# Graph retrieval (personalized PageRank)
# ---------------------------------------------------------------------------


def test_ppr_ranks_connected_nodes(tmp_path):
    graph = {
        "nodes": [
            {"id": f"n{i}", "name": f"Node {i}", "entity_type": "T"} for i in range(4)
        ],
        "links": [
            {"source": "n0", "target": "n1"},
            {"source": "n1", "target": "n2"},
            {"source": "n2", "target": "n3"},
        ],
    }
    path = tmp_path / "graph_data.json"
    path.write_text(json.dumps(graph))
    ranked = graph_retrieval.expand_from_seeds(path, ["n0"], top_k=5)
    ids = [r["id"] for r in ranked]
    assert "n0" not in ids  # seeds excluded by default
    assert ids[0] == "n1"  # closest neighbor ranks highest
    assert ids.index("n1") < ids.index("n3")  # nearer beats farther


def test_ppr_empty_for_unknown_seed(tmp_path):
    graph = {"nodes": [{"id": "n0", "name": "A"}], "links": []}
    path = tmp_path / "graph_data.json"
    path.write_text(json.dumps(graph))
    assert graph_retrieval.expand_from_seeds(path, ["missing"], top_k=5) == []


# ---------------------------------------------------------------------------
# CLI wiring (end-to-end through argparse)
# ---------------------------------------------------------------------------


def test_cli_full_flow(home, tmp_path, capsys):
    src = tmp_path / "note.txt"
    src.write_text("Aspirin inhibits COX-1 and COX-2 enzymes to reduce inflammation.")

    assert (
        cli.main(
            [
                "init",
                "cliproj",
                "--dir",
                str(tmp_path / "cliproj"),
                "--domain",
                "drug-discovery",
            ]
        )
        == 0
    )
    assert cli.main(["add", "files", str(src), "--project", "cliproj"]) == 0
    assert cli.main(["index", "--project", "cliproj"]) == 0

    capsys.readouterr()
    assert cli.main(["search", "COX enzymes", "--project", "cliproj", "--json"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["chunks"], "expected chunk hits from CLI search"

    assert cli.main(["projects", "list", "--json"]) == 0
    listing = json.loads(capsys.readouterr().out)
    assert any(p["name"] == "cliproj" for p in listing)


def test_cli_unknown_project_errors(home, capsys):
    assert cli.main(["status", "--project", "ghost"]) == 1
    assert "Unknown project" in capsys.readouterr().err
