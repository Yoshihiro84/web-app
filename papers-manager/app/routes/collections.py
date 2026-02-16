from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.templating import templates
from app.models import Collection, Paper
from app.services import paper_service

router = APIRouter(prefix="/collections", tags=["collections"])


@router.get("")
def collection_list(request: Request, db: Session = Depends(get_db)):
    collections = db.query(Collection).options(joinedload(Collection.papers)).order_by(Collection.name).all()
    return templates.TemplateResponse("collections/list.html", {
        "request": request,
        "collections": collections,
    })


@router.get("/new")
def collection_new(request: Request):
    return templates.TemplateResponse("collections/form.html", {
        "request": request,
        "collection": None,
        "editing": False,
    })


@router.post("/new")
def collection_create(name: str = Form(...), description: str = Form(""), db: Session = Depends(get_db)):
    name = name.strip()
    if name:
        existing = db.query(Collection).filter(Collection.name == name).first()
        if not existing:
            db.add(Collection(name=name, description=description))
            db.commit()
    return RedirectResponse(url="/collections", status_code=303)


@router.get("/{collection_id}")
def collection_detail(request: Request, collection_id: int, page: int = 1, db: Session = Depends(get_db)):
    collection = db.query(Collection).filter(Collection.id == collection_id).first()
    if not collection:
        return RedirectResponse(url="/collections", status_code=303)
    papers, total_count, page, total_pages = paper_service.list_papers(
        db, collection_id=collection_id, page=page
    )
    collection_paper_ids = {p.id for p in collection.papers}
    all_papers = db.query(Paper).order_by(Paper.title).all()
    available_papers = [p for p in all_papers if p.id not in collection_paper_ids]

    return templates.TemplateResponse("collections/detail.html", {
        "request": request,
        "collection": collection,
        "papers": papers,
        "available_papers": available_papers,
        "page": page,
        "total_pages": total_pages,
        "total_count": total_count,
        "base_url": f"/collections/{collection_id}",
        "extra_params": "",
    })


@router.get("/{collection_id}/edit")
def collection_edit(request: Request, collection_id: int, db: Session = Depends(get_db)):
    collection = db.query(Collection).filter(Collection.id == collection_id).first()
    if not collection:
        return RedirectResponse(url="/collections", status_code=303)
    return templates.TemplateResponse("collections/form.html", {
        "request": request,
        "collection": collection,
        "editing": True,
    })


@router.post("/{collection_id}/edit")
def collection_update(
    collection_id: int,
    name: str = Form(...),
    description: str = Form(""),
    db: Session = Depends(get_db),
):
    collection = db.query(Collection).filter(Collection.id == collection_id).first()
    if collection:
        collection.name = name.strip()
        collection.description = description
        db.commit()
    return RedirectResponse(url=f"/collections/{collection_id}", status_code=303)


@router.post("/{collection_id}/delete")
def collection_delete(collection_id: int, db: Session = Depends(get_db)):
    collection = db.query(Collection).filter(Collection.id == collection_id).first()
    if collection:
        db.delete(collection)
        db.commit()
    return RedirectResponse(url="/collections", status_code=303)


@router.post("/{collection_id}/add-paper")
def collection_add_paper(collection_id: int, paper_id: int = Form(...), db: Session = Depends(get_db)):
    collection = db.query(Collection).filter(Collection.id == collection_id).first()
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if collection and paper and paper not in collection.papers:
        collection.papers.append(paper)
        db.commit()
    return RedirectResponse(url=f"/collections/{collection_id}", status_code=303)


@router.post("/{collection_id}/remove-paper/{paper_id}")
def collection_remove_paper(collection_id: int, paper_id: int, db: Session = Depends(get_db)):
    collection = db.query(Collection).filter(Collection.id == collection_id).first()
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if collection and paper and paper in collection.papers:
        collection.papers.remove(paper)
        db.commit()
    return RedirectResponse(url=f"/collections/{collection_id}", status_code=303)
