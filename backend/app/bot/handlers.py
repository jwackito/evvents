from __future__ import annotations

import io
import structlog

import qrcode
from telegram import Update
from telegram.ext import CallbackContext, CommandHandler

from app.bot.helpers import (
    build_events_keyboard,
    build_main_keyboard,
    build_ticket_card_text,
    build_tickets_keyboard,
    build_welcome_text,
)
from app.services.telegram_bot_service import (
    get_attendee_tickets,
    get_org_events,
    link_attendee,
)

logger = structlog.get_logger()


async def _start(update: Update, context: CallbackContext) -> None:
    org_id = context.bot_data.get("org_id", "")
    org_name = context.bot_data.get("org_name", "Evvents")
    text = build_welcome_text(org_name)
    keyboard = build_main_keyboard(org_id)
    await update.message.reply_text(text, reply_markup=keyboard)


async def _link(update: Update, context: CallbackContext) -> None:
    if not context.args:
        await update.message.reply_text(
            "Please provide your link code. Example:\n/link abc123"
        )
        return

    link_code = context.args[0]
    chat_id = update.effective_chat.id

    from app import create_app
    from app.extensions import db

    app = create_app()
    with app.app_context():
        attendee = link_attendee(link_code, chat_id)

    if attendee is None:
        await update.message.reply_text(
            "Invalid link code. Check your ticket or order confirmation for the correct code."
        )
    else:
        await update.message.reply_text(
            f"✅ Successfully linked! Welcome {attendee.name}.\n"
            "Use /my_tickets to view your tickets."
        )


async def _my_tickets(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id

    from app import create_app

    app = create_app()
    with app.app_context():
        tickets = get_attendee_tickets(chat_id)

    if not tickets:
        await update.message.reply_text(
            "No tickets found. Have you linked your account?\n"
            "Use /link <code> to link your tickets."
        )
        return

    if len(tickets) == 1:
        text = build_ticket_card_text(tickets[0])
        qr_bytes = _generate_qr(tickets[0]["qr_hash"])
        await update.message.reply_photo(
            photo=qr_bytes,
            caption=text,
        )
    else:
        text = f"You have {len(tickets)} tickets:"
        keyboard = build_tickets_keyboard(tickets)
        await update.message.reply_text(text, reply_markup=keyboard)


async def _events(update: Update, context: CallbackContext) -> None:
    org_id = context.bot_data.get("org_id", "")

    from app import create_app
    from app.extensions import db

    app = create_app()
    with app.app_context():
        from app.models.organization import Organization

        org = db.session.get(Organization, org_id)
        if org is None:
            await update.message.reply_text("No events available.")
            return
        events = get_org_events(org.id)

    if not events:
        await update.message.reply_text("No upcoming events at the moment.")
        return

    text = "Upcoming events:\n" + "\n".join(
        f"• {e['title']} — {e['date'][:10]}" for e in events
    )
    keyboard = build_events_keyboard(events)
    await update.message.reply_text(text, reply_markup=keyboard)


def _generate_qr(data: str) -> io.BytesIO:
    qr = qrcode.make(data)
    buf = io.BytesIO()
    qr.save(buf, format="PNG")
    buf.seek(0)
    return buf


def get_handlers() -> list[CommandHandler]:
    return [
        CommandHandler("start", _start),
        CommandHandler("link", _link),
        CommandHandler("my_tickets", _my_tickets),
        CommandHandler("events", _events),
    ]
