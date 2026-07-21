#!/usr/bin/env python3
"""Tests for OKF (Open Knowledge Format) bundle export.

Fixtures below are small, self-authored synthetic graphs — nothing is
derived from GoogleCloudPlatform/knowledge-catalog's (Apache-2.0) sample
bundles or reference code. See docs/plans/2026-07-14-okf-export-decision.md
for the license rationale.

Run: python -m pytest tests/test_okf_export.py -v
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from core import cli
from core import okf_export
from core import registry
from core.okf_export import export_okf

RESERVED_MD_NAMES = {"index.md", "log.md"}
_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


# ---------------------------------------------------------------------------
# Fixture graph builders
# ---------------------------------------------------------------------------


def _sample_graph() -> dict:
    """A small synthetic graph exercising: a same-directory slug collision
    (two "Acme Corp" Organization nodes), a unicode name, a DOCUMENT node, a
    MENTIONED_IN edge, and contested/superseded epistemic statuses.
    """
    return {
        "metadata": {
            "domain": "contracts",
            "created_at": "2026-01-01T00:00:00+00:00",
            "updated_at": "2026-01-20T00:00:00+00:00",
            "entity_count": 5,
            "relation_count": 5,
        },
        "nodes": [
            {
                "id": "org:acme-1",
                "name": "Acme Corp",
                "entity_type": "Organization",
                "context": "Acme Corp is the primary vendor on the master services agreement.",
                "attributes": {"jurisdiction": "DE"},
                "confidence": 0.9,
                "source_documents": ["contract1"],
            },
            {
                # Same rendered name as org:acme-1, same directory -> slug collision.
                "id": "org:acme-2",
                "name": "Acme Corp",
                "entity_type": "Organization",
                "context": "A second Acme Corp division tracked separately in the graph.",
                "confidence": 0.85,
            },
            {
                "id": "org:zurich",
                "name": "Zürich Insurance Co.",
                "entity_type": "Organization",
                "context": "Zürich Insurance Co. underwrites the liability policy.",
                "confidence": 0.8,
            },
            {
                "id": "risk:overrun",
                "name": "Cost Overrun Risk",
                "entity_type": "Risk",
                "context": "Cost Overrun Risk covers budget exposure across the contract term.",
                "confidence": 0.7,
                "community": "risk-cluster",
            },
            {
                "id": "doc:contract1",
                "name": "contract1.pdf",
                "entity_type": "DOCUMENT",
                "attributes": {"path": "corpus/contract1.pdf"},
            },
        ],
        "links": [
            {
                "source": "org:acme-1",
                "target": "doc:contract1",
                "relation_type": "MENTIONED_IN",
                "confidence": 0.99,
            },
            {
                "source": "org:acme-1",
                "target": "org:zurich",
                "relation_type": "PARTY_TO",
                "confidence": 0.75,
                "epistemic_status": "contested",
                "evidence": "Acme Corp entered into agreement with Zurich Insurance Co. "
                "per section 4.2, though the effective date is disputed by the counterparty.",
            },
            {
                "source": "org:acme-2",
                "target": "risk:overrun",
                "relation_type": "EXPOSED_TO",
                "confidence": 0.6,
                "epistemic_status": "superseded",
                "invalid_at": "2026-01-15T00:00:00+00:00",
                "superseded_by": "org:acme-1",
                "evidence": "Initial risk assessment flagged cost overrun exposure for the "
                "Acme Corp division 2 budget line.",
            },
            {
                "source": "org:zurich",
                "target": "risk:overrun",
                "relation_type": "EXPOSED_TO",
                "confidence": 0.2,
                "evidence": "Passing mention of overrun exposure in the underwriting notes.",
            },
            {
                "source": "risk:overrun",
                "target": "org:acme-1",
                "relation_type": "AFFECTS",
                "confidence": 0.85,
                "evidence": "Cost overrun risk affects Acme Corp directly per section 7.",
            },
        ],
    }


def _sample_claims() -> dict:
    return {
        "super_domain": {
            "conflicts": [
                {
                    "id": "conflict-1",
                    "description": "Disputed effective date between Acme Corp and Zurich Insurance Co.",
                    "severity": "high",
                    "entities_involved": ["org:acme-1", "org:zurich"],
                    "evidence": "Section 4.2 states Jan 1; a later amendment claims Jan 15.",
                }
            ],
            "coverage_gaps": [],
            "risks": [
                {
                    "id": "risk-1",
                    "description": "Cost overrun risk is under-mitigated in the current contract.",
                    "severity": "medium",
                    "entities_involved": ["risk:overrun"],
                }
            ],
        }
    }


def _sample_communities() -> dict:
    return {"org:acme-1": "vendor-cluster"}


def _write_project(
    root: Path, *, with_claims: bool = True, with_communities: bool = True
) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "graph_data.json").write_text(json.dumps(_sample_graph(), indent=2))
    if with_claims:
        (root / "claims_layer.json").write_text(json.dumps(_sample_claims(), indent=2))
    if with_communities:
        (root / "communities.json").write_text(
            json.dumps(_sample_communities(), indent=2)
        )
    return root


# ---------------------------------------------------------------------------
# Bundle-structure helpers
# ---------------------------------------------------------------------------


def _read_frontmatter(md_path: Path) -> tuple[dict | None, str]:
    text = md_path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return None, text
    end = text.find("\n---", 4)
    assert end != -1, f"unterminated frontmatter block in {md_path}"
    header = text[4:end]
    body = text[end + 4 :].lstrip("\n")
    return yaml.safe_load(header), body


def _resolve_link(bundle_dir: Path, md_path: Path, target: str) -> Path:
    if target.startswith("/"):
        return bundle_dir / target.lstrip("/")
    return md_path.parent / target


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def project_root(tmp_path) -> Path:
    return _write_project(tmp_path / "proj")


@pytest.fixture
def home(tmp_path, monkeypatch):
    """Isolate EPISTRACT_HOME for CLI-level tests (mirrors test_multiproject.py)."""
    monkeypatch.setenv("EPISTRACT_HOME", str(tmp_path / "home"))
    monkeypatch.delenv("EPISTRACT_PROJECT", raising=False)
    return tmp_path


# ---------------------------------------------------------------------------
# 1. OKF conformance — every non-reserved .md has frontmatter with a type
# ---------------------------------------------------------------------------


def test_every_concept_has_type_frontmatter(project_root):
    summary = export_okf(project_root)
    bundle_dir = Path(summary["bundle_path"])
    md_files = list(bundle_dir.rglob("*.md"))
    assert md_files, "expected at least one markdown file in the bundle"

    checked = 0
    for md_path in md_files:
        if md_path.name in RESERVED_MD_NAMES:
            continue
        fields, _body = _read_frontmatter(md_path)
        assert fields is not None, f"{md_path} has no frontmatter block"
        assert isinstance(fields, dict), f"{md_path} frontmatter is not a mapping"
        assert fields.get("type"), f"{md_path} missing non-empty 'type'"
        checked += 1
    assert checked > 0


def test_root_index_has_okf_version_frontmatter(project_root):
    summary = export_okf(project_root)
    bundle_dir = Path(summary["bundle_path"])
    fields, _body = _read_frontmatter(bundle_dir / "index.md")
    assert fields is not None
    assert fields.get("okf_version")


# ---------------------------------------------------------------------------
# 2. Link integrity — every bundle-relative link resolves
# ---------------------------------------------------------------------------


def test_link_integrity(project_root):
    summary = export_okf(project_root)
    bundle_dir = Path(summary["bundle_path"])
    checked_links = 0
    for md_path in bundle_dir.rglob("*.md"):
        text = md_path.read_text(encoding="utf-8")
        for target in _LINK_RE.findall(text):
            resolved = _resolve_link(bundle_dir, md_path, target)
            if target.endswith("/"):
                assert resolved.is_dir(), f"{md_path}: link to missing dir '{target}'"
            else:
                assert resolved.is_file(), f"{md_path}: link to missing file '{target}'"
            checked_links += 1
    assert checked_links > 0


# ---------------------------------------------------------------------------
# 3. index.md per directory + log.md deprecation entry
# ---------------------------------------------------------------------------


def test_index_and_log_present(project_root):
    summary = export_okf(project_root)
    bundle_dir = Path(summary["bundle_path"])
    assert (bundle_dir / "index.md").exists()
    dirs = [p for p in bundle_dir.iterdir() if p.is_dir()]
    assert dirs, "expected at least one concept-type directory"
    for path in dirs:
        assert (path / "index.md").exists(), f"missing index.md in {path}"

    log_text = (bundle_dir / "log.md").read_text(encoding="utf-8")
    assert "Deprecation" in log_text
    assert "2026-01-15" in log_text  # invalid_at date of the superseded edge
    assert "Cost Overrun Risk" in log_text


# ---------------------------------------------------------------------------
# 4. Redaction — evidence stripped from bodies and sidecars
# ---------------------------------------------------------------------------


def test_redaction_strips_evidence(project_root):
    needle = "disputed by the counterparty"

    unredacted = export_okf(
        project_root, project_root / "okf-full", include_evidence=True
    )
    full_text = (
        Path(unredacted["bundle_path"]) / "organization" / "acme-corp.md"
    ).read_text()
    assert needle in full_text
    assert "Evidence" in full_text

    redacted = export_okf(
        project_root, project_root / "okf-redacted", include_evidence=False
    )
    bundle_dir = Path(redacted["bundle_path"])
    redacted_text = (bundle_dir / "organization" / "acme-corp.md").read_text()
    assert needle not in redacted_text
    assert "Evidence" not in redacted_text  # column itself is dropped

    sidecar = json.loads((bundle_dir / "graph_data.json").read_text())
    for link in sidecar["links"]:
        assert link.get("evidence", "") == ""

    claims_sidecar = json.loads((bundle_dir / "claims_layer.json").read_text())
    for item in claims_sidecar["super_domain"]["conflicts"]:
        assert item.get("evidence") in ("", {})


# ---------------------------------------------------------------------------
# 5. Slug collisions + unicode names
# ---------------------------------------------------------------------------


def test_slug_collision_and_unicode(project_root):
    summary = export_okf(project_root)
    org_dir = Path(summary["bundle_path"]) / "organization"

    assert (org_dir / "acme-corp.md").exists()
    assert (org_dir / "acme-corp-2.md").exists()
    first_id = _read_frontmatter(org_dir / "acme-corp.md")[0]["epistract_id"]
    second_id = _read_frontmatter(org_dir / "acme-corp-2.md")[0]["epistract_id"]
    assert {first_id, second_id} == {"org:acme-1", "org:acme-2"}

    zurich_path = org_dir / "zurich-insurance-co.md"
    assert zurich_path.exists()
    assert zurich_path.name.isascii()


# ---------------------------------------------------------------------------
# 6. Sidecar fidelity
# ---------------------------------------------------------------------------


def test_sidecar_present_and_byte_identical_when_unredacted(project_root):
    original_text = (project_root / "graph_data.json").read_text()
    summary = export_okf(project_root, include_evidence=True)
    sidecar_path = Path(summary["bundle_path"]) / "graph_data.json"
    assert sidecar_path.exists()
    assert sidecar_path.read_text() == original_text


# ---------------------------------------------------------------------------
# 7. min_confidence filter
# ---------------------------------------------------------------------------


def test_min_confidence_filters_relations(project_root):
    filtered = export_okf(
        project_root, project_root / "okf-filtered", min_confidence=0.5
    )
    filtered_zurich = (
        Path(filtered["bundle_path"]) / "organization" / "zurich-insurance-co.md"
    ).read_text()
    assert "EXPOSED_TO" not in filtered_zurich  # 0.2-confidence edge dropped
    assert filtered["skipped_edges"] == 1

    baseline = export_okf(project_root, project_root / "okf-baseline")
    baseline_zurich = (
        Path(baseline["bundle_path"]) / "organization" / "zurich-insurance-co.md"
    ).read_text()
    assert "EXPOSED_TO" in baseline_zurich
    assert baseline["skipped_edges"] == 0


# ---------------------------------------------------------------------------
# 8. Missing optional files tolerated; re-export leaves no stale files
# ---------------------------------------------------------------------------


def test_missing_optional_files_tolerated(tmp_path):
    root = _write_project(tmp_path / "proj", with_claims=False, with_communities=False)
    summary = export_okf(root)
    bundle_dir = Path(summary["bundle_path"])
    assert not (bundle_dir / "claims").exists()
    assert (bundle_dir / "index.md").exists()
    assert not any("claims_layer" in w for w in summary["warnings"])
    assert not any("communities" in w for w in summary["warnings"])


def test_reexport_removes_stale_files(project_root):
    first = export_okf(project_root)
    bundle_dir = Path(first["bundle_path"])
    assert (bundle_dir / "claims").exists()
    assert (bundle_dir / "organization" / "acme-corp-2.md").exists()

    graph = json.loads((project_root / "graph_data.json").read_text())
    graph["nodes"] = [n for n in graph["nodes"] if n["id"] != "org:acme-2"]
    graph["links"] = [
        link
        for link in graph["links"]
        if link["source"] != "org:acme-2" and link["target"] != "org:acme-2"
    ]
    (project_root / "graph_data.json").write_text(json.dumps(graph, indent=2))
    (project_root / "claims_layer.json").unlink()

    second = export_okf(project_root)
    bundle_dir2 = Path(second["bundle_path"])
    assert not (bundle_dir2 / "claims").exists()
    assert not (bundle_dir2 / "organization" / "acme-corp-2.md").exists()
    assert (bundle_dir2 / "organization" / "acme-corp.md").exists()


# ---------------------------------------------------------------------------
# 9. CLI wiring
# ---------------------------------------------------------------------------


def test_cli_export_okf(home, tmp_path, capsys):
    project = registry.init_project(
        "okfproj", root=tmp_path / "okfproj", domain="contracts"
    )
    _write_project(Path(project["root"]))

    exit_code = cli.main(
        ["export", "--format", "okf", "--project", "okfproj", "--json"]
    )
    assert exit_code == 0
    out = json.loads(capsys.readouterr().out)
    bundle_dir = Path(out["bundle_path"])
    assert bundle_dir.exists()
    assert (bundle_dir / "index.md").exists()


def test_cli_export_okf_flags(home, tmp_path, capsys):
    project = registry.init_project(
        "okfproj-flags", root=tmp_path / "okfproj-flags", domain="contracts"
    )
    _write_project(Path(project["root"]))
    out_dir = tmp_path / "custom-bundle"

    exit_code = cli.main(
        [
            "export",
            "--format",
            "okf",
            "--project",
            "okfproj-flags",
            "--out",
            str(out_dir),
            "--no-evidence",
            "--min-confidence",
            "0.5",
            "--json",
        ]
    )
    assert exit_code == 0
    out = json.loads(capsys.readouterr().out)
    assert out["bundle_path"] == str(out_dir)
    assert out["skipped_edges"] == 1
    acme_text = (out_dir / "organization" / "acme-corp.md").read_text()
    assert "disputed by the counterparty" not in acme_text


def test_cli_export_rejects_other_formats(home, tmp_path, capsys):
    registry.init_project(
        "okfproj-bad", root=tmp_path / "okfproj-bad", domain="contracts"
    )
    exit_code = cli.main(["export", "--format", "graphml", "--project", "okfproj-bad"])
    assert exit_code != 0
    assert "okf" in capsys.readouterr().err.lower()


def test_cli_export_missing_graph(home, tmp_path, capsys):
    registry.init_project(
        "okfproj-empty", root=tmp_path / "okfproj-empty", domain="contracts"
    )
    exit_code = cli.main(["export", "--format", "okf", "--project", "okfproj-empty"])
    assert exit_code == 1
    assert "graph_data.json" in capsys.readouterr().err


# ---------------------------------------------------------------------------
# 10. Regression tests for review findings
# ---------------------------------------------------------------------------


def test_output_dir_overlapping_project_root_raises(tmp_path):
    """`--out` pointed at the project root (or an ancestor of it) must not
    wipe project files -- it must raise instead of running shutil.rmtree."""
    root = _write_project(tmp_path / "proj")
    (root / "other_file.txt").write_text("do not delete me")

    with pytest.raises(ValueError):
        export_okf(root, root)

    # An ancestor of project_root is equally destructive.
    with pytest.raises(ValueError):
        export_okf(root, root.parent)

    assert (root / "other_file.txt").exists()
    assert (root / "graph_data.json").exists()


def test_node_missing_id_is_skipped_not_fatal(tmp_path):
    graph = _sample_graph()
    graph["nodes"].append({"name": "Orphan", "entity_type": "Organization"})
    root = tmp_path / "proj"
    root.mkdir()
    (root / "graph_data.json").write_text(json.dumps(graph))

    summary = export_okf(root)
    assert any("missing 'id'" in w for w in summary["warnings"])


def test_bracket_in_name_is_escaped_in_relation_link(tmp_path):
    """A '[' / ']' in a name must not break the generated markdown link.

    Note: the naive `_LINK_RE` used by `test_link_integrity` above cannot
    detect a bracket-containing label either way (it has no notion of
    backslash-escaping), so this asserts the escaped substring directly
    rather than relying on that regex.
    """
    graph = _sample_graph()
    for node in graph["nodes"]:
        if node["id"] == "org:zurich":
            node["name"] = "Zurich [Legacy] Insurance"
    root = tmp_path / "proj"
    root.mkdir()
    (root / "graph_data.json").write_text(json.dumps(graph))

    summary = export_okf(root)
    bundle_dir = Path(summary["bundle_path"])
    assert (bundle_dir / "organization" / "zurich-legacy-insurance.md").exists()
    acme_text = (bundle_dir / "organization" / "acme-corp.md").read_text()
    expected = (
        "[Zurich \\[Legacy\\] Insurance](/organization/zurich-legacy-insurance.md)"
    )
    assert expected in acme_text


def test_duplicate_document_names_warn_and_stay_deterministic(tmp_path):
    graph = {
        "metadata": {"created_at": "2026-01-01T00:00:00+00:00"},
        "nodes": [
            {"id": "doc:a", "name": "report.pdf", "entity_type": "DOCUMENT"},
            {"id": "doc:b", "name": "report.pdf", "entity_type": "DOCUMENT"},
            {
                "id": "product:widget",
                "name": "Widget",
                "entity_type": "PRODUCT",
                "source_documents": ["report.pdf"],
            },
        ],
        "links": [],
    }
    root = tmp_path / "proj"
    root.mkdir()
    (root / "graph_data.json").write_text(json.dumps(graph))

    summary = export_okf(root)
    assert any("duplicate document name" in w for w in summary["warnings"])
    widget_text = (Path(summary["bundle_path"]) / "product" / "widget.md").read_text()
    assert "sources/report-pdf.md" in widget_text  # first-seen (doc:a) wins


def test_entity_type_colliding_with_sources_dirname_is_diverted(tmp_path):
    graph = {
        "metadata": {"created_at": "2026-01-01T00:00:00+00:00"},
        "nodes": [
            {"id": "doc:paper1", "name": "paper1.pdf", "entity_type": "DOCUMENT"},
            {"id": "src:pmc", "name": "PubMed Central", "entity_type": "Sources"},
        ],
        "links": [],
    }
    root = tmp_path / "proj"
    root.mkdir()
    (root / "graph_data.json").write_text(json.dumps(graph))

    summary = export_okf(root)
    bundle_dir = Path(summary["bundle_path"])
    assert (bundle_dir / "sources" / "paper1-pdf.md").exists()
    assert (bundle_dir / "sources-type" / "pubmed-central.md").exists()
    assert summary["concept_counts"]["sources"] == 1
    assert any("reserved directory" in w for w in summary["warnings"])


def test_dangling_relation_target_is_warned(tmp_path):
    graph = _sample_graph()
    graph["links"].append(
        {
            "source": "org:acme-1",
            "target": "does-not-exist",
            "relation_type": "TREATS",
            "confidence": 0.9,
        }
    )
    root = tmp_path / "proj"
    root.mkdir()
    (root / "graph_data.json").write_text(json.dumps(graph))

    summary = export_okf(root)
    assert any("has no matching node" in w for w in summary["warnings"])


def test_node_slugifying_to_index_does_not_clobber_directory_index(tmp_path):
    graph = _sample_graph()
    graph["nodes"].append(
        {"id": "org:index", "name": "Index", "entity_type": "Organization"}
    )
    root = tmp_path / "proj"
    root.mkdir()
    (root / "graph_data.json").write_text(json.dumps(graph))

    summary = export_okf(root)
    bundle_dir = Path(summary["bundle_path"])
    org_dir = bundle_dir / "organization"
    fields, _body = _read_frontmatter(org_dir / "index-2.md")
    assert fields["epistract_id"] == "org:index"

    # The directory's real index.md must remain the auto-generated listing,
    # not the clobbered concept file.
    index_fields, _ = _read_frontmatter(org_dir / "index.md")
    assert index_fields is None  # no frontmatter -> auto-generated listing


def test_empty_or_null_entity_type_gets_nonempty_type_frontmatter(tmp_path):
    graph = {
        "metadata": {"created_at": "2026-01-01T00:00:00+00:00"},
        "nodes": [
            {"id": "n:empty", "name": "Empty Type", "entity_type": ""},
            {"id": "n:null", "name": "Null Type", "entity_type": None},
        ],
        "links": [],
    }
    root = tmp_path / "proj"
    root.mkdir()
    (root / "graph_data.json").write_text(json.dumps(graph))

    summary = export_okf(root)
    bundle_dir = Path(summary["bundle_path"])
    for slug in ("empty-type.md", "null-type.md"):
        fields, _body = _read_frontmatter(bundle_dir / "unknown" / slug)
        assert fields.get("type"), f"{slug} missing non-empty 'type'"


def test_log_date_heading_never_unknown_date(tmp_path):
    graph = _sample_graph()
    del graph["metadata"]["created_at"]
    del graph["metadata"]["updated_at"]
    root = tmp_path / "proj"
    root.mkdir()
    (root / "graph_data.json").write_text(json.dumps(graph))

    export_okf(root)
    log_text = (root / "okf" / "log.md").read_text()
    assert "unknown-date" not in log_text


def test_export_reads_edges_key_relations(tmp_path):
    """A graph keyed `edges` (not `links`) must export its relations,
    contested/superseded tags, and log deprecations — and the verbatim
    sidecar must stay `edges`-keyed (graph_data is never mutated)."""
    graph = _sample_graph()
    graph["edges"] = graph.pop("links")
    del graph["metadata"]["relation_count"]  # force recomputation from edges
    root = tmp_path / "proj"
    root.mkdir()
    (root / "graph_data.json").write_text(json.dumps(graph))

    summary = export_okf(root)
    bundle_dir = Path(summary["bundle_path"])

    acme_path = bundle_dir / "organization" / "acme-corp.md"
    acme_text = acme_path.read_text()
    assert "PARTY_TO" in acme_text, "edges-keyed relations missing from concept file"
    fields, _body = _read_frontmatter(acme_path)
    assert "contested" in fields.get("tags", []), (
        f"expected 'contested' tag from edges-keyed graph, got {fields.get('tags')}"
    )

    log_text = (bundle_dir / "log.md").read_text()
    assert "Deprecation" in log_text
    assert "2026-01-15" in log_text  # invalid_at of the superseded edge
    assert "Cost Overrun Risk" in log_text

    # Verbatim sidecar stays lossless: still keyed "edges", not "links".
    sidecar = json.loads((bundle_dir / "graph_data.json").read_text())
    assert "edges" in sidecar and "links" not in sidecar


def test_write_log_skips_superseded_link_missing_endpoint(tmp_path):
    """A superseded link missing source/target must be skipped in the log
    walk, never rendered as a literal `None`."""
    graph = _sample_graph()
    graph["links"].append(
        {
            "source": "org:acme-1",
            "relation_type": "X",
            "epistemic_status": "superseded",
            "invalid_at": "2026-01-16T00:00:00+00:00",
        }
    )
    root = tmp_path / "proj"
    root.mkdir()
    (root / "graph_data.json").write_text(json.dumps(graph))

    summary = export_okf(root)
    log_text = (Path(summary["bundle_path"]) / "log.md").read_text()
    assert "`None`" not in log_text, "malformed superseded link rendered `None`"
    assert "Cost Overrun Risk" in log_text  # well-formed entry still present
    assert any("link missing source/target" in w for w in summary["warnings"])


def test_redaction_strips_evidence_from_drug_discovery_shape(tmp_path):
    graph = _sample_graph()
    root = tmp_path / "proj"
    root.mkdir()
    (root / "graph_data.json").write_text(json.dumps(graph))
    claims = {
        "super_domain": {
            "hypotheses": [
                {
                    "id": "hypothesis:1",
                    "evidence_summary": "SECRET VERBATIM QUOTE",
                }
            ],
            "contradictions": [
                {
                    "type": "evidence_direction",
                    "relation_id": "r1",
                    "positive_mentions": [
                        {"document": "d1", "evidence": "SECRET A", "confidence": 0.9}
                    ],
                    "negative_mentions": [
                        {"document": "d2", "evidence": "SECRET B", "confidence": 0.3}
                    ],
                }
            ],
        }
    }
    (root / "claims_layer.json").write_text(json.dumps(claims))

    summary = export_okf(root, include_evidence=False)
    sidecar_text = (Path(summary["bundle_path"]) / "claims_layer.json").read_text()
    assert "SECRET VERBATIM QUOTE" not in sidecar_text
    assert "SECRET A" not in sidecar_text
    assert "SECRET B" not in sidecar_text


def test_no_evidence_preserves_evidence_tier_metadata(tmp_path):
    """--no-evidence must blank verbatim evidence text but preserve
    non-confidential tier metadata (`evidence_tier`, `evidence_tier_counts`)
    in the claims sidecar — a substring match on 'evidence' over-blanks."""
    root = tmp_path / "proj"
    root.mkdir()
    (root / "graph_data.json").write_text(json.dumps(_sample_graph()))
    claims = {
        "super_domain": {
            "conflicts": [
                {
                    "id": "conflict-tiered",
                    "description": "Tiered conflict with metadata.",
                    "evidence": "SECRET TEXT",
                    "evidence_tier": "high",
                    "evidence_tier_counts": {"high": 3, "low": 1},
                }
            ]
        }
    }
    (root / "claims_layer.json").write_text(json.dumps(claims))

    summary = export_okf(root, include_evidence=False)
    sidecar = json.loads(
        (Path(summary["bundle_path"]) / "claims_layer.json").read_text()
    )
    conflict = sidecar["super_domain"]["conflicts"][0]
    assert conflict["evidence"] == "", "verbatim evidence must be blanked"
    assert conflict["evidence_tier"] == "high", "evidence_tier must survive"
    assert conflict["evidence_tier_counts"] == {"high": 3, "low": 1}, (
        "evidence_tier_counts must survive"
    )


def test_no_evidence_redacts_derived_evidence_from_claim_frontmatter(tmp_path):
    """--no-evidence must redact nested/derived evidence text (e.g.
    evidence_summary) from claim frontmatter, matching sidecar redaction —
    while non-confidential tier metadata still passes through."""
    root = tmp_path / "proj"
    root.mkdir()
    (root / "graph_data.json").write_text(json.dumps(_sample_graph()))
    claims = {
        "super_domain": {
            "conflicts": [
                {
                    "id": "conflict-tier",
                    "description": "Conflict with derived evidence.",
                    "evidence_summary": "SECRET SUMMARY",
                    "evidence_tier": "high",
                }
            ]
        }
    }
    (root / "claims_layer.json").write_text(json.dumps(claims))

    summary = export_okf(root, include_evidence=False)
    claim_path = Path(summary["bundle_path"]) / "claims" / "conflict-tier.md"
    claim_text = claim_path.read_text()
    assert "SECRET SUMMARY" not in claim_text, (
        "derived evidence leaked into claim frontmatter"
    )
    fields, _body = _read_frontmatter(claim_path)
    assert fields.get("epistract_evidence_tier") == "high", (
        "allowlist must be selective: evidence_tier passes through"
    )


def test_index_description_with_newline_stays_single_line(tmp_path):
    """A mid-sentence newline in a node description must be collapsed to a
    space in the directory index.md, not split the list entry."""
    graph = _sample_graph()
    graph["nodes"].append(
        {
            "id": "org:multiline",
            "name": "Multiline Org",
            "entity_type": "Organization",
            # Deliberately no .!? before the newline: _first_sentence splits
            # on `(?<=[.!?])\s+`, so the whole string (newline intact)
            # becomes the description.
            "context": "First part\nsecond part",
        }
    )
    root = tmp_path / "proj"
    root.mkdir()
    (root / "graph_data.json").write_text(json.dumps(graph))

    summary = export_okf(root)
    index_text = (
        Path(summary["bundle_path"]) / "organization" / "index.md"
    ).read_text()
    assert "First part second part" in index_text, (
        "newline in description must collapse to a space in index.md"
    )


def test_main_flag_missing_value_exits_cleanly():
    """A trailing --out (no value) or a flag as first argument must exit 2
    with a stderr message, not raise IndexError or consume the flag as the
    project root. Neither invocation reaches export (no fs side effects)."""
    script = Path(okf_export.__file__)

    trailing = subprocess.run(
        [sys.executable, str(script), "somepath", "--out"],
        capture_output=True,
        text=True,
    )
    assert trailing.returncode == 2, f"expected exit 2, got {trailing.returncode}"
    assert "--out" in trailing.stderr

    flag_as_root = subprocess.run(
        [sys.executable, str(script), "--no-evidence"],
        capture_output=True,
        text=True,
    )
    assert flag_as_root.returncode == 2, (
        f"expected exit 2, got {flag_as_root.returncode}"
    )


def test_export_refuses_to_wipe_non_bundle_directory(tmp_path):
    """`--out` pointed at a pre-existing non-empty directory that is NOT a
    previous OKF bundle must raise instead of shutil.rmtree'ing it -- the
    ancestor guard alone would happily wipe e.g. `--out ~/Documents`."""
    root = _write_project(tmp_path / "proj")
    out = tmp_path / "not-a-bundle"
    out.mkdir()
    (out / "keepme.txt").write_text("do not delete")

    with pytest.raises(ValueError):
        export_okf(root, out)

    assert (out / "keepme.txt").exists(), "unrelated file was deleted"
    assert (out / "keepme.txt").read_text() == "do not delete", (
        "unrelated file contents were clobbered"
    )


def test_export_into_empty_directory_succeeds(tmp_path):
    """An existing but EMPTY output directory is a safe boundary case: there
    is nothing to lose, so export must proceed rather than refuse."""
    root = _write_project(tmp_path / "proj")
    out = tmp_path / "empty-out"
    out.mkdir()

    summary = export_okf(root, out)
    assert (Path(summary["bundle_path"]) / "index.md").exists()


def test_reexport_over_previous_bundle_succeeds(tmp_path):
    """Re-exporting over this exporter's own previous bundle must stay
    idempotent: the root index.md `okf_version` sentinel identifies the
    directory as a bundle that is safe to wipe and recreate."""
    root = _write_project(tmp_path / "proj")
    out = tmp_path / "bundle-out"

    export_okf(root, out)
    export_okf(root, out)  # second export over the same bundle must not raise
    assert (out / "index.md").exists()


def test_claim_hostile_frontmatter_key_is_dropped(tmp_path):
    """A claims-layer key containing ':' or a newline must not be interpolated
    into the claim frontmatter YAML block: unfixed, `epistract_bad: key` +
    `name: "HOSTILE_VALUE"` render as two physical lines, yielding a spurious
    top-level `name` field and leaking the value."""
    root = tmp_path / "proj"
    root.mkdir()
    (root / "graph_data.json").write_text(json.dumps(_sample_graph()))
    claims = {
        "super_domain": {
            "conflicts": [
                {
                    "id": "conflict-hostile",
                    "description": "Conflict carrying a hostile extra key.",
                    "safe_key": "kept",
                    "bad: key\nname": "HOSTILE_VALUE",
                }
            ]
        }
    }
    (root / "claims_layer.json").write_text(json.dumps(claims))

    summary = export_okf(root)
    claim_path = Path(summary["bundle_path"]) / "claims" / "conflict-hostile.md"
    fields, _body = _read_frontmatter(claim_path)
    assert isinstance(fields, dict), "frontmatter no longer parses as a mapping"
    assert fields.get("epistract_id") == "conflict-hostile"
    assert fields.get("epistract_safe_key") == "kept", (
        "legit identifier keys must survive -- filter must be selective"
    )
    assert "name" not in fields, "injected newline created a spurious top-level key"
    assert "HOSTILE_VALUE" not in claim_path.read_text(), "hostile value leaked"


def test_main_min_confidence_non_numeric_exits_cleanly():
    """`--min-confidence abc` in the standalone __main__ must exit 2 with a
    clean stderr message, not an uncaught ValueError traceback. (The argparse
    path in core/cli.py uses type=float and handles this on its own.)"""
    script = Path(okf_export.__file__)
    result = subprocess.run(
        [sys.executable, str(script), "somepath", "--min-confidence", "abc"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2, f"expected exit 2, got {result.returncode}"
    assert "--min-confidence" in result.stderr
    assert "Traceback" not in result.stderr
