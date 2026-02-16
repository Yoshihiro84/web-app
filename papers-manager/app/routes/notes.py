from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.templating import templates
from app.models import Note, Paper

router = APIRouter(tags=["notes"])


@router.post("/papers/{paper_id}/notes")
def note_create(paper_id: int, content: str = Form(...), db: Session = Depends(get_db)):
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        return RedirectResponse(url="/papers", status_code=303)
    note = Note(paper_id=paper_id, content=content)
    db.add(note)
    db.commit()
    return RedirectResponse(url=f"/papers/{paper_id}", status_code=303)


@router.get("/papers/{paper_id}/notes/{note_id}/edit")
def note_edit(request: Request, paper_id: int, note_id: int, db: Session = Depends(get_db)):
    note = db.query(Note).filter(Note.id == note_id, Note.paper_id == paper_id).first()
    if not note:
        return RedirectResponse(url=f"/papers/{paper_id}", status_code=303)
    return templates.TemplateResponse("notes/edit.html", {
        "request": request,
        "note": note,
        "paper_id": paper_id,
    })


@router.post("/papers/{paper_id}/notes/{note_id}/edit")
def note_update(paper_id: int, note_id: int, content: str = Form(...), db: Session = Depends(get_db)):
    note = db.query(Note).filter(Note.id == note_id, Note.paper_id == paper_id).first()
    if note:
        note.content = content
        db.commit()
    return RedirectResponse(url=f"/papers/{paper_id}", status_code=303)


@router.post("/papers/{paper_id}/notes/{note_id}/delete")
def note_delete(paper_id: int, note_id: int, db: Session = Depends(get_db)):
    note = db.query(Note).filter(Note.id == note_id, Note.paper_id == paper_id).first()
    if note:
        db.delete(note)
        db.commit()
    return RedirectResponse(url=f"/papers/{paper_id}", status_code=303)
