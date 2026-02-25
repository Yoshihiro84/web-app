import json

from fastapi import APIRouter, Request, Depends, Form, Body
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session, joinedload
from typing import Optional

from app.database import get_db
from app.templating import templates
from app.services import paper_service, drive_service
from app.models import Paper, Tag, Collection

router = APIRouter(prefix="/papers", tags=["papers"])
api_router = APIRouter(prefix="/api/papers", tags=["papers-api"])


@api_router.get("/{paper_id}")
def paper_api_detail(paper_id: int, db: Session = Depends(get_db)):
    paper = paper_service.get_paper(db, paper_id)
    if not paper:
        return JSONResponse({"error": "Not found"}, status_code=404)
    return JSONResponse({
        "id": paper.id,
        "title": paper.title,
        "authors": paper.authors,
        "year": paper.year,
        "doi": paper.doi,
        "arxiv_id": paper.arxiv_id,
        "abstract": paper.abstract,
        "journal": paper.journal,
        "url": paper.url,
        "bibtex_key": paper.bibtex_key,
        "bibtex_type": paper.bibtex_type,
        "status": paper.status,
        "pdf_drive_file_id": paper.pdf_drive_file_id,
        "created_at": paper.created_at.isoformat() if paper.created_at else None,
        "updated_at": paper.updated_at.isoformat() if paper.updated_at else None,
        "tags": [{"id": t.id, "name": t.name} for t in paper.tags],
        "collections": [{"id": c.id, "name": c.name} for c in paper.collections],
        "notes": [{"id": n.id, "content": n.content} for n in paper.notes],
    })


@api_router.patch("/{paper_id}/status")
def paper_api_update_status(paper_id: int, status: str = Body(..., embed=True), db: Session = Depends(get_db)):
    if status not in ("unread", "reading", "done"):
        return JSONResponse({"error": "Invalid status"}, status_code=400)
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        return JSONResponse({"error": "Not found"}, status_code=404)
    paper.status = status
    db.commit()
    return JSONResponse({"id": paper.id, "status": paper.status})


@router.get("")
def paper_list(
    request: Request,
    q: str = "",
    status: str = "",
    tag_id: Optional[int] = None,
    collection_id: Optional[int] = None,
    page: int = 1,
    db: Session = Depends(get_db),
):
    papers, total_count, page, total_pages = paper_service.list_papers(
        db, q=q, status=status, tag_id=tag_id, collection_id=collection_id, page=page
    )
    extra_params = ""
    if q:
        extra_params += f"&q={q}"
    if status:
        extra_params += f"&status={status}"
    if tag_id:
        extra_params += f"&tag_id={tag_id}"
    if collection_id:
        extra_params += f"&collection_id={collection_id}"

    all_collections = db.query(Collection).options(joinedload(Collection.papers)).order_by(Collection.name).all()
    all_tags = db.query(Tag).order_by(Tag.name).all()

    return templates.TemplateResponse("papers/list.html", {
        "request": request,
        "papers": papers,
        "q": q,
        "status": status,
        "tag_id": tag_id,
        "collection_id": collection_id,
        "page": page,
        "total_pages": total_pages,
        "total_count": total_count,
        "base_url": "/papers",
        "extra_params": extra_params,
        "all_collections": all_collections,
        "all_tags": all_tags,
    })


@router.get("/new")
def paper_new(request: Request):
    return templates.TemplateResponse("papers/form.html", {
        "request": request,
        "paper": None,
        "editing": False,
    })


@router.post("/new")
def paper_create(
    request: Request,
    title: str = Form(...),
    authors: str = Form(""),
    year: Optional[int] = Form(None),
    doi: Optional[str] = Form(None),
    arxiv_id: Optional[str] = Form(None),
    abstract: str = Form(""),
    journal: str = Form(""),
    url: str = Form(""),
    bibtex_key: str = Form(""),
    bibtex_type: str = Form("article"),
    status: str = Form("unread"),
    tags_str: str = Form(""),
    db: Session = Depends(get_db),
):
    data = {
        "title": title, "authors": authors, "year": year,
        "doi": doi or None, "arxiv_id": arxiv_id or None,
        "abstract": abstract, "journal": journal, "url": url,
        "bibtex_key": bibtex_key, "bibtex_type": bibtex_type,
        "status": status, "tags_str": tags_str,
    }
    paper = paper_service.create_paper(db, data)
    return RedirectResponse(url=f"/papers/{paper.id}", status_code=303)


@router.get("/import-from-bookmarklet")
def import_from_bookmarklet_form(request: Request, metadata: str = ""):
    meta = {}
    if metadata:
        try:
            meta = json.loads(metadata)
        except json.JSONDecodeError:
            pass
    return templates.TemplateResponse("papers/import_bookmarklet.html", {
        "request": request,
        "meta": meta,
    })


@router.post("/import-from-bookmarklet")
def import_from_bookmarklet_post(
    request: Request,
    metadata: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
    authors: str = Form(""),
    year: Optional[int] = Form(None),
    doi: Optional[str] = Form(None),
    arxiv_id: Optional[str] = Form(None),
    abstract: str = Form(""),
    journal: str = Form(""),
    url: str = Form(""),
    tags_str: str = Form(""),
    db: Session = Depends(get_db),
):
    # If metadata JSON is provided (from bookmarklet), show the preview form
    if metadata and not title:
        meta = {}
        try:
            meta = json.loads(metadata)
        except json.JSONDecodeError:
            pass
        return templates.TemplateResponse("papers/import_bookmarklet.html", {
            "request": request,
            "meta": meta,
        })

    # Otherwise, save the paper (form submission)
    if not title:
        return RedirectResponse(url="/papers/import-from-bookmarklet", status_code=303)

    # Duplicate check
    if doi:
        existing = db.query(Paper).filter(Paper.doi == doi).first()
        if existing:
            return templates.TemplateResponse("papers/import_bookmarklet.html", {
                "request": request,
                "meta": {"title": title, "authors": authors, "year": year, "doi": doi,
                         "arxiv_id": arxiv_id, "abstract": abstract, "journal": journal, "url": url},
                "error": "Paper with this DOI already exists.",
                "existing_id": existing.id,
            })
    if arxiv_id:
        existing = db.query(Paper).filter(Paper.arxiv_id == arxiv_id).first()
        if existing:
            return templates.TemplateResponse("papers/import_bookmarklet.html", {
                "request": request,
                "meta": {"title": title, "authors": authors, "year": year, "doi": doi,
                         "arxiv_id": arxiv_id, "abstract": abstract, "journal": journal, "url": url},
                "error": "Paper with this arXiv ID already exists.",
                "existing_id": existing.id,
            })

    data = {
        "title": title, "authors": authors, "year": year,
        "doi": doi or None, "arxiv_id": arxiv_id or None,
        "abstract": abstract, "journal": journal, "url": url,
        "status": "unread", "tags_str": tags_str,
    }
    paper = paper_service.create_paper(db, data)

    return templates.TemplateResponse("papers/import_bookmarklet.html", {
        "request": request,
        "meta": {},
        "success": True,
        "paper_id": paper.id,
    })


@router.get("/{paper_id}")
def paper_detail(request: Request, paper_id: int, db: Session = Depends(get_db)):
    paper = paper_service.get_paper(db, paper_id)
    if not paper:
        return RedirectResponse(url="/papers", status_code=303)
    return templates.TemplateResponse("papers/detail.html", {
        "request": request,
        "paper": paper,
        "drive_configured": drive_service.is_configured(),
    })


@router.get("/{paper_id}/edit")
def paper_edit(request: Request, paper_id: int, db: Session = Depends(get_db)):
    paper = paper_service.get_paper(db, paper_id)
    if not paper:
        return RedirectResponse(url="/papers", status_code=303)
    return templates.TemplateResponse("papers/form.html", {
        "request": request,
        "paper": paper,
        "editing": True,
    })


@router.post("/{paper_id}/edit")
def paper_update(
    request: Request,
    paper_id: int,
    title: str = Form(...),
    authors: str = Form(""),
    year: Optional[int] = Form(None),
    doi: Optional[str] = Form(None),
    arxiv_id: Optional[str] = Form(None),
    abstract: str = Form(""),
    journal: str = Form(""),
    url: str = Form(""),
    bibtex_key: str = Form(""),
    bibtex_type: str = Form("article"),
    status: str = Form("unread"),
    tags_str: str = Form(""),
    db: Session = Depends(get_db),
):
    data = {
        "title": title, "authors": authors, "year": year,
        "doi": doi or None, "arxiv_id": arxiv_id or None,
        "abstract": abstract, "journal": journal, "url": url,
        "bibtex_key": bibtex_key, "bibtex_type": bibtex_type,
        "status": status, "tags_str": tags_str,
    }
    paper_service.update_paper(db, paper_id, data)
    return RedirectResponse(url=f"/papers/{paper_id}", status_code=303)


@router.post("/{paper_id}/delete")
def paper_delete(paper_id: int, db: Session = Depends(get_db)):
    paper_service.delete_paper(db, paper_id)
    return RedirectResponse(url="/papers", status_code=303)
