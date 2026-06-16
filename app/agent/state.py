from enum import Enum


class ConversationState(str, Enum):
    IDLE = "idle"
    COLLECTING_CONSENT = "collecting_consent"
    COLLECTING_NAME = "collecting_name"
    COLLECTING_RUT = "collecting_rut"
    COLLECTING_PHONE = "collecting_phone"
    COLLECTING_EMAIL = "collecting_email"
    COLLECTING_SERVICE = "collecting_service"
    COLLECTING_ENTITY = "collecting_entity"
    COLLECTING_DATETIME = "collecting_datetime"
    CONFIRMING = "confirming"
    SCHEDULED = "scheduled"
    CANCELLED = "cancelled"
    ESCALATED = "escalated"


STATE_PROMPTS: dict[str, str] = {
    "collecting_consent": (
        "Hola, soy el asistente virtual de {tenant_name} 👋\n\n"
        "Antes de continuar, necesito tu autorización para guardar tus datos "
        "personales (nombre, RUT, teléfono, correo) con el único fin de gestionar "
        "tus citas.\n\n"
        "Tus datos se almacenan cifrados y no se comparten con terceros.\n\n"
        "¿Aceptas los términos? Responde *SÍ* para continuar."
    ),
    "collecting_name": "¿Cuál es tu nombre completo?",
    "collecting_rut": "¿Cuál es tu RUT? (formato: 12.345.678-9)",
    "collecting_phone": "¿Cuál es tu número de teléfono?",
    "collecting_email": "¿Cuál es tu correo electrónico?",
    "collecting_service": "¿Qué servicio necesitas? Las opciones disponibles son:\n{services}",
    "collecting_entity": "¿Cuál es el nombre de tu {entity_label}?",
    "collecting_datetime": "¿Para qué fecha y hora deseas la cita?\n(Ejemplo: viernes 20 de junio a las 15:00)",
    "confirming": (
        "Perfecto, voy a agendar lo siguiente:\n\n"
        "📋 Servicio: {service}\n"
        "{entity_line}"
        "📅 Fecha y hora: {datetime_str}\n\n"
        "¿Confirmas? Responde *SÍ* o *NO*."
    ),
    "scheduled": "✅ ¡Tu cita está agendada! Te recordaremos antes de la hora. ¿Hay algo más en que pueda ayudarte?",
    "cancelled": "Tu cita ha sido cancelada. Si deseas agendar una nueva, escríbeme cuando quieras.",
}


class ConversationStateMachine:
    def next_state(
        self,
        current: str,
        client_registered: bool,
        context: dict,
        requires_entity: bool = False,
    ) -> str:
        if current == "idle":
            return "collecting_service" if client_registered else "collecting_consent"

        if current == "collecting_consent":
            return "collecting_name" if context.get("consent") else "collecting_consent"

        if current == "collecting_service":
            return "collecting_entity" if requires_entity else "collecting_datetime"

        transitions = {
            "collecting_name": "collecting_rut",
            "collecting_rut": "collecting_phone",
            "collecting_phone": "collecting_email",
            "collecting_email": "collecting_service",
            "collecting_entity": "collecting_datetime",
            "collecting_datetime": "confirming",
        }
        return transitions.get(current, "idle")

    def get_prompt(
        self,
        state: str,
        tenant_name: str = "",
        services: str = "",
        entity_label: str = "mascota",
        entity_line: str = "",
        service: str = "",
        datetime_str: str = "",
        **kwargs,
    ) -> str:
        template = STATE_PROMPTS.get(state, "¿En qué más puedo ayudarte?")
        return template.format(
            tenant_name=tenant_name,
            services=services,
            entity_label=entity_label,
            entity_line=entity_line,
            service=service,
            datetime_str=datetime_str,
            **kwargs,
        )
