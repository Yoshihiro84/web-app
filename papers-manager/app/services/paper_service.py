from typing import Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.models import Paper, Tag

PER_PAGE = 20


def get_or_create_tag(db: Session, name: str) -> Tag:
    name = name.strip()
    tag = db.query(Tag).filter(Tag.name == name).first()
    if not tag:
        tag = Tag(name=name)
        db.add(tag)
        db.flush()
    return tag


def sync_tags(db: Session, paper: Paper, tags_str: str):
    tag_names = [t.strip() for t in tags_str.split(",") if t.strip()]
    tags = [get_or_create_tag(db, name) for name in tag_names]
    paper.tags = tags


def create_paper(db: Session, data: dict) -> Paper:
    tags_str = data.pop("tags_str", "")
    paper = Paper(**data)
    db.add(paper)
    db.flush()
    if tags_str:
        sync_tags(db, paper, tags_str)
    db.commit()
    db.refresh(paper)
    return paper


def get_paper(db: Session, paper_id: int) -> Optional[Paper]:
    return (
        db.query(Paper)
        .options(joinedload(Paper.tags), joinedload(Paper.collections), joinedload(Paper.notes))
        .filter(Paper.id == paper_id)
        .first()
    )


def update_paper(db: Session, paper_id: int, data: dict) -> Optional[Paper]:
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        return None
    tags_str = data.pop("tags_str", "")
    for key, value in data.items():
        setattr(paper, key, value)
    sync_tags(db, paper, tags_str)
    db.commit()
    db.refresh(paper)
    return paper


def delete_paper(db: Session, paper_id: int) -> bool:
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        return False
    # Delete associated PDF from Google Drive
    if paper.pdf_drive_file_id:
        from app.services import drive_service
        drive_service.delete_pdf(paper.pdf_drive_file_id)
    db.delete(paper)
    db.commit()
    return True


def list_papers(
    db: Session,
    q: str = "",
    status: str = "",
    tag_id: Optional[int] = None,
    collection_id: Optional[int] = None,
    page: int = 1,
):
    query = db.query(Paper).options(joinedload(Paper.tags))

    if q:
        pattern = f"%{q}%"
        query = query.filter(
            or_(
                Paper.title.ilike(pattern),
                Paper.authors.ilike(pattern),
                Paper.abstract.ilike(pattern),
                Paper.journal.ilike(pattern),
            )
        )
    if status:
        query = query.filter(Paper.status == status)
    if tag_id:
        query = query.filter(Paper.tags.any(Tag.id == tag_id))
    if collection_id:
        from app.models import Collection
        query = query.filter(Paper.collections.any(Collection.id == collection_id))

    total_count = query.distinct().count()
    total_pages = max(1, (total_count + PER_PAGE - 1) // PER_PAGE)
    page = max(1, min(page, total_pages))

    papers = (
        query.distinct()
        .order_by(Paper.created_at.desc())
        .offset((page - 1) * PER_PAGE)
        .limit(PER_PAGE)
        .all()
    )

    # Deduplicate from joinedload
    seen = set()
    unique_papers = []
    for p in papers:
        if p.id not in seen:
            seen.add(p.id)
            unique_papers.append(p)

    return unique_papers, total_count, page, total_pages
