from app.models import Paper
from app.services.bibtex_service import parse_bibtex, generate_bibtex, find_duplicates


SAMPLE_BIBTEX = """
@article{smith2024deep,
  title={Deep Learning for NLP},
  author={Smith, John and Doe, Jane},
  journal={Journal of AI},
  year={2024},
  doi={10.1234/example},
}

@inproceedings{jones2023quantum,
  title={Quantum Machine Learning},
  author={Jones, Alice},
  booktitle={ICML 2023},
  year={2023},
  eprint={2301.12345},
  archiveprefix={arXiv},
}
"""


def test_parse_bibtex():
    entries = parse_bibtex(SAMPLE_BIBTEX)
    assert len(entries) == 2

    e1 = entries[0]
    assert e1["title"] == "Deep Learning for NLP"
    assert e1["authors"] == "Smith, John and Doe, Jane"
    assert e1["year"] == 2024
    assert e1["doi"] == "10.1234/example"
    assert e1["bibtex_key"] == "smith2024deep"
    assert e1["bibtex_type"] == "article"

    e2 = entries[1]
    assert e2["title"] == "Quantum Machine Learning"
    assert e2["arxiv_id"] == "2301.12345"
    assert e2["journal"] == "ICML 2023"


def test_parse_bibtex_empty():
    entries = parse_bibtex("")
    assert entries == []


def test_generate_bibtex(db):
    paper = Paper(
        title="Test Paper",
        authors="Author A",
        year=2024,
        doi="10.1234/test",
        journal="Test Journal",
        bibtex_key="author2024test",
        bibtex_type="article",
    )
    db.add(paper)
    db.commit()

    bib_str = generate_bibtex([paper])
    assert "author2024test" in bib_str
    assert "Test Paper" in bib_str
    assert "Author A" in bib_str
    assert "2024" in bib_str


def test_find_duplicates_by_doi():
    entries = [
        {"title": "Paper A", "doi": "10.1234/a", "arxiv_id": None},
        {"title": "Paper B", "doi": "10.1234/b", "arxiv_id": None},
    ]
    existing = [Paper(title="Existing", doi="10.1234/a")]

    new, dupes = find_duplicates(entries, existing)
    assert len(new) == 1
    assert len(dupes) == 1
    assert new[0]["title"] == "Paper B"


def test_find_duplicates_by_arxiv():
    entries = [
        {"title": "Paper A", "doi": None, "arxiv_id": "2301.12345"},
        {"title": "Paper B", "doi": None, "arxiv_id": "2301.99999"},
    ]
    existing = [Paper(title="Existing", arxiv_id="2301.12345")]

    new, dupes = find_duplicates(entries, existing)
    assert len(new) == 1
    assert len(dupes) == 1


def test_find_duplicates_no_match():
    entries = [{"title": "New Paper", "doi": "10.1234/new", "arxiv_id": None}]
    existing = [Paper(title="Different", doi="10.1234/different")]

    new, dupes = find_duplicates(entries, existing)
    assert len(new) == 1
    assert len(dupes) == 0
