from __future__ import annotations

import structlog
from flask import Flask

from app.plugins.base import AuthProvider, NotificationChannel, PaymentProvider, PluginBase

logger = structlog.get_logger()


class PluginRegistry:
    def __init__(self) -> None:
        self._plugins: list[PluginBase] = []

    def register(self, plugin: PluginBase) -> None:
        self._plugins.append(plugin)
        logger.info("plugin_registered", name=plugin.name, version=plugin.version)

    def register_routes(self, app: Flask) -> None:
        for plugin in self._plugins:
            plugin.register_routes(app)

    def get_payment_providers(self) -> list[PaymentProvider]:
        return [p for p in self._plugins if isinstance(p, PaymentProvider)]

    def get_notification_channels(self) -> list[NotificationChannel]:
        return [p for p in self._plugins if isinstance(p, NotificationChannel)]

    def get_auth_providers(self) -> list[AuthProvider]:
        return [p for p in self._plugins if isinstance(p, AuthProvider)]

    def all(self) -> list[PluginBase]:
        return list(self._plugins)
