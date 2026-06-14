import json
from dataclasses import dataclass
from datetime import date
from typing import Optional
from app.llm.base import BaseLLM

ENTITY_PROMPT = """Extrae entidades del mensaje del usuario.
Responde ÚNICAMENTE con un JSON válido en este formato exacto (usa null si el dato no aparece):
{{
  "datetime_str": "YYYY-MM-DD HH:MM o null",
  "service": "nombre del servicio mencionado o null",
  "pet_name": "nombre de la mascota o null",
  "rut": "RUT chileno formato 12.345.678-9 o null",
  "phone": "número de teléfono o null",
  "email": "correo electrónico o null",
  "name": "nombre completo de la persona o null",
  "reason": "motivo de consulta médica u odontológica o null"
}}

La fecha de hoy es {today}. Usa esta referencia para convertir fechas relativas como "mañana", "el viernes", "la próxima semana".
Solo responde el JSON, nada más."""


@dataclass
class ExtractedEntities:
    datetime_str: Optional[str] = None
    service: Optional[str] = None
    pet_name: Optional[str] = None
    rut: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None
    reason: Optional[str] = None


class EntityExtractor:
    def __init__(self, llm: BaseLLM):
        self._llm = llm

    async def extract(self, user_message: str) -> ExtractedEntities:
        prompt = ENTITY_PROMPT.format(today=date.today().isoformat())
        try:
            response = await self._llm.chat(
                system_prompt=prompt,
                user_message=user_message,
            )
            data = json.loads(response.content.strip())
            valid_fields = ExtractedEntities.__dataclass_fields__
            return ExtractedEntities(**{k: v for k, v in data.items() if k in valid_fields})
        except (json.JSONDecodeError, TypeError):
            return ExtractedEntities()
