from __future__ import annotations

import json
import structlog

from apiflask import APIBlueprint
from flask import request
from telegram import Update
from telegram.ext import Application

from app.bot.handlers import get_handlers
from app.services.telegram_bot_service import get_org_by_bot_token

logger = structlog.get_logger()

bot_webhook_bp = APIBlueprint("bot_webhook", __name__, url_prefix="/api/v1/bot")


@bot_webhook_bp.post("/webhook/<token>")
def bot_webhook(token: str):
    from app import create_app

    app = create_app()
    with app.app_context():
        org = get_org_by_bot_token(token)

    if org is None:
        logger.warning("bot_webhook_unknown_token")
        return {"error": "Invalid token"}, 404

    data = json.loads(request.get_data())
    update = Update.de_json(data, None)

    _process_update(update, str(org.id), org.name, token)

    return {"ok": True}, 200


def _process_update(update: Update, org_id: str, org_name: str, token: str) -> None:
    import asyncio

    bot_app = Application.builder().token(token).build()
    bot_app.bot_data["org_id"] = org_id
    bot_app.bot_data["org_name"] = org_name

    for handler in get_handlers():
        bot_app.add_handler(handler)

    async def _run():
        await bot_app.initialize()
        try:
            await bot_app.process_update(update)
        finally:
            await bot_app.shutdown()

    asyncio.run(_run())
