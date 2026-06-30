from __future__ import annotations

import pytest

from app.plugins.base import AuthProvider, NotificationChannel, PaymentProvider, PluginBase


class ConcretePlugin(PluginBase):
    name = "test"
    version = "1.0.0"

    def register_routes(self, app) -> None:
        pass


def test_plugin_base_can_instantiate():
    p = ConcretePlugin()
    assert isinstance(p, PluginBase)


def test_plugin_base_defaults():
    p = ConcretePlugin()
    assert p.register_routes(None) is None


def test_concrete_plugin():
    p = ConcretePlugin()
    assert p.name == "test"
    assert p.version == "1.0.0"


def test_payment_provider_raises():
    p = PaymentProvider
    for method in ["charge", "refund", "validate", "handle_webhook"]:
        assert getattr(p, method).__isabstractmethod__


def test_notification_channel_raises():
    p = NotificationChannel
    for method in ["send", "validate_config"]:
        assert getattr(p, method).__isabstractmethod__


def test_auth_provider_raises():
    p = AuthProvider
    for method in ["authenticate", "get_login_url", "get_user_info"]:
        assert getattr(p, method).__isabstractmethod__
