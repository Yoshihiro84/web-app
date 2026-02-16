SAMPLE_BIBTEX = """@article{test2024,
  title={Test Article},
  author={Test Author},
  journal={Test Journal},
  year={2024},
  doi={10.1234/test},
}"""


def test_import_page(client):
    response = client.get("/bibtex/import")
    assert response.status_code == 200
    assert "Import BibTeX" in response.text


def test_import_preview(client):
    response = client.post("/bibtex/import/preview", data={
        "bibtex_text": SAMPLE_BIBTEX,
    })
    assert response.status_code == 200
    assert "Test Article" in response.text
    assert "Test Author" in response.text


def test_import_confirm(client):
    response = client.post("/bibtex/import/confirm", data={
        "bibtex_text": SAMPLE_BIBTEX,
        "selected": ["0"],
    })
    assert response.status_code == 200
    assert "Successfully imported 1 paper" in response.text

    response = client.get("/papers")
    assert "Test Article" in response.text


def test_import_duplicate_detection(client):
    # Import once
    client.post("/bibtex/import/confirm", data={
        "bibtex_text": SAMPLE_BIBTEX,
    })

    # Preview again should detect duplicate
    response = client.post("/bibtex/import/preview", data={
        "bibtex_text": SAMPLE_BIBTEX,
    })
    assert "duplicate" in response.text.lower() or "No new entries" in response.text


def test_export_page(client):
    response = client.get("/bibtex/export")
    assert response.status_code == 200
    assert "Export BibTeX" in response.text


def test_export_download(client):
    client.post("/papers/new", data={
        "title": "Export Paper",
        "authors": "Author",
        "year": "2024",
        "bibtex_key": "export2024",
        "bibtex_type": "article",
        "status": "unread",
    }, follow_redirects=False)

    response = client.post("/bibtex/export/download", data={"paper_ids": ["1"]})
    assert response.status_code == 200
    assert "export2024" in response.text
    assert "Export Paper" in response.text
