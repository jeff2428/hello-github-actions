from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# A helper function to get a valid token for a test user
def get_user_token_headers(client: TestClient, email: str = "test@example.com", password: str = "password123") -> dict:
    # Create user
    client.post("/users/", json={"email": email, "password": password})

    # Login to get token
    login_response = client.post(
        "/token",
        data={"username": email, "password": password}
    )
    assert login_response.status_code == 200
    token_data = login_response.json()
    access_token = token_data["access_token"]
    return {"Authorization": f"Bearer {access_token}"}


def test_create_and_read_value(client: TestClient, db_session: Session):
    """
    Test creating a value and then reading it back.
    """
    headers = get_user_token_headers(client)

    # Create a value
    response = client.post(
        "/users/me/values/",
        json={"title": "Health", "description": "Prioritize physical and mental well-being."},
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Health"
    assert data["description"] == "Prioritize physical and mental well-being."
    assert "id" in data
    value_id = data["id"]

    # Read the values back
    response = client.get("/users/me/values/", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Health"
    assert data[0]["id"] == value_id


def test_update_value(client: TestClient, db_session: Session):
    """
    Test updating an existing value.
    """
    headers = get_user_token_headers(client)

    # Create a value first
    create_response = client.post("/users/me/values/", json={"title": "Career"}, headers=headers)
    assert create_response.status_code == 201
    value_id = create_response.json()["id"]

    # Update the value
    update_response = client.put(
        f"/users/me/values/{value_id}",
        json={"title": "Career Growth", "description": "Focus on professional development."},
        headers=headers,
    )
    assert update_response.status_code == 200
    data = update_response.json()
    assert data["title"] == "Career Growth"
    assert data["description"] == "Focus on professional development."

    # Verify the update
    get_response = client.get("/users/me/values/", headers=headers)
    assert get_response.json()[0]["title"] == "Career Growth"


def test_delete_value(client: TestClient, db_session: Session):
    """
    Test deleting an existing value.
    """
    headers = get_user_token_headers(client)

    # Create a value
    create_response = client.post("/users/me/values/", json={"title": "To Be Deleted"}, headers=headers)
    assert create_response.status_code == 201
    value_id = create_response.json()["id"]

    # Delete the value
    delete_response = client.delete(f"/users/me/values/{value_id}", headers=headers)
    assert delete_response.status_code == 200
    assert delete_response.json()["title"] == "To Be Deleted"

    # Verify it's gone
    get_response = client.get("/users/me/values/", headers=headers)
    assert get_response.status_code == 200
    assert len(get_response.json()) == 0


def test_value_authorization(client: TestClient, db_session: Session):
    """
    Test that a user cannot access or modify another user's values.
    """
    # User 1 creates a value
    user1_headers = get_user_token_headers(client, email="user1@example.com", password="password1")
    create_response = client.post("/users/me/values/", json={"title": "User1's Private Value"}, headers=user1_headers)
    assert create_response.status_code == 201
    value_id = create_response.json()["id"]

    # User 2 logs in
    user2_headers = get_user_token_headers(client, email="user2@example.com", password="password2")

    # User 2 tries to read User 1's values (should get an empty list)
    response = client.get("/users/me/values/", headers=user2_headers)
    assert response.status_code == 200
    assert len(response.json()) == 0

    # User 2 tries to update User 1's value
    update_response = client.put(
        f"/users/me/values/{value_id}",
        json={"title": "Hacked"},
        headers=user2_headers,
    )
    assert update_response.status_code == 403 # Forbidden
    assert update_response.json()["detail"] == "Not authorized to update this value"

    # User 2 tries to delete User 1's value
    delete_response = client.delete(f"/users/me/values/{value_id}", headers=user2_headers)
    assert delete_response.status_code == 403 # Forbidden
    assert delete_response.json()["detail"] == "Not authorized to delete this value"

    # Verify User 1's value is unchanged
    final_check_response = client.get("/users/me/values/", headers=user1_headers)
    assert final_check_response.status_code == 200
    assert len(final_check_response.json()) == 1
    assert final_check_response.json()[0]["title"] == "User1's Private Value"