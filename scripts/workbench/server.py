"""Sample Contract Analysis Workbench - FastAPI server."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from scripts.workbench.api_chat import router as chat_router
from scripts.workbench.api_graph import router as graph_router
from scripts.workbench.api_sources import router as sources_router
from scripts.workbench.data_loader import WorkbenchData

STATIC_DIR = Path(__file__).parent / "static"


def create_app(output_dir: Path) -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(title="Sample Contract Analysis Workbench")

    # CORS for local development (per D-07, localhost only)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Load data at startup
    app.state.data = WorkbenchData(output_dir)

    # Store output_dir for later use
    app.state.output_dir = output_dir

    # Include API routers
    app.include_router(graph_router)
    app.include_router(sources_router)
    app.include_router(chat_router)

    # Mount static files (create dir if needed for dev)
    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/")
    async def root():
        index = STATIC_DIR / "index.html"
        if index.exists():
            return FileResponse(str(index))
        return {
            "message": "Sample Contract Analysis Workbench",
            "status": "running",
            "static_dir": "not found - create scripts/workbench/static/index.html",
        }

    @app.get("/api/health")
    async def health():
        import os

        data = app.state.data
        return {
            "status": "ok",
            "output_dir": str(data.output_dir),
            "nodes": len(data.get_nodes()),
            "edges": len(data.get_edges()),
            "documents": len(data.documents),
            "has_claims": bool(data.claims_layer),
            "has_api_key": bool(os.environ.get("ANTHROPIC_API_KEY")),
        }

    return app
