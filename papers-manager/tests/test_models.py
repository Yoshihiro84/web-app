from app.models import Paper, Tag, Collection, Note


def test_create_paper(db):
    paper = Paper(title="Test Paper", authors="Author A", year=2024, status="unread")
    db.add(paper)
    db.commit()
    db.refresh(paper)
    assert paper.id is not None
    assert paper.title == "Test Paper"
    assert paper.status == "unread"


def test_paper_tag_relationship(db):
    paper = Paper(title="Tagged Paper")
    tag = Tag(name="ml")
    paper.tags.append(tag)
    db.add(paper)
    db.commit()
    db.refresh(paper)
    assert len(paper.tags) == 1
    assert paper.tags[0].name == "ml"
    assert len(tag.papers) == 1


def test_paper_collection_relationship(db):
    paper = Paper(title="Collected Paper")
    col = Collection(name="My Collection")
    paper.collections.append(col)
    db.add(paper)
    db.commit()
    db.refresh(paper)
    assert len(paper.collections) == 1
    assert paper.collections[0].name == "My Collection"


def test_paper_note_relationship(db):
    paper = Paper(title="Paper with Note")
    db.add(paper)
    db.commit()
    note = Note(paper_id=paper.id, content="Some notes here")
    db.add(note)
    db.commit()
    db.refresh(paper)
    assert len(paper.notes) == 1
    assert paper.notes[0].content == "Some notes here"


def test_cascade_delete_paper_notes(db):
    paper = Paper(title="Paper to Delete")
    db.add(paper)
    db.commit()
    note = Note(paper_id=paper.id, content="Note to cascade")
    db.add(note)
    db.commit()
    db.delete(paper)
    db.commit()
    assert db.query(Note).count() == 0
