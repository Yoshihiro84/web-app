from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, Table
)
from sqlalchemy.orm import relationship

from app.database import Base

paper_tags = Table(
    "paper_tags",
    Base.metadata,
    Column("paper_id", Integer, ForeignKey("papers.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)

paper_collections = Table(
    "paper_collections",
    Base.metadata,
    Column("paper_id", Integer, ForeignKey("papers.id", ondelete="CASCADE"), primary_key=True),
    Column("collection_id", Integer, ForeignKey("collections.id", ondelete="CASCADE"), primary_key=True),
)


class Paper(Base):
    __tablename__ = "papers"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    authors = Column(String(1000), default="")
    year = Column(Integer, nullable=True)
    doi = Column(String(200), nullable=True)
    arxiv_id = Column(String(100), nullable=True)
    abstract = Column(Text, default="")
    journal = Column(String(300), default="")
    url = Column(String(500), default="")
    bibtex_key = Column(String(200), default="")
    bibtex_type = Column(String(50), default="article")
    status = Column(String(20), default="unread")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tags = relationship("Tag", secondary=paper_tags, back_populates="papers")
    collections = relationship("Collection", secondary=paper_collections, back_populates="papers")
    notes = relationship("Note", back_populates="paper", cascade="all, delete-orphan")


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)

    papers = relationship("Paper", secondary=paper_tags, back_populates="tags")


class Collection(Base):
    __tablename__ = "collections"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), unique=True, nullable=False)
    description = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    papers = relationship("Paper", secondary=paper_collections, back_populates="collections")


class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey("papers.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    paper = relationship("Paper", back_populates="notes")
