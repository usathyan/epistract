#!/usr/bin/env python3
"""Domain resolution infrastructure for epistract.

Discovers and loads domain schemas from the domains/ directory.
Each domain is a self-contained package with domain.yaml, SKILL.md,
references, validation scripts, and epistemic analysis.

Usage:
    from core.domain_resolver import resolve_domain, list_domains

    schema = resolve_domain("drug-discovery")
    schema = resolve_domain("contracts")
    all_domains = list_domains()
"""

from __future__ import annotations

import json
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DOMAINS_DIR = Path(__file__).parent.parent / "domains"
DEFAULT_DOMAIN = "drug-discovery"

# Aliases map common short names to directory names
DOMAIN_ALIASES: dict[str, str] = {
    "contract": "contracts",
    "biomedical": "drug-discovery",
    "drug_discovery": "drug-discovery",
    "pharma": "drug-discovery",
    "clinicaltrial": "clinicaltrials",
    "clinical_trials": "clinicaltrials",
}


def _resolve_domain_dir(name: str) -> Path:
    """Resolve a domain name to its directory path.

    Handles aliases and direct directory name lookups.
    """
    # Check aliases first
    resolved = DOMAIN_ALIASES.get(name, name)
    domain_dir = DOMAINS_DIR / resolved
    if domain_dir.is_dir():
        return domain_dir

    # Try the name directly
    domain_dir = DOMAINS_DIR / name
    if domain_dir.is_dir():
        return domain_dir

    raise FileNotFoundError(
        f"Domain '{name}' not found in {DOMAINS_DIR}. "
        f"Available: {', '.join(list_domains())}"
    )


def get_validation_dir(domain_name: str) -> Path | None:
    """Return the domain's validation/ directory if it exists and ships a run_validation.py.

    FIDL-07 (D-03): Convention-based auto-discovery of optional post-build
    validators. A domain "has a validator" iff
    ``<domain_dir>/validation/run_validation.py`` exists. Missing directory,
    missing ``run_validation.py``, or unknown domain → None (silent —
    per D-08 the absence of a validator is not a warning condition).

    Args:
        domain_name: Domain name (handles aliases via ``_resolve_domain_dir``).

    Returns:
        Path to ``<domain_dir>/validation`` when the convention file is
        present, else None.
    """
    try:
        domain_dir = _resolve_domain_dir(domain_name)
    except FileNotFoundError:
        return None
    validation_dir = domain_dir / "validation"
    if not validation_dir.is_dir():
        return None
    if not (validation_dir / "run_validation.py").is_file():
        return None
    return validation_dir


def resolve_domain(name: str | None = None) -> dict:
    """Resolve a domain by name and return its schema as a dict.

    Args:
        name: Domain name (e.g., "drug-discovery", "contracts").
              Defaults to DEFAULT_DOMAIN if None.

    Returns:
        Dict with keys: name, dir, yaml_path, skill_path, schema, validation_dir.
        The ``validation_dir`` key (FIDL-07 D-03) is None when the domain
        ships no ``validation/run_validation.py`` convention entry point.
    """
    name = name or DEFAULT_DOMAIN
    domain_dir = _resolve_domain_dir(name)
    yaml_path = domain_dir / "domain.yaml"

    if not yaml_path.exists():
        raise FileNotFoundError(
            f"Domain schema not found: {yaml_path}"
        )

    # Load YAML schema
    try:
        import yaml
        schema = yaml.safe_load(yaml_path.read_text())
    except ImportError:
        # Fallback: return path only, caller loads with their own YAML parser
        schema = None

    validation_dir = get_validation_dir(name)

    return {
        "name": name,
        "dir": str(domain_dir),
        "yaml_path": str(yaml_path),
        "skill_path": str(domain_dir / "SKILL.md"),
        "schema": schema,
        "validation_dir": str(validation_dir) if validation_dir else None,
    }


def list_domains() -> list[str]:
    """List all available domain names.

    Returns:
        List of domain directory names found in DOMAINS_DIR.
    """
    if not DOMAINS_DIR.is_dir():
        return []
    return sorted(
        d.name for d in DOMAINS_DIR.iterdir()
        if d.is_dir() and (d / "domain.yaml").exists()
    )


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        domain = resolve_domain(sys.argv[1])
        print(json.dumps({k: v for k, v in domain.items() if k != "schema"}, indent=2))
    else:
        domains = list_domains()
        print(f"Available domains: {', '.join(domains) or 'none found'}")
        print(f"Domains directory: {DOMAINS_DIR}")
