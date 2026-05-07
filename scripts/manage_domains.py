#!/usr/bin/env python3
"""Domain management utilities for epistract.

Usage:
    python3 scripts/manage_domains.py list
    python3 scripts/manage_domains.py info <name>
    python3 scripts/manage_domains.py archive <name>
    python3 scripts/manage_domains.py remove <name>
    python3 scripts/manage_domains.py validate <name>
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

# ---------------------------------------------------------------------------
# Constants — EPISTRACT_DOMAINS_DIR env var overrides at module startup
# ---------------------------------------------------------------------------

_env_override = os.environ.get("EPISTRACT_DOMAINS_DIR")
if _env_override:
    DOMAINS_DIR = Path(_env_override)
else:
    DOMAINS_DIR = Path(__file__).parent.parent / "domains"
ARCHIVED_DIR = DOMAINS_DIR / "_archived"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _validate_active_name(name: str) -> Path | None:
    """Return domain dir only if name appears in the enumerated active list.

    Enumerates DOMAINS_DIR.iterdir() into a set first; checks name membership
    before constructing path — rejects traversal strings like '../secrets'
    that won't appear in iterdir().

    Args:
        name: Domain name to validate.

    Returns:
        Path to domain directory if valid active domain, else None.
    """
    if not DOMAINS_DIR.is_dir():
        return None
    active_names = {
        d.name
        for d in DOMAINS_DIR.iterdir()
        if d.is_dir() and not d.name.startswith("_") and (d / "domain.yaml").exists()
    }
    if name not in active_names:
        return None
    return DOMAINS_DIR / name


def _build_domain_row(domain_dir: Path, yaml_path: Path, status: str) -> dict:
    """Build a domain metadata row dict from a domain directory.

    Args:
        domain_dir: Path to the domain directory.
        yaml_path: Path to domain.yaml within the directory.
        status: 'active' or 'archived'.

    Returns:
        Dict with keys: name, entity_types, relation_types, last_modified,
        status, file_count, dir.
    """
    schema = yaml.safe_load(yaml_path.read_text())
    entity_count = len(schema.get("entity_types", {}))
    relation_count = len(schema.get("relation_types", {}))
    mtime = os.path.getmtime(yaml_path)
    last_modified = datetime.fromtimestamp(mtime, tz=timezone.utc).strftime("%Y-%m-%d")
    file_count = len(list(domain_dir.rglob("*")))
    return {
        "name": domain_dir.name,
        "entity_types": entity_count,
        "relation_types": relation_count,
        "last_modified": last_modified,
        "status": status,
        "file_count": file_count,
        "dir": str(domain_dir),
    }


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------


def cmd_list() -> int:
    """List all domains — active and archived — as a JSON array.

    Returns:
        Exit code 0.
    """
    rows = []
    if DOMAINS_DIR.is_dir():
        for d in sorted(DOMAINS_DIR.iterdir()):
            if d.name.startswith("_"):
                continue
            yaml_path = d / "domain.yaml"
            if d.is_dir() and yaml_path.exists():
                rows.append(_build_domain_row(d, yaml_path, "active"))
    if ARCHIVED_DIR.is_dir():
        for d in sorted(ARCHIVED_DIR.iterdir()):
            yaml_path = d / "domain.yaml"
            if d.is_dir() and yaml_path.exists():
                rows.append(_build_domain_row(d, yaml_path, "archived"))
    print(json.dumps(rows, indent=2))
    return 0


def cmd_info(name: str) -> int:
    """Return metadata for a single domain as a JSON object.

    Checks active domains first, then archived.

    Args:
        name: Domain name.

    Returns:
        Exit code 0 on success, 1 if domain not found.
    """
    src = _validate_active_name(name)
    if src is None:
        # Check archived location before returning not-found error
        archived_path = ARCHIVED_DIR / name
        if archived_path.is_dir() and (archived_path / "domain.yaml").exists():
            print(
                json.dumps(
                    _build_domain_row(
                        archived_path, archived_path / "domain.yaml", "archived"
                    ),
                    indent=2,
                )
            )
            return 0
        print(
            json.dumps(
                {
                    "error": f"Domain '{name}' not found.",
                    "hint": "Check 'manage_domains.py list' for available domains.",
                },
                indent=2,
            )
        )
        return 1
    yaml_path = src / "domain.yaml"
    if not yaml_path.exists():
        print(
            json.dumps(
                {"error": f"Domain '{name}' directory exists but has no domain.yaml."},
                indent=2,
            )
        )
        return 1
    print(json.dumps(_build_domain_row(src, yaml_path, "active"), indent=2))
    return 0


def cmd_archive(name: str) -> int:
    """Move an active domain to the _archived/ directory.

    Creates ARCHIVED_DIR only at archive time (never at import time).
    Checks for collision before moving.

    Args:
        name: Domain name to archive.

    Returns:
        Exit code 0 on success, 1 on error.
    """
    src = _validate_active_name(name)
    if src is None:
        print(
            json.dumps(
                {"error": f"Domain '{name}' not found or not a valid domain package."},
                indent=2,
            )
        )
        return 1
    ARCHIVED_DIR.mkdir(parents=True, exist_ok=True)
    dst = ARCHIVED_DIR / name
    if dst.exists():
        print(
            json.dumps(
                {"error": (f"Archived copy already exists at {dst}. Remove it first.")},
                indent=2,
            )
        )
        return 1
    shutil.move(str(src), str(dst))
    print(json.dumps({"archived": name, "destination": str(dst)}, indent=2))
    return 0


def cmd_remove(name: str) -> int:
    """Permanently delete a domain — checks active location first, then archived.

    Args:
        name: Domain name to remove.

    Returns:
        Exit code 0 on success, 1 if domain not found.
    """
    # Check active location first
    src = DOMAINS_DIR / name
    if src.is_dir() and (src / "domain.yaml").exists():
        shutil.rmtree(src)
        print(json.dumps({"removed": name, "from": "active"}, indent=2))
        return 0
    # Check archived location
    archived = ARCHIVED_DIR / name
    if archived.is_dir() and (archived / "domain.yaml").exists():
        shutil.rmtree(archived)
        print(json.dumps({"removed": name, "from": "archived"}, indent=2))
        return 0
    print(
        json.dumps(
            {"error": f"Domain '{name}' not found (active or archived)."},
            indent=2,
        )
    )
    return 1


def validate_schema(entity_types: dict, relation_types: dict) -> list[str]:
    """Validate schema consistency: no dangling relation endpoints, no duplicate names.

    Implements D-06 validation rules (three checks):
      1. No duplicate names within entity_types namespace.
      2. No duplicate names within relation_types namespace.
      3. No dangling endpoints — for relations that declare source_types, target_types,
         source, or target fields, every referenced name must exist in entity_types.
         Relations with no endpoint fields (contracts-domain pattern) are skipped.

    Namespaces are independent: an entity type and a relation type may share a name
    without triggering a duplicate error.

    Args:
        entity_types: Dict of entity type name -> definition dict.
        relation_types: Dict of relation type name -> definition dict.

    Returns:
        List of error strings. Empty list means schema is valid.
    """
    errors: list[str] = []
    entity_names = set(entity_types.keys())

    # Check 1: No duplicate entity type names
    entity_keys = list(entity_types.keys())
    if len(set(entity_keys)) != len(entity_keys):
        errors.append("Duplicate entity type name detected.")

    # Check 2: No duplicate relation type names
    rel_keys = list(relation_types.keys())
    if len(set(rel_keys)) != len(rel_keys):
        errors.append("Duplicate relation type name detected.")

    # Check 3: No dangling endpoints (only for relations that declare endpoint fields)
    for rel_name, rel_def in relation_types.items():
        if not isinstance(rel_def, dict):
            continue
        for field in ("source_types", "target_types"):
            if field in rel_def:
                for ep in rel_def[field] or []:
                    if ep not in entity_names:
                        errors.append(
                            f"Relation type '{rel_name}' references entity type "
                            f"'{ep}' which does not exist in entity_types."
                        )
        for field in ("source", "target"):
            if field in rel_def:
                ep = rel_def[field]
                if ep not in entity_names:
                    errors.append(
                        f"Relation type '{rel_name}' references entity type "
                        f"'{ep}' which does not exist in entity_types."
                    )
    return errors


def cmd_validate(name: str) -> int:
    """Validate schema consistency for a domain and print results as JSON.

    Loads domain.yaml for the named domain, runs validate_schema(), and prints
    {"valid": bool, "errors": list[str]}. Exits 0 whether or not violations are
    found — the JSON payload communicates validity. Exits 1 only if domain is not
    found or domain.yaml cannot be loaded.

    Args:
        name: Domain name (active or archived).

    Returns:
        Exit code 0 on success, 1 if domain not found.
    """
    src = _validate_active_name(name)
    if src is None:
        archived_path = ARCHIVED_DIR / name
        if archived_path.is_dir() and (archived_path / "domain.yaml").exists():
            src = archived_path
        else:
            print(
                json.dumps(
                    {
                        "error": f"Domain '{name}' not found.",
                        "hint": "Check 'manage_domains.py list' for available domains.",
                    },
                    indent=2,
                )
            )
            return 1
    yaml_path = src / "domain.yaml"
    schema = yaml.safe_load(yaml_path.read_text())
    entity_types = schema.get("entity_types", {}) or {}
    relation_types = schema.get("relation_types", {}) or {}
    errors = validate_schema(entity_types, relation_types)
    print(
        json.dumps(
            {"valid": len(errors) == 0, "errors": errors},
            indent=2,
        )
    )
    return 0


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    _USAGE = (
        "Usage:\n"
        "  manage_domains.py list\n"
        "  manage_domains.py info <name>\n"
        "  manage_domains.py archive <name>\n"
        "  manage_domains.py remove <name>\n"
        "  manage_domains.py validate <name>\n"
    )

    if len(sys.argv) < 2:
        print(_USAGE, file=sys.stderr)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "list":
        sys.exit(cmd_list())
    elif cmd in ("info", "archive", "remove", "validate"):
        if len(sys.argv) < 3:
            print(f"Usage: manage_domains.py {cmd} <name>", file=sys.stderr)
            sys.exit(1)
        name = sys.argv[2]
        if cmd == "info":
            sys.exit(cmd_info(name))
        elif cmd == "archive":
            sys.exit(cmd_archive(name))
        elif cmd == "remove":
            sys.exit(cmd_remove(name))
        elif cmd == "validate":
            sys.exit(cmd_validate(name))
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        print(_USAGE, file=sys.stderr)
        sys.exit(1)
