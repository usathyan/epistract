#!/usr/bin/env python3
"""Label communities with descriptive names based on member composition.

Reads communities.json and graph_data.json, generates semantic labels for each
community, and writes updated files.

Usage:
    python label_communities.py <output_dir>
"""

import json
import sys
from collections import Counter
from pathlib import Path


def _anchor_label(members: list[dict], anchors: list[str]) -> str | None:
    """Generate a community label using domain-configured anchor entity types.

    Walks the priority list (anchors) in order; first anchor type that has
    at least one member in the community becomes the label source.

    Args:
        members: List of node dicts with keys "name" and "entity_type".
        anchors: Ordered priority list of entity type names from domain.yaml
                 community_label_anchors. First match wins.

    Returns:
        Label string if any anchor matches, else None (caller falls back to
        _generate_label for backward compatibility).
    """
    MAX_NAME_LEN = 40

    def _truncate(name: str) -> str:
        cleaned = _clean_name(name)
        return cleaned[:MAX_NAME_LEN] + "…" if len(cleaned) > MAX_NAME_LEN else cleaned

    for anchor_type in anchors:
        matched = [m for m in members if m.get("entity_type") == anchor_type]
        if not matched:
            continue
        names = [_truncate(m["name"]) for m in matched]
        if len(names) == 1:
            return names[0]
        if len(names) == 2:
            return f"{names[0]} / {names[1]}"
        return f"{names[0]} + {len(names) - 1} more"
    return None


def _load_domain_anchors(graph_data: dict) -> list[str]:
    """Load community_label_anchors from the domain yaml referenced by graph_data.

    Reads metadata.domain from graph_data, resolves the domain via
    core.domain_resolver.resolve_domain, and returns community_label_anchors.
    Returns empty list on any failure to preserve backward compatibility.

    Args:
        graph_data: Parsed graph_data.json dict.

    Returns:
        List of anchor entity type names, or [] if not configured or on error.
    """
    try:
        from core.domain_resolver import resolve_domain

        domain_name = graph_data.get("metadata", {}).get("domain")
        if not domain_name:
            return []
        info = resolve_domain(domain_name)
        schema = info.get("schema") or {}
        anchors = schema.get("community_label_anchors", [])
        return anchors if isinstance(anchors, list) else []
    except Exception:
        return []


def _top_entities(members: list[dict], n: int = 5) -> list[str]:
    """Return the top-N most-connected entity names (by link count) in a community."""
    # Sort by number of connections (approximated by confidence or just alphabetically)
    # Prefer genes/proteins/pathways as label anchors
    priority = {
        # Biomedical (existing)
        "GENE": 1, "PROTEIN": 2, "PATHWAY": 3, "DISEASE": 4,
        "MECHANISM_OF_ACTION": 5, "PHENOTYPE": 6, "SEQUENCE_VARIANT": 7,
        "COMPOUND": 0, "BIOMARKER": 8, "CELL_OR_TISSUE": 9,
        # Contract domain
        "PARTY": 0, "VENUE": 1, "SERVICE": 2, "OBLIGATION": 3,
        "COST": 4, "DEADLINE": 5, "CLAUSE": 6,
    }
    sorted_members = sorted(
        members,
        key=lambda m: (priority.get(m.get("entity_type", ""), 99), m.get("name", "")),
    )
    return [m["name"] for m in sorted_members[:n]]


def _generate_label(members: list[dict]) -> str:
    """Generate a descriptive community label from member composition."""
    type_counts = Counter(m.get("entity_type", "UNKNOWN") for m in members)
    total = len(members)

    # --- Contract domain labeling ---
    parties = [m["name"] for m in members if m.get("entity_type") == "PARTY"]
    venues = [m["name"] for m in members if m.get("entity_type") == "VENUE"]
    services = [m["name"] for m in members if m.get("entity_type") == "SERVICE"]
    obligations = [m["name"] for m in members if m.get("entity_type") == "OBLIGATION"]
    costs = [m["name"] for m in members if m.get("entity_type") == "COST"]
    deadlines_c = [m["name"] for m in members if m.get("entity_type") == "DEADLINE"]
    clauses = [m["name"] for m in members if m.get("entity_type") == "CLAUSE"]

    # Detect contract domain (any contract entity type present)
    is_contract = bool(parties or venues or services or obligations or costs or deadlines_c or clauses)

    if is_contract:
        # Party-anchored community
        if parties and len(parties) <= 3:
            party_str = " & ".join(_clean_name(p) for p in parties[:2])
            if services:
                return f"{party_str}: {_clean_name(services[0])}"
            if venues:
                return f"{party_str} at {_clean_name(venues[0])}"
            if obligations:
                return f"{party_str} Obligations ({len(obligations)})"
            return f"{party_str} Contract Terms"

        # Venue-anchored community
        if venues and not parties:
            venue_str = _clean_name(venues[0])
            if services:
                return f"{venue_str}: {_clean_name(services[0])}"
            return f"{venue_str} Requirements"

        # Cost/deadline cluster
        if costs and len(costs) > total * 0.4:
            if parties:
                return f"{_clean_name(parties[0])} Costs ({len(costs)} items)"
            return f"Cost Schedule ({len(costs)} items)"

        if deadlines_c and len(deadlines_c) > total * 0.4:
            return f"Timeline & Deadlines ({len(deadlines_c)} dates)"

        # Generic contract fallback
        top = _top_entities(members, 3)
        return " / ".join(_clean_name(t) for t in top)

    # --- Biomedical domain labeling ---
    genes = [m["name"] for m in members if m.get("entity_type") == "GENE"]
    proteins = [m["name"] for m in members if m.get("entity_type") == "PROTEIN"]
    pathways = [m["name"] for m in members if m.get("entity_type") == "PATHWAY"]
    diseases = [m["name"] for m in members if m.get("entity_type") == "DISEASE"]
    variants = [m["name"] for m in members if m.get("entity_type") == "SEQUENCE_VARIANT"]
    mechanisms = [m["name"] for m in members if m.get("entity_type") == "MECHANISM_OF_ACTION"]
    phenotypes = [m["name"] for m in members if m.get("entity_type") == "PHENOTYPE"]
    cells = [m["name"] for m in members if m.get("entity_type") == "CELL_OR_TISSUE"]
    compounds = [m["name"] for m in members if m.get("entity_type") == "COMPOUND"]
    biomarkers = [m["name"] for m in members if m.get("entity_type") == "BIOMARKER"]

    # 1. Gene-dominant cluster (GWAS-like) — only for truly gene-heavy clusters
    #    Must be >50% genes AND >15 members to qualify as a GWAS locus cluster.
    #    Smaller clusters with genes + pathways are better labeled by pathway.
    if len(genes) > total * 0.5 and total > 15:
        if diseases:
            disease = _clean_name(diseases[0])
            return f"{disease} Risk Loci ({len(genes)} genes)"
        return f"Genetic Risk Loci ({', '.join(_clean_name(g) for g in genes[:4])})"

    # 2. Variant-dominant cluster — majority must be variants
    if variants and len(variants) > total * 0.5:
        gene_prefixes = set()
        for v in variants:
            parts = v.replace("_", " ").split()
            if parts:
                gene_prefixes.add(parts[0].upper())
        if len(gene_prefixes) == 1:
            gene = gene_prefixes.pop()
            return f"{gene} Genetic Variants"
        prefix_str = ", ".join(sorted(gene_prefixes)[:3])
        return f"Genetic Variants ({prefix_str})"

    # 3. Mechanism + cell type cluster (specific biological finding)
    if mechanisms and cells:
        mech = _clean_name(mechanisms[0])
        cell = _clean_name(cells[0])
        return f"{mech} in {cell}"

    # 4. Mechanism-driven cluster
    if mechanisms and total < 15:
        mech = _clean_name(mechanisms[0])
        if phenotypes:
            return f"{mech} / {_clean_name(phenotypes[0])}"
        return mech

    # 5. Pathway-driven cluster (only for small/medium communities)
    if pathways and total < 20:
        pathway_str = " / ".join(_clean_name(p) for p in pathways[:2])
        if cells:
            return f"{pathway_str} in {_clean_name(cells[0])}"
        if genes and len(genes) <= 5:
            return f"{pathway_str} ({', '.join(_clean_name(g) for g in genes[:3])})"
        return pathway_str

    # 6. Disease + protein cluster (core pathology)
    if diseases and proteins:
        disease = _clean_name(diseases[0])
        protein_str = ", ".join(_clean_name(p) for p in proteins[:3])
        return f"{disease} — {protein_str}"

    # 7. Phenotype-driven cluster
    if phenotypes and len(phenotypes) > total * 0.3:
        return " / ".join(_clean_name(p) for p in phenotypes[:3])

    # 8. Fallback: top entities by priority
    top = _top_entities(members, 3)
    return " / ".join(_clean_name(t) for t in top)


def _clean_name(name: str) -> str:
    """Clean an entity name for display."""
    return name.replace("_", " ").replace("  ", " ").strip().title()


def label_communities(output_dir: Path) -> dict:
    """Read communities.json and graph_data.json, generate labels, update files."""
    communities_path = output_dir / "communities.json"
    graph_path = output_dir / "graph_data.json"

    if not communities_path.exists():
        print("No communities.json found", file=sys.stderr)
        return {}

    communities = json.loads(communities_path.read_text())
    graph_data = json.loads(graph_path.read_text()) if graph_path.exists() else {}

    # Build node lookup from graph_data
    node_lookup = {}
    for node in graph_data.get("nodes", []):
        node_lookup[node["id"]] = node

    # Load domain-configured label anchors (FDA-09). Returns [] when
    # community_label_anchors is absent from domain.yaml (backward compat).
    domain_anchors = _load_domain_anchors(graph_data)

    # Group members by community
    community_members = {}
    for entity_id, community_name in communities.items():
        if community_name not in community_members:
            community_members[community_name] = []
        node = node_lookup.get(entity_id, {"name": entity_id.split(":", 1)[-1], "entity_type": entity_id.split(":", 1)[0].upper()})
        community_members[community_name].append(node)

    # Generate labels
    label_map = {}  # old name -> new name
    results = []

    for old_name in sorted(community_members.keys()):
        members = community_members[old_name]
        if domain_anchors:
            label = _anchor_label(members, domain_anchors) or _generate_label(members)
        else:
            label = _generate_label(members)
        label_map[old_name] = label
        results.append({"community": old_name, "label": label, "members": len(members)})

    # Update communities.json with new labels
    new_communities = {}
    for entity_id, old_name in communities.items():
        new_communities[entity_id] = label_map.get(old_name, old_name)
    communities_path.write_text(json.dumps(new_communities, indent=2))

    # Update graph_data.json nodes with community labels
    if graph_data:
        for node in graph_data.get("nodes", []):
            old_community = None
            for entity_id, comm in communities.items():
                if entity_id == node["id"]:
                    old_community = comm
                    break
            if old_community and old_community in label_map:
                node["community"] = label_map[old_community]
        graph_path.write_text(json.dumps(graph_data, indent=2))

    print(json.dumps(results, indent=2))
    return label_map


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python label_communities.py <output_dir>", file=sys.stderr)
        sys.exit(1)
    label_communities(Path(sys.argv[1]))
