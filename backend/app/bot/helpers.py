from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def build_welcome_text(org_name: str) -> str:
    return (
        f"Welcome to {org_name}! 🎉\n\n"
        "I can help you with:\n"
        "• Browse upcoming events\n"
        "• Link your tickets to Telegram\n"
        "• View your tickets\n\n"
        "Use the buttons below or type /help to see all commands."
    )


def build_ticket_card_text(data: dict) -> str:
    lines = [
        f"🎫 {data.get('event_title', 'Event')}",
    ]
    if data.get("event_date"):
        lines.append(f"📅 {data['event_date']}")
    if data.get("event_location"):
        lines.append(f"📍 {data['event_location']}")
    if data.get("attendee_name"):
        lines.append(f"👤 {data['attendee_name']}")
    if data.get("ticket_type_name"):
        lines.append(f"🎟️ {data['ticket_type_name']}")
    return "\n".join(lines)


def build_main_keyboard(org_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📋 Events", callback_data=f"events_{org_id}"),
            InlineKeyboardButton("🎟️ My Tickets", callback_data="my_tickets"),
        ],
        [InlineKeyboardButton("🔗 Link Ticket", callback_data="link_prompt")],
    ])


def build_events_keyboard(events: list[dict]) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(e["title"], callback_data=f"event_{e['id']}")]
        for e in events[:8]
    ]
    return InlineKeyboardMarkup(buttons)


def build_tickets_keyboard(tickets: list[dict]) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(
            f"🎫 {t.get('event_title', 'Ticket')[:30]}",
            callback_data=f"ticket_{t['id']}",
        )]
        for t in tickets[:10]
    ]
    return InlineKeyboardMarkup(buttons)
