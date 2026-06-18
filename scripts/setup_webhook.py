"""
Registra el webhook de Telegram apuntando a la URL pública de ngrok.

Uso:
    python scripts/setup_webhook.py <ngrok_url>

Ejemplo:
    python scripts/setup_webhook.py https://abc123.ngrok-free.app
"""
import sys
import httpx
from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
SECRET_TOKEN = os.getenv("TELEGRAM_SECRET_TOKEN")


def set_webhook(ngrok_url: str) -> None:
    if not BOT_TOKEN or not SECRET_TOKEN:
        print("ERROR: TELEGRAM_BOT_TOKEN y TELEGRAM_SECRET_TOKEN deben estar en .env")
        sys.exit(1)

    webhook_url = f"{ngrok_url.rstrip('/')}/webhook/{BOT_TOKEN}/{SECRET_TOKEN}"

    response = httpx.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook",
        json={
            "url": webhook_url,
            "secret_token": SECRET_TOKEN,
            "allowed_updates": ["message"],
            "drop_pending_updates": True,
        },
    )
    data = response.json()

    if data.get("ok"):
        print(f"✅ Webhook registrado exitosamente")
        print(f"   URL: {webhook_url}")
    else:
        print(f"❌ Error al registrar webhook: {data}")
        sys.exit(1)


def get_webhook_info() -> None:
    response = httpx.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo")
    data = response.json()
    print("\nEstado actual del webhook:")
    print(f"  URL: {data['result'].get('url', 'No configurado')}")
    print(f"  Pending updates: {data['result'].get('pending_update_count', 0)}")
    last_error = data['result'].get('last_error_message')
    if last_error:
        print(f"  Último error: {last_error}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python scripts/setup_webhook.py <ngrok_url>")
        print("Ejemplo: python scripts/setup_webhook.py https://abc123.ngrok-free.app")
        sys.exit(1)

    ngrok_url = sys.argv[1]
    set_webhook(ngrok_url)
    get_webhook_info()
