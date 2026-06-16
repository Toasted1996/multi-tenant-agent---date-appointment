import json
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.messaging.telegram import TelegramMessenger
from app.security.middleware import WebhookValidator, RateLimiter
from app.notifications.scheduler import ReminderScheduler
from app.agent.core import AgentCore
from app.llm.ollama import OllamaLLM
from app.db import get_db_client
from config.settings import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()
_apscheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Arranque: iniciar scheduler de recordatorios
    _apscheduler.start()
    logger.info("Scheduler de recordatorios iniciado")
    yield
    # Cierre limpio
    _apscheduler.shutdown(wait=False)
    logger.info("Scheduler detenido")


app = FastAPI(title="Agente de Agendamiento", lifespan=lifespan)
rate_limiter = RateLimiter(max_per_minute=settings.rate_limit_per_minute)
webhook_validator = WebhookValidator(secret_token=settings.telegram_secret_token)


def get_tenant_by_bot_token(bot_token: str) -> dict | None:
    db = get_db_client()
    result = db.table("tenants").select("*").eq("telegram_bot_token", bot_token).execute()
    return result.data[0] if result.data else None


def _register_reminder_job(tenant: dict, messenger: TelegramMessenger) -> None:
    """Registra el job de recordatorios para este tenant si no existe."""
    job_id = f"reminders_{tenant['id']}"
    if not _apscheduler.get_job(job_id):
        reminder_scheduler = ReminderScheduler(db=get_db_client(), messenger=messenger)
        _apscheduler.add_job(
            reminder_scheduler.tick,
            trigger="interval",
            minutes=5,
            id=job_id,
            replace_existing=True,
        )


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

    # Registrar job de recordatorios para este tenant (idempotente)
    _register_reminder_job(tenant, messenger)

    # Delegar al AgentCore
    llm = OllamaLLM(base_url=settings.ollama_base_url, model=settings.ollama_model)
    core = AgentCore(llm=llm, messenger=messenger, tenant=tenant)
    await core.handle(incoming)

    return {"ok": True}


@app.get("/health")
async def health():
    return {"status": "ok", "scheduler_running": _apscheduler.running}
