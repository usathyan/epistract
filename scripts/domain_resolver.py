#!/usr/bin/env python3
"""Domain resolution infrastructure for cross-domain knowledge graph framework.

Provides functions to resolve domain names to paths, discover available domains,
validate domain package completeness, and access domain resources (SKILL.md,
validation-scripts).

Functions:
    resolve_domain(domain_name) -> Path to domain.yaml
    list_domains() -> list of domain info dicts
    get_domain_skill_md(domain_name) -> SKILL.md content string
    get_validation_scripts_dir(domain_name) -> Path or None
    validate_domain_cross_refs(domain_path) -> list of error strings

Usage:
    from domain_resolver import resolve_domain, list_domains

    # Default (backward compat): returns drug-discovery domain
    path = resolve_domain(None)

    # Explicit domain
    path = resolve_domain("contract")

    # List all available domains
    for d in list_domains():
        print(f"{d['name']}: {d['description']}")
"""

from __future__ import annotations

from pathlib import Path


# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

SKILLS_DIR = Path(__file__).parent.parent / "skills"
DEFAULT_DOMAIN = "drug-discovery"


# ---------------------------------------------------------------------------
# Domain resolution
# ---------------------------------------------------------------------------


def resolve_domain(domain_name: str | None = None) -> Path:
    """Resolve a domain name to the path of its domain.yaml file.

    Args:
        domain_name: Short domain name (e.g. "drug-discovery", "contract").
            If None, defaults to DEFAULT_DOMAIN for backward compatibility.

    Returns:
        Path to domain.yaml within the domain package directory.

    Raises:
        FileNotFoundError: If domain directory, domain.yaml, SKILL.md, or
            references/ directory is missing. Error message lists available
            domains when directory not found.
    """
    name = domain_name if domain_name is not None else DEFAULT_DOMAIN
    domain_dir = SKILLS_DIR / f"{name}-extraction"

    if not domain_dir.is_dir():
        available = [d["name"] for d in list_domains()]
        raise FileNotFoundError(
            f"Domain '{name}' not found at {domain_dir}. "
            f"Available domains: {available}"
        )

    # Validate required domain package files (D-03)
    domain_yaml = domain_dir / "domain.yaml"
    if not domain_yaml.is_file():
        raise FileNotFoundError(
            f"Domain '{name}' is missing domain.yaml at {domain_yaml}"
        )

    skill_md = domain_dir / "SKILL.md"
    if not skill_md.is_file():
        raise FileNotFoundError(f"Domain '{name}' is missing SKILL.md at {skill_md}")

    references_dir = domain_dir / "references"
    if not references_dir.is_dir():
        raise FileNotFoundError(
            f"Domain '{name}' is missing references/ directory at {references_dir}"
        )

    return domain_yaml


def list_domains() -> list[dict[str, str]]:
    """Discover all available domains under SKILLS_DIR.

    Scans for directories containing domain.yaml, parses each to extract
    name, description, and version metadata.

    Returns:
        List of dicts with keys: name, description, version.
        Domains that fail to parse are silently skipped.
    """
    import yaml

    domains: list[dict[str, str]] = []

    if not SKILLS_DIR.is_dir():
        return domains

    for entry in sorted(SKILLS_DIR.iterdir()):
        if not entry.is_dir():
            continue
        yaml_path = entry / "domain.yaml"
        if not yaml_path.is_file():
            continue

        try:
            data = yaml.safe_load(yaml_path.read_text())
            # Strip -extraction suffix from directory name for short name
            dir_name = entry.name
            short_name = (
                dir_name[: -len("-extraction")]
                if dir_name.endswith("-extraction")
                else dir_name
            )

            description = data.get("description", "")
            # Take first line only for brevity
            if isinstance(description, str):
                description = description.strip().split("\n")[0]

            domains.append(
                {
                    "name": short_name,
                    "description": description,
                    "version": str(data.get("version", "unknown")),
                }
            )
        except Exception:
            # Skip unparseable domains
            continue

    return domains


# ---------------------------------------------------------------------------
# Domain resource accessors
# ---------------------------------------------------------------------------


def get_domain_skill_md(domain_name: str | None = None) -> str:
    """Read and return the SKILL.md content for a domain.

    Args:
        domain_name: Short domain name, or None for default.

    Returns:
        Content of SKILL.md as a string.

    Raises:
        FileNotFoundError: If domain or SKILL.md not found.
    """
    domain_yaml = resolve_domain(domain_name)
    skill_md = domain_yaml.parent / "SKILL.md"
    return skill_md.read_text()


def get_validation_scripts_dir(domain_name: str | None = None) -> Path | None:
    """Get the validation-scripts directory for a domain, if it exists.

    Args:
        domain_name: Short domain name, or None for default.

    Returns:
        Path to validation-scripts/ directory if it exists, None otherwise.

    Raises:
        FileNotFoundError: If domain not found.
    """
    domain_yaml = resolve_domain(domain_name)
    vs_dir = domain_yaml.parent / "validation-scripts"
    return vs_dir if vs_dir.is_dir() else None


# ---------------------------------------------------------------------------
# Cross-reference validation
# ---------------------------------------------------------------------------


def validate_domain_cross_refs(domain_path: Path) -> list[str]:
    """Validate that all relation source/target types reference valid entity types.

    Args:
        domain_path: Path to domain.yaml file.

    Returns:
        List of error strings. Empty list means all cross-references are valid.
    """
    import yaml

    data = yaml.safe_load(domain_path.read_text())

    entity_types = set(data.get("entity_types", {}).keys())
    errors: list[str] = []

    for rel_name, rel_def in data.get("relation_types", {}).items():
        if not isinstance(rel_def, dict):
            continue

        for field in ("source_types", "target_types"):
            type_list = rel_def.get(field, [])
            if not isinstance(type_list, list):
                continue
            for t in type_list:
                if t not in entity_types:
                    errors.append(
                        f"Relation '{rel_name}' {field} references "
                        f"unknown entity type '{t}'"
                    )

    return errors
