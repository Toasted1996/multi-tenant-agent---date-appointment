import json
import logging
from fastapi import FastAPI, Request, HTTPException
from app.messaging.telegram import TelegramMessenger
from app.security.middleware import WebhookValidator, RateLimiter
from app.db import get_db_client
from config.settings import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Agente de Agendamiento")
settings = get_settings()
rate_limiter = RateLimiter(max_per_minute=settings.rate_limit_per_minute)
webhook_validator = WebhookValidator(secret_token=settings.telegram_secret_token)


def get_tenant_by_bot_token(bot_token: str) -> dict | None:
    db = get_db_client()
    result = db.table("tenants").select("*").eq("telegram_bot_token", bot_token).execute()
    return result.data[0] if result.data else None


@app.post("/webhook/{bot_token}/{secret_token}")
async def telegram_webhook(bot_token: str, secret_token: str, request: Request):
    if secret_token != settings.telegram_secret_token:
        raise HTTPException(status_code=403, detail="Forbidden")

    body = await request.body()

    telegram_sig = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    if not webhook_validator.is_valid(body, telegram_sig):
        raise HTTPException(status_code=403, detail="Invalid signature")

    payload = json.loads(body)

    tenant = get_tenant_by_bot_token(bot_token)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    messenger = TelegramMessenger(bot_token=bot_token)
    incoming = messenger.extract_message(payload, bot_token=bot_token)

    if not rate_limiter.allow(str(incoming.user_id)):
        await messenger.send_message(
            incoming.user_id,
            "Has enviado demasiados mensajes. Por favor espera un momento.",
        )
        return {"ok": True}

    # Delegación al AgentCore — se implementa en Tarea 9
    logger.info(f"Mensaje recibido de {incoming.user_id}: {incoming.text}")
    await messenger.send_message(incoming.user_id, "Hola, el agente está en construcción.")

    return {"ok": True}


@app.get("/health")
async def health():
    return {"status": "ok"}
