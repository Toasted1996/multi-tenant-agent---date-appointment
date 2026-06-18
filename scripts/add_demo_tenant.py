"""
Inserta un tenant de demo en Supabase para la primera prueba.

Uso:
    python scripts/add_demo_tenant.py

Requiere que .env tenga SUPABASE_URL y SUPABASE_KEY configurados
y que el schema SQL ya haya sido ejecutado en Supabase.
"""
from dotenv import load_dotenv
load_dotenv()

from supabase import create_client
import os

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


def add_tenant() -> None:
    if not all([SUPABASE_URL, SUPABASE_KEY, BOT_TOKEN]):
        print("ERROR: Configura SUPABASE_URL, SUPABASE_KEY y TELEGRAM_BOT_TOKEN en .env")
        return

    db = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Verificar si ya existe un tenant con este bot token
    existing = db.table("tenants").select("id").eq("telegram_bot_token", BOT_TOKEN).execute()
    if existing.data:
        print(f"✅ Ya existe un tenant con este bot token: {existing.data[0]['id']}")
        return

    tenant = {
        "name": "PetShop Demo",
        "niche": "grooming",
        "telegram_bot_token": BOT_TOKEN,
        "escalation_contact": "",   # Reemplaza con tu Telegram user ID numérico
        "plan_tier": "free",
    }

    result = db.table("tenants").insert(tenant).execute()
    if result.data:
        t = result.data[0]
        print(f"✅ Tenant creado exitosamente")
        print(f"   ID:     {t['id']}")
        print(f"   Nombre: {t['name']}")
        print(f"   Nicho:  {t['niche']}")
        print()
        print("💡 Para cambiar el nicho o nombre, edita este script antes de ejecutarlo.")
        print("   Nichos disponibles: grooming, veterinary, boarding, barbershop,")
        print("                       cosmetics, dental, salon, medical")
    else:
        print("❌ Error al crear el tenant")


if __name__ == "__main__":
    add_tenant()
