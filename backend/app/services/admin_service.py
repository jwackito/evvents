from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select

from app.exceptions import ConflictError, NotFoundError, ValidationError
from app.extensions import db
from app.models.organization import Organization
from app.models.user import User, UserRole
from app.services.auth_service import hash_password


def list_orgs(page: int = 1, per_page: int = 20) -> dict:
    query = select(Organization).where(Organization.deleted_at.is_(None))

    total = db.session.execute(
        select(func.count(Organization.id)).where(Organization.deleted_at.is_(None))
    ).scalar()

    orgs = db.session.execute(
        query.order_by(Organization.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    ).scalars().all()

    return {
        "data": [_org_to_dict(o) for o in orgs],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


def get_org(org_id: uuid.UUID) -> dict:
    org = db.session.get(Organization, org_id)
    if org is None or org.deleted_at is not None:
        raise NotFoundError("Organization not found")
    return {"data": _org_to_dict(org)}


def create_org(data: dict) -> dict:
    existing = db.session.execute(
        select(Organization).where(Organization.slug == data["slug"])
    ).scalar_one_or_none()
    if existing:
        raise ConflictError("An organization with this slug already exists")

    org = Organization(
        id=uuid.uuid4(),
        name=data["name"],
        slug=data["slug"],
        settings=data.get("settings", {}),
        telegram_bot_token=data.get("telegram_bot_token"),
        telegram_webhook_url=data.get("telegram_webhook_url"),
    )
    db.session.add(org)
    db.session.commit()

    return {"data": _org_to_dict(org)}


def update_org(org_id: uuid.UUID, data: dict) -> dict:
    org = db.session.get(Organization, org_id)
    if org is None or org.deleted_at is not None:
        raise NotFoundError("Organization not found")

    if "slug" in data and data["slug"] != org.slug:
        existing = db.session.execute(
            select(Organization).where(
                Organization.slug == data["slug"],
                Organization.id != org_id,
            )
        ).scalar_one_or_none()
        if existing:
            raise ConflictError("An organization with this slug already exists")

    for field in ("name", "slug", "settings", "telegram_bot_token", "telegram_webhook_url"):
        if field in data:
            setattr(org, field, data[field])

    db.session.commit()
    return {"data": _org_to_dict(org)}


def delete_org(org_id: uuid.UUID) -> None:
    org = db.session.get(Organization, org_id)
    if org is None or org.deleted_at is not None:
        raise NotFoundError("Organization not found")

    org.deleted_at = datetime.now(timezone.utc)
    db.session.commit()


def list_users(page: int = 1, per_page: int = 20) -> dict:
    query = select(User)

    total = db.session.execute(select(func.count(User.id))).scalar()

    users = db.session.execute(
        query.order_by(User.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    ).scalars().all()

    return {
        "data": [_user_to_dict(u) for u in users],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


def get_user(user_id: uuid.UUID) -> dict:
    user = db.session.get(User, user_id)
    if user is None:
        raise NotFoundError("User not found")
    return {"data": _user_to_dict(user)}


def admin_create_user(data: dict) -> dict:
    existing = db.session.execute(
        select(User).where(User.email == data["email"])
    ).scalar_one_or_none()
    if existing:
        raise ConflictError("Email already registered")

    org_id = None
    if "organization_id" in data and data["organization_id"]:
        org_id = uuid.UUID(data["organization_id"])
        org = db.session.get(Organization, org_id)
        if org is None or org.deleted_at is not None:
            raise ValidationError("Organization not found")

    role = UserRole(data.get("role", "operator"))

    user = User(
        id=uuid.uuid4(),
        email=data["email"],
        password_hash=hash_password(data["password"]),
        name=data["name"],
        role=role,
        organization_id=org_id,
    )
    db.session.add(user)
    db.session.commit()

    return {"data": _user_to_dict(user)}


def admin_update_user(user_id: uuid.UUID, data: dict) -> dict:
    user = db.session.get(User, user_id)
    if user is None:
        raise NotFoundError("User not found")

    if "email" in data and data["email"] != user.email:
        existing = db.session.execute(
            select(User).where(User.email == data["email"], User.id != user_id)
        ).scalar_one_or_none()
        if existing:
            raise ConflictError("Email already in use")

    if "organization_id" in data:
        if data["organization_id"]:
            org_id = uuid.UUID(data["organization_id"])
            org = db.session.get(Organization, org_id)
            if org is None or org.deleted_at is not None:
                raise ValidationError("Organization not found")
            user.organization_id = org_id
        else:
            user.organization_id = None

    if "role" in data:
        user.role = UserRole(data["role"])
    if "name" in data:
        user.name = data["name"]
    if "email" in data:
        user.email = data["email"]
    if "password" in data and data["password"]:
        user.password_hash = hash_password(data["password"])

    db.session.commit()
    return {"data": _user_to_dict(user)}


def admin_delete_user(user_id: uuid.UUID) -> None:
    user = db.session.get(User, user_id)
    if user is None:
        raise NotFoundError("User not found")
    if user.role == UserRole.ADMIN:
        admin_count = db.session.execute(
            select(func.count(User.id)).where(User.role == UserRole.ADMIN)
        ).scalar()
        if admin_count <= 1:
            raise ValidationError("Cannot delete the last admin user")

    db.session.delete(user)
    db.session.commit()


def _org_to_dict(org: Organization) -> dict:
    return {
        "id": str(org.id),
        "name": org.name,
        "slug": org.slug,
        "settings": org.settings,
        "telegram_bot_token": org.telegram_bot_token,
        "telegram_webhook_url": org.telegram_webhook_url,
        "created_at": org.created_at.isoformat(),
        "updated_at": org.updated_at.isoformat(),
    }


def _user_to_dict(user: User) -> dict:
    return {
        "id": str(user.id),
        "email": user.email,
        "name": user.name,
        "role": user.role.value,
        "organization_id": str(user.organization_id) if user.organization_id else None,
        "created_at": user.created_at.isoformat(),
        "updated_at": user.updated_at.isoformat(),
    }
