from __future__ import annotations

URL = "/api/v1/events"


def test_list_events_empty(client):
    resp = client.get(URL)
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["data"] == []
    assert body["total"] == 0
    assert body["page"] == 1
    assert body["per_page"] == 20


def test_list_events_with_published(client, published_event):
    resp = client.get(URL)
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["total"] == 1
    assert body["data"][0]["slug"] == "python-conf-2026"


def test_list_events_hides_drafts(client, published_event, draft_event):
    resp = client.get(URL)
    assert resp.status_code == 200
    slugs = [e["slug"] for e in resp.get_json()["data"]]
    assert "python-conf-2026" in slugs
    assert "draft-event" not in slugs


def test_list_events_multiple(client, published_event):
    from datetime import datetime, timezone
    from app.extensions import db
    from app.models.event import Event, EventStatus, SeatingType
    import uuid

    e2 = Event(
        id=uuid.uuid4(),
        organization_id=published_event.organization_id,
        title="Workshop",
        date=datetime(2026, 10, 1, 14, 0, tzinfo=timezone.utc),
        capacity=50,
        status=EventStatus.PUBLISHED,
        seating_type=SeatingType.GENERAL,
        slug="workshop",
    )
    db.session.add(e2)
    db.session.commit()

    resp = client.get(URL)
    assert resp.get_json()["total"] == 2


def test_list_events_pagination(client):
    resp = client.get(f"{URL}?page=1&per_page=5")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["page"] == 1
    assert body["per_page"] == 5


def test_event_detail_found(client, published_event):
    resp = client.get(f"{URL}/{published_event.slug}")
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert data["title"] == "Python Conference"
    assert data["slug"] == "python-conf-2026"
    assert "ticket_types" in data


def test_event_detail_not_found(client):
    resp = client.get(f"{URL}/nonexistent-slug")
    assert resp.status_code == 404


def test_event_detail_draft_hidden(client, draft_event):
    resp = client.get(f"{URL}/{draft_event.slug}")
    assert resp.status_code == 404
