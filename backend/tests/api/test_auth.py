from __future__ import annotations

import uuid

from app.utils.jwt import create_access_token

URL = "/api/v1/auth"


def test_register_success(client):
    resp = client.post(f"{URL}/register", json={
        "email": "new@test.com",
        "password": "password123",
        "name": "New User",
    })
    assert resp.status_code == 201
    data = resp.get_json()["data"]
    assert data["user"]["email"] == "new@test.com"
    assert data["user"]["name"] == "New User"
    assert "access_token" in data
    assert "refresh_token" in data


def test_register_duplicate_email(client):
    client.post(f"{URL}/register", json={
        "email": "dup@test.com",
        "password": "password123",
        "name": "First",
    })
    resp = client.post(f"{URL}/register", json={
        "email": "dup@test.com",
        "password": "password123",
        "name": "Second",
    })
    assert resp.status_code == 409
    assert resp.get_json()["code"] == "CONFLICT"


def test_register_missing_fields(client):
    resp = client.post(f"{URL}/register", json={"email": "x@y.com"})
    assert resp.status_code == 422


def test_register_short_password(client):
    resp = client.post(f"{URL}/register", json={
        "email": "x@y.com",
        "password": "123",
        "name": "X",
    })
    assert resp.status_code == 422


def test_register_invalid_email(client):
    resp = client.post(f"{URL}/register", json={
        "email": "not-an-email",
        "password": "password123",
        "name": "X",
    })
    assert resp.status_code == 422


def test_login_success(client):
    client.post(f"{URL}/register", json={
        "email": "user@test.com",
        "password": "password123",
        "name": "User",
    })
    resp = client.post(f"{URL}/login", json={
        "email": "user@test.com",
        "password": "password123",
    })
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert "access_token" in data
    assert "refresh_token" in data


def test_login_wrong_password(client):
    client.post(f"{URL}/register", json={
        "email": "user@test.com",
        "password": "password123",
        "name": "User",
    })
    resp = client.post(f"{URL}/login", json={
        "email": "user@test.com",
        "password": "wrongpassword",
    })
    assert resp.status_code == 401
    assert resp.get_json()["code"] == "UNAUTHORIZED"


def test_login_nonexistent_user(client):
    resp = client.post(f"{URL}/login", json={
        "email": "nobody@test.com",
        "password": "password123",
    })
    assert resp.status_code == 401


def test_magic_link_existing_email(client):
    client.post(f"{URL}/register", json={
        "email": "user@test.com",
        "password": "password123",
        "name": "User",
    })
    resp = client.post(f"{URL}/magic-link", json={"email": "user@test.com"})
    assert resp.status_code == 200
    assert resp.get_json()["data"]["message"] == "Magic link sent"


def test_magic_link_nonexistent_email(client):
    resp = client.post(f"{URL}/magic-link", json={"email": "nobody@test.com"})
    assert resp.status_code == 200
    assert resp.get_json()["data"]["message"]


def test_magic_link_verify_success(client):
    reg = client.post(f"{URL}/register", json={
        "email": "user@test.com",
        "password": "password123",
        "name": "User",
    })
    user_id = reg.get_json()["data"]["user"]["id"]
    token = create_access_token(uuid.UUID(user_id), {"purpose": "magic_link"})

    resp = client.get(f"{URL}/magic-link/verify?token={token}")
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert "access_token" in data
    assert "refresh_token" in data


def test_magic_link_verify_invalid_token(client):
    resp = client.get(f"{URL}/magic-link/verify?token=garbage-token")
    assert resp.status_code == 401


def test_magic_link_verify_wrong_purpose(client):
    reg = client.post(f"{URL}/register", json={
        "email": "user@test.com",
        "password": "password123",
        "name": "User",
    })
    user_id = reg.get_json()["data"]["user"]["id"]
    token = create_access_token(uuid.UUID(user_id))

    resp = client.get(f"{URL}/magic-link/verify?token={token}")
    assert resp.status_code == 401


def test_magic_link_verify_missing_token(client):
    resp = client.get(f"{URL}/magic-link/verify")
    assert resp.status_code == 422


def test_refresh_success(client):
    reg = client.post(f"{URL}/register", json={
        "email": "user@test.com",
        "password": "password123",
        "name": "User",
    })
    refresh = reg.get_json()["data"]["refresh_token"]

    resp = client.post(f"{URL}/refresh", json={"refresh_token": refresh})
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert "access_token" in data
    assert "refresh_token" in data


def test_refresh_invalid_token(client):
    resp = client.post(f"{URL}/refresh", json={"refresh_token": "invalid-token"})
    assert resp.status_code == 401


def test_me_success(client):
    reg = client.post(f"{URL}/register", json={
        "email": "user@test.com",
        "password": "password123",
        "name": "Test User",
    })
    token = reg.get_json()["data"]["access_token"]

    resp = client.get(f"{URL}/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert data["email"] == "user@test.com"
    assert data["name"] == "Test User"


def test_me_no_auth(client):
    resp = client.get(f"{URL}/me")
    assert resp.status_code == 401


def test_me_expired_token(client):
    fake_token = client.application.extensions  # force app context
    expired = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwidHlwZSI6ImFjY2VzcyIsImV4cCI6MX0.dE_UZ7I1b8FDXCMJQOGa1e5mG7DBBy5kM_vCg6JRIQk"
    resp = client.get(f"{URL}/me", headers={"Authorization": f"Bearer {expired}"})
    assert resp.status_code == 401


def test_me_deleted_user(client, db):
    reg = client.post(f"{URL}/register", json={
        "email": "todelete@test.com",
        "password": "password123",
        "name": "To Delete",
    })
    token = reg.get_json()["data"]["access_token"]
    user_id = reg.get_json()["data"]["user"]["id"]

    from app.models.user import User
    user = db.session.get(User, uuid.UUID(user_id))
    db.session.delete(user)
    db.session.commit()

    resp = client.get(f"{URL}/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 404
    assert resp.get_json()["code"] == "NOT_FOUND"
