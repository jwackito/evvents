from __future__ import annotations

import uuid

import click
from flask import current_app
from sqlalchemy import select

from app.extensions import db
from app.models.organization import Organization
from app.models.user import User, UserRole
from app.services.auth_service import create_user


def init_app(app):
    app.cli.add_command(seed_command)


@click.command("seed")
def seed_command():
    """Seed the database with initial dev data."""
    with current_app.app_context():
        org = db.session.execute(
            select(Organization).where(Organization.slug == "acme")
        ).scalar_one_or_none()

        if org is None:
            org = Organization(
                id=uuid.uuid4(),
                name="Acme Events",
                slug="acme",
            )
            db.session.add(org)
            db.session.commit()
            click.echo("Created organization: Acme Events")
        else:
            click.echo("Organization already exists, skipping")

        existing = db.session.execute(
            select(User).where(User.email == "admin@evvents.io")
        ).scalar_one_or_none()

        if existing is None:
            create_user(
                email="admin@evvents.io",
                password="12345678",
                name="Admin User",
                role=UserRole.ADMIN,
                organization_id=org.id,
            )
            click.echo("Created admin user: admin@evvents.io / 12345678")
        else:
            click.echo("Admin user already exists, skipping")
