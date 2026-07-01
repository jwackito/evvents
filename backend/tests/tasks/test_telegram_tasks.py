from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.order import OrderStatus
from app.tasks.telegram_tasks import (
    enqueue_ticket_card,
    send_ticket_card,
    send_ticket_card_job,
)
from tests.factories import (
    AttendeeFactory,
    EventFactory,
    OrderFactory,
    TicketFactory,
    TicketTypeFactory,
)


def test_enqueue_ticket_card(db):
    order_id = str(uuid.uuid4())
    bot_token = "123:abc"

    with patch("app.tasks.telegram_tasks.task_queue.enqueue") as mock_enqueue:
        enqueue_ticket_card(order_id, bot_token)

    mock_enqueue.assert_called_once_with(
        "app.tasks.telegram_tasks.send_ticket_card_job",
        order_id,
        bot_token,
    )


def test_send_ticket_card_sends_photo_and_updates_db(db):
    qr_hash = "a" * 64
    ticket = TicketFactory(qr_hash=qr_hash)
    db.session.commit()

    ticket_data = {
        "event_title": "Test Event",
        "event_date": "2026-07-01",
        "event_location": "Test Venue",
        "attendee_name": "Alice",
        "ticket_type_name": "VIP",
        "qr_hash": qr_hash,
    }

    mock_qr = MagicMock()

    with patch("app.tasks.telegram_tasks.qrcode.make", return_value=mock_qr):
        with patch("telegram.Bot.send_photo", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = MagicMock(message_id=42)

            send_ticket_card(
                chat_id=12345,
                bot_token="test:token",
                ticket_data=ticket_data,
            )

    mock_qr.save.assert_called_once()

    mock_send.assert_called_once()
    _, send_kwargs = mock_send.call_args
    assert send_kwargs["chat_id"] == 12345

    db.session.expire_all()
    updated = db.session.get(type(ticket), ticket.id)
    assert updated.telegram_message_id == 42


def test_send_ticket_card_job_sends_cards_for_linked_attendees(db):
    event = EventFactory(
        title="Test Event",
        date=datetime(2026, 7, 1, 10, 0, tzinfo=timezone.utc),
        location="Test Venue",
    )
    ticket_type = TicketTypeFactory(event=event, name="General")
    attendee = AttendeeFactory(name="Bob", telegram_chat_id=12345)
    order = OrderFactory(event=event, status=OrderStatus.CONFIRMED)
    ticket = TicketFactory(order=order, attendee=attendee, ticket_type=ticket_type)
    db.session.commit()

    with patch("app.tasks.telegram_tasks.send_ticket_card") as mock_send:
        send_ticket_card_job(str(order.id), "test:token")

    mock_send.assert_called_once()
    call_args, _ = mock_send.call_args
    assert call_args[0] == 12345
    assert call_args[1] == "test:token"
    assert call_args[2]["attendee_name"] == "Bob"
    assert call_args[2]["event_title"] == "Test Event"
    assert call_args[2]["event_location"] == "Test Venue"
    assert call_args[2]["qr_hash"] == ticket.qr_hash
    assert call_args[2]["ticket_type_name"] == "General"


def test_send_ticket_card_job_handles_missing_order(db):
    with patch("app.tasks.telegram_tasks.send_ticket_card") as mock_send:
        send_ticket_card_job(str(uuid.uuid4()), "test:token")

    mock_send.assert_not_called()


def test_send_ticket_card_job_skips_unlinked_attendees(db):
    event = EventFactory()
    ticket_type = TicketTypeFactory(event=event)
    attendee = AttendeeFactory(name="Unlinked", telegram_chat_id=None)
    order = OrderFactory(event=event, status=OrderStatus.CONFIRMED)
    TicketFactory(order=order, attendee=attendee, ticket_type=ticket_type)
    db.session.commit()

    with patch("app.tasks.telegram_tasks.send_ticket_card") as mock_send:
        send_ticket_card_job(str(order.id), "test:token")

    mock_send.assert_not_called()


def test_send_ticket_card_job_handles_multiple_tickets(db):
    event = EventFactory()
    ticket_type = TicketTypeFactory(event=event)
    attendee1 = AttendeeFactory(name="Linked1", telegram_chat_id=1001)
    attendee2 = AttendeeFactory(name="Linked2", telegram_chat_id=1002)
    attendee3 = AttendeeFactory(name="Unlinked", telegram_chat_id=None)
    order = OrderFactory(event=event, status=OrderStatus.CONFIRMED)
    TicketFactory(order=order, attendee=attendee1, ticket_type=ticket_type)
    TicketFactory(order=order, attendee=attendee2, ticket_type=ticket_type)
    TicketFactory(order=order, attendee=attendee3, ticket_type=ticket_type)
    db.session.commit()

    with patch("app.tasks.telegram_tasks.send_ticket_card") as mock_send:
        send_ticket_card_job(str(order.id), "test:token")

    assert mock_send.call_count == 2
