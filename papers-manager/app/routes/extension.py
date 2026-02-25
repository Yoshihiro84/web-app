from fastapi import APIRouter, Depends, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
import json

from app.database import get_db
from app.models import Paper
from app.services import drive_service, paper_service

router = APIRouter(prefix="/api/extension", tags=["extension"])


@router.get("/status")
def extension_status():
    return JSONResponse({
        "status": "ok",
        "drive_configured": drive_service.is_configured(),
    })


@router.post("/import")
async def extension_import(
    metadata: str = Form(...),
    pdf_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    try:
        meta = json.loads(metadata)
    except json.JSONDecodeError:
        return JSONResponse({"error": "Invalid JSON in metadata"}, status_code=400)

    title = meta.get("title", "").strip()
    if not title:
        return JSONResponse({"error": "Title is required"}, status_code=400)

    # Duplicate check by DOI or arXiv ID
    doi = meta.get("doi", "").strip() or None
    arxiv_id = meta.get("arxiv_id", "").strip() or None

    if doi:
        existing = db.query(Paper).filter(Paper.doi == doi).first()
        if existing:
            return JSONResponse(
                {"error": "Paper with this DOI already exists", "paper_id": existing.id},
                status_code=409,
            )
    if arxiv_id:
        existing = db.query(Paper).filter(Paper.arxiv_id == arxiv_id).first()
        if existing:
            return JSONResponse(
                {"error": "Paper with this arXiv ID already exists", "paper_id": existing.id},
                status_code=409,
            )

    # Create paper
    data = {
        "title": title,
        "authors": meta.get("authors", ""),
        "year": meta.get("year"),
        "doi": doi,
        "arxiv_id": arxiv_id,
        "abstract": meta.get("abstract", ""),
        "journal": meta.get("journal", ""),
        "url": meta.get("url", ""),
        "bibtex_key": meta.get("bibtex_key", ""),
        "bibtex_type": meta.get("bibtex_type", "article"),
        "status": "unread",
        "tags_str": meta.get("tags_str", ""),
    }
    paper = paper_service.create_paper(db, data)

    # Upload PDF if provided
    pdf_drive_file_id = None
    if pdf_file and drive_service.is_configured():
        file_bytes = await pdf_file.read()
        if file_bytes:
            filename = f"paper_{paper.id}_{pdf_file.filename or 'paper.pdf'}"
            pdf_drive_file_id = drive_service.upload_pdf(file_bytes, filename)
            if pdf_drive_file_id:
                paper.pdf_drive_file_id = pdf_drive_file_id
                db.commit()

    return JSONResponse({
        "status": "created",
        "paper_id": paper.id,
        "pdf_drive_file_id": pdf_drive_file_id,
    }, status_code=201)
