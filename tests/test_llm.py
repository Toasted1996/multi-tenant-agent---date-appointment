import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.llm.base import LLMResponse
from data.niche_config import NICHE_CONFIG, get_niche_config, list_niches


class TestLLMResponse:
    def test_creates_response(self):
        resp = LLMResponse(content="Hola, ¿en qué puedo ayudarte?", raw={})
        assert resp.content == "Hola, ¿en qué puedo ayudarte?"

    def test_raw_defaults_to_empty_dict(self):
        resp = LLMResponse(content="test")
        assert resp.raw == {}


class TestOllamaLLM:
    @pytest.mark.asyncio
    async def test_chat_returns_llm_response(self):
        mock_response_data = {"message": {"content": "Entendido, ¿para qué fecha?"}}

        with patch("app.llm.ollama.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_http_response = MagicMock()
            mock_http_response.json.return_value = mock_response_data
            mock_http_response.raise_for_status = MagicMock()
            mock_client.post = AsyncMock(return_value=mock_http_response)
            MockClient.return_value = mock_client

            from app.llm.ollama import OllamaLLM
            llm = OllamaLLM(base_url="http://localhost:11434", model="llama3.2")
            result = await llm.chat(
                system_prompt="Eres un asistente",
                user_message="Hola",
            )
            assert result.content == "Entendido, ¿para qué fecha?"
            assert isinstance(result, LLMResponse)

    @pytest.mark.asyncio
    async def test_chat_sends_correct_payload(self):
        mock_response_data = {"message": {"content": "ok"}}

        with patch("app.llm.ollama.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_http_response = MagicMock()
            mock_http_response.json.return_value = mock_response_data
            mock_http_response.raise_for_status = MagicMock()
            mock_client.post = AsyncMock(return_value=mock_http_response)
            MockClient.return_value = mock_client

            from app.llm.ollama import OllamaLLM
            llm = OllamaLLM(base_url="http://localhost:11434", model="llama3.2")
            await llm.chat(system_prompt="Sistema", user_message="Usuario")

            call_kwargs = mock_client.post.call_args
            payload = call_kwargs.kwargs["json"]
            assert payload["model"] == "llama3.2"
            assert payload["stream"] is False
            assert payload["messages"][0]["role"] == "system"
            assert payload["messages"][1]["role"] == "user"


class TestNicheConfig:
    def test_grooming_has_required_fields(self):
        cfg = NICHE_CONFIG["grooming"]
        assert "service_type" in cfg["required_fields"]
        assert "entity_name" in cfg["required_fields"]
        assert "datetime" in cfg["required_fields"]

    def test_veterinary_has_reason_field(self):
        assert "reason" in NICHE_CONFIG["veterinary"]["required_fields"]

    def test_all_niches_have_services(self):
        for niche in ["grooming", "veterinary", "boarding", "barbershop", "cosmetics", "dental", "salon", "medical"]:
            assert len(NICHE_CONFIG[niche]["services"]) > 0

    def test_barbershop_does_not_require_entity(self):
        assert NICHE_CONFIG["barbershop"]["requires_entity"] is False

    def test_grooming_requires_entity(self):
        assert NICHE_CONFIG["grooming"]["requires_entity"] is True

    def test_get_niche_config_returns_correct_niche(self):
        cfg = get_niche_config("dental")
        assert cfg["display_name"] == "Centro Odontológico"

    def test_get_niche_config_raises_on_unknown(self):
        with pytest.raises(ValueError, match="Nicho desconocido"):
            get_niche_config("pizza_delivery")

    def test_list_niches_returns_all_eight(self):
        niches = list_niches()
        assert len(niches) == 8
        assert "grooming" in niches
        assert "medical" in niches
