from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class IncomingMessage:
    user_id: int
    text: str
    tenant_bot_token: str
    username: Optional[str] = None


class BaseMessenger(ABC):
    @abstractmethod
    async def send_message(self, user_id: int, text: str) -> None:
        """Enviar un mensaje de texto al usuario."""

    @abstractmethod
    def extract_message(self, payload: dict, bot_token: str) -> IncomingMessage:
        """Extraer un IncomingMessage del payload raw del proveedor."""
