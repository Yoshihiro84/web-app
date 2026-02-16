from fastapi import APIRouter, Request, Depends, Form, UploadFile, File
from fastapi.responses import RedirectResponse, Response
from sqlalchemy.orm import Session
from typing import Optional, List

from app.database import get_db
from app.templating import templates
from app.models import Paper
from app.services.bibtex_service import parse_bibtex, generate_bibtex, find_duplicates

router = APIRouter(prefix="/bibtex", tags=["bibtex"])


@router.get("/import")
def import_page(request: Request):
    return templates.TemplateResponse("bibtex/import.html", {
        "request": request,
        "entries": None,
        "duplicates": None,
        "bibtex_text": "",
    })


@router.post("/import/preview")
async def import_preview(
    request: Request,
    bibtex_text: str = Form(""),
    bibtex_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    text = bibtex_text
    if bibtex_file and bibtex_file.filename:
        content = await bibtex_file.read()
        text = content.decode("utf-8", errors="replace")

    if not text.strip():
        return templates.TemplateResponse("bibtex/import.html", {
            "request": request,
            "entries": None,
            "duplicates": None,
            "bibtex_text": "",
            "flash_message": "Please paste BibTeX text or upload a file.",
            "flash_type": "error",
        })

    entries = parse_bibtex(text)
    existing = db.query(Paper).all()
    new_entries, duplicates = find_duplicates(entries, existing)

    return templates.TemplateResponse("bibtex/import.html", {
        "request": request,
        "entries": new_entries,
        "duplicates": duplicates,
        "bibtex_text": text,
    })


@router.post("/import/confirm")
def import_confirm(
    request: Request,
    bibtex_text: str = Form(""),
    selected: List[int] = Form([]),
    db: Session = Depends(get_db),
):
    entries = parse_bibtex(bibtex_text)
    existing = db.query(Paper).all()
    new_entries, _ = find_duplicates(entries, existing)

    imported = 0
    for i, entry in enumerate(new_entries):
        if i in selected or not selected:
            paper = Paper(
                title=entry["title"],
                authors=entry.get("authors", ""),
                year=entry.get("year"),
                doi=entry.get("doi"),
                arxiv_id=entry.get("arxiv_id"),
                abstract=entry.get("abstract", ""),
                journal=entry.get("journal", ""),
                url=entry.get("url", ""),
                bibtex_key=entry.get("bibtex_key", ""),
                bibtex_type=entry.get("bibtex_type", "article"),
            )
            db.add(paper)
            imported += 1

    db.commit()

    return templates.TemplateResponse("bibtex/import.html", {
        "request": request,
        "entries": None,
        "duplicates": None,
        "bibtex_text": "",
        "flash_message": f"Successfully imported {imported} paper(s).",
        "flash_type": "success",
    })


@router.get("/export")
def export_page(request: Request, db: Session = Depends(get_db)):
    papers = db.query(Paper).order_by(Paper.created_at.desc()).all()
    return templates.TemplateResponse("bibtex/export.html", {
        "request": request,
        "papers": papers,
    })


@router.post("/export/download")
def export_download(
    paper_ids: List[int] = Form([]),
    db: Session = Depends(get_db),
):
    if paper_ids:
        papers = db.query(Paper).filter(Paper.id.in_(paper_ids)).all()
    else:
        papers = db.query(Paper).all()

    bibtex_str = generate_bibtex(papers)
    return Response(
        content=bibtex_str,
        media_type="application/x-bibtex",
        headers={"Content-Disposition": "attachment; filename=papers.bib"},
    )
