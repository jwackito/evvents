from __future__ import annotations

import asyncio
import structlog

from telegram.ext import Application

from app.bot.handlers import get_handlers
from app.services.telegram_bot_service import get_bot_token_orgs

logger = structlog.get_logger()


async def main() -> None:
    from app import create_app

    app = create_app()
    with app.app_context():
        orgs = get_bot_token_orgs()

    if not orgs:
        logger.warning("no_bot_orgs_found", message="No organizations with bot tokens configured")
        return

    apps = []
    for org in orgs:
        bot_app = Application.builder().token(org.telegram_bot_token).build()
        bot_app.bot_data["org_id"] = str(org.id)
        bot_app.bot_data["org_name"] = org.name
        for handler in get_handlers():
            bot_app.add_handler(handler)

        await bot_app.initialize()
        await bot_app.start()
        apps.append(bot_app)
        logger.info("bot_started", org_id=str(org.id), org_name=org.name)

    logger.info("all_bots_running", count=len(apps))

    try:
        await asyncio.Event().wait()
    finally:
        for bot_app in apps:
            await bot_app.stop()
            await bot_app.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
