def test_home_requires_login(client):
    resp = client.get("/", follow_redirects=False)
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_login_success(client, seeded):
    resp = client.post(
        "/login", data={"email": "test@example.com", "password": "password123"}, follow_redirects=True
    )
    assert resp.status_code == 200
    assert b"Dashboard" in resp.data


def test_login_failure(client, seeded):
    resp = client.post("/login", data={"email": "test@example.com", "password": "wrong"})
    assert b"Incorrect" in resp.data


def test_logout(logged_in_client):
    resp = logged_in_client.post("/logout", follow_redirects=True)
    assert resp.status_code == 200
    assert b"Log in" in resp.data
