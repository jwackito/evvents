from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://evvents:evvents@db:5432/evvents"
    redis_url: str = "redis://redis:6379/0"
    secret_key: str = "dev-secret-key-change-me"
    jwt_secret: str = "dev-jwt-secret-change-me"
    jwt_access_expiry: int = 900
    jwt_refresh_expiry: int = 604800
    flask_env: str = "development"
    debug: bool = True

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    def to_flask_config(self) -> dict:
        return {
            "SQLALCHEMY_DATABASE_URI": self.database_url,
            "SECRET_KEY": self.secret_key,
            "DEBUG": self.debug,
            "ENV": self.flask_env,
            "REDIS_URL": self.redis_url,
            "JWT_SECRET": self.jwt_secret,
            "JWT_ACCESS_EXPIRY": self.jwt_access_expiry,
            "JWT_REFRESH_EXPIRY": self.jwt_refresh_expiry,
        }
