from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class LLMResponse:
    content: str
    raw: dict = field(default_factory=dict)


class BaseLLM(ABC):
    @abstractmethod
    async def chat(self, system_prompt: str, user_message: str) -> LLMResponse:
        """Enviar un mensaje al LLM y retornar la respuesta."""
