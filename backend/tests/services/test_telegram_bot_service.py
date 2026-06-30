from __future__ import annotations

import json
import uuid

import pytest

from app.models.attendee import Attendee
from app.models.event import Event, EventStatus, SeatingType, TicketType
from app.models.order import Order, OrderStatus
from app.models.organization import Organization
from app.models.ticket import Ticket
from app.services.telegram_bot_service import (
    get_attendee_tickets,
    get_bot_token_orgs,
    get_org_by_bot_token,
    get_org_events,
    link_attendee,
)


def test_link_attendee_success(db, created_order):
    _, attendee, ticket = created_order
    result = link_attendee(attendee.link_code, 12345)
    assert result is not None
    assert result.telegram_chat_id == 12345
    assert result.telegram_linked is True
    assert result.id == attendee.id


def test_link_attendee_wrong_code(db):
    result = link_attendee("nonexistent-code", 12345)
    assert result is None


def test_get_attendee_tickets_empty(db):
    assert get_attendee_tickets(99999) == []


def test_get_attendee_tickets_found(db, created_order):
    _, attendee, _ = created_order
    link_attendee(attendee.link_code, 12345)
    tickets = get_attendee_tickets(12345)
    assert len(tickets) >= 1
    assert tickets[0]["attendee_name"] == attendee.name


def test_get_org_events(db, org, published_event):
    events = get_org_events(org.id)
    assert len(events) == 1
    assert events[0]["title"] == "Python Conference"


def test_get_org_events_excludes_drafts(db, org, published_event, draft_event):
    events = get_org_events(org.id)
    assert len(events) == 1
    assert events[0]["slug"] == "python-conf-2026"


def test_get_org_events_empty(db, org):
    events = get_org_events(org.id)
    assert events == []


def test_get_org_by_bot_token_found(db, org):
    org.telegram_bot_token = "123:abc"
    db.session.commit()

    result = get_org_by_bot_token("123:abc")
    assert result is not None
    assert result.id == org.id


def test_get_org_by_bot_token_not_found(db):
    result = get_org_by_bot_token("nonexistent")
    assert result is None


def test_get_bot_token_orgs(db, org):
    org2 = Organization(id=uuid.uuid4(), name="Other", slug="other")
    db.session.add(org2)
    db.session.commit()

    org.telegram_bot_token = "123:abc"
    db.session.commit()

    orgs = get_bot_token_orgs()
    assert len(orgs) == 1
    assert orgs[0].id == org.id


def test_get_bot_token_orgs_empty(db):
    assert get_bot_token_orgs() == []


# --- Webhook endpoint ---


def test_webhook_invalid_token(client):
    resp = client.post("/api/v1/bot/webhook/invalid-token", json={"update_id": 1})
    assert resp.status_code == 404


def test_webhook_known_token(client, db, org):
    org.telegram_bot_token = "123:abc"
    db.session.commit()

    from unittest.mock import patch

    with patch("app.api.bot_webhook._process_update"):
        payload = {
            "update_id": 1,
            "message": {
                "message_id": 1,
                "date": 1000000000,
                "text": "/start",
                "chat": {"id": 1, "type": "private"},
                "from": {"id": 1, "is_bot": False, "first_name": "Test"},
            },
        }
        resp = client.post(
            "/api/v1/bot/webhook/123:abc",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert resp.status_code == 200


# --- Helpers ---


def test_helpers_build_welcome_text():
    from app.bot.helpers import build_welcome_text
    text = build_welcome_text("My Org")
    assert "My Org" in text
    assert "/help" in text


def test_helpers_build_ticket_card_text():
    from app.bot.helpers import build_ticket_card_text
    data = {"event_title": "Test", "event_date": "2026-07-01", "attendee_name": "Alice"}
    text = build_ticket_card_text(data)
    assert "Test" in text
    assert "Alice" in text


def test_helpers_main_keyboard():
    from app.bot.helpers import build_main_keyboard
    keyboard = build_main_keyboard("org-1")
    assert len(keyboard.inline_keyboard) == 2


def test_helpers_events_keyboard():
    from app.bot.helpers import build_events_keyboard
    events = [{"id": "e1", "title": "Event 1"}, {"id": "e2", "title": "Event 2"}]
    keyboard = build_events_keyboard(events)
    assert len(keyboard.inline_keyboard) == 2

