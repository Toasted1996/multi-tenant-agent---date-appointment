import pytest
from unittest.mock import AsyncMock
from app.agent.intent import IntentClassifier, Intent
from app.llm.base import LLMResponse


class TestIntent:
    def test_all_intents_defined(self):
        expected = [
            "SCHEDULE_APPOINTMENT", "CHECK_AVAILABILITY", "CANCEL_APPOINTMENT",
            "FAQ_QUERY", "HUMAN_ESCALATION", "GREETING", "DELETE_MY_DATA", "OUT_OF_SCOPE",
        ]
        for name in expected:
            assert Intent(name) is not None


class TestIntentClassifier:
    @pytest.mark.asyncio
    async def test_classifies_schedule_intent(self):
        mock_llm = AsyncMock()
        mock_llm.chat = AsyncMock(return_value=LLMResponse(
            content='{"intent": "SCHEDULE_APPOINTMENT"}', raw={}
        ))
        classifier = IntentClassifier(llm=mock_llm)
        result = await classifier.classify("Quiero agendar una cita para el viernes")
        assert result == Intent.SCHEDULE_APPOINTMENT

    @pytest.mark.asyncio
    async def test_classifies_faq_intent(self):
        mock_llm = AsyncMock()
        mock_llm.chat = AsyncMock(return_value=LLMResponse(
            content='{"intent": "FAQ_QUERY"}', raw={}
        ))
        classifier = IntentClassifier(llm=mock_llm)
        result = await classifier.classify("¿Cuánto cuesta el baño?")
        assert result == Intent.FAQ_QUERY

    @pytest.mark.asyncio
    async def test_classifies_cancel_intent(self):
        mock_llm = AsyncMock()
        mock_llm.chat = AsyncMock(return_value=LLMResponse(
            content='{"intent": "CANCEL_APPOINTMENT"}', raw={}
        ))
        classifier = IntentClassifier(llm=mock_llm)
        result = await classifier.classify("Necesito cancelar mi cita de mañana")
        assert result == Intent.CANCEL_APPOINTMENT

    @pytest.mark.asyncio
    async def test_classifies_human_escalation(self):
        mock_llm = AsyncMock()
        mock_llm.chat = AsyncMock(return_value=LLMResponse(
            content='{"intent": "HUMAN_ESCALATION"}', raw={}
        ))
        classifier = IntentClassifier(llm=mock_llm)
        result = await classifier.classify("Quiero hablar con una persona")
        assert result == Intent.HUMAN_ESCALATION

    @pytest.mark.asyncio
    async def test_classifies_delete_data(self):
        mock_llm = AsyncMock()
        mock_llm.chat = AsyncMock(return_value=LLMResponse(
            content='{"intent": "DELETE_MY_DATA"}', raw={}
        ))
        classifier = IntentClassifier(llm=mock_llm)
        result = await classifier.classify("Quiero que eliminen mis datos")
        assert result == Intent.DELETE_MY_DATA

    @pytest.mark.asyncio
    async def test_returns_out_of_scope_on_invalid_json(self):
        mock_llm = AsyncMock()
        mock_llm.chat = AsyncMock(return_value=LLMResponse(
            content="respuesta no válida sin JSON", raw={}
        ))
        classifier = IntentClassifier(llm=mock_llm)
        result = await classifier.classify("qwerty gibberish")
        assert result == Intent.OUT_OF_SCOPE

    @pytest.mark.asyncio
    async def test_returns_out_of_scope_on_unknown_intent(self):
        mock_llm = AsyncMock()
        mock_llm.chat = AsyncMock(return_value=LLMResponse(
            content='{"intent": "INTENT_INVENTADA"}', raw={}
        ))
        classifier = IntentClassifier(llm=mock_llm)
        result = await classifier.classify("algo raro")
        assert result == Intent.OUT_OF_SCOPE

    @pytest.mark.asyncio
    async def test_llm_receives_user_message(self):
        mock_llm = AsyncMock()
        mock_llm.chat = AsyncMock(return_value=LLMResponse(
            content='{"intent": "GREETING"}', raw={}
        ))
        classifier = IntentClassifier(llm=mock_llm)
        await classifier.classify("Hola buenas tardes")
        call_kwargs = mock_llm.chat.call_args.kwargs
        assert call_kwargs["user_message"] == "Hola buenas tardes"
