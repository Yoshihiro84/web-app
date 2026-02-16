from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.templating import templates
from app.models import Tag

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("")
def tag_list(request: Request, db: Session = Depends(get_db)):
    tags = db.query(Tag).order_by(Tag.name).all()
    return templates.TemplateResponse("tags/list.html", {
        "request": request,
        "tags": tags,
    })


@router.post("/create")
def tag_create(name: str = Form(...), db: Session = Depends(get_db)):
    name = name.strip()
    if name:
        existing = db.query(Tag).filter(Tag.name == name).first()
        if not existing:
            db.add(Tag(name=name))
            db.commit()
    return RedirectResponse(url="/tags", status_code=303)


@router.post("/{tag_id}/delete")
def tag_delete(tag_id: int, db: Session = Depends(get_db)):
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if tag:
        db.delete(tag)
        db.commit()
    return RedirectResponse(url="/tags", status_code=303)
