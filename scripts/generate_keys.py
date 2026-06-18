"""
Genera las claves necesarias para el archivo .env.
Ejecutar una sola vez al configurar el proyecto.
"""
import secrets
from cryptography.fernet import Fernet

fernet_key = Fernet.generate_key().decode()
secret_token = secrets.token_hex(32)

print("=" * 60)
print("Copia estos valores en tu archivo .env")
print("=" * 60)
print(f"\nFERNET_ENCRYPTION_KEY={fernet_key}")
print(f"TELEGRAM_SECRET_TOKEN={secret_token}")
print()
