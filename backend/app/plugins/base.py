from __future__ import annotations

from abc import ABC, abstractmethod


class PluginBase(ABC):
    name: str = ""
    version: str = "0.1.0"

    def register_routes(self, app) -> None:
        pass


class PaymentProvider(PluginBase):
    @abstractmethod
    def charge(self, amount: int, currency: str, **kwargs) -> dict:
        ...

    @abstractmethod
    def refund(self, transaction_id: str, **kwargs) -> dict:
        ...

    @abstractmethod
    def validate(self, **kwargs) -> bool:
        ...

    @abstractmethod
    def handle_webhook(self, payload: dict, headers: dict | None = None) -> dict:
        ...


class NotificationChannel(PluginBase):
    @abstractmethod
    def send(self, recipient: str, message: str, **kwargs) -> dict:
        ...

    @abstractmethod
    def validate_config(self, config: dict) -> bool:
        ...


class AuthProvider(PluginBase):
    @abstractmethod
    def authenticate(self, **kwargs) -> dict:
        ...

    @abstractmethod
    def get_login_url(self) -> str:
        ...

    @abstractmethod
    def get_user_info(self, token: str) -> dict:
        ...
