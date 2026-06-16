import logging
from datetime import datetime, timezone
from app.messaging.base import IncomingMessage, BaseMessenger
from app.llm.base import BaseLLM
from app.agent.intent import IntentClassifier, Intent
from app.agent.entities import EntityExtractor
from app.agent.state import ConversationStateMachine
from app.agent.escalation import EscalationHandler
from app.security.middleware import FernetCipher
from app.db import get_db_client
from data.niche_config import get_niche_config
from config.settings import get_settings

logger = logging.getLogger(__name__)

CONSENT_KEYWORDS = {"sí", "si", "s", "yes", "acepto", "ok", "dale", "claro"}
CONFIRM_KEYWORDS = {"sí", "si", "s", "yes", "confirmo", "ok", "dale", "claro"}
DENY_KEYWORDS = {"no", "n", "nop", "nope", "cancelar"}


class AgentCore:
    def __init__(self, llm: BaseLLM, messenger: BaseMessenger, tenant: dict):
        self._llm = llm
        self._messenger = messenger
        self._tenant = tenant
        self._classifier = IntentClassifier(llm)
        self._extractor = EntityExtractor(llm)
        self._state_machine = ConversationStateMachine()
        self._escalation = EscalationHandler(messenger)
        settings = get_settings()
        self._cipher = FernetCipher(key=settings.fernet_encryption_key)
        self._db = get_db_client()

    async def handle(self, incoming: IncomingMessage) -> None:
        tenant_id = self._tenant["id"]
        niche_cfg = get_niche_config(self._tenant["niche"])

        client = self._get_or_create_client(tenant_id, incoming)
        conversation = self._get_or_create_conversation(tenant_id, client["id"])
        current_state = conversation["state"]
        context = dict(conversation.get("context_json") or {})

        intent = await self._classifier.classify(incoming.text)
        logger.info(f"[tenant={tenant_id}] user={incoming.user_id} state={current_state} intent={intent}")

        # --- Intents que se manejan sin importar el estado ---
        if intent == Intent.HUMAN_ESCALATION:
            await self._escalation.escalate(
                db=self._db,
                tenant_id=tenant_id,
                conversation_id=conversation["id"],
                client_user_id=incoming.user_id,
                escalation_contact=self._tenant.get("escalation_contact", ""),
                reason="El cliente solicitó hablar con una persona",
                conversation_summary=f"Estado: {current_state}\nContexto: {context}",
            )
            self._update_state(conversation["id"], "escalated", context)
            return

        if intent == Intent.DELETE_MY_DATA:
            self._anonymize_client(client["id"], tenant_id)
            await self._messenger.send_message(
                incoming.user_id,
                "Tus datos personales han sido eliminados de nuestro sistema ✅",
            )
            return

        # --- Extracción de entidades y fusión al contexto ---
        entities = await self._extractor.extract(incoming.text)
        context = self._merge_entities(context, entities, niche_cfg)

        client_registered = client.get("consent_accepted_at") is not None

        # --- Manejo de consentimiento ---
        if current_state == "collecting_consent":
            if incoming.text.strip().lower() in CONSENT_KEYWORDS:
                context["consent"] = True
                self._register_consent(client["id"])
                client_registered = True
            else:
                prompt = self._state_machine.get_prompt(
                    "collecting_consent", tenant_name=self._tenant["name"]
                )
                await self._messenger.send_message(incoming.user_id, prompt)
                return

        # --- Manejo de confirmación de cita ---
        if current_state == "confirming":
            if incoming.text.strip().lower() in CONFIRM_KEYWORDS:
                await self._messenger.send_message(
                    incoming.user_id,
                    self._state_machine.get_prompt("scheduled"),
                )
                self._update_state(conversation["id"], "scheduled", context)
                return
            elif incoming.text.strip().lower() in DENY_KEYWORDS:
                await self._messenger.send_message(
                    incoming.user_id,
                    "Entendido, no se agendó la cita. ¿Deseas elegir otra fecha o servicio?",
                )
                self._update_state(conversation["id"], "collecting_service", context)
                return

        # --- Avanzar en la máquina de estados ---
        requires_entity = niche_cfg.get("requires_entity", False)
        next_state = self._state_machine.next_state(
            current=current_state,
            client_registered=client_registered,
            context=context,
            requires_entity=requires_entity,
        )

        # Saltar estados que ya tienen datos en el contexto
        next_state = self._skip_collected_states(next_state, context, requires_entity)

        # --- Generar respuesta ---
        response_text = self._build_response(next_state, context, niche_cfg)
        self._update_state(conversation["id"], next_state, context)
        await self._messenger.send_message(incoming.user_id, response_text)

    def _skip_collected_states(self, state: str, context: dict, requires_entity: bool) -> str:
        """Avanza automáticamente si el dato del estado actual ya está en el contexto."""
        skip_map = {
            "collecting_name": "name",
            "collecting_rut": "rut",
            "collecting_phone": "phone",
            "collecting_email": "email",
            "collecting_service": "service",
            "collecting_entity": "pet_name",
            "collecting_datetime": "datetime_str",
        }
        while state in skip_map and context.get(skip_map[state]):
            state = self._state_machine.next_state(
                state, client_registered=True, context=context, requires_entity=requires_entity
            )
        return state

    def _build_response(self, state: str, context: dict, niche_cfg: dict) -> str:
        entity_label = niche_cfg.get("entity_label") or "entidad"
        entity_line = f"🐾 {entity_label.capitalize()}: {context.get('pet_name', '')}\n" if context.get("pet_name") else ""
        services_str = "\n".join(f"• {s}" for s in niche_cfg.get("services", []))

        return self._state_machine.get_prompt(
            state,
            tenant_name=self._tenant["name"],
            services=services_str,
            entity_label=entity_label,
            entity_line=entity_line,
            service=context.get("service", ""),
            datetime_str=context.get("datetime_str", ""),
        )

    def _get_or_create_client(self, tenant_id: str, incoming: IncomingMessage) -> dict:
        result = (
            self._db.table("clients")
            .select("*")
            .eq("tenant_id", tenant_id)
            .eq("telegram_user_id", incoming.user_id)
            .execute()
        )
        if result.data:
            return result.data[0]
        new_client = {
            "tenant_id": tenant_id,
            "telegram_user_id": incoming.user_id,
            "name": incoming.username or "",
        }
        return self._db.table("clients").insert(new_client).execute().data[0]

    def _get_or_create_conversation(self, tenant_id: str, client_id: str) -> dict:
        result = (
            self._db.table("conversations")
            .select("*")
            .eq("tenant_id", tenant_id)
            .eq("client_id", client_id)
            .execute()
        )
        if result.data:
            return result.data[0]
        new_conv = {
            "tenant_id": tenant_id,
            "client_id": client_id,
            "state": "idle",
            "context_json": {},
        }
        return self._db.table("conversations").insert(new_conv).execute().data[0]

    def _update_state(self, conv_id: str, state: str, context: dict) -> None:
        self._db.table("conversations").update({
            "state": state,
            "context_json": context,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", conv_id).execute()

    def _register_consent(self, client_id: str) -> None:
        self._db.table("clients").update({
            "consent_accepted_at": datetime.now(timezone.utc).isoformat(),
            "consent_version": "1.0",
        }).eq("id", client_id).execute()

    def _anonymize_client(self, client_id: str, tenant_id: str) -> None:
        self._db.table("clients").update({
            "name": "ANONIMIZADO",
            "rut_encrypted": None,
            "phone_encrypted": None,
            "email_encrypted": None,
        }).eq("id", client_id).eq("tenant_id", tenant_id).execute()

    def _merge_entities(self, context: dict, entities, niche_cfg: dict) -> dict:
        mapping = {
            "name": entities.name,
            "rut": entities.rut,
            "phone": entities.phone,
            "email": entities.email,
            "service": entities.service,
            "pet_name": entities.pet_name,
            "datetime_str": entities.datetime_str,
            "reason": entities.reason,
        }
        for key, value in mapping.items():
            if value is not None:
                # Cifrar datos sensibles antes de guardar en contexto
                if key in ("rut", "phone", "email"):
                    context[f"{key}_encrypted"] = self._cipher.encrypt(value)
                context[key] = value
        return context
