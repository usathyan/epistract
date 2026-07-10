#!/usr/bin/env python3
"""Project registry for multi-project epistract datasets.

A "project" is a named, persistent dataset directory (corpus + extractions +
graph + index) that can be created, extended, and queried independently:

    epistract init glp1-research --domain drug-discovery
    epistract add files paper1.pdf paper2.pdf --project glp1-research
    epistract index --project glp1-research
    epistract search "semaglutide" --project glp1-research

State model:
- Global registry:  $EPISTRACT_HOME/registry.json  (default ~/.epistract/)
  maps project name -> {root, domain, created_at}
- Per-project manifest:  <root>/.epistract/project.json
  records domain and every source file with its sha256 content hash,
  which is what makes `epistract index` incremental (unchanged sources
  are skipped on re-index).

Project root layout mirrors the existing pipeline output_dir so all
current commands (build/epistemic/view/export) work on it unchanged:
  <root>/corpus/       source documents (added via `add files` / `add url`)
  <root>/ingested/     extracted text (pipeline)
  <root>/extractions/  per-document DocumentExtraction JSON (pipeline)
  <root>/graph_data.json, claims_layer.json, ...  (pipeline)
  <root>/.epistract/   project.json manifest + index.db
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

REGISTRY_FILENAME = "registry.json"
STATE_DIRNAME = ".epistract"
MANIFEST_FILENAME = "project.json"
NAME_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
MAX_DOWNLOAD_BYTES = 50 * 1024 * 1024

DEFAULT_DOMAIN = "drug-discovery"


class ProjectError(Exception):
    """Raised for user-facing project registry failures."""


# ---------------------------------------------------------------------------
# Registry (global, name -> project root)
# ---------------------------------------------------------------------------


def epistract_home() -> Path:
    """Root for global epistract state. Overridable for tests/relocation."""
    return Path(os.environ.get("EPISTRACT_HOME", str(Path.home() / ".epistract")))


def _registry_path() -> Path:
    return epistract_home() / REGISTRY_FILENAME


def load_registry() -> dict:
    path = _registry_path()
    if not path.exists():
        return {"version": 1, "projects": {}}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        raise ProjectError(f"Corrupt JSON in {path}: {e}") from e


def _save_registry(registry: dict) -> None:
    path = _registry_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(registry, indent=2) + "\n")


def list_projects() -> list[dict]:
    registry = load_registry()
    return [
        {"name": name, **entry} for name, entry in sorted(registry["projects"].items())
    ]


# ---------------------------------------------------------------------------
# Project lifecycle
# ---------------------------------------------------------------------------


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def state_dir(project: dict) -> Path:
    return Path(project["root"]) / STATE_DIRNAME


def corpus_dir(project: dict) -> Path:
    return Path(project["root"]) / "corpus"


def _manifest_path(root: Path) -> Path:
    return root / STATE_DIRNAME / MANIFEST_FILENAME


def save_manifest(project: dict) -> None:
    _manifest_path(Path(project["root"])).write_text(
        json.dumps(project["manifest"], indent=2) + "\n"
    )


def init_project(
    name: str, root: str | Path | None = None, domain: str | None = None
) -> dict:
    """Create a project directory, manifest, and registry entry.

    The directory may already exist (adopting an existing corpus dir is
    fine); an existing epistract manifest in it is an error.
    """
    if not NAME_PATTERN.fullmatch(name):
        raise ProjectError(
            f"Invalid project name '{name}' (use letters, digits, '.', '_', '-')"
        )
    registry = load_registry()
    if name in registry["projects"]:
        existing = registry["projects"][name]["root"]
        raise ProjectError(f"Project '{name}' already exists at {existing}")

    root_path = Path(root).expanduser().resolve() if root else Path.cwd() / name
    if _manifest_path(root_path).exists():
        raise ProjectError(f"{root_path} is already an epistract project")

    (root_path / STATE_DIRNAME).mkdir(parents=True, exist_ok=True)
    (root_path / "corpus").mkdir(exist_ok=True)

    manifest = {
        "name": name,
        "domain": domain or DEFAULT_DOMAIN,
        "created_at": _now(),
        "sources": {},
    }
    project = {
        "name": name,
        "root": str(root_path),
        "domain": manifest["domain"],
        "manifest": manifest,
    }
    save_manifest(project)

    registry["projects"][name] = {
        "root": str(root_path),
        "domain": manifest["domain"],
        "created_at": manifest["created_at"],
    }
    _save_registry(registry)
    return project


def get_project(name: str) -> dict:
    registry = load_registry()
    entry = registry["projects"].get(name)
    if entry is None:
        known = ", ".join(sorted(registry["projects"])) or "(none)"
        raise ProjectError(f"Unknown project '{name}'. Registered projects: {known}")
    root = Path(entry["root"])
    manifest_file = _manifest_path(root)
    if not manifest_file.exists():
        raise ProjectError(
            f"Project '{name}' is registered at {root} but its manifest is missing "
            f"(directory moved or deleted?). Use `epistract projects delete {name}`."
        )
    try:
        manifest = json.loads(manifest_file.read_text())
    except json.JSONDecodeError as e:
        raise ProjectError(f"Corrupt JSON in {manifest_file}: {e}") from e
    return {
        "name": name,
        "root": str(root),
        "domain": manifest.get("domain", entry.get("domain", DEFAULT_DOMAIN)),
        "manifest": manifest,
    }


def resolve_project(name: str | None = None, cwd: str | Path | None = None) -> dict:
    """Resolve the target project: explicit name > $EPISTRACT_PROJECT > cwd walk-up."""
    if name:
        return get_project(name)
    env_name = os.environ.get("EPISTRACT_PROJECT")
    if env_name:
        return get_project(env_name)

    current = Path(cwd).resolve() if cwd else Path.cwd()
    for candidate in (current, *current.parents):
        manifest_file = _manifest_path(candidate)
        if manifest_file.exists():
            try:
                manifest = json.loads(manifest_file.read_text())
            except json.JSONDecodeError as e:
                raise ProjectError(f"Corrupt JSON in {manifest_file}: {e}") from e
            return {
                "name": manifest.get("name", candidate.name),
                "root": str(candidate),
                "domain": manifest.get("domain", DEFAULT_DOMAIN),
                "manifest": manifest,
            }
    known = ", ".join(p["name"] for p in list_projects()) or "(none)"
    raise ProjectError(
        "No project specified and none found in the current directory. "
        f"Pass --project or run inside a project. Registered projects: {known}"
    )


def delete_project(name: str, purge: bool = False) -> dict:
    """Remove a project from the registry.

    With purge=True, also removes the project's .epistract state dir
    (manifest + index). Corpus files and pipeline outputs are never
    deleted — that is left to the user.
    """
    registry = load_registry()
    entry = registry["projects"].pop(name, None)
    if entry is None:
        raise ProjectError(f"Unknown project '{name}'")
    _save_registry(registry)
    if purge:
        state = Path(entry["root"]) / STATE_DIRNAME
        if state.exists():
            shutil.rmtree(state)
    return {"name": name, **entry, "purged": purge}


# ---------------------------------------------------------------------------
# Sources: add files / add url
# ---------------------------------------------------------------------------


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _known_hashes(project: dict) -> set[str]:
    return {src["sha256"] for src in project["manifest"]["sources"].values()}


def _unique_target(directory: Path, filename: str, digest: str) -> Path:
    target = directory / filename
    if not target.exists():
        return target
    return directory / f"{digest[:8]}-{filename}"


def _record_source(project: dict, target: Path, digest: str, origin: str) -> None:
    rel = str(target.relative_to(project["root"]))
    project["manifest"]["sources"][rel] = {
        "sha256": digest,
        "origin": origin,
        "added_at": _now(),
    }


def add_files(project: dict, paths: list[str | Path]) -> dict:
    """Copy files into the project corpus, deduplicated by content hash."""
    corpus = corpus_dir(project)
    corpus.mkdir(parents=True, exist_ok=True)
    known = _known_hashes(project)
    report = {"added": [], "skipped_duplicate": [], "missing": []}

    for raw in paths:
        source = Path(raw).expanduser()
        if not source.is_file():
            report["missing"].append(str(source))
            continue
        data = source.read_bytes()
        digest = _sha256(data)
        if digest in known:
            report["skipped_duplicate"].append(str(source))
            continue
        target = _unique_target(corpus, source.name, digest)
        target.write_bytes(data)
        _record_source(project, target, digest, str(source.resolve()))
        known.add(digest)
        report["added"].append(str(target))

    save_manifest(project)
    return report


def _default_fetcher(url: str) -> bytes:
    scheme = urlparse(url).scheme
    if scheme not in {"http", "https"}:
        raise ProjectError(
            f"Unsupported URL scheme '{scheme}' for {url} (only http/https)"
        )
    request = Request(url, headers={"User-Agent": "epistract/1.0"})
    with urlopen(request, timeout=60) as response:  # noqa: S310 — scheme checked above
        data = response.read(MAX_DOWNLOAD_BYTES + 1)
    if len(data) > MAX_DOWNLOAD_BYTES:
        raise ProjectError(f"{url} exceeds the {MAX_DOWNLOAD_BYTES} byte download cap")
    return data


def _filename_from_url(url: str) -> str:
    parsed = urlparse(url)
    name = Path(parsed.path).name
    if not name:
        name = f"{parsed.netloc or 'download'}.html"
    if "." not in name:
        name = f"{name}.html"
    return name


def add_url(project: dict, url: str, fetcher=None) -> dict:
    """Fetch a URL into the project corpus, deduplicated by content hash."""
    fetch = fetcher or _default_fetcher
    data = fetch(url)
    digest = _sha256(data)
    if digest in _known_hashes(project):
        return {"url": url, "status": "skipped_duplicate"}
    corpus = corpus_dir(project)
    corpus.mkdir(parents=True, exist_ok=True)
    target = _unique_target(corpus, _filename_from_url(url), digest)
    target.write_bytes(data)
    _record_source(project, target, digest, url)
    save_manifest(project)
    return {"url": url, "status": "added", "file": str(target)}
