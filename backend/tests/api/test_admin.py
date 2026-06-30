from __future__ import annotations

import uuid

from app.models.organization import Organization
from app.models.user import User, UserRole

ORG_URL = "/api/v1/admin/orgs"
USER_URL = "/api/v1/admin/users"


def _admin_headers(admin_token: str) -> dict:
    return {"Authorization": f"Bearer {admin_token}"}


# --- Organization CRUD ---


def test_list_orgs_empty(client, super_admin_token):
    resp = client.get(ORG_URL, headers=_admin_headers(super_admin_token))
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["data"] == []
    assert data["total"] == 0


def test_list_orgs_with_data(client, admin_token, db, org):
    resp = client.get(ORG_URL, headers=_admin_headers(admin_token))
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data["data"]) == 1
    assert data["data"][0]["name"] == "Test Organization"
    assert data["total"] == 1


def test_list_orgs_pagination(client, super_admin_token, db):
    for i in range(5):
        o = Organization(id=uuid.uuid4(), name=f"Org {i}", slug=f"org-{i}")
        db.session.add(o)
    db.session.commit()

    resp = client.get(f"{ORG_URL}?page=1&per_page=2", headers=_admin_headers(super_admin_token))
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data["data"]) == 2
    assert data["total"] == 5
    assert data["page"] == 1
    assert data["per_page"] == 2


def test_create_org(client, admin_token):
    resp = client.post(ORG_URL, json={
        "name": "New Org",
        "slug": "new-org",
    }, headers=_admin_headers(admin_token))
    assert resp.status_code == 201
    data = resp.get_json()["data"]
    assert data["name"] == "New Org"
    assert data["slug"] == "new-org"


def test_create_org_duplicate_slug(client, admin_token, db, org):
    resp = client.post(ORG_URL, json={
        "name": "Duplicate",
        "slug": "test-org",
    }, headers=_admin_headers(admin_token))
    assert resp.status_code == 409


def test_get_org(client, admin_token, db, org):
    resp = client.get(f"{ORG_URL}/{org.id}", headers=_admin_headers(admin_token))
    assert resp.status_code == 200
    assert resp.get_json()["data"]["name"] == "Test Organization"


def test_get_org_not_found(client, admin_token):
    resp = client.get(f"{ORG_URL}/{uuid.uuid4()}", headers=_admin_headers(admin_token))
    assert resp.status_code == 404


def test_update_org(client, admin_token, db, org):
    resp = client.put(f"{ORG_URL}/{org.id}", json={
        "name": "Updated Org",
    }, headers=_admin_headers(admin_token))
    assert resp.status_code == 200
    assert resp.get_json()["data"]["name"] == "Updated Org"


def test_update_org_duplicate_slug(client, admin_token, db, org):
    other = Organization(id=uuid.uuid4(), name="Other", slug="other-org")
    db.session.add(other)
    db.session.commit()

    resp = client.put(f"{ORG_URL}/{org.id}", json={
        "slug": "other-org",
    }, headers=_admin_headers(admin_token))
    assert resp.status_code == 409


def test_delete_org(client, admin_token, db, org):
    resp = client.delete(f"{ORG_URL}/{org.id}", headers=_admin_headers(admin_token))
    assert resp.status_code == 204

    resp = client.get(f"{ORG_URL}/{org.id}", headers=_admin_headers(admin_token))
    assert resp.status_code == 404


def test_delete_org_not_found(client, admin_token):
    resp = client.delete(f"{ORG_URL}/{uuid.uuid4()}", headers=_admin_headers(admin_token))
    assert resp.status_code == 404


# --- User CRUD ---


def test_list_users_empty(client, super_admin_token):
    resp = client.get(USER_URL, headers=_admin_headers(super_admin_token))
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data["data"]) == 1  # super_admin_user exists
    assert data["total"] == 1


def test_list_users_pagination(client, admin_token, db):
    resp = client.get(f"{USER_URL}?page=1&per_page=1", headers=_admin_headers(admin_token))
    assert resp.status_code == 200
    assert len(resp.get_json()["data"]) == 1


def test_create_user(client, admin_token, db, org):
    resp = client.post(USER_URL, json={
        "email": "newuser@test.com",
        "password": "password123",
        "name": "New User",
        "role": "operator",
        "organization_id": str(org.id),
    }, headers=_admin_headers(admin_token))
    assert resp.status_code == 201
    data = resp.get_json()["data"]
    assert data["email"] == "newuser@test.com"
    assert data["name"] == "New User"
    assert data["role"] == "operator"
    assert data["organization_id"] == str(org.id)


def test_create_user_no_org(client, admin_token):
    resp = client.post(USER_URL, json={
        "email": "noorg@test.com",
        "password": "password123",
        "name": "No Org",
        "role": "checkin_staff",
    }, headers=_admin_headers(admin_token))
    assert resp.status_code == 201
    assert resp.get_json()["data"]["organization_id"] is None


def test_create_user_duplicate_email(client, admin_token):
    resp = client.post(USER_URL, json={
        "email": "dup@test.com",
        "password": "password123",
        "name": "First",
    }, headers=_admin_headers(admin_token))
    assert resp.status_code == 201

    resp = client.post(USER_URL, json={
        "email": "dup@test.com",
        "password": "password123",
        "name": "Second",
    }, headers=_admin_headers(admin_token))
    assert resp.status_code == 409


def test_create_user_invalid_org(client, admin_token):
    resp = client.post(USER_URL, json={
        "email": "badorg@test.com",
        "password": "password123",
        "name": "Bad Org",
        "organization_id": str(uuid.uuid4()),
    }, headers=_admin_headers(admin_token))
    assert resp.status_code == 422


def test_get_user(client, admin_token, db, admin_user):
    resp = client.get(f"{USER_URL}/{admin_user.id}", headers=_admin_headers(admin_token))
    assert resp.status_code == 200
    assert resp.get_json()["data"]["email"] == "admin@test.com"


def test_get_user_not_found(client, admin_token):
    resp = client.get(f"{USER_URL}/{uuid.uuid4()}", headers=_admin_headers(admin_token))
    assert resp.status_code == 404


def test_update_user(client, admin_token, db, operator_user):
    resp = client.put(f"{USER_URL}/{operator_user.id}", json={
        "name": "Updated Name",
        "role": "admin",
    }, headers=_admin_headers(admin_token))
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert data["name"] == "Updated Name"
    assert data["role"] == "admin"


def test_update_user_email(client, admin_token, db, operator_user):
    resp = client.put(f"{USER_URL}/{operator_user.id}", json={
        "email": "newemail@test.com",
    }, headers=_admin_headers(admin_token))
    assert resp.status_code == 200
    assert resp.get_json()["data"]["email"] == "newemail@test.com"


def test_update_user_duplicate_email(client, admin_token, db, admin_user, operator_user):
    resp = client.put(f"{USER_URL}/{operator_user.id}", json={
        "email": "admin@test.com",
    }, headers=_admin_headers(admin_token))
    assert resp.status_code == 409


def test_update_user_remove_org(client, admin_token, db, operator_user):
    resp = client.put(f"{USER_URL}/{operator_user.id}", json={
        "organization_id": None,
    }, headers=_admin_headers(admin_token))
    assert resp.status_code == 200
    assert resp.get_json()["data"]["organization_id"] is None


def test_delete_user(client, admin_token, db, checkin_user):
    resp = client.delete(f"{USER_URL}/{checkin_user.id}", headers=_admin_headers(admin_token))
    assert resp.status_code == 204


def test_delete_user_not_found(client, admin_token):
    resp = client.delete(f"{USER_URL}/{uuid.uuid4()}", headers=_admin_headers(admin_token))
    assert resp.status_code == 404


def test_delete_last_admin_blocked(client, admin_token, db):
    # Only the admin_token user exists with role=admin
    resp = client.get(USER_URL, headers=_admin_headers(admin_token))
    admins = [u for u in resp.get_json()["data"] if u["role"] == "admin"]
    assert len(admins) == 1

    resp = client.delete(f"{USER_URL}/{admins[0]['id']}", headers=_admin_headers(admin_token))
    assert resp.status_code == 422


# --- Role enforcement ---


def test_operator_cannot_list_orgs(client, operator_token):
    resp = client.get(ORG_URL, headers=_auth_header(operator_token))
    assert resp.status_code == 403


def test_checkin_staff_cannot_list_orgs(client, checkin_token):
    resp = client.get(ORG_URL, headers=_auth_header(checkin_token))
    assert resp.status_code == 403


def test_no_auth_returns_unauthorized(client):
    resp = client.get(ORG_URL)
    assert resp.status_code == 401


def test_operator_cannot_list_users(client, operator_token):
    resp = client.get(USER_URL, headers=_auth_header(operator_token))
    assert resp.status_code == 403


def test_no_org_user_cannot_access_admin(client, no_org_token):
    resp = client.get(ORG_URL, headers=_auth_header(no_org_token))
    assert resp.status_code == 403


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
