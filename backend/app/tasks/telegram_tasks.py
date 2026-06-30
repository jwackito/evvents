from __future__ import annotations

import io
import structlog

import qrcode
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

from app.queue import task_queue

logger = structlog.get_logger()


def send_ticket_card(chat_id: int, bot_token: str, ticket_data: dict) -> None:
    import asyncio

    text = (
        f"🎫 {ticket_data.get('event_title', 'Event')}\n"
        f"📅 {ticket_data.get('event_date', '')}\n"
        f"📍 {ticket_data.get('event_location', '')}\n"
        f"👤 {ticket_data.get('attendee_name', '')}\n"
        f"🎟️ {ticket_data.get('ticket_type_name', '')}"
    )

    qr = qrcode.make(ticket_data.get("qr_hash", ""))
    buf = io.BytesIO()
    qr.save(buf, format="PNG")
    buf.seek(0)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Add to Calendar", callback_data="add_calendar")],
    ])

    async def _send():
        bot = Bot(token=bot_token)
        msg = await bot.send_photo(chat_id=chat_id, photo=buf, caption=text, reply_markup=keyboard)

        from sqlalchemy import select
        from app import create_app
        from app.extensions import db
        from app.models.ticket import Ticket

        app = create_app()
        with app.app_context():
            ticket = db.session.execute(
                select(Ticket).where(Ticket.qr_hash == ticket_data["qr_hash"])
            ).scalar_one_or_none()
            if ticket:
                ticket.telegram_message_id = msg.message_id
                db.session.commit()

        logger.info("ticket_card_sent", chat_id=chat_id, message_id=msg.message_id)

    asyncio.run(_send())


def enqueue_ticket_card(order_id: str, bot_token: str) -> None:
    task_queue.enqueue(
        "app.tasks.telegram_tasks.send_ticket_card_job",
        order_id,
        bot_token,
    )


def send_ticket_card_job(order_id: str, bot_token: str) -> None:
    from app import create_app

    app = create_app()
    with app.app_context():
        from sqlalchemy import select
        from app.extensions import db
        from app.models.event import Event, TicketType
        from app.models.order import Order
        from app.models.ticket import Ticket

        order = db.session.get(Order, order_id)
        if order is None:
            logger.warning("order_not_found", order_id=order_id)
            return

        event = db.session.get(Event, order.event_id)
        tickets = db.session.execute(
            select(Ticket).where(Ticket.order_id == order.id)
        ).scalars().all()

        for ticket in tickets:
            tt = db.session.get(TicketType, ticket.ticket_type_id)
            attendee = ticket.attendee
            if attendee is None or attendee.telegram_chat_id is None:
                continue

            ticket_data = {
                "event_title": event.title if event else "",
                "event_date": event.date.isoformat() if event and event.date else "",
                "event_location": event.location or "",
                "attendee_name": attendee.name or "",
                "ticket_type_name": tt.name if tt else "",
                "qr_hash": ticket.qr_hash,
            }
            send_ticket_card(attendee.telegram_chat_id, bot_token, ticket_data)

        logger.info("ticket_cards_sent_for_order", order_id=order_id, count=len(tickets))
