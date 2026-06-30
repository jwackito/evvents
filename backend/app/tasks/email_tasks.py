from __future__ import annotations

import structlog

from app.queue import task_queue

logger = structlog.get_logger()


def send_magic_link(email: str, token: str, base_url: str) -> None:
    task_queue.enqueue(
        "app.tasks.email_tasks.send_magic_link_job",
        email,
        token,
        base_url,
    )


def send_magic_link_job(email: str, token: str, base_url: str) -> dict:
    from app import create_app
    from app.services.email_service import send_magic_link_email

    app = create_app()
    with app.app_context():
        result = send_magic_link_email(email, token, base_url)
        logger.info("magic_link_job_complete", email=email, provider=result.get("provider"))
        return result
