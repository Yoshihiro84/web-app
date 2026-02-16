from app.models import Paper, Tag
from app.services.paper_service import (
    create_paper, get_paper, update_paper, delete_paper, list_papers
)


def test_create_paper_basic(db):
    paper = create_paper(db, {"title": "My Paper", "authors": "Author A", "year": 2024, "tags_str": ""})
    assert paper.id is not None
    assert paper.title == "My Paper"


def test_create_paper_with_tags(db):
    paper = create_paper(db, {"title": "Tagged Paper", "tags_str": "ml, nlp, transformers"})
    assert len(paper.tags) == 3
    tag_names = {t.name for t in paper.tags}
    assert tag_names == {"ml", "nlp", "transformers"}


def test_create_paper_tags_reuse(db):
    paper1 = create_paper(db, {"title": "Paper 1", "tags_str": "ml"})
    paper2 = create_paper(db, {"title": "Paper 2", "tags_str": "ml"})
    assert paper1.tags[0].id == paper2.tags[0].id
    assert db.query(Tag).filter(Tag.name == "ml").count() == 1


def test_get_paper(db):
    paper = create_paper(db, {"title": "Findable Paper", "tags_str": ""})
    found = get_paper(db, paper.id)
    assert found is not None
    assert found.title == "Findable Paper"


def test_get_paper_not_found(db):
    assert get_paper(db, 9999) is None


def test_update_paper(db):
    paper = create_paper(db, {"title": "Old Title", "tags_str": ""})
    updated = update_paper(db, paper.id, {"title": "New Title", "status": "reading", "tags_str": "updated"})
    assert updated.title == "New Title"
    assert updated.status == "reading"
    assert len(updated.tags) == 1


def test_delete_paper(db):
    paper = create_paper(db, {"title": "To Delete", "tags_str": ""})
    assert delete_paper(db, paper.id) is True
    assert get_paper(db, paper.id) is None


def test_delete_paper_not_found(db):
    assert delete_paper(db, 9999) is False


def test_list_papers_empty(db):
    papers, total, page, total_pages = list_papers(db)
    assert papers == []
    assert total == 0


def test_list_papers_search(db):
    create_paper(db, {"title": "Deep Learning Survey", "authors": "Smith", "tags_str": ""})
    create_paper(db, {"title": "Quantum Computing", "authors": "Jones", "tags_str": ""})

    papers, total, _, _ = list_papers(db, q="Deep Learning")
    assert total == 1
    assert papers[0].title == "Deep Learning Survey"


def test_list_papers_status_filter(db):
    create_paper(db, {"title": "Paper A", "status": "unread", "tags_str": ""})
    create_paper(db, {"title": "Paper B", "status": "done", "tags_str": ""})

    papers, total, _, _ = list_papers(db, status="done")
    assert total == 1
    assert papers[0].title == "Paper B"


def test_list_papers_tag_filter(db):
    create_paper(db, {"title": "ML Paper", "tags_str": "ml"})
    create_paper(db, {"title": "Bio Paper", "tags_str": "biology"})

    ml_tag = db.query(Tag).filter(Tag.name == "ml").first()
    papers, total, _, _ = list_papers(db, tag_id=ml_tag.id)
    assert total == 1
    assert papers[0].title == "ML Paper"
