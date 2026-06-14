import pytest
from unittest.mock import AsyncMock
from app.agent.entities import EntityExtractor, ExtractedEntities
from app.llm.base import LLMResponse


class TestExtractedEntities:
    def test_all_fields_default_to_none(self):
        e = ExtractedEntities()
        assert e.datetime_str is None
        assert e.service is None
        assert e.pet_name is None
        assert e.rut is None
        assert e.phone is None
        assert e.email is None
        assert e.name is None
        assert e.reason is None


class TestEntityExtractor:
    @pytest.mark.asyncio
    async def test_extracts_service_and_pet_name(self):
        mock_llm = AsyncMock()
        mock_llm.chat = AsyncMock(return_value=LLMResponse(
            content='{"datetime_str": null, "service": "baño", "pet_name": "Luna", "rut": null, "phone": null, "email": null, "name": null, "reason": null}',
            raw={}
        ))
        extractor = EntityExtractor(llm=mock_llm)
        result = await extractor.extract("El baño de mi perra Luna")
        assert result.service == "baño"
        assert result.pet_name == "Luna"

    @pytest.mark.asyncio
    async def test_extracts_datetime(self):
        mock_llm = AsyncMock()
        mock_llm.chat = AsyncMock(return_value=LLMResponse(
            content='{"datetime_str": "2026-06-20 15:00", "service": null, "pet_name": null, "rut": null, "phone": null, "email": null, "name": null, "reason": null}',
            raw={}
        ))
        extractor = EntityExtractor(llm=mock_llm)
        result = await extractor.extract("Para el viernes a las 3 de la tarde")
        assert result.datetime_str == "2026-06-20 15:00"

    @pytest.mark.asyncio
    async def test_extracts_rut(self):
        mock_llm = AsyncMock()
        mock_llm.chat = AsyncMock(return_value=LLMResponse(
            content='{"datetime_str": null, "service": null, "pet_name": null, "rut": "12.345.678-9", "phone": null, "email": null, "name": null, "reason": null}',
            raw={}
        ))
        extractor = EntityExtractor(llm=mock_llm)
        result = await extractor.extract("Mi RUT es 12.345.678-9")
        assert result.rut == "12.345.678-9"

    @pytest.mark.asyncio
    async def test_extracts_name_and_email(self):
        mock_llm = AsyncMock()
        mock_llm.chat = AsyncMock(return_value=LLMResponse(
            content='{"datetime_str": null, "service": null, "pet_name": null, "rut": null, "phone": null, "email": "juan@example.com", "name": "Juan Pérez", "reason": null}',
            raw={}
        ))
        extractor = EntityExtractor(llm=mock_llm)
        result = await extractor.extract("Me llamo Juan Pérez, mi correo es juan@example.com")
        assert result.name == "Juan Pérez"
        assert result.email == "juan@example.com"

    @pytest.mark.asyncio
    async def test_extracts_reason_for_medical_niche(self):
        mock_llm = AsyncMock()
        mock_llm.chat = AsyncMock(return_value=LLMResponse(
            content='{"datetime_str": null, "service": null, "pet_name": null, "rut": null, "phone": null, "email": null, "name": null, "reason": "dolor de muelas"}',
            raw={}
        ))
        extractor = EntityExtractor(llm=mock_llm)
        result = await extractor.extract("Tengo dolor de muelas")
        assert result.reason == "dolor de muelas"

    @pytest.mark.asyncio
    async def test_returns_empty_entities_on_invalid_json(self):
        mock_llm = AsyncMock()
        mock_llm.chat = AsyncMock(return_value=LLMResponse(
            content="esto no es JSON", raw={}
        ))
        extractor = EntityExtractor(llm=mock_llm)
        result = await extractor.extract("texto cualquiera")
        assert isinstance(result, ExtractedEntities)
        assert result.rut is None
        assert result.service is None

    @pytest.mark.asyncio
    async def test_prompt_includes_todays_date(self):
        mock_llm = AsyncMock()
        mock_llm.chat = AsyncMock(return_value=LLMResponse(
            content='{"datetime_str": null, "service": null, "pet_name": null, "rut": null, "phone": null, "email": null, "name": null, "reason": null}',
            raw={}
        ))
        extractor = EntityExtractor(llm=mock_llm)
        await extractor.extract("hola")
        call_kwargs = mock_llm.chat.call_args.kwargs
        from datetime import date
        assert date.today().isoformat() in call_kwargs["system_prompt"]
