from __future__ import annotations

import structlog
from flask import Flask
from importlib.metadata import entry_points

from app.plugins.base import PluginBase
from app.plugins.registry import PluginRegistry

logger = structlog.get_logger()

PLUGIN_ENTRY_POINT_GROUP = "tickets.plugins"


def discover_plugins() -> list[type[PluginBase]]:
    eps = entry_points(group=PLUGIN_ENTRY_POINT_GROUP)
    plugins: list[type[PluginBase]] = []
    for ep in eps:
        try:
            cls = ep.load()
            if isinstance(cls, type) and issubclass(cls, PluginBase) and cls is not PluginBase:
                plugins.append(cls)
                logger.info("plugin_discovered", name=ep.name, module=ep.value)
            else:
                logger.warning("plugin_ignored_not_a_plugin_class", name=ep.name, module=ep.value)
        except Exception:
            logger.exception("plugin_load_failed", name=ep.name, module=ep.value)
    return plugins


def init_plugins(app: Flask) -> PluginRegistry:
    registry = PluginRegistry()
    for plugin_cls in discover_plugins():
        instance = plugin_cls()
        registry.register(instance)
    registry.register_routes(app)
    logger.info("plugins_initialized", count=len(registry.all()))
    return registry
