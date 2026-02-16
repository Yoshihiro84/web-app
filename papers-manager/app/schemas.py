from pydantic import BaseModel, Field
from typing import Optional


class PaperCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    authors: str = ""
    year: Optional[int] = None
    doi: Optional[str] = None
    arxiv_id: Optional[str] = None
    abstract: str = ""
    journal: str = ""
    url: str = ""
    bibtex_key: str = ""
    bibtex_type: str = "article"
    status: str = "unread"
    tags_str: str = ""


class PaperUpdate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    authors: str = ""
    year: Optional[int] = None
    doi: Optional[str] = None
    arxiv_id: Optional[str] = None
    abstract: str = ""
    journal: str = ""
    url: str = ""
    bibtex_key: str = ""
    bibtex_type: str = "article"
    status: str = "unread"
    tags_str: str = ""


class CollectionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str = ""


class CollectionUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str = ""


class NoteCreate(BaseModel):
    content: str = Field(..., min_length=1)


class NoteUpdate(BaseModel):
    content: str = Field(..., min_length=1)
