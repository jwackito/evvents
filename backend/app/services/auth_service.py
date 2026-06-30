from __future__ import annotations

import uuid

import bcrypt
from sqlalchemy import select

from app.exceptions import ConflictError, ValidationError
from app.extensions import db
from app.models.user import User, UserRole


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def create_user(
    email: str,
    password: str,
    name: str,
    role: UserRole = UserRole.OPERATOR,
    organization_id: uuid.UUID | None = None,
) -> User:
    existing = db.session.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if existing:
        raise ConflictError("Email already registered")

    user = User(
        id=uuid.uuid4(),
        email=email,
        password_hash=hash_password(password),
        name=name,
        role=role,
        organization_id=organization_id,
    )
    db.session.add(user)
    db.session.commit()
    return user


def authenticate(email: str, password: str) -> User | None:
    user = db.session.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if not user or not verify_password(password, user.password_hash):
        return None
    return user


def get_user_by_id(user_id: uuid.UUID) -> User | None:
    return db.session.get(User, user_id)
