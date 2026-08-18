"""Every core/ module that commands/ invokes by absolute path must be runnable
that way.

`python3 /abs/path/to/core/foo.py` puts `core/` on `sys.path[0]`, NOT the
project root — so a `from core.domain_resolver import ...` inside that module
raises `ModuleNotFoundError: No module named 'core'`. `python3 -m core.foo`
does not have this problem, which is why the failure hid: the test suite and
the docs in `docs/` use the module form, while `commands/*.md` uses the script
form, and only the latter is what actually runs in the plugin.

The failure is worse for a deferred import (one inside a function): the script
starts, does real work, and dies partway through. `core/label_epistemic.py`
shipped this way — `/epistract:epistemic` died mid-run on every domain.

The fix is a `_PROJECT_ROOT` sys.path insert at the top of each such module.
These tests discover the entry points rather than hardcoding a list, so a new
module with the same shape is covered the day it lands.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CORE_DIR = PROJECT_ROOT / "core"

# A real `core.*` import: at the start of a line (optionally indented, i.e.
# deferred inside a function), not inside a docstring's "Usage:" example. The
# docstring examples in domain_resolver.py and okf_export.py are indented four
# spaces at module level, so indentation alone cannot separate them — we strip
# docstrings via a crude but sufficient triple-quote split instead.
_CORE_IMPORT = re.compile(r"^[ \t]*(?:from|import)\s+core\.", re.M)


def _strip_docstrings(src: str) -> str:
    """Drop everything inside triple-quoted regions.

    Crude (it does not parse), but it only has to be good enough to keep a
    `Usage:` example out of the import scan, and being wrong in the
    conservative direction just means testing one extra module.
    """
    for quote in ('"""', "'''"):
        parts = src.split(quote)
        src = "".join(parts[::2])
    return src


def _script_entry_points() -> list[Path]:
    """core/*.py modules that are script-invokable AND import the core package."""
    found = []
    for path in sorted(CORE_DIR.glob("*.py")):
        src = path.read_text(encoding="utf-8")
        if '__name__ == "__main__"' not in src:
            continue
        if not _CORE_IMPORT.search(_strip_docstrings(src)):
            continue
        found.append(path)
    return found


ENTRY_POINTS = _script_entry_points()


def test_the_discovery_itself_found_something():
    """A regex that silently matches nothing would make every test below
    vacuously pass."""
    names = {p.name for p in ENTRY_POINTS}
    assert "label_epistemic.py" in names, f"discovery is broken; found {sorted(names)}"
    assert "run_sift.py" in names, f"discovery is broken; found {sorted(names)}"


@pytest.mark.parametrize("module_path", ENTRY_POINTS, ids=lambda p: p.name)
def test_runnable_as_a_script_from_an_unrelated_cwd(module_path, tmp_path):
    """The plugin condition: absolute script path, arbitrary working directory.

    Run with no arguments — every one of these prints usage or an argument
    error and exits. We assert only that it does not die on the core-package
    import; the exit code is deliberately not checked, because "usage, exit 1"
    is a correct outcome here.
    """
    proc = subprocess.run(
        [sys.executable, str(module_path.resolve())],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
        timeout=60,
    )
    combined = proc.stdout + proc.stderr
    assert "No module named 'core'" not in combined, (
        f"{module_path.name} is not runnable as a script — it needs the "
        f"_PROJECT_ROOT sys.path insert (see core/run_sift.py). Output:\n{combined[-1500:]}"
    )


@pytest.mark.parametrize("module_path", ENTRY_POINTS, ids=lambda p: p.name)
def test_carries_the_project_root_guard(module_path):
    """The behavioural test above can pass by accident when a module's
    `core.*` imports are all deferred and no argument-free code path reaches
    them. Assert the guard is actually present as well."""
    src = module_path.read_text(encoding="utf-8")
    assert "_PROJECT_ROOT" in src and "sys.path.insert" in src, (
        f"{module_path.name} imports the core package and is script-invokable, "
        "but has no _PROJECT_ROOT sys.path insert."
    )
