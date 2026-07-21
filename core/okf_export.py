#!/usr/bin/env python3
"""Export an epistract project's knowledge graph as an OKF v0.1 bundle.

OKF (Open Knowledge Format) is a directory of markdown "concept" files with
YAML frontmatter, where file paths double as concept IDs and markdown links
form an untyped graph. See:
  docs/plans/2026-07-14-okf-export-decision.md  (mapping design, this repo)
  https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md

`graph_data.json` remains the source of truth; the bundle is a publication
surface. A verbatim sidecar copy of graph_data.json (+ claims_layer.json, if
present) is written at the bundle root for lossless round-tripping.

Usage:
    from core.okf_export import export_okf

    summary = export_okf("/path/to/project")
    summary = export_okf("/path/to/project", "/path/to/out", include_evidence=False)

CLI:
    python okf_export.py <project_root> [--out <dir>] [--no-evidence]
                          [--min-confidence <float>] [--json]
"""

from __future__ import annotations

import json
import re
import shutil
import sys
from collections import defaultdict
from pathlib import Path

from unidecode import unidecode

OKF_VERSION = "0.1"
DEFAULT_BUNDLE_DIRNAME = "okf"
SOURCES_DIRNAME = "sources"
CLAIMS_DIRNAME = "claims"
FALLBACK_TIMESTAMP = "1970-01-01T00:00:00+00:00"

_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")
_NON_SLUG = re.compile(r"[^a-z0-9]+")


# ---------------------------------------------------------------------------
# Slugs / text helpers
# ---------------------------------------------------------------------------


def _slugify(text: str) -> str:
    """Unidecode + lowercase-kebab a string; never returns an empty string."""
    ascii_text = unidecode(str(text)).lower()
    slug = _NON_SLUG.sub("-", ascii_text).strip("-")
    return slug or "item"


def _unique_slug(base: str, used: set[str]) -> str:
    """Return `base`, or `base-2`, `base-3`, ... on collision. Registers the result."""
    if base not in used:
        used.add(base)
        return base
    n = 2
    while f"{base}-{n}" in used:
        n += 1
    slug = f"{base}-{n}"
    used.add(slug)
    return slug


def _first_sentence(text: str) -> str:
    parts = _SENTENCE_END.split(text.strip(), maxsplit=1)
    return parts[0].strip()


def _excerpt(text: str, limit: int = 160) -> str:
    text = (text or "").strip().replace("\n", " ")
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _cell(value: object) -> str:
    """Render a value for a markdown table cell or link label, escaping
    pipes/newlines/brackets. Bracket escaping matters even outside tables:
    an unescaped ']' in a name embedded in a `[label](target)` link breaks
    the link (CommonMark backslash-escapes always render as the literal
    character, so this is safe everywhere `_cell` is used)."""
    if isinstance(value, (dict, list)):
        text = json.dumps(value, ensure_ascii=False)
    else:
        text = str(value)
    return (
        text.replace("|", "\\|")
        .replace("\n", " ")
        .replace("[", "\\[")
        .replace("]", "\\]")
    )


def _date_part(timestamp: str | None) -> str:
    if not timestamp or len(timestamp) < 10:
        return "unknown-date"
    return timestamp[:10]


def _titleize(slug: str) -> str:
    return " ".join(word.capitalize() for word in slug.split("-"))


# ---------------------------------------------------------------------------
# Frontmatter
# ---------------------------------------------------------------------------


def _frontmatter(fields: dict[str, object]) -> str:
    """Render a YAML frontmatter block. Values are JSON-encoded (valid YAML)."""
    lines = ["---"]
    for key, value in fields.items():
        if value is None:
            continue
        if isinstance(value, (list, dict)) and not value:
            continue
        lines.append(f"{key}: {json.dumps(value, ensure_ascii=False)}")
    lines.append("---")
    return "\n".join(lines)


def _write_concept(path: Path, fields: dict[str, object], body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = _frontmatter(fields) + "\n\n" + body.rstrip() + "\n"
    path.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Body section builders
# ---------------------------------------------------------------------------


def _description_for(node: dict) -> str:
    context = (node.get("context") or "").strip()
    if context:
        return _first_sentence(context)
    name = node.get("name") or node.get("id", "")
    entity_type = node.get("entity_type") or ""
    return f"{name} ({entity_type})." if entity_type else f"{name}."


def _attributes_table(attributes: dict) -> str:
    if not attributes:
        return ""
    lines = ["# Attributes", "", "| Key | Value |", "| --- | --- |"]
    for key, value in attributes.items():
        lines.append(f"| {_cell(key)} | {_cell(value)} |")
    return "\n".join(lines)


def _relations_table(
    rels: list[dict],
    node_path: dict[str, str],
    node_title: dict[str, str],
    include_evidence: bool,
    warnings: list[str],
    owner_id: str,
) -> str:
    if not rels:
        return ""
    header = ["Relation", "Target", "Confidence", "Status"]
    if include_evidence:
        header.append("Evidence")
    lines = [
        "# Relations",
        "",
        "| " + " | ".join(header) + " |",
        "| " + " | ".join(["---"] * len(header)) + " |",
    ]
    for link in rels:
        target_id = link.get("target", "")
        target_path = node_path.get(target_id)
        target_name = node_title.get(target_id, target_id)
        if target_path:
            target_md = f"[{_cell(target_name)}]({target_path})"
        else:
            target_md = _cell(target_id)
            warnings.append(
                f"{owner_id}: relation target '{target_id}' has no matching node"
            )
        confidence = link.get("confidence")
        conf_str = f"{confidence:.2f}" if isinstance(confidence, (int, float)) else ""
        row = [
            _cell(link.get("relation_type", "")),
            target_md,
            conf_str,
            _cell(link.get("epistemic_status", "")),
        ]
        if include_evidence:
            row.append(_cell(_excerpt(link.get("evidence", ""))))
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def _citations_section(
    source_documents: list[str],
    doc_key_to_path: dict[str, str],
    doc_key_to_title: dict[str, str],
    warnings: list[str],
    owner_id: str,
) -> str:
    if not source_documents:
        return ""
    seen: list[str] = []
    for key in source_documents:
        if key not in seen:
            seen.append(key)
    lines = ["# Citations", ""]
    for n, key in enumerate(seen, start=1):
        path = doc_key_to_path.get(key)
        title = doc_key_to_title.get(key, key)
        if path:
            lines.append(f"[{n}] [{_cell(title)}]({path})")
        else:
            lines.append(f"[{n}] {_cell(title)}")
            warnings.append(
                f"{owner_id}: source document '{key}' has no matching DOCUMENT node"
            )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------


def export_okf(
    project_root: str | Path,
    output_dir: str | Path | None = None,
    *,
    include_evidence: bool = True,
    min_confidence: float = 0.0,
) -> dict:
    """Export a project's graph_data.json as an OKF v0.1 bundle.

    Args:
        project_root: Project directory containing graph_data.json (and
            optionally claims_layer.json, communities.json).
        output_dir: Bundle destination. Defaults to `<project_root>/okf/`.
            Wiped and recreated ONLY when it is empty or a previous OKF
            bundle (root index.md with okf_version frontmatter), so removed
            entities don't leave stale files behind. A non-empty directory
            that is not a previous bundle raises ValueError instead --
            unrelated files are never deleted.
        include_evidence: When False, strips evidence text from concept
            Relations tables and from the sidecar JSON copies (redaction
            for confidential corpora).
        min_confidence: Relations (non-MENTIONED_IN edges) below this
            confidence are omitted from Relations tables; the count is
            reported in the summary.

    Returns:
        Summary dict: {"bundle_path": str, "concept_counts": dict[str, int],
        "skipped_edges": int, "warnings": list[str]}.
    """
    project_root = Path(project_root)
    graph_path = project_root / "graph_data.json"
    if not graph_path.exists():
        raise FileNotFoundError(f"No graph_data.json found at {graph_path}")
    graph_data = json.loads(graph_path.read_text(encoding="utf-8"))

    claims_data: dict | None = None
    claims_path = project_root / "claims_layer.json"
    warnings: list[str] = []
    if claims_path.exists():
        try:
            claims_data = json.loads(claims_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            warnings.append(f"claims_layer.json is not valid JSON, skipping: {e}")

    communities_data: dict = {}
    communities_path = project_root / "communities.json"
    if communities_path.exists():
        try:
            loaded = json.loads(communities_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                communities_data = loaded
        except json.JSONDecodeError as e:
            warnings.append(f"communities.json is not valid JSON, skipping: {e}")

    bundle_dir = (
        Path(output_dir) if output_dir else project_root / DEFAULT_BUNDLE_DIRNAME
    )
    resolved_bundle = bundle_dir.resolve()
    resolved_project = project_root.resolve()
    if (
        resolved_bundle == resolved_project
        or resolved_bundle in resolved_project.parents
    ):
        raise ValueError(
            f"Refusing to export: output directory ({resolved_bundle}) is the "
            f"project root or an ancestor of it ({resolved_project}); wiping it "
            "would delete project files. Choose an --out directory that is not "
            "the project root or one of its parents."
        )
    if bundle_dir.exists():
        root_index = bundle_dir / "index.md"
        looks_like_bundle = (
            root_index.is_file()
            and "okf_version" in root_index.read_text(encoding="utf-8")
        )
        if any(bundle_dir.iterdir()) and not looks_like_bundle:
            raise ValueError(
                f"Refusing to export: output directory ({resolved_bundle}) "
                "exists, is not empty, and does not look like a previous OKF "
                "bundle (no root index.md with okf_version frontmatter); "
                "wiping it would delete unrelated files. Choose an empty "
                "--out directory or the location of a previous bundle."
            )
        shutil.rmtree(bundle_dir)
    bundle_dir.mkdir(parents=True, exist_ok=True)

    metadata = graph_data.get("metadata") or {}
    timestamp = (
        metadata.get("updated_at") or metadata.get("created_at") or FALLBACK_TIMESTAMP
    )
    nodes = graph_data.get("nodes") or []
    links = graph_data.get("links") or graph_data.get("edges") or []

    doc_nodes = [n for n in nodes if n.get("entity_type") == "DOCUMENT" and n.get("id")]
    concept_nodes = [
        n for n in nodes if n.get("entity_type") != "DOCUMENT" and n.get("id")
    ]
    for n in nodes:
        if not n.get("id"):
            warnings.append(f"node missing 'id', skipped: {n!r}")

    # --- slug assignment -----------------------------------------------
    # "index" is reserved in every concept directory: `_write_indexes` later
    # overwrites `<dir>/index.md` with an auto-generated listing, so a node
    # slugifying to "index" must be bumped to "index-2" instead of colliding.
    dir_used: dict[str, set[str]] = defaultdict(lambda: {"index"})
    node_path: dict[str, str] = {}
    node_dir_slug: dict[str, tuple[str, str]] = {}
    node_entity_type: dict[str, str] = {}
    node_title: dict[str, str] = {
        n["id"]: n.get("name") or n["id"] for n in nodes if n.get("id")
    }

    for node in doc_nodes:
        slug = _unique_slug(
            _slugify(node.get("name") or node["id"]), dir_used[SOURCES_DIRNAME]
        )
        node_dir_slug[node["id"]] = (SOURCES_DIRNAME, slug)
        node_path[node["id"]] = f"/{SOURCES_DIRNAME}/{slug}.md"

    for node in concept_nodes:
        entity_type = node.get("entity_type")
        if not entity_type:
            warnings.append(f"{node['id']}: missing entity_type, filed under 'unknown'")
            entity_type = "unknown"
        node_entity_type[node["id"]] = entity_type
        dir_slug = _slugify(entity_type)
        if dir_slug in (SOURCES_DIRNAME, CLAIMS_DIRNAME):
            warnings.append(
                f"{node['id']}: entity_type {entity_type!r} slugifies to reserved "
                f"directory '{dir_slug}'; filed under '{dir_slug}-type' instead"
            )
            dir_slug = f"{dir_slug}-type"
        slug = _unique_slug(
            _slugify(node.get("name") or node["id"]), dir_used[dir_slug]
        )
        node_dir_slug[node["id"]] = (dir_slug, slug)
        node_path[node["id"]] = f"/{dir_slug}/{slug}.md"

    # source_document string -> DOCUMENT node's bundle path/title. Nodes carry
    # `source_documents` as bare document identifiers (no "doc:" prefix), which
    # is how DOCUMENT nodes are keyed in `name` (and often `id` minus prefix).
    # Two DOCUMENT nodes may share a `name` (epistract dedups by content hash,
    # not filename) -- first-seen wins deterministically, with a warning, so
    # citations don't silently misattribute to whichever node was processed last.
    doc_key_to_path: dict[str, str] = {}
    doc_key_to_title: dict[str, str] = {}
    for node in doc_nodes:
        keys = {node.get("name", ""), node["id"]}
        if node["id"].startswith("doc:"):
            keys.add(node["id"][len("doc:") :])
        for key in keys:
            if not key:
                continue
            existing_path = doc_key_to_path.get(key)
            if existing_path is not None and existing_path != node_path[node["id"]]:
                warnings.append(
                    f"duplicate document name '{key}' ({doc_key_to_title[key]!r} "
                    f"and {node.get('name') or node['id']!r}); citations "
                    f"referencing '{key}' resolve to {doc_key_to_title[key]!r}"
                )
                continue
            doc_key_to_path[key] = node_path[node["id"]]
            doc_key_to_title[key] = node.get("name") or key

    # --- edges: outgoing non-MENTIONED_IN relations, min_confidence filter --
    outgoing: dict[str, list[dict]] = defaultdict(list)
    skipped_edges = 0
    # Contested/superseded statuses are intentionally collected from ALL links
    # BEFORE the MENTIONED_IN skip and min_confidence filter below: a node's
    # status tags reflect its standing in the full graph, not the filtered
    # Relations-table view.
    incident_status: dict[str, set[str]] = defaultdict(set)
    for link in links:
        status = link.get("epistemic_status")
        if status in ("contested", "superseded"):
            if link.get("source"):
                incident_status[link["source"]].add(status)
            if link.get("target"):
                incident_status[link["target"]].add(status)

        rel_type = link.get("relation_type", "")
        if rel_type == "MENTIONED_IN":
            continue
        if not link.get("source") or not link.get("target"):
            warnings.append(f"link missing source/target, skipped: {link!r}")
            continue
        confidence = link.get("confidence")
        confidence_val = confidence if isinstance(confidence, (int, float)) else 0.0
        if confidence_val < min_confidence:
            skipped_edges += 1
            continue
        outgoing[link["source"]].append(link)

    if skipped_edges:
        warnings.append(
            f"skipped {skipped_edges} edge(s) below min_confidence={min_confidence}"
        )

    # --- write concept files for non-DOCUMENT nodes ---------------------
    concept_counts: dict[str, int] = defaultdict(int)
    for node in concept_nodes:
        node_id = node["id"]
        dir_slug, slug = node_dir_slug[node_id]
        community = node.get("community") or communities_data.get(node_id)
        tags = list(
            dict.fromkeys(
                ([_slugify(community)] if community else [])
                + sorted(incident_status.get(node_id, ()))
            )
        )
        description = _description_for(node)
        fields = {
            "type": node_entity_type[node_id],
            "title": node.get("name") or node_id,
            "description": description,
            "tags": tags,
            "timestamp": timestamp,
            "epistract_id": node_id,
            "epistract_confidence": node.get("confidence"),
            "epistract_source_documents": node.get("source_documents") or [],
        }
        body_sections = [
            description,
            _attributes_table(node.get("attributes") or {}),
            _relations_table(
                outgoing.get(node_id, []),
                node_path,
                node_title,
                include_evidence,
                warnings,
                node_id,
            ),
            _citations_section(
                node.get("source_documents") or [],
                doc_key_to_path,
                doc_key_to_title,
                warnings,
                node_id,
            ),
        ]
        body = "\n\n".join(s for s in body_sections if s)
        _write_concept(bundle_dir / dir_slug / f"{slug}.md", fields, body)
        concept_counts[dir_slug] += 1

    # --- write source documents ------------------------------------------
    for node in doc_nodes:
        node_id = node["id"]
        _dir_slug, slug = node_dir_slug[node_id]
        attributes = dict(node.get("attributes") or {})
        resource = None
        for key in ("url", "source_url", "origin_url", "origin"):
            value = attributes.get(key)
            if isinstance(value, str) and value:
                resource = value
                break
        if resource is None:
            path_value = attributes.get("path")
            if isinstance(path_value, str) and path_value:
                resource = path_value
        description = (
            _description_for(node)
            if node.get("context")
            else (f"Source document '{node.get('name') or node_id}'.")
        )
        fields = {
            "type": "Source Document",
            "title": node.get("name") or node_id,
            "description": description,
            "resource": resource,
            "timestamp": timestamp,
            "epistract_id": node_id,
            "epistract_confidence": node.get("confidence"),
        }
        body_sections = [description, _attributes_table(attributes)]
        body = "\n\n".join(s for s in body_sections if s)
        _write_concept(bundle_dir / SOURCES_DIRNAME / f"{slug}.md", fields, body)
        concept_counts[SOURCES_DIRNAME] += 1

    # --- claims (conflicts / coverage gaps / risks) ----------------------
    if claims_data is not None:
        super_domain = claims_data.get("super_domain") or {}
        claim_specs = (
            ("conflicts", "Conflict"),
            ("coverage_gaps", "Coverage Gap"),
            ("risks", "Risk"),
        )
        claim_used: set[str] = {"index"}
        for field_name, claim_type in claim_specs:
            items = super_domain.get(field_name) or []
            for item in items:
                slug = _unique_slug(
                    _slugify(item.get("id") or item.get("description") or claim_type),
                    claim_used,
                )
                _write_claim(
                    bundle_dir / CLAIMS_DIRNAME / f"{slug}.md",
                    item,
                    claim_type,
                    timestamp,
                    include_evidence,
                    node_path,
                    node_title,
                    doc_key_to_path,
                    doc_key_to_title,
                )
                concept_counts[f"{CLAIMS_DIRNAME}:{_slugify(claim_type)}"] += 1

    # --- log.md -----------------------------------------------------------
    _write_log(bundle_dir, graph_data, node_title, timestamp, links)

    # --- index.md (root + per-directory) ----------------------------------
    _write_indexes(bundle_dir, metadata, concept_counts)

    # --- sidecars: verbatim (or redacted) copies for lossless fidelity ----
    _write_sidecar(bundle_dir / "graph_data.json", graph_data, include_evidence)
    if claims_data is not None:
        _write_sidecar(bundle_dir / "claims_layer.json", claims_data, include_evidence)

    return {
        "bundle_path": str(bundle_dir),
        "concept_counts": dict(concept_counts),
        "skipped_edges": skipped_edges,
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# Claims
# ---------------------------------------------------------------------------


def _write_claim(
    path: Path,
    item: dict,
    claim_type: str,
    timestamp: str,
    include_evidence: bool,
    node_path: dict[str, str],
    node_title: dict[str, str],
    doc_key_to_path: dict[str, str],
    doc_key_to_title: dict[str, str],
) -> None:
    if not include_evidence:
        # _redact_evidence returns a new dict (caller's item untouched);
        # all subsequent reads operate on the redacted copy.
        item = _redact_evidence(item)
    reserved = {"id", "type", "severity", "description"}
    description = item.get("description") or claim_type
    fields: dict[str, object] = {
        "type": claim_type,
        "title": _excerpt(description, 80),
        "description": description,
        "timestamp": timestamp,
        "epistract_id": item.get("id", ""),
    }
    severity = item.get("severity")
    if severity:
        fields["tags"] = [_slugify(str(severity))]
    for key, value in item.items():
        if key in reserved:
            continue
        # Non-identifier keys (e.g. containing ':' or newlines) are dropped:
        # interpolated as-is they would corrupt the frontmatter YAML block.
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
            continue
        fields[f"epistract_{key}"] = value

    body_parts = [description]
    suggested_action = item.get("suggested_action")
    if suggested_action:
        body_parts.append(f"**Suggested action:** {suggested_action}")

    entity_ids = item.get("entities_involved") or []
    if entity_ids:
        lines = ["# Related Concepts", ""]
        for eid in entity_ids:
            target_path = node_path.get(eid)
            title = node_title.get(eid, eid)
            lines.append(
                f"* [{_cell(title)}]({target_path})"
                if target_path
                else f"* {_cell(title)}"
            )
        body_parts.append("\n".join(lines))

    doc_keys = item.get("contracts_involved") or item.get("contracts_affected") or []
    if doc_keys:
        lines = ["# Related Sources", ""]
        for key in doc_keys:
            target_path = doc_key_to_path.get(key)
            title = doc_key_to_title.get(key, key)
            lines.append(
                f"* [{_cell(title)}]({target_path})"
                if target_path
                else f"* {_cell(title)}"
            )
        body_parts.append("\n".join(lines))

    _write_concept(path, fields, "\n\n".join(body_parts))


# ---------------------------------------------------------------------------
# log.md
# ---------------------------------------------------------------------------


def _write_log(
    bundle_dir: Path,
    graph_data: dict,
    node_title: dict[str, str],
    timestamp: str,
    links: list[dict],
) -> None:
    metadata = graph_data.get("metadata") or {}
    entries: dict[str, list[str]] = defaultdict(list)

    entity_count = metadata.get("entity_count", len(graph_data.get("nodes") or []))
    relation_count = metadata.get("relation_count", len(links))
    entries[_date_part(timestamp)].append(
        f"**Initialization**: bundle generated from epistract graph "
        f"({entity_count} entities, {relation_count} relations)."
    )

    for link in links:
        if link.get("epistemic_status") != "superseded":
            continue
        if not link.get("source") or not link.get("target"):
            continue
        invalid_at = link.get("invalid_at") or timestamp
        source_title = node_title.get(link.get("source"), link.get("source"))
        target_title = node_title.get(link.get("target"), link.get("target"))
        relation_type = link.get("relation_type", "")
        superseded_by = link.get("superseded_by")
        detail = f"`{source_title}` {relation_type} `{target_title}` marked superseded"
        if superseded_by:
            detail += f" (superseded by `{superseded_by}`)"
        entries[_date_part(invalid_at)].append(f"**Deprecation**: {detail}.")

    lines = ["# Bundle Update Log", ""]
    for date in sorted(entries.keys(), reverse=True):
        lines.append(f"## {date}")
        lines.append("")
        for entry in entries[date]:
            lines.append(f"* {entry}")
        lines.append("")
    (bundle_dir / "log.md").write_text(
        "\n".join(lines).rstrip() + "\n", encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# index.md
# ---------------------------------------------------------------------------


def _write_indexes(
    bundle_dir: Path, metadata: dict, concept_counts: dict[str, int]
) -> None:
    # Per-directory index.md: no frontmatter (reserved for root per OKF spec).
    for path in sorted(bundle_dir.glob("*/")):
        if not path.is_dir():
            continue
        entries = []
        for md_path in sorted(path.glob("*.md")):
            fields, _body = _read_frontmatter(md_path)
            title = fields.get("title", md_path.stem)
            description = fields.get("description", "")
            entries.append(f"* [{_cell(title)}]({md_path.name}) - {_cell(description)}")
        heading = _titleize(path.name)
        lines = [f"# {heading}", ""] + entries
        (path / "index.md").write_text(
            "\n".join(lines).rstrip() + "\n", encoding="utf-8"
        )

    # Root index.md: frontmatter carries okf_version per OKF spec.
    domain = metadata.get("domain")
    heading = f"# {domain} Knowledge Graph" if domain else "# Knowledge Graph"
    lines = [_frontmatter({"okf_version": OKF_VERSION}), "", heading, ""]
    dir_slugs = sorted(
        k for k in concept_counts if ":" not in k and k != SOURCES_DIRNAME
    )
    if dir_slugs:
        lines.append("# Entities")
        lines.append("")
        for dir_slug in dir_slugs:
            lines.append(
                f"* [{_titleize(dir_slug)}]({dir_slug}/) - {concept_counts[dir_slug]} concept(s)"
            )
        lines.append("")
    if SOURCES_DIRNAME in concept_counts:
        lines.append("# Sources")
        lines.append("")
        lines.append(
            f"* [Sources]({SOURCES_DIRNAME}/) - {concept_counts[SOURCES_DIRNAME]} source document(s)"
        )
        lines.append("")
    claim_keys = sorted(k for k in concept_counts if k.startswith(f"{CLAIMS_DIRNAME}:"))
    if claim_keys:
        lines.append("# Claims")
        lines.append("")
        breakdown = ", ".join(
            f"{k.split(':', 1)[1]}: {concept_counts[k]}" for k in claim_keys
        )
        lines.append(f"* [Claims]({CLAIMS_DIRNAME}/) - {breakdown}")
        lines.append("")
    (bundle_dir / "index.md").write_text(
        "\n".join(lines).rstrip() + "\n", encoding="utf-8"
    )


def _read_frontmatter(md_path: Path) -> tuple[dict, str]:
    """Minimal frontmatter reader for index generation (JSON-valued YAML only)."""
    text = md_path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end == -1:
        return {}, text
    header = text[4:end]
    body = text[end + 4 :].lstrip("\n")
    fields: dict[str, object] = {}
    for line in header.splitlines():
        if ":" not in line:
            continue
        key, _, raw_value = line.partition(":")
        key = key.strip()
        raw_value = raw_value.strip()
        try:
            fields[key] = json.loads(raw_value)
        except json.JSONDecodeError:
            fields[key] = raw_value
    return fields, body


# ---------------------------------------------------------------------------
# Sidecar (lossless fidelity, with optional redaction)
# ---------------------------------------------------------------------------


_EVIDENCE_KEYS = frozenset(
    {
        "evidence",
        "evidence_summary",
        "evidence_text",
        "mentions",
        "positive_mentions",
        "negative_mentions",
    }
)


def _redact_evidence(value: object) -> object:
    """Recursively blank dict entries whose key is in the `_EVIDENCE_KEYS`
    allowlist, preserving the original value's container shape.

    Only listed text-bearing keys are blanked, so non-confidential metadata
    like `evidence_tier`/`evidence_tier_counts` (and any other non-listed
    keys) survive — a substring match on 'evidence' would over-blank them.
    Domain epistemic layers vary in shape: the contracts domain uses a flat
    `evidence` key on conflicts/coverage_gaps/risks, while drug-discovery
    nests it under `evidence_summary` and inside `positive_mentions[]`/
    `negative_mentions[]`/`mentions[]`. Intentional tradeoff: blanking
    `mentions`/`positive_mentions`/`negative_mentions` wholesale also drops
    their `document`/`confidence` metadata (the confidentiality-safe
    direction; nested `evidence` inside a mention is caught either way
    because the parent list is blanked, and any stray nested `evidence` key
    elsewhere is caught by the recursive per-key check).
    """
    if isinstance(value, dict):
        redacted: dict[str, object] = {}
        for key, val in value.items():
            if key in _EVIDENCE_KEYS:
                redacted[key] = (
                    {} if isinstance(val, dict) else [] if isinstance(val, list) else ""
                )
            else:
                redacted[key] = _redact_evidence(val)
        return redacted
    if isinstance(value, list):
        return [_redact_evidence(item) for item in value]
    return value


def _write_sidecar(path: Path, data: dict, include_evidence: bool) -> None:
    if include_evidence:
        path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
        return

    copy = json.loads(json.dumps(data, default=str))  # cheap deep copy
    redacted = _redact_evidence(copy)
    path.write_text(json.dumps(redacted, indent=2, default=str), encoding="utf-8")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    project_root_arg = sys.argv[1]
    if project_root_arg.startswith("--"):
        print(
            f"Error: first argument must be the project root, not a flag "
            f"({project_root_arg!r})",
            file=sys.stderr,
        )
        sys.exit(2)

    def _flag_value(flag: str) -> str | None:
        """Return the value following `flag`, None if absent; exit 2 if
        the flag is present but trailing (no value to consume)."""
        if flag not in sys.argv:
            return None
        index = sys.argv.index(flag)
        if index + 1 >= len(sys.argv):
            print(f"Error: {flag} requires a value", file=sys.stderr)
            sys.exit(2)
        return sys.argv[index + 1]

    output_dir_arg = _flag_value("--out")

    include_evidence_arg = "--no-evidence" not in sys.argv

    min_confidence_str = _flag_value("--min-confidence")
    min_confidence_arg = 0.0
    if min_confidence_str is not None:
        try:
            min_confidence_arg = float(min_confidence_str)
        except ValueError:
            print(
                f"Error: --min-confidence requires a number, "
                f"got {min_confidence_str!r}",
                file=sys.stderr,
            )
            sys.exit(2)

    as_json = "--json" in sys.argv

    try:
        result = export_okf(
            project_root_arg,
            output_dir_arg,
            include_evidence=include_evidence_arg,
            min_confidence=min_confidence_arg,
        )
    except (FileNotFoundError, ValueError) as e:
        if as_json:
            print(json.dumps({"error": str(e)}))
        else:
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if as_json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Exported OKF bundle: {result['bundle_path']}")
        print(f"Concepts by kind: {result['concept_counts']}")
        print(f"Skipped edges (below min-confidence): {result['skipped_edges']}")
        if result["warnings"]:
            print("Warnings:")
            for warning in result["warnings"]:
                print(f"  - {warning}")
