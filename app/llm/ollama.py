import httpx
from app.llm.base import BaseLLM, LLMResponse


class OllamaLLM(BaseLLM):
    def __init__(self, base_url: str, model: str):
        self._base_url = base_url.rstrip("/")
        self._model = model

    async def chat(self, system_prompt: str, user_message: str) -> LLMResponse:
        payload = {
            "model": self._model,
            "stream": False,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self._base_url}/api/chat",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return LLMResponse(content=data["message"]["content"], raw=data)
