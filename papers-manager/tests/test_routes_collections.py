def test_collection_list_empty(client):
    response = client.get("/collections")
    assert response.status_code == 200
    assert "No collections yet" in response.text


def test_create_collection(client):
    response = client.post("/collections/new", data={
        "name": "My Collection",
        "description": "A test collection",
    }, follow_redirects=False)
    assert response.status_code == 303

    response = client.get("/collections")
    assert "My Collection" in response.text


def test_collection_detail(client):
    client.post("/collections/new", data={"name": "Test Col", "description": "Desc"}, follow_redirects=False)
    response = client.get("/collections/1")
    assert response.status_code == 200
    assert "Test Col" in response.text


def test_edit_collection(client):
    client.post("/collections/new", data={"name": "Old Name", "description": ""}, follow_redirects=False)
    client.post("/collections/1/edit", data={"name": "New Name", "description": "Updated"}, follow_redirects=False)
    response = client.get("/collections/1")
    assert "New Name" in response.text


def test_delete_collection(client):
    client.post("/collections/new", data={"name": "To Delete", "description": ""}, follow_redirects=False)
    response = client.post("/collections/1/delete", follow_redirects=False)
    assert response.status_code == 303
    response = client.get("/collections")
    assert "To Delete" not in response.text


def test_add_paper_to_collection(client, db):
    client.post("/papers/new", data={"title": "Paper for Col", "status": "unread"}, follow_redirects=False)
    client.post("/collections/new", data={"name": "Col", "description": ""}, follow_redirects=False)
    client.post("/collections/1/add-paper", data={"paper_id": "1"}, follow_redirects=False)
    response = client.get("/collections/1")
    assert "Paper for Col" in response.text
