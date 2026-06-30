from __future__ import annotations

from unittest.mock import patch

from app.plugins.base import PluginBase
from app.plugins.loader import discover_plugins, init_plugins


def test_discover_empty(app):
    with patch("app.plugins.loader.entry_points") as mock_eps:
        mock_eps.return_value = []
        plugins = discover_plugins()
        assert plugins == []


def test_discover_with_plugin(app):
    class TestPlugin(PluginBase):
        name = "test"

    mock_ep = type("EntryPoint", (), {
        "name": "test", "value": "test:Plugin",
        "load": lambda self: TestPlugin,
    })()

    with patch("app.plugins.loader.entry_points") as mock_eps:
        mock_eps.return_value = [mock_ep]
        plugins = discover_plugins()
        assert len(plugins) == 1


def test_init_plugins_no_plugins(app):
    with patch("app.plugins.loader.entry_points") as mock_eps:
        mock_eps.return_value = []
        reg = init_plugins(app)
        assert len(reg.all()) == 0


def test_init_plugins_with_mock(app):
    class TestPlugin(PluginBase):
        name = "test"
        version = "0.1.0"

    mock_ep = type("EntryPoint", (), {
        "name": "test", "value": "test:Plugin",
        "load": lambda self: TestPlugin,
    })()

    with patch("app.plugins.loader.entry_points") as mock_eps:
        mock_eps.return_value = [mock_ep]
        reg = init_plugins(app)
        assert len(reg.all()) == 1
        assert reg.all()[0].name == "test"
