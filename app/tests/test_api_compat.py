def test_users_endpoints_compat(client):
    create_response = client.post(
        "/users",
        json={"username": "test_user", "email": "test_user@example.com"},
    )
    assert create_response.status_code == 201

    list_response = client.get("/users")
    assert list_response.status_code == 200
    users = list_response.get_json()
    assert isinstance(users, list)
    assert len(users) >= 1

    pagination_response = client.get("/users?page=1&per_page=1")
    assert pagination_response.status_code == 200
    assert len(pagination_response.get_json()) == 1

    user_id = create_response.get_json()["id"]
    by_id_response = client.get(f"/users/{user_id}")
    assert by_id_response.status_code == 200
    assert by_id_response.get_json()["id"] == user_id

    update_response = client.put(
        f"/users/{user_id}",
        json={"username": "updated_username"},
    )
    assert update_response.status_code == 200
    assert update_response.get_json()["username"] == "updated_username"

    bulk_response = client.post("/users/bulk", json={"file": "users.csv", "row_count": 20})
    assert bulk_response.status_code in (200, 201)


def test_urls_endpoints_compat(client, sample_user):
    create_response = client.post(
        "/urls",
        json={
            "original_url": "https://example.com/test-path",
            "title": "Test Create URL",
            "user_id": sample_user.id,
        },
    )
    assert create_response.status_code == 201
    create_payload = create_response.get_json()
    assert "short_code" in create_payload

    url_id = create_payload["id"]
    by_id_response = client.get(f"/urls/{url_id}")
    assert by_id_response.status_code == 200
    assert by_id_response.get_json()["id"] == url_id

    update_response = client.put(
        f"/urls/{url_id}",
        json={"title": "Updated Title"},
    )
    assert update_response.status_code == 200

    deactivate_response = client.put(
        f"/urls/{url_id}",
        json={"is_active": False},
    )
    assert deactivate_response.status_code == 200

    list_response = client.get("/urls")
    assert list_response.status_code == 200
    assert isinstance(list_response.get_json(), list)

    active_response = client.get("/urls?is_active=true")
    assert active_response.status_code == 200
    assert isinstance(active_response.get_json(), list)


def test_events_endpoints_compat(client, sample_url):
    create_response = client.post(
        "/events",
        json={
            "url_id": sample_url.id,
            "user_id": sample_url.user_id,
            "event_type": "click",
            "details": {"referrer": "https://google.com"},
        },
    )
    assert create_response.status_code == 201
    assert create_response.get_json()["event_type"] == "click"

    list_response = client.get("/events")
    assert list_response.status_code == 200
    assert isinstance(list_response.get_json(), list)

    by_url_response = client.get(f"/events?url_id={sample_url.id}")
    assert by_url_response.status_code == 200

    by_user_response = client.get(f"/events?user_id={sample_url.user_id}")
    assert by_user_response.status_code == 200

    by_type_response = client.get("/events?event_type=click")
    assert by_type_response.status_code == 200


def test_create_user_api(client):
    response = client.post(
        "/users",
        json={"username": "integration_user", "email": "integration_user@example.com"},
    )
    assert response.status_code == 201


def test_create_url_api(client, sample_user):
    response = client.post(
        "/urls",
        json={
            "original_url": "https://example.com/integration",
            "title": "Integration URL",
            "user_id": sample_user.id,
        },
    )
    assert response.status_code == 201


def test_create_event_api(client, sample_url):
    response = client.post(
        "/events",
        json={
            "url_id": sample_url.id,
            "user_id": sample_url.user_id,
            "event_type": "click",
            "details": {"source": "integration"},
        },
    )
    assert response.status_code == 201
