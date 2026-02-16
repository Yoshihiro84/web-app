def test_paper_list_empty(client):
    response = client.get("/papers")
    assert response.status_code == 200
    assert "No papers found" in response.text


def test_create_paper_and_view(client):
    response = client.post("/papers/new", data={
        "title": "Test Paper",
        "authors": "Author A",
        "year": "2024",
        "status": "unread",
        "tags_str": "ml, nlp",
    }, follow_redirects=False)
    assert response.status_code == 303

    response = client.get("/papers/1")
    assert response.status_code == 200
    assert "Test Paper" in response.text
    assert "Author A" in response.text
    assert "ml" in response.text
    assert "nlp" in response.text


def test_edit_paper(client):
    client.post("/papers/new", data={"title": "Original Title", "status": "unread"}, follow_redirects=False)

    response = client.get("/papers/1/edit")
    assert response.status_code == 200
    assert "Original Title" in response.text

    client.post("/papers/1/edit", data={
        "title": "Updated Title",
        "status": "reading",
        "tags_str": "",
    }, follow_redirects=False)

    response = client.get("/papers/1")
    assert "Updated Title" in response.text
    assert "reading" in response.text


def test_delete_paper(client):
    client.post("/papers/new", data={"title": "To Delete", "status": "unread"}, follow_redirects=False)
    response = client.post("/papers/1/delete", follow_redirects=False)
    assert response.status_code == 303

    response = client.get("/papers")
    assert "To Delete" not in response.text


def test_paper_search(client):
    client.post("/papers/new", data={"title": "Deep Learning", "status": "unread"}, follow_redirects=False)
    client.post("/papers/new", data={"title": "Quantum Computing", "status": "unread"}, follow_redirects=False)

    response = client.get("/papers?q=Deep")
    assert "Deep Learning" in response.text
    assert "Quantum Computing" not in response.text


def test_paper_status_filter(client):
    client.post("/papers/new", data={"title": "Unread Paper", "status": "unread"}, follow_redirects=False)
    client.post("/papers/new", data={"title": "Done Paper", "status": "done"}, follow_redirects=False)

    response = client.get("/papers?status=done")
    assert "Done Paper" in response.text
    assert "Unread Paper" not in response.text
