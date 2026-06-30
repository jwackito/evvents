from __future__ import annotations

from app.plugins.base import PaymentProvider, PluginBase
from app.plugins.registry import PluginRegistry


class MockPaymentPlugin(PaymentProvider):
    name = "mock-pay"
    version = "0.1.0"

    def charge(self, amount, **kwargs):
        return {}

    def refund(self, transaction_id, **kwargs):
        return {}

    def validate(self, **kwargs):
        return True

    def handle_webhook(self, payload, headers=None):
        return {}


class AnotherPlugin(PluginBase):
    name = "another"
    version = "0.1.0"


def test_register():
    reg = PluginRegistry()
    p = MockPaymentPlugin()
    reg.register(p)
    assert p in reg.all()


def test_get_payment_providers():
    reg = PluginRegistry()
    reg.register(MockPaymentPlugin())
    reg.register(AnotherPlugin())
    providers = reg.get_payment_providers()
    assert len(providers) == 1
    assert providers[0].name == "mock-pay"


def test_get_notification_channels_empty():
    reg = PluginRegistry()
    assert reg.get_notification_channels() == []


def test_get_auth_providers_empty():
    reg = PluginRegistry()
    assert reg.get_auth_providers() == []


def test_all_returns_copy():
    reg = PluginRegistry()
    reg.register(MockPaymentPlugin())
    all_plugins = reg.all()
    all_plugins.clear()
    assert len(reg.all()) == 1


def test_multiple_plugins():
    reg = PluginRegistry()
    reg.register(MockPaymentPlugin())
    reg.register(AnotherPlugin())
    assert len(reg.all()) == 2
