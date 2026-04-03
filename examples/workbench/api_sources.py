"""Source document API endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse


router = APIRouter(prefix="/api/sources", tags=["sources"])


@router.get("")
async def list_sources(request: Request):
    """Return list of available ingested documents."""
    data = request.app.state.data
    return {"documents": data.documents}


@router.get("/{doc_id}")
async def get_source(request: Request, doc_id: str):
    """Return ingested text content for a document."""
    data = request.app.state.data
    text = data.get_document_text(doc_id)
    if text is None:
        return {"error": f"Document not found: {doc_id}"}, 404
    return {"doc_id": doc_id, "text": text}


@router.get("/pdf/{doc_id}")
async def get_pdf(request: Request, doc_id: str):
    """Serve original PDF file if available."""
    data = request.app.state.data
    pdf_path = data.get_document_pdf_path(doc_id)
    if pdf_path and pdf_path.exists():
        return FileResponse(
            path=str(pdf_path),
            media_type="application/pdf",
            filename=pdf_path.name,
        )
    return {"error": f"PDF not found for: {doc_id}"}, 404
