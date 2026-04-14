#!/usr/bin/env python3
"""Launch the Epistract Workbench — domain-agnostic knowledge graph explorer.

Usage:
    python scripts/launch_workbench.py <output_dir> [--domain <name>] [--port 8000] [--host 127.0.0.1]

The output_dir should contain graph_data.json from a prior /epistract:ingest run.
Optionally pass --domain to load the domain-specific workbench template
(entity colors, persona prompt, starter questions). If omitted, the workbench
infers the domain from graph_data.json metadata.

Example:
    /epistract:ingest ./my-papers/ --output ./graph-output --domain drug-discovery
    python scripts/launch_workbench.py ./graph-output --domain drug-discovery

Then open http://127.0.0.1:8000 in your browser.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on sys.path so `examples.workbench` is importable
_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# ---------------------------------------------------------------------------
# Optional Rich
# ---------------------------------------------------------------------------
try:
    from rich.console import Console

    _console = Console(stderr=True)
    HAS_RICH = True
except ImportError:
    HAS_RICH = False


def main():
    """Parse args and start the workbench server."""
    if "--help" in sys.argv or "-h" in sys.argv or len(sys.argv) < 2:
        print((__doc__ or "").strip())
        sys.exit(0)

    output_dir = Path(sys.argv[1])
    if not output_dir.exists():
        print(f"Error: output directory not found: {output_dir}", file=sys.stderr)
        sys.exit(1)

    # Parse optional flags
    port = 8000
    host = "127.0.0.1"
    if "--port" in sys.argv:
        idx = sys.argv.index("--port")
        port = int(sys.argv[idx + 1])
    if "--host" in sys.argv:
        idx = sys.argv.index("--host")
        host = sys.argv[idx + 1]

    # Check for graph data
    graph_path = output_dir / "graph_data.json"
    if not graph_path.exists():
        print(
            f"Warning: No graph_data.json found in {output_dir}", file=sys.stderr
        )
        print(
            "Run extraction pipeline first: python scripts/extract_contracts.py <output_dir>",
            file=sys.stderr,
        )

    # Import and create app
    from examples.workbench.server import create_app

    app = create_app(output_dir)

    if HAS_RICH:
        _console.print("[bold green]Sample Contract Analysis Workbench[/]")
        _console.print(f"  Output dir: {output_dir}")
        _console.print(f"  Server: http://{host}:{port}")
        _console.print("  Press Ctrl+C to stop\n")
    else:
        print("Sample Contract Analysis Workbench")
        print(f"  Output dir: {output_dir}")
        print(f"  Server: http://{host}:{port}")
        print("  Press Ctrl+C to stop\n")

    import uvicorn

    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
