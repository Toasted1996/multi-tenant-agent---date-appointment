import json
from enum import Enum
from app.llm.base import BaseLLM

INTENT_PROMPT = """Analiza el mensaje del usuario y clasifica su intención.
Responde ÚNICAMENTE con un JSON válido en este formato exacto:
{"intent": "NOMBRE_INTENCIÓN"}

Las intenciones válidas son:
- SCHEDULE_APPOINTMENT: quiere agendar una cita
- CHECK_AVAILABILITY: pregunta por disponibilidad de horarios
- CANCEL_APPOINTMENT: quiere cancelar una cita existente
- FAQ_QUERY: hace una pregunta sobre el negocio (precios, servicios, dirección, horarios)
- HUMAN_ESCALATION: quiere hablar con una persona humana
- GREETING: saludo inicial sin intención clara
- DELETE_MY_DATA: quiere eliminar sus datos personales del sistema
- OUT_OF_SCOPE: cualquier otra cosa no relacionada con agendamiento

Solo responde el JSON, nada más. Sin explicaciones."""


class Intent(str, Enum):
    SCHEDULE_APPOINTMENT = "SCHEDULE_APPOINTMENT"
    CHECK_AVAILABILITY = "CHECK_AVAILABILITY"
    CANCEL_APPOINTMENT = "CANCEL_APPOINTMENT"
    FAQ_QUERY = "FAQ_QUERY"
    HUMAN_ESCALATION = "HUMAN_ESCALATION"
    GREETING = "GREETING"
    DELETE_MY_DATA = "DELETE_MY_DATA"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"


class IntentClassifier:
    def __init__(self, llm: BaseLLM):
        self._llm = llm

    async def classify(self, user_message: str) -> Intent:
        try:
            response = await self._llm.chat(
                system_prompt=INTENT_PROMPT,
                user_message=user_message,
            )
            data = json.loads(response.content.strip())
            return Intent(data["intent"])
        except (json.JSONDecodeError, KeyError, ValueError):
            return Intent.OUT_OF_SCOPE
